#!/usr/bin/env python3

import pygame
import asyncio
import time
import copy
import os
import sys

import common_code

COLOR_BLACK = (56, 63, 78)
COLOR_WHITE = (201, 209, 224)
# COLOR_BLACK = (0, 0, 0)
# COLOR_WHITE = (255, 255, 255)

SCREEN_WIDTH = 40
SCREEN_HEIGHT = 72 
SCREEN_SCALE = 8

FRAME_LIMITING = False
MAX_FRAME_TIME = 1.0/60

PARENT_FOLDER = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE_PATH = PARENT_FOLDER + '/config.cfg'

print('PARENT_FOLDER', PARENT_FOLDER)
print('CONFIG_FILE_PATH', CONFIG_FILE_PATH)

class Sprite:
	x = 0
	y = 0
	width = 0
	height = 0
	bitmapData = bytearray()
	key = -1
	
	def __init__(self, width, height, bitmapData, x, y, key=-1):
		self.x = x
		self.y = y
		self.width = width
		self.height = height
		self.bitmapData = copy.deepcopy(bitmapData)
		self.key = key
		
class game_interface:
	logical_screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
	sprites = dict()
	draw_offset = [0, 0]
	
	def convert_color(self, color):
		return COLOR_WHITE if color == 1 else COLOR_BLACK
	
	def setPixel(self, x, y, color):
		x += self.draw_offset[0]
		y += self.draw_offset[1]
		self.logical_screen.set_at((int(x), SCREEN_HEIGHT - int(y) - 1), self.convert_color(color))
	
	def drawLine(self, x1, y1, x2, y2, color):
		x1 += self.draw_offset[0]
		y2 += self.draw_offset[1]
		x1 += self.draw_offset[0]
		y2 += self.draw_offset[1]
		pygame.draw.line(self.logical_screen, self.convert_color(color), (x1, SCREEN_HEIGHT - y1 - 1), (x2, SCREEN_HEIGHT - (y2) - 1))
		
	def drawRectangle(self, x, y, w, h, color):
		x += self.draw_offset[0]
		y += self.draw_offset[1]
		pygame.draw.rect(self.logical_screen, self.convert_color(color), pygame.Rect(x, SCREEN_HEIGHT - (y) - h, w, h), 1)
		
	def drawFilledRectangle(self, x, y, w, h, color):
		x += self.draw_offset[0]
		y += self.draw_offset[1]
		pygame.draw.rect(self.logical_screen, self.convert_color(color), pygame.Rect(int(x), int(SCREEN_HEIGHT - (y) - h), int(w), int(h)), 0)
	
	def fill(self, color):
		self.logical_screen.fill(self.convert_color(color))

	def drawSprite(self, name):
		sprite = self.sprites[name]
		
		sprite.x += self.draw_offset[0]
		sprite.y += self.draw_offset[1]
		
		if sprite.y > SCREEN_HEIGHT or sprite.y + sprite.width < 0:
			return;
		
		num_byte_rows = sprite.height // 8
		remainder = sprite.height % 8
		if remainder != 0:
			num_byte_rows += 1
		
		for row_index in range(num_byte_rows):
			for x in range(sprite.width):
				byte_num = sprite.width * row_index + x
				byte = sprite.bitmapData[byte_num]
				
				row_height = 8
				if row_index == num_byte_rows - 1:
					if remainder != 0:
						row_height = remainder
						
				for inner_y in range(0, row_height):
					y = row_index*8 + inner_y
					byte_mask = 1 << inner_y
					value = (0 if ((byte & byte_mask) == 0) else 1)
					
					if sprite.key == -1 or value != sprite.key:
						self.setPixel(sprite.x + y, sprite.y + x, value)
		
		sprite.x -= self.draw_offset[0]
		sprite.y -= self.draw_offset[1]
	
	def drawSprite_location(self, name, x, y, key=-1):
		sprite = self.sprites[name]
		sprite.x = x
		sprite.y = y
		
		self.drawSprite(name)
	
	def init_sprite(self, name, width, height, data, x, y, key=-1):
		if not name in self.sprites:
			self.sprites[name] = Sprite(width, height, data, x, y, key)

	def save_data(self, data_dict):
		if sys.platform == "emscripten":
			for key in data_dict:
				__import__('platform').window.localStorage.setItem("Flucht_" + key, str(data_dict[key]))
		else:
			with open(CONFIG_FILE_PATH, 'w') as file:
				for key in data_dict:
					file.write(str(key) + ':' + str(data_dict[key]))
		
	def load_data(self):
		data_dict = {}
		
		if sys.platform == "emscripten":
			# hack: i have no way to enumerate, so let's just hardcode it, even though it's not clean or extensible
			d = __import__('platform').window.localStorage.getItem("Flucht_highscore")
			if d is not None:
				data_dict['highscore'] = d
		else:
			if os.path.exists(CONFIG_FILE_PATH):
				with open(CONFIG_FILE_PATH, 'r') as file:
					for line in file:
						tokens = line.split(':')
						if len(tokens) >= 2:
							key = tokens[0]
							value = ':'.join(tokens[1:])
							data_dict[key] = value
			
		return data_dict

_game_interface = game_interface()


pygame.init()

icon_pixels = [
	'        ',
	'  xxxxx ',
	' xx xx  ',
	'  xxxxx ',
	'  xxxxx ',
	'  xxxxx ',
	' x   x  ',
	'        ',
]
icon_surface = pygame.Surface([32, 32])
for x in range(8):
	for y in range(8):
		color = COLOR_BLACK if (icon_pixels[y][x] == ' ') else COLOR_WHITE
		for xx in range(4*x, 4*x + 4):
			for yy in range(4*y, 4*y + 4):
				icon_surface.set_at((xx, yy), color)
pygame.display.set_icon(icon_surface)
					
pygame.display.set_caption('Flucht')

async def main():

	last_loop_timestamp = time.time()
	last_frame_timestamp = time.time()
	unprocessed_time_left = 0

	display_screen = pygame.display.set_mode([SCREEN_SCALE * SCREEN_WIDTH, SCREEN_SCALE * SCREEN_HEIGHT])

	game_interface.logical_screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), 0, 32).convert()
	
	pressed = False
	running = True
	while running:
		
		can_render = False
		current_loop_timestamp = time.time()
		elapsed_time_since_last_loop = current_loop_timestamp - last_loop_timestamp
		unprocessed_time_left += elapsed_time_since_last_loop
		last_loop_timestamp = current_loop_timestamp
			
		if FRAME_LIMITING:
			while(unprocessed_time_left >= MAX_FRAME_TIME):
				unprocessed_time_left -= MAX_FRAME_TIME
				can_render = True
		else:
			can_render = True
		
		if can_render:
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					running = False
				if event.type == pygame.KEYDOWN:
					if event.key == pygame.K_ESCAPE:
						running = False
						break
					pressed = True
				elif event.type == pygame.KEYUP:
					pressed = False
				elif event.type == pygame.MOUSEBUTTONDOWN:
					pressed = True
				elif event.type == pygame.MOUSEBUTTONUP:
					pressed = False
			
			if not running:
				break
				
			current_frame_timestamp = time.time()
			delta_time = current_frame_timestamp - last_frame_timestamp
			last_frame_timestamp = current_frame_timestamp
			
			common_code.game_loop(pressed, delta_time, _game_interface)
			
			# scaled copy from logical to display
			pygame.transform.scale(game_interface.logical_screen, (SCREEN_SCALE * SCREEN_WIDTH, SCREEN_SCALE * SCREEN_HEIGHT), display_screen)
			
			pygame.display.update()
			await asyncio.sleep(0)
	
	print('EXITING')
	
asyncio.run( main() )