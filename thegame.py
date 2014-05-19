#!/usr/bin/env python

import pygame, time, math, random, sys, socket, threading, select
from network import *
from Tkinter import *
import Tkinter as tk
import _tkinter

#def import_block(*args):
#	return time

#__import__ = import_block
#__builtins__.__import__ = import_block

SPEED = 0.025
COLOR = (150,150,200)

updated              =   pygame.sprite.RenderUpdates()
drawn                =   pygame.sprite.RenderUpdates()
collidable           =   pygame.sprite.RenderUpdates()
damagers             =   pygame.sprite.RenderUpdates()
explosion_triggers   =   pygame.sprite.RenderUpdates()
projectiles          =   pygame.sprite.RenderUpdates()
barriers             =   pygame.sprite.RenderUpdates()
special              =   pygame.sprite.RenderUpdates()

gravities            =   []
inputters            =   []

controls = {}
for letter in "1234567890qwertyuiopasdfghjklzxcvbnm":
	controls.update({"'"+letter+"'": [False,"_"+letter] })

PORT = 1340

serverhost     = None         #the host name of the server, used to connect to said server
user_input1    = None         #connection establisher
user_input2    = None         #event handler
user_input3    = None         #image sender
user_input4    = None         #script sender
fore           = None         #character to which the event handler is currently sending to
codesender     = None         #the foreground code sender

all_characters  =  {}
eventsenders    =  {}
codesenders     =  {}
images          =  {}
user_info       =  {}

class Moveable(pygame.sprite.Sprite):
	def __init__(self,pos,imageFileName):
		pygame.sprite.Sprite.__init__(self)
		self.init2(pos,imageFileName)
	def init2(self,pos,imageFileName):
		self.right = pygame.image.load(imageFileName).convert_alpha()
		self.left = pygame.transform.flip(self.right,True,False)
		self.vertical = pygame.transform.rotate(self.right,90)
		self.image = self.right
		if self not in projectiles:
			self.direction = "right"
		self.rect = self.image.get_rect()
		self.rect.center = pos
	def move(self,dx,dy):
		#pygame.display.update(self.draw(screen))
		if self in special:
			pygame.display.update(special.draw(screen))
		#print COLOR
		screen.fill((COLOR),self.rect)
		#print COLOR
		if dx > 0:
			self.image = self.right
			if self not in projectiles:
				self.direction = "right"
		elif dx < 0:
			self.image = self.left
			if self not in projectiles:
				self.direction = "left"
		collisions = pygame.sprite.spritecollide(self, collidable, False)
		for other in collisions:
			if other != self:
				(awayDx,awayDy) = self.moveRelative(other,-1)
				if abs(dx + 1*(awayDx)) < abs(dx):
					dx = 0
				if abs(dy + 1*(awayDy)) < abs(dy):
					dy = 0
				dx = dx + 1*(awayDx)
				dy = dy + 1*(awayDy)
		for item in gravities:
			if item != self:
				(toDx,toDy) = self.moveRelative(item,1)
				dx = dx + (item.force*(toDx))/(self.rangeTo(item)/100)
				dy = dy + (item.force*(toDy))/(self.rangeTo(item)/100)
		self.rect.move_ip(dx,dy)
	def moveRelative(self,other,speed,exact=False):
		dx = other.rect.x - self.rect.x
		dy = other.rect.y - self.rect.y
		if exact == False:
			if abs(dx) > abs(dy):
				# other is farther away in x than in y
				if dx > 0:
					return (+speed,0)
				else:
					return (-speed,0)
			else:
				if dy > 0:
					return (0,+speed)
				else:
					return (0,-speed)
		else:
			angle = math.atan2(dx,dy)
			newx = speed*math.cos(angle)
			newy = speed*math.sin(angle)
			return (newy,newx)
	def movePerpendicular(self,other,speed):
		dx = other.rect.x - self.rect.x
		dy = other.rect.y - self.rect.y
		if abs(dx) > abs(dy):
			# this is to dodge a projectile
			if dy > 0:
				if dx > 0:
					return (+speed/2,+speed)
				else:
					return (-speed/2,+speed)
			else:
				if dx > 0:
					return (+speed/2,-speed)
				else:
					return (-speed/2,-speed)
		else:
			if dx > 0:
				if dy > 0:
					return (+speed,+speed/2)
				else:
					return (+speed,-speed/2)
			else:
				if dy > 0:
					return (-speed,+speed/2)
				else:
					return (-speed,-speed/2)
	def rangeTo(self,other):
		dx = other.rect.x - self.rect.x
		dy = other.rect.y - self.rect.y
		return math.sqrt(dx*dx + dy*dy)

class Stationary(pygame.sprite.Sprite):
	def __init__(self,pos,imageFileName,collide,impermeable=False,alpha=False):
		pygame.sprite.Sprite.__init__(self)
		self.init2(pos,imageFileName,collide,alpha)
		self.impermeable = impermeable
	def init2(self,pos,imageFileName,collide,alpha):
		drawn.add(self)
		updated.add(self)
		if collide:
			collidable.add(self)
		if alpha:
			self.image = pygame.image.load(imageFileName).convert_alpha()
		else:
			self.image = pygame.image.load(imageFileName).convert()
		self.rect = self.image.get_rect()
		self.rect.center = pos
	def rangeTo(self,other):
		dx = other.rect.x - self.rect.x
		dy = other.rect.y - self.rect.y
		return math.sqrt(dx*dx + dy*dy)

class unit(Moveable):
	def __init__(self,pos,image,health,projectile_count,fire_rate,team,speed,impermeable=False,special_reload={}):
		Moveable.__init__(self,pos,image)
		self.projectiles = []
		for number in range(projectile_count):
			self.projectiles.append(None)
		self.health = health
		self.team = team
		team.add(self)
		drawn.add(self)
		collidable.add(self)
		updated.add(self)
		self.firetime = fire_rate
		self.fire_rate = fire_rate
		self.reload = special_reload
		self.speed = speed
		self.impermeable = impermeable
	def maintain(self):
		self.firetime -= 1
		for item in self.reload:
			self.reload[item][0] -= 1
		index = 0
		for projectile in self.projectiles:
			if projectile != None:
				if projectile.update() == False:
					projectile.end()
					self.projectiles[index] = None
			index += 1
		collisions = pygame.sprite.spritecollide(self, damagers, False)
		for other in collisions:
			if other != self and other.parent != self:
				try:
					self.health -= other.damage
				except AttributeError:
					print "Error: Unit Damage Collisions:", other.__name__, "lacks the attribute self.damage used to damage object"
					raise RuntimeError
		if self.health <= 0:
			self.end()
	def project(self,bolt,speed=6,direction=None,target=None,accuracy=None,aimed=False):
		if bolt not in self.reload.keys():
			if self.firetime > 0:
				pass
			else:
				if direction == None:
					if aimed == True:
						direction = self.moveRelative(target,speed,exact=True)
					else:
						direction = self.moveRelative(target,speed)
				index = 0
				for projectile in self.projectiles:
					if projectile == None:
						self.projectiles[index] = bolt(self.rect.center,direction,self)
						projectiles.add(self.projectiles[index])
						updated.add(self.projectiles[index])
						break
					index += 1
				self.firetime = self.fire_rate
		else:
			if self.reload[bolt][0] > 0:
				pass
			else:
				if direction == None:
					direction = self.moveRelative(target,speed)
				index = 0
				for projectile in self.projectiles:
					if projectile == None:
						self.projectiles[index] = bolt(self.rect.center,direction,self)
						projectiles.add(self.projectiles[index])
						updated.add(self.projectiles[index])
						break
					index += 1
				self.reload[bolt][0] = self.reload[bolt][1]
	def end(self):
		for projectile in self.projectiles:
			if projectile != None:
				projectile.end()
		drawn.remove(self)
		collidable.remove(self)
		updated.remove(self)
		special.remove(self)
		damagers.remove(self)
		explosion_triggers.remove(self)
		self.team.remove(self)
		screen.fill(COLOR,self.rect)
	def goup(self):
		self.directions = (0,-1)
		self.inertia()
	def godown(self):
		self.directions = (0,1)
		self.inertia()
	def goleft(self):
		self.directions = (-1,0)
		self.inertia()
	def goright(self):
		self.directions = (1,0)
		self.inertia()
	def magnitude(self,factor):
		return (self.directions[0]*factor,self.directions[1]*factor)
	def inertia(self):
		self.move(*self.magnitude(self.speed))
	def shoot(self,bolt):
		self.project(bolt,direction=self.magnitude(10))
	def aimshoot(self,bolt,vector):
		self.project(bolt,direction=vector)

class projectile(Moveable):
	def __init__(self,pos,direction,image,destructcount,damager=False,boomtrigger=False,simple=True,parent=None,arc=False,explodable=False,countdown=None):
		Moveable.__init__(self,pos,image)
		self.arc=arc
		self.destructCountDown = destructcount
		self.full = destructcount
		if self.arc == True:
			magnitude = math.sqrt(direction[0]*direction[0]+direction[1]*direction[1])
			if explodable == True:
				time = float(self.full)-float(countdown)/2.0
			else:
				time = float(self.full)/2.0
			self.change = float(magnitude)/float(time)
		self.parent = parent
		drawn.add(self)
		if boomtrigger != False:
			explosion_triggers.add(self)
		if damager != False:
			self.damage = damager
			damagers.add(self)
		self.directions = list(direction)
		self.explodable = explodable
		self.delay = 0
		if simple == True:
			if abs(self.directions[1]) > abs(self.directions[0]):
				self.image = self.vertical
				self.rect = self.image.get_rect()
				self.rect.center = pos
		else:
			self.image = pygame.transform.rotate(self.vertical,math.degrees(math.atan2(direction[0],direction[1])))
			self.rect = self.image.get_rect()
			self.rect.center = pos
	def update(self):
		if self.delay > 0:
			self.delay -= 1
		else:
			screen.fill((COLOR),self.rect)
			collisions = pygame.sprite.spritecollide(self, collidable, False)
			for other in collisions:
				if other != self:
					if other.impermeable == True:
						self.end()
						return False
			self.destructCountDown = self.destructCountDown - 1
			if self.explodable == True:
				if self.destructCountDown == self.countdown:
					self.destruct()
			if self.destructCountDown <= 0:
				return False
			else:
				if self.explodable == True:
					if self.exploded == False:
						if self.arc == True:
							print self.destructCountDown, (self.full-self.countdown)/2
							if self.destructCountDown > (self.full-self.countdown)/2:
								self.rect.move_ip(*self.directions)
								self.directions[0], self.directions[1] = self.adjustmag(self.directions[0], self.directions[1],-1)
							else:
								self.rect.move_ip(*self.directions)
								self.directions[0], self.directions[1] = self.adjustmag(self.directions[0], self.directions[1],1)
						else:
							self.rect.move_ip(*self.directions)
				else:
					if self.arc == True:
						if self.destructCountDown > self.full/2:
							self.rect.move_ip(*self.directions)
							self.directions[0], self.directions[1] = self.adjustmag(self.directions[0], self.directions[1],-1)
						else:
							self.rect.move_ip(*self.directions)
							self.directions[0], self.directions[1] = self.adjustmag(self.directions[0], self.directions[1],1)
					else:
						self.rect.move_ip(*self.directions)
				return True
	def adjustmag(self,x,y,change):
		angle = math.atan2(y,x)
		print "x, y: ", x, y
		magnitude = math.sqrt(x*x+y*y)
		print "magnitude: ", magnitude
		if magnitude > 1 and change < 0:
			magnitude = float(magnitude) + float(change)
		elif change > 0:
			magnitude = float(magnitude) + float(change)
		nx = math.cos(angle)*float(magnitude)
		ny = math.sin(angle)*float(magnitude)
		return nx, ny
	def end(self):
		drawn.remove(self)
		collidable.remove(self)
		updated.remove(self)
		damagers.remove(self)
		explosion_triggers.remove(self)

class explodable():
	def __init__(self,image,count,damage,triggers=explosion_triggers):
		self.explodable = True
		self.exploded = False
		self.explosion = pygame.image.load(image).convert_alpha()
		self.countdown = count
		self.shots = 0
		self.x = None
		self.damage = damage
		self.triggers = triggers
	def destruct(self):
		self.x = self.rect.center
		screen.fill((COLOR),self.rect)
		self.image = self.explosion
		self.rect = self.image.get_rect()
		self.rect.center = self.x
		collidable.remove(self)
		damagers.add(self)
		self.exploded = True
	def  maintain(self):
		if self.exploded == False:
			collisions = pygame.sprite.spritecollide(self, self.triggers, False)
			for other in collisions:
					if other != self:
							self.destruct()
		else:
			if self.countdown > 0:
				self.countdown = self.countdown - 1
			if self.countdown == 0:
				damagers.remove(self)
				screen.fill((COLOR),self.rect)
				self.end()
		return self.exploded
	def end(self):
		drawn.remove(self)
		collidable.remove(self)
		updated.remove(self)
		damagers.remove(self)
		explosion_triggers.remove(self)

class explodable_projectile(projectile):
	def __init__(self,pos,direction,image,destructcount,boomimage,count,damage,triggers=explosion_triggers,simple=True,parent=None,arc=False):
		projectile.__init__(self,pos,direction,image,destructcount,simple=simple,parent=parent,arc=arc,explodable=True,countdown=count)
		self.explodable = True
		self.exploded = False
		self.explosion = pygame.image.load(boomimage).convert_alpha()
		self.countdown = count
		self.shots = 0
		self.x = None
		self.damage = damage
		self.triggers = triggers
	def destruct(self):
		self.x = self.rect.center
		screen.fill((COLOR),self.rect)
		self.image = self.explosion
		self.rect = self.image.get_rect()
		self.rect.center = self.x
		collidable.remove(self)
		projectiles.remove(self)
		damagers.add(self)
		self.exploded = True
	def update(self):
		if self.exploded == False:
			collisions = pygame.sprite.spritecollide(self, self.triggers, False)
			for other in collisions:
					if other != self:
							self.destruct()
		else:
			if self.countdown > 0:
				self.countdown = self.countdown - 1
			if self.countdown == 0:
				damagers.remove(self)
				screen.fill((COLOR),self.rect)
				self.end()
				return False
		return projectile.update(self)
	def end(self):
		drawn.remove(self)
		collidable.remove(self)
		updated.remove(self)
		damagers.remove(self)
		explosion_triggers.remove(self)

class explodable_stationary():
	def __init__(self,pos,imageFileName,collidable,image,count,damage,triggers=explosion_triggers,impermeable=False):
		Stationary.__init__(self,pos,imageFileName,collidable)
		self.impermeable = impermeable
		self.explodable = True
		self.exploded = False
		self.explosion = pygame.image.load(image).convert_alpha()
		self.countdown = count
		self.shots = 0
		self.x = None
		self.damage = damage
		self.triggers = triggers
	def destruct(self):
		self.x = self.rect.center
		screen.fill((COLOR),self.rect)
		self.image = self.explosion
		self.rect = self.image.get_rect()
		self.rect.center = self.x
		collidable.remove(self)
		damagers.add(self)
		self.exploded = True
	def maintain(self):
		if self.exploded == False:
			collisions = pygame.sprite.spritecollide(self, self.triggers, False)
			for other in collisions:
					if other != self:
							self.destruct()
		else:
			if self.countdown > 0:
				self.countdown = self.countdown - 1
			if self.countdown == 0:
				damagers.remove(self)
				screen.fill((COLOR),self.rect)
				self.end()
		return self.exploded
	def end(self):
		drawn.remove(self)
		collidable.remove(self)
		updated.remove(self)
		damagers.remove(self)
		explosion_triggers.remove(self)

class barrier(Stationary):
	def __init__(self,pos,imageFileName,impermeable=False):
		Stationary.__init__(self,pos,imageFileName,True)
		barriers.add(self)
		self.impermeable = impermeable

class character(unit):
	def __init__(self,pos,image,health,projectile_count,fire_rate,team,speed,special_reload={},socket = None):
		unit.__init__(self,pos,image,health,projectile_count,fire_rate,team,speed,special_reload=special_reload)
		if socket != None:
			self.socket = socket
		else:
			print "You need to pass a socket when you initialize the character. Character independance from sockets has been phased out, though it would be easy to change that."
			raise RuntimeError
		self.speed = speed
		self.directions = (1,0)
		self.aim = [12,0]
		self.aim2 = [12,0]
	def update(self):
		self.maintain()
		event = "EMPTY"
		while event != None:
			event = self.socket.recv_data()
			if event != None and event != '':
				if hasattr(self,event):
					function = getattr(self,event)
					try:
						function()
					except Exception, e:
						function(self)
				else:
					#if len(event) != 1:
					if True:
						print "failed event: ", event, "sync is most likely broken"
	def exit(self):
		raise SystemExit
	def aiming(self,vx,vy,vmax=12):
		x = self.aim[0]
		y = self.aim[1]
		M = math.sqrt((x+vx)*(x+vx)+(y+vy)*(y+vy))
		if M <= vmax:
			self.aim[0] += vx
			self.aim[1] += vy
		else:
			self.aim[0] = (x+vx)/M
			self.aim[1] = (y+vy)/M
	def aimup(self):
		self.aiming(0,-1)
	def aimdown(self):
		self.aiming(0,1)
	def aimleft(self):
		self.aiming(-1,0)
	def aimright(self):
		self.aiming(1,0)
	def aiming2(self,change,magnitude=12):
		x = self.aim2[0]
		y = self.aim2[1]
		angle = math.degrees(math.atan2(y,x))
		angle += change
		angle = math.radians(angle)
		self.aim2[0] = math.cos(angle)*magnitude
		self.aim2[1] = math.sin(angle)*magnitude
	def aimleft2(self):
		self.aiming2(-3)
	def aimright2(self):
		self.aiming2(3)

class bolt(projectile):
		def __init__(self,pos,direction,parent):
			projectile.__init__(self,pos,direction,"pulse.png",30,damager=False,boomtrigger=False,simple=True,parent=parent)

class generic(character):
	def __init__(self,sockets,pos):
		self.aim = [0,0]
		character.__init__(self,pos,"generic.png",20,3,3,pygame.sprite.RenderUpdates(),2,socket=sockets)
	def _w(self):
		self.goup()
	def _s(self):
		self.godown()
	def _a(self):
		self.goleft()
	def _d(self):
		self.goright()
	def _e(self):
		self.shoot(bolt)

class wall(barrier):
	def __init__(self,pos):
		barrier.__init__(self,pos,"thewall.png",impermeable=True)

def load_character(name,kind,pos):
	global serverhost
	netsocket = socket(PORT)
	netsocket.connect(serverhost)
	netsocket.send("character")
	netsocket.send(name)
	avatar = kind(netsocket,pos)
	all_characters.update({name:avatar})
	return avatar

def load_code(character,newfunct,name):
	exec newfunct
	setattr(character,name,new_function)

def addcharacters():
	global port
	global fore
	global codesend
	global serverhost
	global eventsenders
	while True:
		connected = False
		myname = tkinput2("name unit to control")
		if myname in eventsenders:
			fore = eventsenders[myname]
			codesend = codesenders[myname]
		else:
			fore = socket(PORT)
			fore.connect(serverhost)
			fore.send_data("event_handler")
			fore.send_data(myname)
			time.sleep(1)
			codesend = socket(PORT)
			codesend.connect(serverhost)
			codesend.send_data("sender")
			codesend.send_data(myname)
			eventsenders.update({myname:fore})
			codesenders.update({myname:codesend})

def sendimages():
	global port
	global fore
	global serverhost
	imgsend = socket(PORT)
	imgsend.connect(serverhost)
	imgsend.send_data("imagesender")
	while True:
		image = tkinput3("enter image to send")
		imgsend.send_img(image)

def sendcode():
	#use foreground character event sender
	global port
	global fore
	global serverhost
	global codesender
	while True:
		functname = tkinput4("enter function to write")
		codesend.send_data(functname)
		sourcename = tkinput4("enter source file")
		source = str()
		for line in open(sourcename,"r"):
			source += (line)
		codesend.send_data(source)

def start(serverhost):
	imgnet = socket(1337)
	imgnet.connect(serverhost)
	imgnet.send("imagereceiver")
	while True:
		images.update(imgnet.recv_img())

def get_input():
	global user_input1
	user_input1 = inputter.get()
	inputter.delete(0, END)

def get_input2():
	global user_input2
	user_input2 = inputter2.get()
	inputter2.delete(0, END)

def get_input3():
	global user_input3
	user_input3 = inputter3.get()
	inputter3.delete(0, END)

def get_input4():
	global user_input4
	user_input4 = inputter4.get()
	inputter4.delete(0, END)

def keyhandle(event):
	try:
		controls[repr(event.char)][0] = True
	except KeyError:
		pass

def nothing(*args):
	pass

def endhandle(event):
	global root
	global game
	if event.keysym == 'Escape':
		print "Unfortunately, your just going to have to kill the process right now."

def keyhandleup(event):
	try:
		controls[repr(event.char)][0] = False
	except KeyError:
		pass

def tkinput(text):
	global user_input1
	prompt["state"] = NORMAL
	prompt.tag_config("a", justify = CENTER)
	prompt.tag_config("b", foreground="blue")
	prompt.insert('1.0', text,("a","b"))
	prompt["state"] = DISABLED
	while user_input1 == None:
		root.update()
	info = user_input1
	user_input1 = None
	prompt["state"] = NORMAL
	prompt.delete(1.0, END)
	prompt["state"] = DISABLED
	return info

def tkinput2(text):
	global user_input2
	prompt2["state"] = NORMAL
	prompt2.tag_config("a", justify = CENTER)
	prompt2.tag_config("b", foreground="blue")
	prompt2.insert('1.0', text,("a","b"))
	prompt2["state"] = DISABLED
	while user_input2 == None:
		time.sleep(0.05)
	info = user_input2
	user_input2 = None
	prompt2["state"] = NORMAL
	prompt2.delete(1.0, END)
	prompt2["state"] = DISABLED
	return info

def tkinput3(text):
	global user_input3
	prompt3["state"] = NORMAL
	prompt3.tag_config("a", justify = CENTER)
	prompt3.tag_config("b", foreground="blue")
	prompt3.insert('1.0', text,("a","b"))
	prompt3["state"] = DISABLED
	while user_input3 == None:
		time.sleep(0.05)
	info = user_input3
	user_input3 = None
	prompt3["state"] = NORMAL
	prompt3.delete(1.0, END)
	prompt3["state"] = DISABLED
	return info

def tkinput4(text):
	global user_input4
	prompt4["state"] = NORMAL
	prompt4.tag_config("a", justify = CENTER)
	prompt4.tag_config("b", foreground="blue")
	prompt4.insert('1.0', text,("a","b"))
	prompt4["state"] = DISABLED
	while user_input4 == None:
		time.sleep(0.05)
	info = user_input4
	user_input4 = None
	prompt4["state"] = NORMAL
	prompt4.delete(1.0, END)
	prompt4["state"] = DISABLED
	return info

def make_account():
	conn = socket(1340)
	conn.connect(serverhost)
	conn.send_data("new_user")
	conn.send_data(tkinput("enter username: "))
	conn.send_data(tkinput("enter password: "))
	conn.send_data(tkinput("enter email: "))

def login():
	server_conn.send(tkinput("enter username"))
	server_conn.send(tkinput("enter id"))
	CURRENCY = int(server_conn.recv_data(poll=False))

def add_others():
	account_adder = socket(1340)
	account_adder.connect(serverhost)
	account_adder.send("account_adder")
	while True:
		info = account_adder.recv_data(poll=False)
		exec info
		user_info.update({account_name:[default,others]})
		#{"trevor":[generic,{"canine":canine}]}
		#account_name = "trevor"
		#default = generic
		#others = {"canine":canine} #implies that canine is defined here
		#make sure that the server asserts that all of these are instances of units.

root = tk.Tk()
embed = tk.Frame(root, width = 600, height = 600)
embed.grid(columnspan = (600), rowspan = 600)
embed.pack(side = LEFT)
tkwin = tk.Frame(root, width = 200, height = 500)
tkwin.pack(side = RIGHT)
os.environ['SDL_WINDOWID'] = str(embed.winfo_id())
os.environ['SDL_VIDEODRIVER'] = 'windib'

pygame.init()
screen = pygame.display.set_mode((600,600))

eventgetter = Text(tkwin, width=10,height=5, state = DISABLED)
eventgetter.place(relx=0.5, rely=0.25, anchor=CENTER)
eventgetter.bind("<KeyPress>", keyhandle)
eventgetter.bind("<KeyRelease>", keyhandleup)
root.bind("<KeyRelease>", keyhandleup)
root.bind("<KeyPress>", endhandle)

inputter = Entry(tkwin)
inputter.place(relx=0.5, rely=0.45, anchor=CENTER)

button1 = Button(tkwin,text = 'enter',  command=get_input)
button1.place(relx=0.5, rely=0.50, anchor=CENTER)

prompt = Text(tkwin, width=25, height=2, state = DISABLED)
prompt.place(relx=0.5, rely=0.375, anchor=CENTER)

inputter2 = Entry(tkwin)
inputter2.place(relx=0.5, rely=0.6, anchor=CENTER)

button2 = Button(tkwin,text = 'enter',  command=get_input2)
button2.place(relx=0.5, rely=0.65, anchor=CENTER)

prompt2 = Text(tkwin, width=25, height=1, state = DISABLED)
prompt2.place(relx=0.5, rely=0.55, anchor=CENTER)

inputter3 = Entry(tkwin)
inputter3.place(relx=0.5, rely=0.75, anchor=CENTER)

button3 = Button(tkwin,text = 'enter',  command=get_input3)
button3.place(relx=0.5, rely=0.80, anchor=CENTER)

prompt3 = Text(tkwin, width=25, height=1, state = DISABLED)
prompt3.place(relx=0.5, rely=0.70, anchor=CENTER)

inputter4 = Entry(tkwin)
inputter4.place(relx=0.5, rely=0.9, anchor=CENTER)

button4 = Button(tkwin,text = 'enter',  command=get_input4)
button4.place(relx=0.5, rely=0.95, anchor=CENTER)

prompt4 = Text(tkwin, width=25, height=1, state = DISABLED)
prompt4.place(relx=0.5, rely=0.85, anchor=CENTER)

serverhost = tkinput("enter server host")

server_conn = socket(PORT)
server_conn.connect(serverhost)
server_conn.send("game")

'''
server_conn.send(tkinput("enter username")
server_conn.send(tkinput("enter id"))

initscript = server_conn.recv_data(poll=False)
exec initscript
'''

mythread1 = threading.Thread(target = addcharacters)
mythread1.start()

mythread1 = threading.Thread(target = sendcode)
mythread1.start()

mythread1 = threading.Thread(target = sendimages)
mythread1.start()

mythread = threading.Thread(target=start,args=[serverhost])
mythread.start()

class globe():
	def __init__(self):
		self.loading = [False,None,None,None]
		self.downloading = 0
		self.imgdata = [str(),str(),str()]
	def run(self):
		loading = self.loading
		downloading = self.downloading
		imgdata = self.imgdata
		if fore != None:
			for item in controls:
				if controls[item][0]:
					print "sending", controls[item][1]
					fore.send(controls[item][1])
		command = "BLANK"
		while command != None:
			command = server_conn.recv_data()
			if command != None:
				if command[:10] == "load code ":
					loading = [True,all_characters[command[10:]],None,None]
				elif loading[0] == True and loading[2] == None:
					loading[2] = command
				elif loading[0] == True and loading[3] == None:
					loading[3] = command
					load_code(loading[1],loading[3],loading[2])
					loading = [False,None,None,None]
				elif command[:15] == "load character ":
					load_character(command[15:],default_new,(100,100))
		time.sleep(SPEED)
		updated.update()
		pygame.display.update(drawn.draw(screen))
		self.loading = loading
		self.downloading = downloading
		self.imgdata = imgdata

def start():
	global server_conn
	screen.fill((COLOR))
	pygame.display.flip()
	pygame.display.update(drawn.draw(screen))
	game = globe()
	marker = 0
	while True:
		game.run()
		root.update()

wall((400,400))
wall((300,400))
wall((400,300))
wall((300,300))

default_new = generic

start()

"""
Todo:
1. institute accounts
2 create a modular "item" class that modifies characters. This is what you gain from defeating an enemy. A spirit can be made to utilize a host by inheriting from item, though this is difficult
3. Add builtin security features, namely the special attribute objects that are changeable only through functions that charge a price... Also make units like canines have different costs associated, like cheaper speed
	-life force (max health, regen, projected healing)
	-damage (health removal, health drain, health sacrafice to amplify abilities)
		-damage is actually 1 of three paired forces:
			-ruin (damage, drain)
			-preservation (healing, protecting)
			-balance (store and release)
	-speed (motion speed, projectile speed)
	-supply (fire rate, max number of projectiles)
	-spacial impact (apply stronger collisions to you and projectiles, less stagger/knockback from collisions, make other objects move towards or away from self)
	-energy (Use to support scripts. Basically, the intermediate scripting which has some built in principals, like weather manipulation, can be increased with this. More advanced scripts will not use it...)
	-creation force (used to spawn new objects, AI units, and even map slices)
4. add legitimate security against malicous code
5. add map panning features, basically multiple maps running at once with warp points between them
	-see map
6. add "key" locks onto the infastructure
7. write documentation in full, including the secret docs
8. Design an actually bomb-proof, easy to install and use package for users. This includes multiplatform and actually closable programs. This also means pyinstaller for windows, and a py2app on mac that installs python interpreter and sets up the program, and also a linux zipfile with an sh file that apt-gets python than installs
"""


'''
ideas:

able to take image of last sprite it touched (one button to assign rect of last collision, other to assume true form, this is done by overlaying a projectile onto oneself, a slightly larger square with the same color as the background but with other rect blitted onto it)
able to create "projectile" units and walls
able to synthesize keypresses on all devices at once (best to do this for keys that you don't have doing anything)
Able to possess units that died because they are no longer in groups being watched. As the system has no hook to them, you can overwrite their update function, reverse their death, and, while unable to change any attributes, can control them. Can even give possessed
Able to heal by shooting self with a projectile of negative damage, which has a different parent. Can even create healing bases this way.
Able to cause the wrath of the anti-cheat mainframe on a unit by shooting it with a projectile whose damage, when subtracted from the test numbers, does not change anything, but sometimes when subtracted from actual health numbers will give user irregularities in health so that it fails security tests
Able to move walls by using the teleporter power exception of the otherwise banned move_ip function

'True Form' burns up everything nearby, able to possess people at will, turn people at stone at will, immune to most other powers, really big and bright, a scripted entity that inhabits any unit you tell it to (even enemies), allowing them to be extremely powerful and assume this form. It also is technically a unit, in a sense that it has a stockpile of resources that are used on its "stats," only because the entity itself does not die but the host, these never diminish. Also has an altar building much like itself, able to inhabit anything. This will assimilate the scripts and resources of a unit into the spirit, then use part of the energy to burn up the drained unit and surrounding units. Compells nearby people towards it.

silver robed ones that can combust in map changing cataclysms, cause storms, turn enemies to stone with glances, occasionally possess defeated enemies, and pool resources to channel and give power to and from the spirit entity (they permanently increase its power, and it in turn grants some help), also able to transfer resources between units that belong to you. Other, allied teams, can actually have these units. These units, while not completely powerless on their own, mostly channel power from the spirit, and do not have any useful scripts contained within themselves.

dragons: 3 uniquely designed dragon units. One capable of flight, fire, extreme speed, and shooting hallucinogenic spines. Another capable of enthralling enemies, possessing them, hiding, moving quickly, and spawning shadow units and walls. A final one capable of controlling weather, and granting armies that rally to it bonuses. This one, while still formidabble in combat and fast, is best used to cause collateral affects and support for armies.

troll: A troll faced unit that throws explosive rubber ducks at people. Capable of possession, usually has a herd of goats on jetpacks accompanying it. Dictated by an AI, always in a game (even one without its creator), harms everyone but those who are its allies. Just causes general chaos.

tower: basically a teleporter building. but not quite, and looks waaay cooler. A really good tower graphic that reaches out of sight into the clouds in the character's territory. Teleport points are suspension-bridge/drawbridge type ramps reaching down from the clouds. Can also spawn units, and can send people jumping down to any point as well as on ramp.



infastructure:
-make the security program
-make documentation for scripters, basically the source with some info not included, like the spirit class that can be used to script possession though even with this class its not easy
-make map
'''