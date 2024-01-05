import pygame
import csv
import pickle

pygame.init()
clock = pygame.time.Clock()
FPS = 60

#game window
screen_width = 800
screen_height = 640
lower_margin = 100
side_margin = 300

screen = pygame.display.set_mode((screen_width + side_margin, screen_height + lower_margin))
pygame.display.set_caption('Level Editor')

#define game variables
rows = 16
max_cols = 150
tile_size = screen_height // rows
tile_types = 21
level = 0
current_tile = 0
scroll_left = False
scroll_right = False
scroll = 0
scroll_speed = 1

#load images
pine_img = pygame.image.load('shooter_game/img/background/pine1.png').convert_alpha()
pine2_img = pygame.image.load('shooter_game/img/background/pine2.png').convert_alpha()
mountain_img = pygame.image.load('shooter_game/img/background/mountain.png').convert_alpha()
sky_img = pygame.image.load('shooter_game/img/background/sky_cloud.png').convert_alpha()
#store tiles in a list
img_list = []
for x in range(tile_types):
    img = pygame.image.load(f'shooter_game/img/tile/{x}.png').convert_alpha()
    img = pygame.transform.scale(img, (tile_size, tile_size))
    img_list.append(img)

save_img = pygame.image.load('shooter_game/img/buttons/save_btn.png').convert_alpha()
load_img = pygame.image.load('shooter_game/img/buttons/load_btn.png').convert_alpha()

#define colours
green = (144, 201, 120)
white = (255, 255, 255)
red = (200, 25, 25)
black = (0, 0, 0)

#define font
font = pygame.font.SysFont('Futura', 30)

#create empty tile list
world_data = []
for row in range(rows):
    r = [-1] * max_cols
    world_data.append(r)

#create ground
for tile in range(0, max_cols):
    world_data[rows - 1][tile] = 0

#button class
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

#function for outputting text onto the screen
def draw_text(text, font, text_col, x, y):
    img = font.render(text, True, text_col)
    screen.blit(img, (x, y))

#create function for drawing background
def draw_bg():
    screen.fill(green)
    width = sky_img.get_width()
    for x in range(4):
        screen.blit(sky_img, ((x * width) - scroll * 0.5, 0))
        screen.blit(mountain_img, ((x * width) - scroll * 0.6, screen_height - mountain_img.get_height() - 300))
        screen.blit(pine_img, ((x * width) - scroll * 0.7, screen_height - pine_img.get_height() - 150))
        screen.blit(pine2_img, ((x * width) - scroll * 0.8, screen_height - pine2_img.get_height()))

#draw grid
def draw_grid():
    #vertical lines
    for c in range(max_cols + 1):
        pygame.draw.line(screen, white, (c * tile_size - scroll, 0), (c * tile_size - scroll, screen_height))
    for c in range(rows + 1):
       pygame.draw.line(screen, white, (0, c * tile_size), (screen_width, c * tile_size))

#function for drawing the world tiles
def draw_world():
    for y, row in enumerate(world_data):
        for x, tile in enumerate(row):
            if tile >= 0:
                screen.blit(img_list[tile], (x * tile_size - scroll, y * tile_size))

#create buttons
save_button = Button(screen_width // 2, screen_height + lower_margin - 50, save_img, 1)
load_button = Button(screen_width // 2 + 200, screen_height + lower_margin - 50, load_img, 1)
#make a button list
button_list = []
button_col = 0
button_row = 0
for i in range(len(img_list)):
    tile_button = Button(screen_width + (75 * button_col) + 50, 75 * button_row + 50, img_list[i], 1)
    button_list.append(tile_button)
    button_col += 1
    if button_col == 3:
        button_row += 1
        button_col = 0
    

running = True
while running:

    clock.tick(FPS)

    draw_bg()
    draw_grid()
    draw_world()

    draw_text(f'Level: {level}', font, white, 10, screen_height + lower_margin - 90)
    draw_text('Press UP or DOWN to change level', font, white, 10, screen_height + lower_margin - 60)

    #save and load data
    if save_button.draw(screen):
        #save level data
        #save data with csv
        with open(f'level{level}_data.csv', 'w', newline = '') as csvfile:
            writer = csv.writer(csvfile, delimiter=',')
            for row in world_data:
                writer.writerow(row)
   
    if load_button.draw(screen):
        #load in level data
        #reset scroll back to the start of the level
        scroll = 0
        #load data with csv
        with open(f'level{level}_data.csv', newline = '') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            for x, row in enumerate(reader):
                for y, tile in enumerate(row):
                    world_data[x][y] = int(tile)
   

    #draw tile panel and tiles
    pygame.draw.rect(screen, green, (screen_width, 0, side_margin, screen_height))

    #choose a tile
    button_count = 0
    for button_count, i in enumerate(button_list):
        if i.draw(screen):
            current_tile = button_count

    #highlight the selected tile
    pygame.draw.rect(screen, white, button_list[current_tile].rect, 2)

    #scroll the map
    if scroll_left == True and scroll > 0:
        scroll -= 5 * scroll_speed
    if scroll_right == True and scroll < (max_cols * tile_size) - screen_width:
        scroll += 5 * scroll_speed

    #add new tiles to the screen
    #get mouse position
    pos = pygame.mouse.get_pos()
    x = (pos[0] + scroll) // tile_size
    y = pos[1] // tile_size

    #check that the coordinates are within the tile area
    if pos[0] < screen_width and pos[1] < screen_height:
        #update tile values
        if pygame.mouse.get_pressed()[0] == 1:
            if world_data[y][x] != current_tile:
                world_data[y][x] = current_tile
        if pygame.mouse.get_pressed()[2] == 1:
            world_data[y][x] = -1

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        #keyboard presses
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                scroll_left = True
            if event.key == pygame.K_RIGHT:
                scroll_right = True
            if event.key == pygame.K_RSHIFT or event.key == pygame.K_LSHIFT:
                scroll_speed = 5
            if event.key == pygame.K_UP:
                level += 1
            if event.key == pygame.K_DOWN and level > 0:
                level -= 1

        if event.type == pygame.KEYUP:
            if event.key == pygame.K_LEFT:
                scroll_left = False
            if event.key == pygame.K_RIGHT:
                scroll_right = False
            if event.key == pygame.K_RSHIFT or event.key == pygame.K_LSHIFT:
                scroll_speed = 1

    pygame.display.update()

pygame.quit()