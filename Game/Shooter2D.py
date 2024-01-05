import pygame
from pygame import mixer
import os
import random as rd
import csv
import pickle

mixer.init()
pygame.init()

screen_width = 800
screen_height = int(screen_width * 0.8)

screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption('Mario Shooter')

# Set Framerate
clock = pygame.time.Clock()
FPS = 60

# Define Game Variables
gravity = 0.75
scroll_thresh = 200
rows = 16
cols = 150
max_cols = 150
tile_size = screen_height // rows
tile_types = 21
max_levels = 3

screen_scroll = 0
bg_scroll = 0
level = 1
start_game = False
start_intro = False

# Define Player Action Variables
moving_left = False
moving_right = False
shoot = False
grenade = False
grenade_thrown = False


#load music and sound
pygame.mixer.music.load('shooter_game/audio/audio_music2.mp3')
pygame.mixer.music.set_volume(0.3)
pygame.mixer.music.play(-1, 0.0, 5000)
jump_fx = pygame.mixer.Sound('shooter_game/audio/audio_jump.wav')
jump_fx.set_volume(0.5)
shot_fx = pygame.mixer.Sound('shooter_game/audio/audio_shot.wav')
shot_fx.set_volume(0.5)
grenade_fx = pygame.mixer.Sound('shooter_game/audio/audio_grenade.wav')
grenade_fx.set_volume(0.5)
# Load Images
#load button images
start_img = pygame.image.load('shooter_game/img/buttons/start_btn.png').convert_alpha()
exit_img = pygame.image.load('shooter_game/img/buttons/exit_btn.png').convert_alpha()
restart_img = pygame.image.load('shooter_game/img/buttons/restart_btn.png').convert_alpha()
#load background images
pine_img = pygame.image.load('shooter_game/img/background/pine1.png').convert_alpha()
pine2_img = pygame.image.load('shooter_game/img/background/pine2.png').convert_alpha()
mountain_img = pygame.image.load('shooter_game/img/background/mountain.png').convert_alpha()
sky_img = pygame.image.load('shooter_game/img/background/sky_cloud.png').convert_alpha()
# Store Tiles In A List
img_list = []
for x in range(tile_types):
	img = pygame.image.load(f'shooter_game/img/tile/{x}.png').convert_alpha()
	img = pygame.transform.scale(img, (tile_size, tile_size))
	img_list.append(img)
# Bullet
bullet_img = pygame.image.load('shooter_game/img/icons/bullet.png').convert_alpha()
# Grenade
grenade_img = pygame.image.load('shooter_game/img/icons/grenade.png').convert_alpha()
# Pick Up Boxes
health_box_img = pygame.image.load('shooter_game/img/icons/health_box.png').convert_alpha()
ammo_box_img = pygame.image.load('shooter_game/img/icons/ammo_box.png').convert_alpha()
grenade_box_img = pygame.image.load('shooter_game/img/icons/grenade_box.png').convert_alpha()
item_boxes = {
	'Health': health_box_img,
	'Ammo': ammo_box_img,
	'Grenade': grenade_box_img
}

# Define Colours
bg = (144, 201, 120)
red = (255, 0, 0)
white = (255, 255, 255)
green = (0, 255, 0)
black = (0, 0, 0)
pink = (235, 65, 54)

# Define Font
font = pygame.font.SysFont('Futura', 30)

def draw_text(text, font, text_col, x, y):
	img = font.render(text, True, text_col)
	screen.blit(img, (x, y))

def draw_bg():
	screen.fill(bg)
	width = sky_img.get_width()
	for x in range(5):
		screen.blit(sky_img, ((x * width)  - bg_scroll * 0.5, 0))
		screen.blit(mountain_img, ((x * width) - bg_scroll * 0.6, screen_height - mountain_img.get_height() - 300))
		screen.blit(pine_img, ((x * width) - bg_scroll * 0.7, screen_height - pine_img.get_height() - 150))
		screen.blit(pine2_img, ((x * width) - bg_scroll * 0.8, screen_height - pine2_img.get_height()))

#function to reset level
def reset_level():
	enemy_group.empty()
	bullet_group.empty()
	grenade_group.empty()
	explosion_group.empty()
	item_box_group.empty()
	decoration_group.empty()
	water_group.empty()
	exit_group.empty()

	#create empty tile list
	data = []
	for row in range(rows):
		r = [-1] * max_cols
		data.append(r)

	return data

class Soldier(pygame.sprite.Sprite):
	def __init__(self, char_type, x, y, scale, speed, ammo, grenades):
		pygame.sprite.Sprite.__init__(self)
		self.alive = True
		self.char_type = char_type
		self.speed = speed
		self.ammo = ammo
		self.start_ammo = ammo
		self.shoot_cooldown = 0
		self.grenades = grenades
		self.start_grenades = grenades
		self.health = 100
		self.max_health = self.health
		self.direction = 1
		self.vel_y = 0
		self.jump = False
		self.in_air = True
		self.flip = False
		self.animation_list = []
		self.frame_index = 0
		self.action = 0
		self.update_time = pygame.time.get_ticks()
		# Create AI Specific Variables
		self.move_counter = 0
		self.vision = pygame.Rect(0, 0, 150, 20)
		self.idling = False
		self.idling_counter = 0

		# Load All Images For Players
		animation_types = ['idle', 'run', 'jump', 'death']
		for animation in animation_types:
			temp_list = []
			# Count Number Of Files In The Folder
			num_of_frames = len(os.listdir(f'shooter_game/img/{self.char_type}/{animation}'))
			for i in range(num_of_frames):
				img = pygame.image.load(f'shooter_game/img/{self.char_type}/{animation}/{i}.png').convert_alpha()
				img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
				temp_list.append(img)
			self.animation_list.append(temp_list)
		self.image = self.animation_list[self.action][self.frame_index]
		self.rect = self.image.get_rect()
		self.rect.center = (x, y)
		self.width = self.image.get_width()
		self.height = self.image.get_height()

	def update(self):
		self.update_animation()
		self.check_alive()
		# Update Cooldown
		if self.shoot_cooldown > 0:
			self.shoot_cooldown -= 1

	def move(self, moving_left, moving_right):
		# Reset Movment Variables
		screen_scroll = 0
		dx = 0
		dy = 0

		# Assign Movment Variables If Moving Left Or Right
		if moving_left:
			dx = -self.speed
			self.flip = True 
			self.direction = -1
		if moving_right:
			dx = self.speed
			self.flip = False
			self.direction = 1

		# Jump
		if self.jump == True and self.in_air == False:
			self.vel_y = -11
			self.jump = False
			self.in_air = True

		# Aplly Gravity
		self.vel_y += gravity
		if self.vel_y > 10:
			self.vel_y = 10
		dy += self.vel_y

		# Check For Collision
		for tile in world.obstacle_list:
			#check collision in the x direction
			if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
				dx = 0
				#if the AI has hit the wall then make it turn around
				if self.char_type == 'enemy':
					self.direction *= -1
					self.move_counter = 0
			#check collision in the y direction
			if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
				#check if below the ground, i.e. jumping
				if self.vel_y < 0:
					self.vel_y = 0
					dy = tile[1].bottom - self.rect.top
				#check if above the ground, i.e. falling
				elif self.vel_y >= 0:
					self.vel_y = 0
					self.in_air = False
					dy = tile[1].top - self.rect.bottom
		
		#check for collision with water
		if pygame.sprite.spritecollide(self, water_group, False):
			self.health = 0

		#check for collision with exit sign
		level_complete = False
		if pygame.sprite.spritecollide(self, exit_group, False):
			level_complete = True

		#check if fallen off the map
		if self.rect.bottom > screen_height:
			self.health = 0

		#check if player going off the edges of the screen
		if self.char_type == 'soldier':
			if self.rect.left + dx < 0 or self.rect.right + dx > screen_width:
				dx = 0

		# Update Rectangle Position
		self.rect.x += dx
		self.rect.y += dy

		#update scroll based on player position
		if self.char_type == 'soldier':
			if (self.rect.right > screen_width - scroll_thresh and bg_scroll < (world.level_length * tile_size) - screen_width) or (self.rect.left < scroll_thresh and bg_scroll > abs(dx)):
				self.rect.x -= dx
				screen_scroll = dx * -1

		return screen_scroll, level_complete

	def shoot(self):
		if self.shoot_cooldown == 0 and self.ammo > 0:
			self.shoot_cooldown = 20
			bullet = Bullet(self.rect.centerx + (0.75 * self.rect.size[0] * self.direction), self.rect.centery, self.direction)
			bullet_group.add(bullet)
			self.ammo -= 1
			shot_fx.play()

	# Define AI
	def ai(self):
		if self.alive and player.alive:
			if self.idling == False and rd.randint(1, 200) == 1:
				self.update_action(0)# 0 : idle
				self.idling = True
				self.idling_counter = 50
			# Check If The AI Is Near The Player
			if self.vision.colliderect(player.rect):
				# Stop Running And Face The Player
				self.update_action(0)# 0 : idle
				# Shoot
				self.shoot()
			else:
				if self.idling == False:
					if self.direction == 1:
						ai_moving_right = True
					else:
						ai_moving_right = False
					ai_moving_left = not ai_moving_right
					self.move(ai_moving_left, ai_moving_right)
					self.update_action(1)# 1 : run
					self.move_counter += 1
					# Update AI Vision As The Enemy Moves
					self.vision.center = (self.rect.centerx + 75 * self.direction, self.rect.centery)

					if self.move_counter > tile_size:
						self.direction *= -1
						self.move_counter *= -1
				else:
					self.idling_counter -= 1
					if self.idling_counter == 0:
						self.idling = False

		#scroll
		self.rect.x += screen_scroll

	# Function That Update The Animation Of The Soldier Or The Enemy
	def update_animation(self):
		# Update Animation
		animation_cooldown = 100
		# Update Image Depending On Current Frame
		self.image = self.animation_list[self.action][self.frame_index]
		# Check If Enough Time Has Passed Since The Last Update
		if pygame.time.get_ticks() - self.update_time > animation_cooldown:
			self.update_time = pygame.time.get_ticks()
			self.frame_index += 1
		# If The Animation Has Run Out Then Reset Back To Normal Start
		if self.frame_index >= len(self.animation_list[self.action]):
			if self.action == 3:
				self.frame_index = len(self.animation_list[self.action]) - 1
			else:
				self.frame_index = 0

	def update_action(self, new_action):
		# Check If The New Action Is Different To The Previous One
		if new_action != self.action:
			self.action = new_action
			# Update The Animation Settings
			self.frame_index = 0 
			self.update_time = pygame.time.get_ticks()

	def check_alive(self):
		if self.health <= 0:
			self.health = 0
			self.speed = 0
			self.alive = False
			self.update_action(3)

	def draw(self):
		screen.blit(pygame.transform.flip(self.image, self.flip, False), self.rect)

class World():
	def __init__(self):
		self.obstacle_list = []

	def process_data(self, data):
		self.level_length = len(data[0])
		#iterate through each value in level data file
		for y, row in enumerate(data):
			for x, tile in enumerate(row):
				if tile >= 0:
					img = img_list[tile]
					img_rect = img.get_rect()
					img_rect.x = x * tile_size  
					img_rect.y = y * tile_size
					tile_data = (img, img_rect)
					if tile >= 0 and tile <= 8:
						self.obstacle_list.append(tile_data)
					elif tile >= 9 and tile <= 10:
						water = Water(img, x * tile_size, y * tile_size)
						water_group.add(water)
					elif tile >= 11 and tile <= 14:
						decoration = Decoration(img, x * tile_size, y * tile_size)
						decoration_group.add(decoration)
					elif tile == 15:
						player = Soldier('soldier', x * tile_size, y * tile_size, 1.65, 4, 20, 5)
						health_bar = HealthBar(10, 10, player.health, player.health)
					elif tile == 16:
						enemy = Soldier('enemy', x * tile_size, y * tile_size, 1.65, 2, 20, 0)
						enemy_group.add(enemy)
					elif tile == 17:
						item_box = ItemBox('Ammo', x * tile_size, y * tile_size)
						item_box_group.add(item_box)
					elif tile == 18:
						item_box = ItemBox('Grenade', x * tile_size, y * tile_size)
						item_box_group.add(item_box)
					elif tile == 19:
						item_box = ItemBox('Health', x * tile_size, y * tile_size)
						item_box_group.add(item_box)
					elif tile == 20:
						exit = Exit(img, x * tile_size, y * tile_size)
						exit_group.add(exit)
		return player, health_bar


	def draw(self):
		for tile in self.obstacle_list:
			tile[1][0] += screen_scroll
			screen.blit(tile[0], tile[1])
	
class Decoration(pygame.sprite.Sprite):
	def __init__(self, img, x, y):
		pygame.sprite.Sprite.__init__(self)
		self.image = img
		self.rect = self.image.get_rect()
		self.rect.midtop = (x + tile_size // 2, y + (tile_size - self.image.get_height()))

	def update(self):
		self.rect.x += screen_scroll

class Water(pygame.sprite.Sprite):
	def __init__(self, img, x, y):
		pygame.sprite.Sprite.__init__(self)
		self.image = img
		self.rect = self.image.get_rect()
		self.rect.midtop = (x + tile_size // 2, y + (tile_size - self.image.get_height()))

	def update(self):
		self.rect.x += screen_scroll

class Exit(pygame.sprite.Sprite):
	def __init__(self, img, x, y):
		pygame.sprite.Sprite.__init__(self)
		self.image = img
		self.rect = self.image.get_rect()
		self.rect.midtop = (x + tile_size // 2, y + (tile_size - self.image.get_height()))

	def update(self):
		self.rect.x += screen_scroll

class ItemBox(pygame.sprite.Sprite):
	def __init__(self, item_type, x, y):
		pygame.sprite.Sprite.__init__(self)
		self.item_type = item_type
		self.image = item_boxes[self.item_type]
		self.rect = self.image.get_rect()
		self.rect.midtop = (x + tile_size // 2, y + (tile_size - self.image.get_height()))
		
	def update(self):
		#scroll
		self.rect.x += screen_scroll
		# Check If The Player Has Picked Up The Box
		if pygame.sprite.collide_rect(self, player):
			# Check What Kind Of Box It Was
			if self.item_type == 'Health':
				player.health += 25
				if player.health > player.max_health:
					player.health = player.max_health
			elif self.item_type == 'Ammo':
				player.ammo += 15
			elif self.item_type == 'Grenade':
				player.grenades += 3
			# Delete The Item Box
			self.kill()

class HealthBar():
	def __init__(self, x, y, health, max_health):
		self.x = x
		self.y = y
		self.health = health
		self.max_health = max_health

	def draw(self, health):
		# Update With New Health
		self.health = health
		# Calculate Health Ratio
		ratio = self.health / self.max_health
		pygame.draw.rect(screen, black, (self.x - 2, self.y - 2, 154, 24))
		pygame.draw.rect(screen, red, (self.x, self.y, 150, 20))
		pygame.draw.rect(screen, green, (self.x, self.y, 150 * ratio, 20))


class Bullet(pygame.sprite.Sprite):
	def __init__(self, x, y, direction):
		pygame.sprite.Sprite.__init__(self)
		self.speed = 10
		self.image = bullet_img
		self.rect = self.image.get_rect()
		self.rect.center = (x, y)
		self.direction = direction

	def update(self):
		# Move Bullet
		self.rect.x +=  (self.direction * self.speed) + screen_scroll
		# Check If Bullet Had Gone Out Off Screen
		if self.rect.right < 0 or self.rect.left > screen_width:
			self.kill()
		#check collision with world
		for tile in world.obstacle_list:
			if tile[1].colliderect(self.rect):
				self.kill()

		#Check Collision With Characters
		if pygame.sprite.spritecollide(player, bullet_group, False):
			if player.alive:
				player.health -= 5
				self.kill()

		for enemy in enemy_group:
			if pygame.sprite.spritecollide(enemy, bullet_group, False):
				if enemy.alive:
					enemy.health -= 25
					self.kill()

class Grenade(pygame.sprite.Sprite):
	def __init__(self, x, y, direction):
		pygame.sprite.Sprite.__init__(self)
		self.timer = 100
		self.vel_y = -9
		self.speed = 4
		self.image = grenade_img
		self.rect = self.image.get_rect()
		self.rect.center = (x, y)
		self.width = self.image.get_width()
		self.height = self.image.get_height()
		self.direction = direction
	 
	def update(self):
		self.vel_y += gravity
		dx = self.direction * self.speed
		dy = self.vel_y

		# Update Grenade Position
		self.rect.x += dx
		self.rect.y += dy
		
		#check collision with world
		for tile in world.obstacle_list:
			#check collision with walls
			if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
				self.direction *= -1
				dx = self.direction * self.speed
			#check collision in the y direction
			if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
				self.speed = 0
				#check if below the ground, i.e. thrown up
				if self.vel_y < 0:
					self.vel_y = 0
					dy = tile[1].bottom - self.rect.top
				#check if above the ground, i.e. falling
				elif self.vel_y >= 0:
					self.vel_y = 0
					self.direction *= -1
					dy = tile[1].top - self.rect.bottom

		# Check If Grenade Had Gone Out Off Screen
		if self.rect.left + dx < 0 or self.rect.right + dx > screen_width:
			self.direction *= -1
			dx = self.direction * self.speed

		# Update Grenade Position
		self.rect.x += dx + screen_scroll
		self.rect.y += dy

		# Countdown Timer
		self.timer -= 1
		if self.timer <= 0:
			self.kill()
			grenade_fx.play()
			explosion = Explosion(self.rect.x, self.rect.y, 0.5)
			explosion_group.add(explosion)
			# Do Damage To Anyone Nearby
			if abs(self.rect.centerx - player.rect.centerx) < tile_size * 1.7 and \
			   abs(self.rect.centery - player.rect.centery) < tile_size * 1.7:
				player.health -= 100
			elif abs(self.rect.centerx - player.rect.centerx) < tile_size * 3 and \
			   abs(self.rect.centery - player.rect.centery) < tile_size * 3:
				player.health -= 50
			elif abs(self.rect.centerx - player.rect.centerx) < tile_size * 3.7 and \
			   abs(self.rect.centery - player.rect.centery) < tile_size * 3.7:
				player.health -= 20
			elif abs(self.rect.centerx - player.rect.centerx) < tile_size * 4.2 and \
			   abs(self.rect.centery - player.rect.centery) < tile_size * 4.2:
				player.health -= 5

			for enemy in enemy_group:
				if abs(self.rect.centerx - enemy.rect.centerx) < tile_size * 2 and \
				   abs(self.rect.centery - enemy.rect.centery) < tile_size * 2:
					enemy.health -= 100
				elif abs(self.rect.centerx - enemy.rect.centerx) < tile_size * 3 and \
				   abs(self.rect.centery - enemy.rect.centery) < tile_size * 3:
					enemy.health -= 50
				elif abs(self.rect.centerx - enemy.rect.centerx) < tile_size * 3.7 and \
				   abs(self.rect.centery - enemy.rect.centery) < tile_size * 3.7:
					enemy.health -= 20
				elif abs(self.rect.centerx - enemy.rect.centerx) < tile_size * 4.2 and \
				   abs(self.rect.centery - enemy.rect.centery) < tile_size * 4.2:
					enemy.health -= 5

class Explosion(pygame.sprite.Sprite):
	def __init__(self, x, y, scale):
		pygame.sprite.Sprite.__init__(self)
		self.images = []
		for num in range(1, 6):
			img = pygame.image.load(f'shooter_game/img/explosion/exp{num}.png').convert_alpha()
			img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
			self.images.append(img)
		self.frame_index = 0
		self.image = self.images[self.frame_index]
		self.rect = self.image.get_rect()
		self.rect.center = (x, y)
		self.counter = 0

	def update(self):
		#scroll
		self.rect.x += screen_scroll
		explosion_speed = 4
		# Update Explosion Animation
		self.counter += 1
		if self.counter >= explosion_speed:
			self.counter = 0
			self.frame_index += 1
			# If The Animation Is Complete Then Delete The Explosion
			if self.frame_index >= len(self.images):
				self.kill()
			else:
				self.image = self.images[self.frame_index]

class Button():
	def __init__(self,x, y, image, scale):
		width = image.get_width()
		height = image.get_height()
		self.image = pygame.transform.scale(image, (int(width * scale), int(height * scale)))
		self.rect = self.image.get_rect()
		self.rect.topleft = (x, y)
		self.clicked = False

	def draw(self, surface):
		action = False

		#get mouse position
		pos = pygame.mouse.get_pos()

		#check mouseover and clicked conditions
		if self.rect.collidepoint(pos):
			if pygame.mouse.get_pressed()[0] == 1 and self.clicked == False:
				action = True
				self.clicked = True

		if pygame.mouse.get_pressed()[0] == 0:
			self.clicked = False

		#draw button
		surface.blit(self.image, (self.rect.x, self.rect.y))

		return action

class ScreenFade():
	def __init__(self, direction, colour, speed):
		self.direction = direction
		self.colour = colour
		self.speed = speed
		self.fade_counter = 0

	def fade(self):
		fade_complete = False
		self.fade_counter += self.speed
		if self.direction == 1:#whole screen fade
			pygame.draw.rect(screen, self.colour, (0 - self.fade_counter, 0, screen_width // 2,  screen_height))
			pygame.draw.rect(screen, self.colour, (screen_width // 2 + self.fade_counter, 0, screen_width, screen_height))
			pygame.draw.rect(screen, self.colour, (0, 0 - self.fade_counter, screen_width, screen_height // 2))
			pygame.draw.rect(screen, self.colour, (0, screen_height // 2 + self.fade_counter, screen_width, screen_height ))
		if self.direction == 2:#vertical screen fade down
			pygame.draw.rect(screen, self.colour, (0, 0, screen_width, 0 + self.fade_counter))
		if self.fade_counter >= screen_width:
			fade_complete = True

		return fade_complete

#create screen fades
intro_fade = ScreenFade(1, black, 4)
death_fade = ScreenFade(2, pink, 4)

#create buttons
start_button = Button(screen_width // 2 -130, screen_height // 2 - 150, start_img, 1)
exit_button = Button(screen_width // 2 -110, screen_height // 2 + 50, exit_img, 1)
restart_button = Button(screen_width // 2 -100, screen_height // 2 - 50, restart_img, 2)

# Create Sprite Groups
enemy_group = pygame.sprite.Group()
bullet_group = pygame.sprite.Group()
grenade_group = pygame.sprite.Group()
explosion_group = pygame.sprite.Group()
item_box_group = pygame.sprite.Group()
water_group = pygame.sprite.Group()
decoration_group = pygame.sprite.Group()
exit_group = pygame.sprite.Group()

#create empty tile list
world_data = []
for row in range(rows):
	r = [-1] * max_cols
	world_data.append(r)
#load data with csv
with open(f'level{level}_data.csv', newline = '') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            for x, row in enumerate(reader):
                for y, tile in enumerate(row):
                    world_data[x][y] = int(tile)

world = World()
player, health_bar = world.process_data(world_data)

running = True
while running:

	clock.tick(FPS)

	if start_game == False:
		#draw menu
		screen.fill(bg)
		#add buttons
		if start_button.draw(screen):
			start_game = True
			start_intro = True
		elif exit_button.draw(screen):
			running = False
	else:
		#update background
		draw_bg()
		#draw world map
		world.draw()
		# Show Player Health
		health_bar.draw(player.health)

		# Show Ammo
		draw_text('AMMO:', font, white, 10, 35)
		for x in range(player.ammo):
			screen.blit(bullet_img, (90 + (x*10), 40))
		# Show Grenade
		draw_text('GRENADES: ', font, white, 10, 60)
		for x in range(player.grenades):
			screen.blit(grenade_img, (135 + (x*15), 60))

		player.update()
		player.draw()

		for enemy in enemy_group:
			enemy.ai()
			enemy.update()
			enemy.draw()

		# Update And Draw Groups
		bullet_group.update()
		bullet_group.draw(screen)

		grenade_group.update()
		grenade_group.draw(screen)

		explosion_group.update()
		explosion_group.draw(screen)

		item_box_group.update()
		item_box_group.draw(screen)

		water_group.update()
		water_group.draw(screen)

		decoration_group.update()
		decoration_group.draw(screen)

		exit_group.update()
		exit_group.draw(screen)

		#show intro
		if start_intro == True:
			if intro_fade.fade():
				start_intro = False
				intro_fade.fade_counter = 0

		# Update Player Actions
		if player.alive:
			# Shoot Bullets
			if shoot:
				player.shoot()
			# Throw Grenade
			elif grenade and grenade_thrown == False and player.grenades > 0:
				grenade = Grenade(player.rect.centerx + (0.5 * player.rect.size[0] * player.direction), player.rect.top, player.direction)
				grenade_group.add(grenade)
				# Reduce Grenades
				player.grenades -= 1
				grenade_thrown = True
			if player.in_air:
				player.update_action(2) # 2: jump
			elif moving_left or moving_right:
				player.update_action(1) # 1: running
			else:
				player.update_action(0) # 0: idle
			screen_scroll, level_complete = player.move(moving_left, moving_right)
			bg_scroll -= screen_scroll
			#check if player has completed the level
			if level_complete:
				start_intro = True
				level += 1
				bg_scroll = 0
				world_data = reset_level()
				if level <= max_levels:
					#load data with pickle
					world_data = []
					with open(f'level{level}_data.csv', newline = '') as csvfile:
						reader = csv.reader(csvfile, delimiter=',')
						for x, row in enumerate(reader):
							for y, tile in enumerate(row):
								world_data[x][y] = int(tile)
					world = World()
					player, health_bar = world.process_data(world_data)
				level_complete = False
		else:
			screen_scroll = 0
			if death_fade.fade():
				if restart_button.draw(screen):
					death_fade.fade_counter = 0
					start_intro = True
					bg_scroll = 0
					world_data = reset_level()
					#load data with pickle
					world_data = []
					with open(f'level{level}_data.csv', newline = '') as csvfile:
						reader = csv.reader(csvfile, delimiter=',')
						for x, row in enumerate(reader):
							for y, tile in enumerate(row):
								world_data[x][y] = int(tile)

					world = World()
					player, health_bar = world.process_data(world_data)

	for event in pygame.event.get():
		# Quit Game
		if event.type == pygame.QUIT:
			running = False

		# Keyboard Presses
		if event.type == pygame.KEYDOWN:
			if event.key == pygame.K_a:
				moving_left = True
			if event.key == pygame.K_d:
				moving_right = True
			if event.key == pygame.K_SPACE:
				shoot = True
			if event.key == pygame.K_q:
				grenade = True
			if event.key == pygame.K_w and player.alive:
				player.jump = True
				jump_fx.play()
			if event.key == pygame.K_ESCAPE:
				running = False
					
		# Keyboard Button Released
		if event.type == pygame.KEYUP:
			if event.key == pygame.K_a:
				moving_left = False
			if event.key == pygame.K_d:
				moving_right = False
			if event.key == pygame.K_ESCAPE:
				running = False
			if event.key == pygame.K_SPACE:
				shoot = False
			if event.key == pygame.K_q:
				grenade = False		
				grenade_thrown = False

	pygame.display.update()

pygame.quit()