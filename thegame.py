#!/usr/bin/env python

import pygame
import time
import math
import random
import sys
import socket
import threading
import select
from network import *
from Tkinter import *
import Tkinter as tk
import _tkinter
import struct

#def import_block(*args):
#	return time

#__import__ = import_block
#__builtins__.__import__ = import_block

def type(obj):
	if isinstance(obj,attribute) or isinstance(obj,realtime_attribute):
		return int
	else:
		return __builtins__.type(obj)

SPEED = 0.025
COLOR = (150,150,200)

updated              =   pygame.sprite.RenderUpdates()
updated2             =   pygame.sprite.RenderUpdates()
drawn                =   pygame.sprite.RenderUpdates()
collidable           =   pygame.sprite.RenderUpdates()
projectiles          =   pygame.sprite.RenderUpdates()
special              =   pygame.sprite.RenderUpdates()

gravities            =   []
inputters            =   []

units                =   []

screenpos            =   [0,0]

spritename           =   None

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

CURRENCY = 0
login = False
playername = None

class Moveable(pygame.sprite.Sprite):
	def __init__(self,pos,imageFileName):
		pygame.sprite.Sprite.__init__(self)
		self.init2(pos,imageFileName)
		#self.constx = 100
		#self.consty = 100
	def init2(self,pos,imageFileName):
		try:
			self.right = pygame.image.load(imageFileName).convert_alpha()
		except:
			self.right = imageFileName
		self.left = pygame.transform.flip(self.right,True,False)
		self.vertical = pygame.transform.rotate(self.right,90)
		self.image = self.right
		if self not in projectiles:
			self.direction = "right"
		self.rect = self.image.get_rect()
		#print pos, "\n\n\n\n\n\n\n\n\n\n\n\n\n"
		self.rect.center = pos
	def move(self,dx,dy):
		#pygame.display.update(self.draw(screen))
		#print COLOR
		#erase(self)
		#doublebuffer.fill((COLOR),self.rect)
		#screen.fill((COLOR),self.rect)
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
		if self.rect.x < 0:
			dx = 1
		if self.rect.x > 9000:
			dx = -1
		if self.rect.y < 0:
			dy = 1
		if self.rect.y > 4500:
			dy = -1
		if dx != 0 or dy != 0:
			fill(self.rect,self)
		if isinstance(self,character):
			global spritename
			if spritename == self.name:
				movescreen((dx,dy))
		#self.constx += dx
		#self.consty += dy
		if hasattr(self,"animate_move"):
			if dx != 0 or dy != 0:
				try:
					self.animate_move(dx,dy)
				except Exception, e:
					print e
		self.rect.move_ip(dx,dy)
		if dx != 0 or dy != 0:
			doublebuffer.blit(self.image,self.rect.topleft)
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
	def __init__(self,pos,imageFileName,collide,alpha):
		pygame.sprite.Sprite.__init__(self)
		self.init2(pos,imageFileName,collide,alpha)
	def init2(self,pos,imageFileName,collide,alpha):
		drawn.add(self)
		updated.add(self)
		if collide:
			collidable.add(self)
		try:
			if alpha:
				self.image = pygame.image.load(imageFileName).convert_alpha()
			else:
				self.image = pygame.image.load(imageFileName).convert()
		except:
			self.image = imageFileName
		self.rect = self.image.get_rect()
		self.rect.center = pos
	def rangeTo(self,other):
		dx = other.rect.x - self.rect.x
		dy = other.rect.y - self.rect.y
		return math.sqrt(dx*dx + dy*dy)

class item():
	def __init__(self,exports):
		self.attributes = {"maxhealth":attribute(0,2,self,0,1),"maxspeed":attribute(0,25,self,0,1),"maxregen":attribute(0,50,self,0,1),"maxdmg":attribute(0,18,self,0,1),"maxprojectiles":attribute(0,18,self,0,0),"firerate":attribute(0,20,self,0,1)}
		self.parent = parent
		self.exports = exports
	def pipe(self,attr,realattr,value,dest):
		#print attr, __builtins__.type(attr)
		try:
			attr2 = attr
			#print attr, __builtins__.type(attr)
			targattr = realattr
			#print attr, __builtins__.type(attr)
			attr = self.attributes[attr]
			#print attr, __builtins__.type(attr)
			if attr2 != "firerate":
				realattr = dest.realattributes[realattr]
			#print attr, __builtins__.type(attr)
			if attr2 == "firerate":
				if self != dest:
					cost = 2
				else:
					cost = 1
				total = cost*abs(value)
				if total <= self.attributes["firerate"].current and dest.firetime > 0:
					self.attributes["firerate"].__dict__["current"] -= total
					dest.firetime += value
				#print self.firetime, self.attributes["firerate"].current, total
				return
			if attr2 in realattr.maxofanames and attr.__dict__["current"] > 0:
				#print "pipe", attr2, "to", realattr
				if value == "all":
					if attr2 != "maxdamage":
						#if attr2 == "maxhealth":
							#print "changing health"
						dest.realattributes[targattr] = realattr.change(dest,attr.__dict__["current"],passkey(),attr)
					#print attr, __builtins__.type(attr)
				elif value == "-all":
					dest.realattributes[targattr] = realattr.change(dest,attr.__dict__["current"],passkey(),attr)
				else:
					if attr2 != "maxdamage" or abs(value) != value:
						dest.realattributes[targattr] = realattr.change(dest,value,passkey(),attr)
					#print attr, __builtins__.type(attr)
				#print "pipe", attr2, "to", dest.realattributes[targattr], "done"
		except KeyError:
			pass
	def upgrade(self,attr,value):
		#print self.realattributes,self.attributes, self.realattributes.values()
		try:
			old = self.attributes[attr]
			#print attr, old
			self.attributes[attr] += value
			for realattr in self.realattributes.values():
				#print realattr, __builtins__.type(realattr), realattr.__dict__.keys(), realattr.__dict__.values()
				if realattr.maxof == old:
					realattr.__dict__["value"] = old.__dict__["value"]
		except KeyError:
			pass
	def upgrade_store(self,attr,value):
		try:
			attr = self.attributes[attr]
			attr.maximum += value
		except AttributeError:
			pass
	def store(self,attr,value):
		try:
			#print self.attributes
			attr = self.attributes[attr]
			attr.store(value)
		except AttributeError:
			pass
	def withdraw(self,attr,value):
		try:
			attr = self.attributes[attr]
			attr.withdraw(value)
		except KeyError:
			pass

class unit(Moveable):
	def __init__(self,pos,image,code):
		Moveable.__init__(self,pos,image)
		drawn.add(self)
		collidable.add(self)
		updated.add(self)
		units.append(self)
		self.inventory = []
		self.attributes = {"maxhealth":attribute(2000,1,self,10000,1),"maxspeed":attribute(1,50,self,100,1),"maxregen":attribute(1,100,self,50,1),"maxdmg":attribute(300,2,self,2000,1),"maxprojectiles":attribute(3,18,self,0,0),"firerate":attribute(2,20,self,50,1)}
		self.realattributes = {"health":realtime_attribute(0,self,"maxhealth",["maxhealth","maxregen","maxdmg"],"health"),"speed":realtime_attribute(2,self,"maxspeed",["maxspeed","maxhealth"],"speed")}
		self.projectiles = []
		self.firetime = 100
		for number in range(self.attributes["maxprojectiles"]):
			self.projectiles.append(None)
		if code != "":
			load_code(self,code,"_start")
			self._start()
		self.directions2 = (0,0)
		self.anchored = False
		self.tissue = []
	def maintain(self):
		if not self.anchored:
			self.inertia()
			self.directions = (0,0)
			index = 0
			for projectile in self.projectiles:
				if projectile != None:
					if projectile.update() == False:
						projectile.end()
						self.projectiles[index] = None
				index += 1
			for attributething in self.attributes.values():
				if not isinstance(attributething,attribute):
					#print attributething, "caused character annihilation"
					#print __builtins__.type(attributething)
					self.end()
			for attributething in self.realattributes.values():
				if not isinstance(attributething,realtime_attribute):
					#print attributething, "caused character annihilation"
					#print __builtins__.type(attributething)
					self.end()
		if self.realattributes["health"] <= 0:
			print "health at", self.realattributes["health"], "ending..."
			self.end()
	def project(self,bolt,speed=6,direction=None,target=None,accuracy=None,aimed=False):
		#print self.firetime
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
					self.firetime = 100
					break
				index += 1
	def cproject(self,bolt,speed=6,direction=None,target=None,accuracy=None,aimed=False,spawn=None):
		#print self.firetime
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
					self.projectiles[index] = bolt(spawn,direction,self)
					projectiles.add(self.projectiles[index])
					self.firetime = 100
					break
				index += 1
	def end(self):
		self.attributes = {}
		self.realattributes = {}
		for projectile in self.projectiles:
			if projectile != None:
				projectile.end()
		drawn.remove(self)
		collidable.remove(self)
		updated.remove(self)
		special.remove(self)
		#doublebuffer.fill((COLOR),self.rect)
		fill(self.rect,self)
		#screen.fill(COLOR,self.rect)
	def goup(self):
		self.directions = (list(self.directions)[0],list(self.directions)[1]-1)
		self.directions2 = (0,-1)
		#self.inertia()
	def godown(self):
		self.directions = (list(self.directions)[0],list(self.directions)[1]+1)
		self.directions2 = (0,1)
		#self.inertia()
	def goleft(self):
		self.directions = (list(self.directions)[0]-1,list(self.directions)[1])
		self.directions2 = (-1,0)
		#self.inertia()
	def goright(self):
		self.directions = (list(self.directions)[0]+1,list(self.directions)[1])
		self.directions2 = (1,0)
		#self.inertia()
	def magnitude(self,factor):
		return (self.directions[0]*factor,self.directions[1]*factor)
	def magnitude2(self,factor):
		return (self.directions2[0]*factor,self.directions2[1]*factor)
	def inertia(self):
		self.move(*self.magnitude(self.realattributes["speed"]))
	def shoot(self,bolt):
		self.project(bolt,direction=self.magnitude2(10))
	def aimshoot(self,bolt,vector):
		self.project(bolt,direction=vector)
	def upgrade_store(self,attr,value):
		try:
			attr = self.attributes[attr]
			attr.maximum += value
		except AttributeError:
			pass
	def store(self,attr,value):
		try:
			#print self.attributes
			attr = self.attributes[attr]
			attr.store(value)
		except AttributeError:
			pass
	def withdraw(self,attr,value):
		try:
			attr = self.attributes[attr]
			attr.withdraw(value)
		except KeyError:
			pass
	def pipe(self,attr,realattr,value,dest):
		#print attr, __builtins__.type(attr)
		try:
			attr2 = attr
			#print attr, __builtins__.type(attr)
			targattr = realattr
			#print attr, __builtins__.type(attr)
			attr = self.attributes[attr]
			#print attr, __builtins__.type(attr)
			if attr2 != "firerate":
				realattr = dest.realattributes[realattr]
			#print attr, __builtins__.type(attr)
			if attr2 == "firerate":
				if self != dest:
					cost = 2
				else:
					cost = 1
				total = cost*abs(value)
				if total <= self.attributes["firerate"].current and dest.firetime > 0:
					self.attributes["firerate"].__dict__["current"] -= total
					dest.firetime += value
				#print self.firetime, self.attributes["firerate"].current, total
				return
			if attr2 in realattr.maxofanames and attr.__dict__["current"] > 0:
				#print "pipe", attr2, "to", realattr
				if value == "all":
					if attr2 != "maxdamage":
						#if attr2 == "maxhealth":
							#print "changing health"
						dest.realattributes[targattr] = realattr.change(dest,attr.__dict__["current"],passkey(),attr)
					#print attr, __builtins__.type(attr)
				elif value == "-all":
					dest.realattributes[targattr] = realattr.change(dest,attr.__dict__["current"],passkey(),attr)
				else:
					if attr2 != "maxdamage" or abs(value) != value:
						dest.realattributes[targattr] = realattr.change(dest,value,passkey(),attr)
					#print attr, __builtins__.type(attr)
				#print "pipe", attr2, "to", dest.realattributes[targattr], "done"
		except KeyError:
			pass
	def upgrade(self,attr,value):
		#print self.realattributes,self.attributes, self.realattributes.values()
		try:
			old = self.attributes[attr]
			#print attr, old
			self.attributes[attr] += value
			for realattr in self.realattributes.values():
				#print realattr, __builtins__.type(realattr), realattr.__dict__.keys(), realattr.__dict__.values()
				if realattr.maxof == old:
					realattr.__dict__["value"] = old.__dict__["value"]
		except KeyError:
			pass
	def __dir__(*args):
		return ["__init__","__new__","pointer","wrapper"]
	def changeimg(self,image):
		pos = self.rect.center
		self.image = image
		self.right = image
		self.left = pygame.transform.flip(image,True,False)
		self.vertical = pygame.transform.rotate(image,90)
		if self.direction == "right":
			self.image = self.right
		elif self.direction == "left":
			self.image = self.left
		else:
			print "direction value for moveable unit invalid"
			raise RuntimeError
		self.rect = image.get_rect()
		self.rect.center = pos
	#def convoy(self):
	#	pass
	#def acceptconvoy(self):
	#	pass
	def onend(self):
		pass #drops item of unit, for example in the case of a tree, wood.
	def add_tissue(self,tissue):
		self.tissue.append(tissue)
		#here is where it ought to update the central graphics bit, overlaying it onto the rest of it...

class projectile(Moveable):
	def __init__(self,pos,direction,image,simple=True,parent=None,countdown=None):
		Moveable.__init__(self,pos,image)
		self.attributes = {"maxhealth":attribute(25,2,self,200,1),"maxspeed":attribute(10,5,self,40,1)}
		self.realattributes = {"health":realtime_attribute(0,self,"maxhealth",["maxhealth","maxregen","maxdmg"],"health"),"speed":realtime_attribute(2,self,"maxspeed",["maxspeed","maxhealth"],"speed")}
		self.parent = parent
		drawn.add(self)
		self.directions = list(direction)
		if simple == True:
			if abs(self.directions[1]) > abs(self.directions[0]):
				self.image = self.vertical
				self.rect = self.image.get_rect()
				self.rect.center = pos
		else:
			self.image = pygame.transform.rotate(self.vertical,math.degrees(math.atan2(direction[0],direction[1])))
			self.rect = self.image.get_rect()
			self.rect.center = pos
		self.pointer = (0,0)
		projectiles.add(self)
		updated.remove(self)
	def update(self):
		self.manage()
		self.secondarypipe("maxhealth","health","all",self)
		self.secondarypipe("maxspeed","speed","all",self)
		self.realattributes["health"].__dict__["value"] -= 1
		self.inertia()
		self.pointer = (0,0)
		#print "projectile health:", self.realattributes["health"]
		if self.realattributes["health"].__dict__["value"] <= 0:
			#print "health at", self.realattributes["health"], "ending..."
			return False
		else:
			self.pointer = self.setmag(self.directions[0],self.directions[1],self.realattributes["speed"])
			return True
	def adjustmag(self,x,y,change):
		angle = math.atan2(y,x)
		#print "x, y: ", x, y
		magnitude = math.sqrt(x*x+y*y)
		#print "magnitude: ", magnitude
		if magnitude > 1 and change < 0:
			magnitude = float(magnitude) + float(change)
		elif change > 0:
			magnitude = float(magnitude) + float(change)
		nx = math.cos(angle)*float(magnitude)
		ny = math.sin(angle)*float(magnitude)
		return nx, ny
	def setmag(self,x,y,change):
		angle = math.atan2(y,x)
		#print "x, y: ", x, y
		#print "magnitude: ", magnitude
		nx = math.cos(angle)*float(change)
		ny = math.sin(angle)*float(change)
		return nx, ny
	def end(self):
		fill(self.rect,self)
		drawn.remove(self)
		collidable.remove(self)
		projectiles.remove(self)
		updated.remove(self)
	def pipe(self,attr,realattr,value,dest):
		#print "projectile piping..."
		proceed = False
		if pygame.sprite.collide_rect(self,dest):
			proceed = True
		if proceed == False:
			#print "projectile not touching target, pipe rejected\n\n\n\n\n\n\n\n\n\n\n\n"
			return
		try:
			attr2 = attr
			#print attr, __builtins__.type(attr)
			targattr = realattr
			#print attr, __builtins__.type(attr)
			attr = self.parent.attributes[attr]
			#print attr, __builtins__.type(attr)
			if attr2 != "firerate":
				realattr = dest.realattributes[realattr]
			#print attr, __builtins__.type(attr)
			if attr2 == "firerate":
				if self.parent != dest:
					cost = 3
				else:
					cost = 1
				total = cost*abs(value)
				if total <= self.parent.attributes["firerate"].current and dest.firetime > 0:
					self.parent.attributes["firerate"].__dict__["current"] -= total
					dest.firetime += value
				#print self.parent.firetime, self.parent.attributes["firerate"].current, total
				return
			if attr2 in realattr.maxofanames:
				#print "pipe", attr2, "to", targattr
				if value == "all":
					if attr2 != "maxdamage":
						dest.realattributes[targattr] = realattr.change(dest,attr.__dict__["current"],passkey(),attr,3,self)
					#print attr, __builtins__.type(attr)
				elif value == "-all":
					dest.realattributes[targattr] = realattr.change(dest,attr.__dict__["current"],passkey(),attr,3,self)
				else:
					if attr2 != "maxdamage" or abs(value) != value:
						dest.realattributes[targattr] = realattr.change(dest,value,passkey(),attr,3,self)
					#print attr, __builtins__.type(attr)
				#print "pipe", attr2, "to", targattr, "done"
		except KeyError:
			pass
	def secondarypipe(self,attr,realattr,value,dest):
		try:
			attr2 = attr
			targattr = realattr
			attr = self.attributes[attr]
			realattr = dest.realattributes[realattr]
			if attr2 in realattr.maxofanames and attr.__dict__["current"] > 0:
				if value == "all":
					dest.realattributes[targattr] = realattr.change(dest,attr.__dict__["current"],passkey(),attr)
				elif value == "-all":
					dest.realattributes[targattr] = realattr.change(dest,attr.__dict__["current"],passkey(),attr)
				else:
					dest.realattributes[targattr] = realattr.change(dest,value,passkey(),attr)
		except KeyError:
			pass
	def upgrade(self,attr,value):
		#print self.realattributes,self.attributes, self.realattributes.values()
		try:
			old = self.attributes[attr]
			#print attr, old
			self.attributes[attr] += value
			for realattr in self.realattributes.values():
				#print realattr, __builtins__.type(realattr), realattr.__dict__.keys(), realattr.__dict__.values()
				if realattr.maxof == old:
					realattr.__dict__["value"] = old.__dict__["value"]
		except KeyError:
			pass
	def magnitude(self,factor):
		return (self.pointer[0]*factor,self.pointer[1]*factor)
	def magnitude2(self,factor):
		return (self.directions2[0]*factor,self.directions2[1]*factor)
	def inertia(self):
		fill(self.rect,self)
		#doublebuffer.fill((COLOR),self.rect)
		self.rect.move_ip(*self.pointer)
		doublebuffer.blit(self.image,self.rect.topleft)

#class thermal(projectile):
#	def __init__(self,pos,direction,parent,temp):
#		self.temp = temp
#		if self.temp > 0:
#			img = images["heat"]
#		else:
#			img = images["cool"]
#		projectile.__init__(self,pos,direction,img,simple=False,parent=parent)
#	def manage(self):
#		collisions = pygame.sprite.spritecollide(self, collidable, False)
#		for other in collisions:
#			if other != self and other != self.parent and isinstance(other,unit):
#				if self.temp > 0:
#					if other.fireproof < self.temp:
#						self.pipe("maxdamage","health",self.temp,other)
#						self.parent.cproject(thermal,direction=(random.choice(range(5)),random.choice(range(5))))
#					if other.melt < self.temp:
#						other.melt()
#				else:
#					self.pipe("maxspeed","speed",self.temp,other)
#					self.pipe("maxdamage","health",-self.temp/4,other)
#			elif other != self and isinstance(other,thermal):
#				other.temp = (other.temp+self.temp)/2
#				self.temp = (other.temp+self.temp)/2

#class electron(projectile):  #Able to travel over objects with upgraded conductivity stats, able to create magnetic feilds, able to create thunderbolt arcs if lined up correctly.
#	pass

#class graviton(projectile):  #Able to push or pull with spacial impact. The advantage to this is that it has a constant push and pull with the projectile's lifetime, so if manipulated carefully it can give a better spacial impact value.
#	pass

#class air(projectile):  #Usually can't do much. However, if manipulated skillfully can create air with vacuum attribute that puts out fire and damages, or create large storms or blasts of air.
#	pass

#class life(projectile):  #Able to boost indigenous wildlife units and plants. Also able to, if used cleverly, revive fallen units, which normally does not work. This has a cost though.
#	pass

#class anomaly(projectile):  #A spacial anomaly. Does weird things if used correctly. For example it can produce portals if arrayed in a circle and made to spin around a fixed point.
#	pass

#class effect(projectile):  #An effect bound to an enemy unit. This is not like an item, it deliberately has restricted access, but it functions autonomously. Most notably used to reduce cost of attacking without shooting a pre-existing projectile, as it attatches to an enemy and extends life upon attattchment, but can only make the same, repeated changes, over and over again.
#	pass

#class water(projectile):  #Drops collidable water formations so that a spray will define a single, largish lake sprite. Control of these projectiles can control water or water body sprites and do damage at high speeds.
#	pass

#class illusion(projectile):  #Creation of shadow and light particles. Both can blind vision.
#	pass

#class timepiece(projectile):  #Can speed up or slow down time, at a very, very high cost. Everyone speeds up together, but it can still throw people off if manipulated in your favor, taking advantage in enemy reaction times.
#	pass

#class magnetic(projectile):  #Attracts metals or ferromagnetic attribute high substances. Useful primarily to, when used with heat and electricity, create electromagnetic storms and plasma arcs.
#	pass

class barrier(Stationary):
	def __init__(self,pos,imageFileName,alphas):
		Stationary.__init__(self,pos,imageFileName,True,alphas)

class character(unit):   #Technically all this is the central tissue object... It has its own manage function. However the number of function calls on this will obviously be limitted and all that. And this holds all the sub-parts.
	def __init__(self,pos,image,code,socket):
		unit.__init__(self,pos,image,code)
		self.directions = (1,0)
		self.aim = [12,0]
		self.aim2 = [12,0]
		self.socket = socket
		self.name = None
	def update(self):
		event = "EMPTY"
		while event != None:
			event = self.socket.recv_data()
			if event != None and event != '':
				if hasattr(self,event):
					function = getattr(self,event)
					try:
						function()
					except Exception, e:
						try:
						#if True:
							function(self)
						except Exception, e:
							print e
				else:
					print "failed event: ", event, "is not a valid function of character", self.name
		self.manage()
		for component in self.tissue:
			if isinstance(component,piece):
				component.manage(self)
			else:
				print "Error... A non-tissue object is stored in "+self.name+"'s tissue list."
		self.maintain()
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

class tree(unit):
	def __init__(self,pos,dna):
		self.dna = dna   #[(trunk rgb), (leaf rgb 1), (leaf rgb 2),angle variability,angle change]   [(120,200,70),(100,180,70),(100,150,100),50,20]
		self.directions = (1,0)
		self.aim = [12,0]
		self.aim2 = [12,0]
		self.socket = None
		self.name = None
		unit.__init__(self,pos,self.maketree(),str())
		self.anchored = True
		del self.attributes["maxspeed"]
		del self.attributes["maxdmg"]
		del self.attributes["maxregen"]
		del self.attributes["maxprojectiles"]
		del self.attributes["firerate"]
		del self.realattributes["speed"]
		self.pipe("maxhealth","health","all",self)
	def drawtree(self,x1, y1, angle, depth,picture):
		if depth:
			#random.seed(self.dna[5][0])
			angle += random.randrange(-self.dna[3]+depth*7,self.dna[3]-depth*7)
			x2 = x1 + int(math.cos(math.radians(angle)) * depth * 3.0)
			y2 = y1 + int(math.sin(math.radians(angle)) * depth * 3.0)
			pygame.draw.line(picture, (self.dna[0][0],self.dna[0][1]-depth*20,self.dna[0][2]), (x1, y1), (x2, y2), depth)
			self.drawtree(x2, y2, angle-self.dna[4], depth-1, picture)
			self.drawtree(x2, y2, angle+self.dna[4], depth-1, picture)
		else:
			#for thing in range(20):
			if True:
				##random.seed(self.dna[5][1])
				x1 += random.randrange(-6,7)
				##random.seed(self.dna[5][2])
				y1 += random.randrange(-6,7)
				shape = []
				for point in range(5):
					##random.seed(self.dna[5][3])
					x3 = x1+random.randrange(-4,5)
					##random.seed(self.dna[5][4])
					y3 = y1+random.randrange(-4,5)
					shape.append((x3,y3))
				##random.seed(self.dna[5][5])
				color1 = self.dna[1][0]+random.randrange(-20,20)
				##random.seed(self.dna[5][6])
				color2 = self.dna[1][1]+random.randrange(-20,20)
				##random.seed(self.dna[5][7])
				color3 = self.dna[1][2]+random.randrange(-20,20)
				##random.seed(self.dna[5][8])
				color4 = self.dna[2][0]+random.randrange(-20,20)
				##random.seed(self.dna[5][9])
				color5 = self.dna[2][1]+random.randrange(-20,20)
				##random.seed(self.dna[5][10])
				color6 = self.dna[2][2]+random.randrange(-20,20)
				pygame.draw.polygon(picture, (color1,color2,color3), shape)
				pygame.draw.polygon(picture, (color4,color5,color6), shape,1)
	def maketree(self):
		img = pygame.Surface((80,80))
		img.fill((255,255,255))
		img.set_colorkey((255,255,255))
		self.drawtree(40,80,-90,6,img)
		return img
	def update(self):
		self.pipe("maxhealth","health","all",self)
		self.maintain()

class bolt(projectile):
		def __init__(self,pos,direction,parent):
			projectile.__init__(self,pos,direction,"pulse.png",simple=True,parent=parent)
		def manage(self):
			collisions = pygame.sprite.spritecollide(self, collidable, False)
			for other in collisions:
				if other != self and other != self.parent and isinstance(other,unit):
					self.pipe("maxdmg","health",-99,other)

class generic(character):
	def __init__(self,sockets,pos):
		self.aim = [0,0]
		character.__init__(self,pos,"generic.png","",sockets)
		self.pipe("maxhealth","health","all",self)
	def manage(self):
		#print self.realattributes["health"]
		#print "manage called"
		self.pipe("maxhealth","health","all",self)
		self.pipe("maxregen","health","all",self)
		self.pipe("firerate","firetime",-2,self)
		self.pipe("maxspeed","speed","all",self)
		#print self.realattributes["health"]
		#print self.realattributes["health"]
	def _w(self,*args):
		self.goup()
	def _s(self,*args):
		self.godown()
	def _a(self,*args):
		self.goleft()
	def _d(self,*args):
		self.goright()
	def _e(self,*args):
		self.shoot(bolt)

class wall(barrier):
	def __init__(self,pos):
		barrier.__init__(self,pos,"thewall.png",True)

class fake_dict2(str):
	def __new__(cls, *args, **kwargs):
		return  super(fake_dict, cls).__new__(cls, "Traceback (most recent call last):\n    File \"<stdin>\", line 634, in <module>\n    AttributeError: 'int' object has no attribute '__dict__'")
	def __init__(self,*args):
		pass
	def __getitem__(self, key):
		return self.__dict__[key]
	def __setitem__(self, key, value):
		self.__dict__[key] = value

class fake_dict(dict):
	def __new__(cls, *args, **kwargs):
		return  super(fake_dict, cls).__new__(cls, {})
	def __init__(self,*args):
		pass
	def __str__(self):
		return "Traceback (most recent call last):\n    File \"<stdin>\", line 17, in <module>\n    AttributeError: 'int' object has no attribute '__dict__'"
	def __repr__(self):
		return "Traceback (most recent call last):\n    File \"<stdin>\", line 12, in <module>\n    AttributeError: 'int' object has no attribute '__dict__'"

def __setattr__(self, name, value):
		if name != "value" and name != "current" and name != "maximum" and name != "decay" and name != "pool" and name[:2] != "__" and name != "rcurrent":
			self.__dict__[name] = value

class attribute(int):
	def __new__(cls, *args, **kwargs):
		return  super(attribute, cls).__new__(cls, args[0])
	def __init__(self,value,cost,parent,maximum,decay,fakedict=True,maximums=True):
		int.__init__(self)
		if fakedict == True:
			self.__dict__ = fake_dict()
		self.__setattr__ = __setattr__
		self.cost = cost
		self.__dict__["value"] = value
		self.parent = parent
		self.__dict__["current"] = self.__dict__["value"]
		self.__dict__["rcurrent"] = self.__dict__["value"]
		if maximums == True:
			self.__dict__["maximum"] = attribute(maximum,1,parent,0,0,fakedict=False,maximums=False)
			self.__dict__["decay"] = decay
			self.__dict__["pool"] = 0
		#updated_attr.insert(0,self)
	def __pos__(self):
		pass
		return attribute(self.__dict__["value"],self.cost,self.parent,self.maximum,self.decay)
	def __neg__(self):
		pass
		return attribute(self.__dict__["value"],self.cost,self.parent,self.maximum,self.decay)
	def __abs__(self):
		pass
		return attribute(self.__dict__["value"],self.cost,self.parent,self.maximum,self.decay)
	def __invert__(self):
		pass
		return attribute(self.__dict__["value"],self.cost,self.parent,self.maximum,self.decay)
	def __round__(self, n):
		pass
		return attribute(self.__dict__["value"],self.cost,self.parent,self.maximum,self.decay)
	def __floor__(self):
		pass
		return attribute(self.__dict__["value"],self.cost,self.parent,self.maximum,self.decay)
	def __ceil__(self):
		pass
		return attribute(self.__dict__["value"],self.cost,self.parent,self.maximum,self.decay)
	def __trunc__(self):
		pass
		return attribute(self.__dict__["value"],self.cost,self.parent,self.maximum,self.decay)
	def __add__(self,other):
		global CURRENCY
		if CURRENCY > self.cost*other:
			CURRENCY -= self.cost*other
			self.__dict__["value"] += other
			pass
			return attribute(self.__dict__["value"],self.cost,self.parent,self.maximum,self.decay)
		else:
			pass
			return attribute(self.__dict__["value"],self.cost,self.parent,self.maximum,self.decay)
	def __sub__(self,other):
		global CURRENCY
		if self.__dict__["value"] > other:
			CURRENCY += self.cost*other
			self.__dict__["value"] -= other
			pass
			return attribute(self.__dict__["value"],self.cost,self.parent,self.maximum,self.decay)
		else:
			pass
			return attribute(self.__dict__["value"],self.cost,self.parent,self.maximum,self.decay)
	def __mul__(self,*args):
		pass
		return attribute(self.__dict__["value"],self.cost,self.parent,self.maximum,self.decay)
	def __div__(self,*args):
		pass
		return attribute(self.__dict__["value"],self.cost,self.parent,self.maximum,self.decay)
	def __floordiv__(self,*args):
		pass
		return attribute(self.__dict__["value"],self.cost,self.parent,self.maximum,self.decay)
	def __truediv__(self,*args):
		pass
		return attribute(self.__dict__["value"],self.cost,self.parent,self.maximum,self.decay)
	def __mod__(self,*args):
		pass
		return attribute(self.__dict__["value"],self.cost,self.parent,self.maximum,self.decay)
	def __divmod__(self,*args):
		pass
		return attribute(self.__dict__["value"],self.cost,self.parent,self.maximum,self.decay)
	def __pow__(self,*args):
		pass
		return attribute(self.__dict__["value"],self.cost,self.parent,self.maximum,self.decay)
	def __lshift__(self,*args):
		pass
		return attribute(self.__dict__["value"],self.cost,self.parent,self.maximum,self.decay)
	def __rshift__(self,*args):
		pass
		return attribute(self.__dict__["value"],self.cost,self.parent,self.maximum,self.decay)
	def __and__(self,*args):
		pass
		return attribute(self.__dict__["value"],self.cost,self.parent,self.maximum,self.decay)
	def __or__(self,*args):
		pass
		return attribute(self.__dict__["value"],self.cost,self.parent,self.maximum,self.decay)
	def __xor__(self,*args):
		pass
		return attribute(self.__dict__["value"],self.cost,self.parent,self.maximum,self.decay)
	def __iadd__(self, other):
		pass
		return self.__add__(other)
	def __isub__(self, other):
		pass
		return self.__sub__(other)
	def __imul__(self,*args):
		pass
		return attribute(self.__dict__["value"],self.cost,self.parent,self.maximum,self.decay)
	def __idiv__(self,*args):
		pass
		return attribute(self.__dict__["value"],self.cost,self.parent,self.maximum,self.decay)
	def __ifloordiv__(self,*args):
		pass
		return attribute(self.__dict__["value"],self.cost,self.parent,self.maximum,self.decay)
	def __itruediv__(self,*args):
		pass
		return attribute(self.__dict__["value"],self.cost,self.parent,self.maximum,self.decay)
	def __imod__(self,*args):
		pass
		return attribute(self.__dict__["value"],self.cost,self.parent,self.maximum,self.decay)
	def __ipow__(self,*args):
		pass
		return attribute(self.__dict__["value"],self.cost,self.parent,self.maximum,self.decay)
	def __ilshift__(self,*args):
		pass
		return attribute(self.__dict__["value"],self.cost,self.parent,self.maximum,self.decay)
	def __irshift__(self,*args):
		pass
		return attribute(self.__dict__["value"],self.cost,self.parent,self.maximum,self.decay)
	def __iand__(self,*args):
		pass
		return attribute(self.__dict__["value"],self.cost,self.parent,self.maximum,self.decay)
	def __ior__(self,*args):
		pass
		return attribute(self.__dict__["value"],self.cost,self.parent,self.maximum,self.decay)
	def __ixor__(self,*args):
		pass
		return attribute(self.__dict__["value"],self.cost,self.parent,self.maximum,self.decay)
	def __dir__(self):
		return dir(self.__dict__["value"])
	def update(self):
		#print "unreal update"
		if self.__dict__["current"] < self.__dict__["value"]:
			self.__dict__["current"] = self.__dict__["value"]
		if hasattr(self,"pool"):
			if random.choice(range(100)) == 5:
				if self.__dict__["pool"] > 0:
					self.__dict__["pool"] -= self.decay
	def store(self,value):
		if hasattr(self,"pool"):
			if self.__dict__["pool"]+value <= self.__dict__["maximum"] and self.__dict__["pool"]+value >= 0 and self.__dict__["current"] >= value:
				if self.__dict__["current"] - value >= 0:
					#print self.__dict__["current"], value, self.__dict__["current"] - value
					self.__dict__["current"] = self.__dict__["current"] - value
					self.__dict__["pool"] += value
	def withdraw(self,value):
		if hasattr(self,"pool"):
			if self.__dict__["pool"]-value <= self.__dict__["maximum"] and self.__dict__["pool"]-value >= 0 and self.__dict__["pool"] >= value:
				self.__dict__["current"] += value
				self.__dict__["rcurrent"] += value
				self.__dict__["pool"] -= value
	def upmax(self,value):
		if hasattr(self,"pool"):
			self.__dict__["maximum"] += value

class passkey():
	def __init__(self):
		pass

class realtime_attribute(int):
	def __new__(cls, *args, **kwargs):
		return  super(realtime_attribute, cls).__new__(cls, args[0])
	def __init__(self,value,parent,maxof,adders,name):
		int.__init__(self)
		self.__dict__ = fake_dict()
		self.__setattr__ = __setattr__
		self.name = name
		self.cost = None
		self.__dict__["value"] = value
		self.parent = parent
		self.maxofanames = adders
		self.maxof = maxof
		#updated_attr2.insert(0,self)
	def __pos__(self):
		#updated_attr2.remove(self)
		return realtime_attribute(self.__dict__["value"],self.parent,self.maxof,self.maxofanames,self.name)
	def __neg__(self):
		#updated_attr2.remove(self)
		return realtime_attribute(self.__dict__["value"],self.parent,self.maxof,self.maxofanames,self.name)
	def __abs__(self):
		#updated_attr2.remove(self)
		return realtime_attribute(self.__dict__["value"],self.parent,self.maxof,self.maxofanames,self.name)
	def __invert__(self):
		#updated_attr2.remove(self)
		return realtime_attribute(self.__dict__["value"],self.parent,self.maxof,self.maxofanames,self.name)
	def __round__(self, n):
		#updated_attr2.remove(self)
		return realtime_attribute(self.__dict__["value"],self.parent,self.maxof,self.maxofanames,self.name)
	def __floor__(self):
		#updated_attr2.remove(self)
		return realtime_attribute(self.__dict__["value"],self.parent,self.maxof,self.maxofanames,self.name)
	def __ceil__(self):
		#updated_attr2.remove(self)
		return realtime_attribute(self.__dict__["value"],self.parent,self.maxof,self.maxofanames,self.name)
	def __trunc__(self):
		#updated_attr2.remove(self)
		return realtime_attribute(self.__dict__["value"],self.parent,self.maxof,self.maxofanames,self.name)
	def __add__(self,other):
		#updated_attr2.remove(self)
		return realtime_attribute(self.__dict__["value"],self.parent,self.maxof,self.maxofanames,self.name)
	def __sub__(self,other):
		#updated_attr2.remove(self)
		return realtime_attribute(self.__dict__["value"],self.parent,self.maxof,self.maxofanames,self.name)
	def __mul__(self,*args):
		#updated_attr2.remove(self)
		return realtime_attribute(self.__dict__["value"],self.parent,self.maxof,self.maxofanames,self.name)
	def __div__(self,*args):
		#updated_attr2.remove(self)
		return realtime_attribute(self.__dict__["value"],self.parent,self.maxof,self.maxofanames,self.name)
	def __floordiv__(self,*args):
		#updated_attr2.remove(self)
		return realtime_attribute(self.__dict__["value"],self.parent,self.maxof,self.maxofanames,self.name)
	def __truediv__(self,*args):
		#updated_attr2.remove(self)
		return realtime_attribute(self.__dict__["value"],self.parent,self.maxof,self.maxofanames,self.name)
	def __mod__(self,*args):
		#updated_attr2.remove(self)
		return realtime_attribute(self.__dict__["value"],self.parent,self.maxof,self.maxofanames,self.name)
	def __divmod__(self,*args):
		#updated_attr2.remove(self)
		return realtime_attribute(self.__dict__["value"],self.parent,self.maxof,self.maxofanames,self.name)
	def __pow__(self,*args):
		#updated_attr2.remove(self)
		return realtime_attribute(self.__dict__["value"],self.parent,self.maxof,self.maxofanames,self.name)
	def __lshift__(self,*args):
		#updated_attr2.remove(self)
		return realtime_attribute(self.__dict__["value"],self.parent,self.maxof,self.maxofanames,self.name)
	def __rshift__(self,*args):
		#updated_attr2.remove(self)
		return realtime_attribute(self.__dict__["value"],self.parent,self.maxof,self.maxofanames,self.name)
	def __and__(self,*args):
		#updated_attr2.remove(self)
		return realtime_attribute(self.__dict__["value"],self.parent,self.maxof,self.maxofanames,self.name)
	def __or__(self,*args):
		#updated_attr2.remove(self)
		return realtime_attribute(self.__dict__["value"],self.parent,self.maxof,self.maxofanames,self.name)
	def __xor__(self,*args):
		#updated_attr2.remove(self)
		return realtime_attribute(self.__dict__["value"],self.parent,self.maxof,self.maxofanames,self.name)
	def __iadd__(self, other):
		return self.__add__(other)
	def __isub__(self, other):
		return self.__sub__(other)
	def __imul__(self,*args):
		#updated_attr2.remove(self)
		return realtime_attribute(self.__dict__["value"],self.parent,self.maxof,self.maxofanames,self.name)
	def __idiv__(self,*args):
		#updated_attr2.remove(self)
		return realtime_attribute(self.__dict__["value"],self.parent,self.maxof,self.maxofanames,self.name)
	def __ifloordiv__(self,*args):
		#updated_attr2.remove(self)
		return realtime_attribute(self.__dict__["value"],self.parent,self.maxof,self.maxofanames,self.name)
	def __itruediv__(self,*args):
		#updated_attr2.remove(self)
		return realtime_attribute(self.__dict__["value"],self.parent,self.maxof,self.maxofanames,self.name)
	def __imod__(self,*args):
		#updated_attr2.remove(self)
		return realtime_attribute(self.__dict__["value"],self.parent,self.maxof,self.maxofanames,self.name)
	def __ipow__(self,*args):
		#updated_attr2.remove(self)
		return realtime_attribute(self.__dict__["value"],self.parent,self.maxof,self.maxofanames,self.name)
	def __ilshift__(self,*args):
		#updated_attr2.remove(self)
		return realtime_attribute(self.__dict__["value"],self.parent,self.maxof,self.maxofanames,self.name)
	def __irshift__(self,*args):
		#updated_attr2.remove(self)
		return realtime_attribute(self.__dict__["value"],self.parent,self.maxof,self.maxofanames,self.name)
	def __iand__(self,*args):
		#updated_attr2.remove(self)
		return realtime_attribute(self.__dict__["value"],self.parent,self.maxof,self.maxofanames,self.name)
	def __ior__(self,*args):
		#updated_attr2.remove(self)
		return realtime_attribute(self.__dict__["value"],self.parent,self.maxof,self.maxofanames,self.name)
	def __ixor__(self,*args):
		#updated_attr2.remove(self)
		return realtime_attribute(self.__dict__["value"],self.parent,self.maxof,self.maxofanames,self.name)
	def __dir__(self):
		return dir(self.__dict__["value"])
	def change(self,other,value,key,maxattr,cost=None,parent=None):
		#print "real pipe"
		#print "pipe", maxattr.current, value, self
		if isinstance(key,passkey):
			if cost == None:
				group = pygame.sprite.RenderUpdates()
				group.add(other)
				if parent == None:
					collisions = pygame.sprite.spritecollide(self.parent, group, False)
				else:
					collisions = pygame.sprite.spritecollide(parent, group, False)
				for contact in collisions:
					if contact != self and isinstance(contact,unit) and contact == other and other != self.parent:
						cost = 2
					elif other == self.parent:
						cost = 1
					else:
						cost = 8
			if maxattr.current >= cost*abs(value):
				if abs(value)+self.__dict__["value"] <= self.parent.attributes[self.maxof].__dict__["current"] or abs(value)+self.__dict__["value"] <= self.parent.attributes[self.maxof].__dict__["value"] or maxattr == self.parent.attributes[self.maxof]:
					maxattr.__dict__["current"] -= cost*abs(value)
					#updated_attr2.remove(self)
					#if self.name != "speed" or self.__dict__["value"]+value >= 0:
					return realtime_attribute(self.__dict__["value"]+value,self.parent,self.maxof,self.maxofanames,self.name)
		#updated_attr2.remove(self)
		return realtime_attribute(self.__dict__["value"],self.parent,self.maxof,self.maxofanames,self.name)
	def update(self):
		#print "real update"
		#the issue is, the current attribute pool is withdrawed from and spent before the update function can empty it, meaning it does not account for the flare in a given attribute, and the attribute is permanently increased.
		if self.__dict__["value"]-self.parent.attributes[self.maxof].__dict__["current"] > 0 or self.name == "health":
			#print "update:", self.__dict__["value"], "to", self.__dict__["value"]-self.parent.attributes[self.maxof].__dict__["rcurrent"]
			rcurrent = self.parent.attributes[self.maxof].__dict__["rcurrent"]
			self.parent.attributes[self.maxof].__dict__["rcurrent"] = self.parent.attributes[self.maxof].__dict__["value"]
			return realtime_attribute(self.__dict__["value"]-rcurrent,self.parent,self.maxof,self.maxofanames,self.name)
		else:
			#print "update:", self.__dict__["value"], "to 0"
			return realtime_attribute(0,self.parent,self.maxof,self.maxofanames,self.name)

"""
several types of attributes in the system:

max attribute- the total of an attribute, like max health, max damage, max heal, max speed
current attribute- stuff like health, speed

Max attributes cost currency to change
Current attributes are changeable per round based upon max attributes. Certain rules are applied that make applying your max attributes to other sprites difficult and more costly. Certain rules also need to be made to make draining practical.

system
----------
- Realtime attributes can be changed by the current max attribute pool per turn. However, this pool also has a third attribute, of charge-up, attatched to it. This is simply its max charge up. There is, essentially, a baseline attribute. However, you also have a supply pool, with a level of decay associated with it. You may store power in this pool (which costs more than using it) or withdraw it during a turn. The pool can be affected by external forces. This means that any other object with a pool of power may transfer its power to another player's pool, or, if you are clever, you can even drain other people's pools. This is most commonly done in several ways. A basic health draining system is already available. One can also steal any number of attributes if they manage to either encapsulate the unit in an item and draw even on their max attributes, or drain whatever realtime attributes remain present in a fallen ememy.

one can also pipe their own health into other attributes.

other things that cost currency:

-initializing a new unit
-initializing a new stationary
-initializing a new item
-changing image of sprite (only works on your own sprite)
"""

def load_character(name,kind,pos):
	global serverhost
	global spritename
	netsocket = socket(PORT)
	netsocket.connect(serverhost)
	netsocket.send("character")
	netsocket.send(name)
	avatar = kind(netsocket,pos)
	avatar.name = name
	if spritename == avatar.name:
		#print "panning data: ", avatar.constx, avatar.consty, screenpos
		#setscreen(((avatar.rect.x-((root.winfo_screenwidth()/5.0)*4.0)-25.0)/2.0,avatar.rect.y-(root.winfo_screenheight()-100)/2))
		setscreen((avatar.rect.x-displaysize[0]/2,avatar.rect.y-displaysize[1]/2))
	if isinstance(avatar,character):
		all_characters.update({name:avatar})
	else:
		if isinstance(avatar,tree):
			all_characters.update({name:avatar})
		else:
			print "rejected fraudulent character"
	doublebuffer.blit(avatar.image,avatar.rect.topleft)
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
	global playername
	global spritename
	while True:
		connected = False
		myname = tkinput2("name unit to control")
		spritename = myname
		if myname in eventsenders:
			fore = eventsenders[myname]
			codesend = codesenders[myname]
			avatar = all_characters[spritename]
			#setscreen(((avatar.rect.x-((root.winfo_screenwidth()/5.0)*4.0)-25.0)/2.0,avatar.rect.y-(root.winfo_screenheight()-100)/2))
			setscreen((avatar.rect.x-displaysize[0]/2,avatar.rect.y-displaysize[1]/2))
		else:
			fore = socket(PORT)
			fore.connect(serverhost)
			fore.send_data("event_handler")
			fore.send_data(myname)
			fore.send_data(playername)
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

def recvimages(serverhost):
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

def movescreen(direction):
	#for sprite in everything:
		#screen.fill((COLOR),sprite.rect)
		#doublebuffer.fill((COLOR),sprite.rect)
		#sprite.rect.move_ip(-direction[0],-direction[1])
	#pygame.display.update(backs.draw(screen))
	#backs.draw(doublebuffer)
	#optimize this
	screenpos[0] += direction[0]
	screenpos[1] += direction[1]
	#print screenpos

def setscreen(direction):
	#for sprite in everything:
		#screen.fill((COLOR),sprite.rect)
		#doublebuffer.fill((COLOR),sprite.rect)
		#sprite.rect.move_ip(-direction[0],-direction[1])
	#pygame.display.update(backs.draw(screen))
	#backs.draw(doublebuffer)
	#optimize this
	screenpos[0] = direction[0]
	screenpos[1] = direction[1]
	screen.fill(COLOR)
	#print screenpos

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
	server_conn.send("new")
	server_conn.send_data(tkinput("enter username"))
	server_conn.send_data(tkinput("enter user id"))
	server_conn.send_data(tkinput("enter email"))

def login():
	global CURRENCY
	global login
	global playername
	server_conn.send("login")
	playername = tkinput("enter username")
	server_conn.send(playername)
	server_conn.send(tkinput("enter user id"))
	CURRENCY = int(server_conn.recv_data(poll=False))
	login = True

def add_others(serverhost):
	account_adder = socket(1340)
	account_adder.connect(serverhost)
	account_adder.send("account_adder")
	while True:
		info = account_adder.recv_data(poll=False)
		#print info
		exec info
		allsprites = others.values()
		allsprites.append(default)
		accepted = True
		#for sprite in allsprites:
		#	if isinstance(sprite,character) != True and sprite != None:
		#		print "rejecting fraudulent character"
		#		print sprite
		#		accepted = False
		if accepted:
			user_info.update({account_name:[default,others]})

root = tk.Tk()
root.wm_title("OpenBox")
displaysize = (((root.winfo_screenwidth()/5)*4)-25, root.winfo_screenheight()-100)
embed = tk.Frame(root, width = displaysize[0], height = displaysize[1])
embed.grid(columnspan = displaysize[0], rowspan = displaysize[1])
embed.pack(side=LEFT)
tkwin = tk.Frame(root, width = (root.winfo_screenwidth()/5)-25, height = root.winfo_screenheight()-100)
tkwin.pack(side=RIGHT)
os.environ['SDL_WINDOWID'] = str(embed.winfo_id())
if sys.platform == "win32":
	os.environ['SDL_VIDEODRIVER'] = 'windib'

if len(sys.argv) > 1:
	if sys.argv[1] == "-f":
		root.attributes("-fullscreen", True)

pygame.init()
screen = pygame.display.set_mode((displaysize[0], displaysize[1]))
doublebuffer = pygame.Surface((9000,4500))

#class background(Stationary):
#	def __init__(self):
#		Stationary.__init__(self,(2248,2248),"background.png",False,alpha=True)
#		drawn.remove(self)
#		backs.add(self)

#back = background()

back = pygame.image.load("background.png").convert_alpha()
backrect = back.get_rect()

eventgetter = Text(tkwin, width=10,height=5, state = DISABLED)
eventgetter.place(relx=0.5, rely=0.15, anchor=CENTER)
eventgetter.bind("<KeyPress>", keyhandle)
eventgetter.bind("<KeyRelease>", keyhandleup)
root.bind("<KeyRelease>", keyhandleup)
root.bind("<KeyPress>", endhandle)

inputter = Entry(tkwin)
inputter.place(relx=0.5, rely=0.45, anchor=CENTER)

button1 = Button(tkwin,text = 'enter',  command=get_input)
button1.place(relx=0.5, rely=0.50, anchor=CENTER)

prompt = Text(tkwin, width=25, height=1, state = DISABLED)
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

button5 = Button(tkwin,text = 'login',  command=login)
button5.place(relx=0.3, rely=0.3, anchor=CENTER)

button6 = Button(tkwin,text = 'create account',  command=make_account)
button6.place(relx=0.7, rely=0.3, anchor=CENTER)

serverhost = tkinput("enter server host")
server_conn = socket(PORT)
server_conn.connect(serverhost)
server_conn.send("game")
while login != True:
	root.update()

mythread1 = threading.Thread(target = addcharacters)
mythread1.start()

mythread1 = threading.Thread(target = sendcode)
mythread1.start()

mythread1 = threading.Thread(target = sendimages)
mythread1.start()

mythread = threading.Thread(target=add_others,args=[serverhost])
mythread.start()

def fill(rect,sprite=None):
	doublebuffer.fill((COLOR),rect)
	doublebuffer.blit(back,rect.topleft,rect)
	if sprite != None:
		collisions = pygame.sprite.spritecollide(sprite, collidable, False)
		for other in collisions:
			if other != sprite and other in drawn:
				tofill = other.rect
				doublebuffer.blit(other.image,tofill.topleft)
	pygame.display.update(rect)

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
					#print "sending", controls[item][1]
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
					#print command, user_info
					if command.split()[2] in user_info[command.split()[3]][1].keys():
						#print user_info[command.split()[3]]
						#load_character(command.split()[2],user_info[command.split()[3]][1][command.split()[2]],(100-(screenpos[0]-300),100-(screenpos[1]-300)))
						load_character(command.split()[2],user_info[command.split()[3]][1][command.split()[2]],(100,100))
					else:
						#load_character(command.split()[2],user_info[command.split()[3]][0],(100-(screenpos[0]-300),100-(screenpos[1]-300)))
						load_character(command.split()[2],user_info[command.split()[3]][0],(100,100))
		time.sleep(SPEED)
		for item in units:
			#print item.realattributes
			for attr in item.attributes.values():
				attr.update()
			for attr in item.realattributes.keys():
				#item.realattributes.remove(attr)
				#item.realattributes[attr] = attr.update()
				item.realattributes.update({attr:item.realattributes[attr].update()})
			#for attr in item.attributes.values():
			#	attr.update()
		for item in projectiles:
			#print item.realattributes
			for attr in item.attributes.values():
				attr.update()
			for attr in item.realattributes.keys():
				#item.realattributes.remove(attr)
				#item.realattributes[attr] = attr.update()
				item.realattributes.update({attr:item.realattributes[attr].update()})
			#for attr in item.attributes.values():
			#	attr.update()
		updated.update()
		#print "drawing sprites"
		#backs.draw(screen)
		#pygame.display.update(drawn.draw(screen))
		#doublebuffer.fill((COLOR),backrect)
		#backs.draw(doublebuffer)
		#doublebuffer.blit(back,(0,0))
		#drawn.draw(doublebuffer)
		screen.blit(doublebuffer,(-screenpos[0],-screenpos[1]))
		pygame.display.flip()
		self.loading = loading
		self.downloading = downloading
		self.imgdata = imgdata

def start():
	global server_conn
	#screen.fill((COLOR))
	doublebuffer.fill((COLOR))
	pygame.display.flip()
	#pygame.display.update(backs.draw(screen))
	#pygame.display.update(drawn.draw(screen))
	#backs.draw(doublebuffer)
	doublebuffer.blit(back,(0,0))
	drawn.draw(doublebuffer)
	screen.blit(doublebuffer,(-screenpos[0],-screenpos[1]))
	pygame.display.flip()
	game = globe()
	marker = 0
	while True:
		game.run()
		root.update()

default_new = generic

#for thing in range(100):
#	tree((random.randrange(50,1200),random.randrange(3200,4450)),[(120,200,70),(100,150,100),(80,180,70),52,20])

#for thing in range(70):
#	tree((random.randrange(3500,4450),random.randrange(2000,4450)),[(120,180,100),(200,200,200),(180,180,200),52,20])

#for thing in range(12):
#	tree((random.randrange(50,900),random.randrange(50,1800)),[(100,200,70),(70,180,100),(100,190,100),56,20])

tree((270,220),[(100,200,70),(70,180,100),(100,190,100),56,20])
tree((300,50),[(100,200,70),(70,180,100),(100,190,100),56,20])
tree((110,460),[(100,200,70),(70,180,100),(100,190,100),56,20])
tree((500,600),[(100,200,70),(70,180,100),(100,190,100),56,20])
tree((700,1100),[(100,200,70),(70,180,100),(100,190,100),56,20])

doublebuffer.fill((COLOR))
screen.blit(doublebuffer,(-screenpos[0],-screenpos[1]))
pygame.font.init()
myfont = pygame.font.SysFont("monospace", 15)
label = myfont.render("Please Wait...", 1, (0,0,0))
screen.blit(label, (displaysize[0]/2, displaysize[1]/2))
pygame.display.flip()
mythread = threading.Thread(target=recvimages,args=[serverhost])
mythread.start()
time.sleep(3)
server_conn.send_data("ready")
start()

"""
random fine tunings:
----------------------

-make sprites that are "above" others to appear behind
-chat- any player can open up a chat from player to player, or shout a message that appears to everyone. However shouting only works once every five seconds.
-Water can only be passed through if the unit's weight is under a certain threshold. Otherwise it exerts quadraticly multiplying force against the unit's speed and health if he tries to pass through. Even lighter units that float get a flat percentage of lost speed in water.
-Make a play without an account option. This makes people resent logging in less, because it tangibly makes it apparent that you only get access to your stuff if you identify yourself.
-Make other interesting map zones... Like, perhaps, an underworld.
-Make the main loop and similar things more organized. More modularized functions.
-Make a sidebar with all your units listed, and the one in focus highlighted.
-spawn points: Players don't get there own map slices to start out in, persay. However, they are always placed in the grassy feild, where fighting is actually not permitted (and few good resources are available). This place is only useful for starting out or forming alliances, but because everyone starts out here it is kind of expected to end up as a city as people build stuff and they don't get destroyed. The player GAIA actually already has one or two builders there, though all they do is make tents and campfires. Some of the random map events dictate that GAIA actually send a guy who trades attribute stockpiles there. Damage piping will not work on a target inside these boundaries.
-Make a virtual environment installer... If you can. Otherwise you may need to use some other kind of high performance security system...
-Note: Build map dynamically... Keep a code base of anything someone uploads, in part for security but also so that it is easy to upload it as one of the things to place on the map.

unimplemented attributes
-creation (Used to spawn new objects, AI units, and even map slices if there is free space in the designated player-made map slice region)
-weight- right now when one moveable collidable pushes another the speed is always reduced to one. This, and general speed and momentum, should be mass dependant. Weight can also, with extreme expenditure, draw objects closer to self. This can effectively control much of a unit's motion when compounded with speed. It actually costs a stored maxattr to change it, but it doesn't empty out or refill via updating. It costs charged up attribute pools to effectively lower weight, not just raise it. Weight will reduce speed, however it also makes you a lot less likely to get knocked far back in a collision.
-hud_overlay (for blindness, flashed, and hallucinations)
-toxic- toxic. straightfoward eneough.
-brute- will cause bloodloss in large amounts
-burn- burn. straightfoward eneough.
-genetic- radiation issues. causes toxification alongside its own damage
-upkeep- food, starvation, etc
-bloodloss- compunds to cause more brute and some asphyxiation, but mostly its own damage type
-asphyxiation- air is everywhere, however it is still a damage type so that suffocation can occur
-temperature- extreme temperatures bring about burn damage, and lesser extremes slow down player unless negated which will cost upkeep or some other stat.
-Players have an internal organ setup, their sprite is the combination of said organ's appearance assembled. Each organ has a damage price for being damaged (AKA lungs give global asphyxiation when they have brute), and a set of functions tied to them. The brain can theoretically be designed so that the body can function autonomously from it, so long as you place the actual connection attribute (which you may only have one instance of in a player) is stored somewhere else, as this actually calls functions. Said organs have these damage multipliers because each one is tied to a maximum of three piping functions, thus if they are damaged that kind of piping is damaged. So yes, you could propell yourself with your nose instead of legs. Organs must also have animations for different directions and different damage levels. Thus creating a player from scratch isn't easy but totally doable. And relatively simple.
-Items are actually similar to said organs. They don't obviously classify the same way, but they dynamically can attatch and detatch from a player, house attributes, functions, and passive functions, and integrate into the player's sprite in the same way.
-There are, however, many non-player, non-objects. Like trees. These are stationaries, that have only basic health attributes (they are immune to all damage types but brute and burn). They use less CPU. Many stationaries also have on-death functions. For example, trees drop wood, an item that is potentially useful as it has a function to withdraw a temeperature reserve into nearby objects and change sprite to fire (which has unique scripting to spread to other objects made of wood), and also may have several kinds of permanent item-type attributes applied to them during runtime, such as attack, which equates sharpening the wood. Finally it can be used in a stationary to contribute its item stats and a plank-like sprite to the object (or start an entirely new stationary). However, the location and angle of said plank has to be coded in. Theoretically you could build a function to make planks into a fence though, for example. The plank would simply have to visually attatch to the sprite it is modifying, and if so than it will redefine said stationary's borders, breaking it off into two or more stationaries as nescessary, not breaking up scripted in L shaped images if they have the DONTBREAK flag active. Finally, obviously you can't make one stationary extend into the space of another very much at all, something like five pixels maximum. The idea of assembling raw attributes and icons can be very powerful, I think.
-Organs may be targeted, again in script, but with the exception of one's own sprite they can only target exposed organs. However ones underneath still take damage, and all organs detatch at a percent of damage threshhold. Obviously your primarily screwed if the residence of your connection dies. Hence it makes sense to give yourself a nice armor plating. However, since all organs require sustenance and said armor is not contributing anything, it may be a helpful in combat but it will provide a serious upkeep drain so be careful...

note: high level issues like confusedness, nerve damage, hallucinations, and necrosis are dealt with via an effect, these are just base damage types. Even paralysis can just be reduced to speed.
-So damage and heal dont pipe into health... They pipe into damage buffers, which pipe into health. Damage buffers will apply secondary effects of specialized damage types, and also must be healed differently. If something like 10 toxic is present, it will keep piping -10 to health until it is reduced to zero. It can not go below zero. Regen still pipes into health, there still is a raw, general life force variable. Its just that damage and healing has to pipe through damage specific buffers, and must be reduced by damage specific de-buffers.
-Also most objects can be used as effects. This means they independantly pipe themselves. Hence poisons and healing agents, things that you can't control. This type of passive use cannot execute code beyond attribute pipes, but may be imposed on an enemy, whereas someone generally has to choose to activate an object. Essentially, most objects support either active (user takes object and manually uses it) and/or passive (user or other player forces user to take it and passive use executes).
-Finally, it is to be noted that new organs cannot theoretically be created ingame. Note the theoretically bit. You can have a bunch of dormant organs to let you regrow em. Just need some raw stats to back the organs up. Also there is an organ cap at 70. And a function cap of 70 per organ. And of coarse the pipe cap. This means you can't get too out of hand... If you work hard eneough to make 70 complex functions per 70 organs you deserve it.



TODO
-------------
1. Implement full set of new attributes.
2. Add a disengaging protocol for when a character leaves. This means storing the character exactly as it is, and reloading. Character can be killed and reinstantiated if desired. Also try for making an engaging protocol where characters will attempt to find an unoccupied location in the grass field to spawn.
3. Add fairness gaurd pre-exec string checker to ban the use of certain keywords and functions.
4. Add "key" locks onto some of the better premade feautures.
5. Make a "map" or at least a generator. Also create a randomizer to make random weather patterns. If this is the only randomized thing one could always control weather by controlling the random seed... Could be interesting.
6. Write documentation in full, and write the secret docs.
7. Make a multiplatform, one file program that actually closes when you click the X button.
8. Create legitimate security features using the pre-exec string checker. This is far from bombproof, however, frankly it doesn't really need to be.


usage notes
----------------
trick unit into taking item or modify upon defeating them and revive or reverse engineer AI so that when not being directly controlld by player actions are manipulable, or sequester enemy controls to controlling a unit imprisoned in own mind or unable to interact with environment, while selectively allowing some controls supplied by them through. Won't work for very long. You can also spread to other units via convoy, even persuade units to convoy themselves upon what they think is an allied unit then modifying them while they are helplessly stored away.
"""