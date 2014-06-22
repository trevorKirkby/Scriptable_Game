import pygame
import random
import math

updated   =  pygame.sprite.RenderUpdates()
drawn     =  pygame.sprite.RenderUpdates()

def drawtree(x1, y1, angle, depth,picture):
	if depth:
		angle += random.randrange(-50+depth*7,50-depth*7)
		x2 = x1 + int(math.cos(math.radians(angle)) * depth * 3.0)
		y2 = y1 + int(math.sin(math.radians(angle)) * depth * 3.0)
		pygame.draw.line(picture, (150,200-depth*20,70), (x1, y1), (x2, y2), depth)
		drawtree(x2, y2, angle-20, depth-1, picture)
		drawtree(x2, y2, angle+20, depth-1, picture)
	else:
		x1 += random.randrange(-6,7)
		y1 += random.randrange(-6,7)
		shape = []
		for point in range(5):
			shape.append((x1+random.randrange(-4,5),y1+random.randrange(-4,5)))
		pygame.draw.polygon(picture, (100+random.randrange(-20,20),180+random.randrange(-20,20),70+random.randrange(-20,20)), shape)
		pygame.draw.polygon(picture, (100+random.randrange(-20,20),150+random.randrange(-20,20),100+random.randrange(-20,20)), shape,1)

def maketree():
	img = pygame.Surface((80,80))
	img.fill((255,255,255))
	img.set_colorkey((255,255,255))
	drawtree(40,80,-90,6,img)
	return img

class tree(pygame.sprite.Sprite):
	def __init__(self,pos):
		pygame.sprite.Sprite.__init__(self)
		self.pos             =   pos
		img                  =   pygame.Surface((80,80))
		img.fill((255,255,255))
		img.set_colorkey((255,255,255))
		drawtree(40,80,-90,6,img)
		self.image           =   img
		self.rect            =   self.image.get_rect()
		self.rect.center     =   self.pos
		drawn.add(self)
		updated.add(self)
	def update(self):
		#screen.fill((200,200,200),self.rect)
		pass

if __name__ == "__main__":
	pygame.init()
	pygame.display.init()
	screen = pygame.display.set_mode((600,600))
	screen.fill((200,200,200))
	pygame.display.flip()
	tree((300,300))
	pygame.display.flip()
	while True:
		pygame.event.pump()
		updated.update()
		pygame.display.update(drawn.draw(screen))