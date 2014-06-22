account_name = 'trevor'

class prototype(character):
	def __init__(self,sockets,pos):
		self.aim = [0,0]
		#character.__init__(self,pos,"generic.png","",sockets)
		imgsend = socket(PORT)
		imgsend.connect(serverhost)
		imgsend.send_data("imagesender")
		imgsend.send_img("wolf.png")
		imgsend.send_img("wolf0.png")
		imgsend.send_img("wolf1.png")
		imgsend.send_img("wolf2.png")
		imgsend.send_img("wolf3.png")
		imgsend.send_img("gun.png")
		character.__init__(self,pos,images["wolf.png"],"",sockets)
		self.pipe("maxhealth","health","all",self)
		self.upgrade("maxspeed",1)
		self.upgrade("maxspeed",1)
		#pos = self.rect.center
		#self.right = images["wolf.png"]
		#self.left = pygame.transform.flip(self.right,True,False)
		#self.vertical = pygame.transform.rotate(self.right,90)
		#self.image = self.right
		#if self not in projectiles:
		#	self.direction = "right"
		#self.rect = self.image.get_rect()
		#self.rect.center = pos
		#self.constx = 100
		#self.consty = 100
		#self.rect.move_ip(200,0)
		class bigbolt(projectile):
			def __init__(self,pos,direction,parent):
				projectile.__init__(self,pos,direction,"pulse.png",simple=True,parent=parent)
				pos = self.rect.center
				self.right = images["gun.png"]
				self.left = pygame.transform.flip(self.right,True,False)
				self.vertical = pygame.transform.rotate(self.right,90)
				self.image = self.right
				if self not in projectiles:
					self.direction = "right"
				self.rect = self.image.get_rect()
				self.rect.center = pos
			def manage(self):
				collisions = pygame.sprite.spritecollide(self, collidable, False)
				for other in collisions:
					if other != self and other != self.parent and isinstance(other,unit):
						self.parent.withdraw("maxdmg",15)
						self.pipe("maxdmg","health",-5,other)
						self.pipe("maxdmg","health",-5,other)
		self.shot = bigbolt
		self.indexes = 0.0
	def manage(self):
		#print self.realattributes["health"]
		self.pipe("maxhealth","health","all",self)
		self.pipe("maxregen","health","all",self)
		self.pipe("firerate","firetime",-2,self)
		self.pipe("maxspeed","speed","all",self)
		for projectile in self.projectiles:
			if projectile != None:
				return
		self.store("maxdmg",7)
		#print self.realattributes["health"]
	def animate_move(self,dx,dy):
		if dx != 0:
			self.indexes += 0.25
			if self.indexes == 5.0:
				self.indexes = 1.0
			if self.indexes == 1.0:
				self.changeimg(images["wolf0.png"])
			if self.indexes == 2.0:
				self.changeimg(images["wolf1.png"])
			if self.indexes == 3.0:
				self.changeimg(images["wolf2.png"])
			if self.indexes == 4.0:
				self.changeimg(images["wolf3.png"])
	def _w(self,*args):
		self.goup()
	def _s(self,*args):
		self.godown()
	def _a(self,*args):
		self.goleft()
	def _d(self,*args):
		self.goright()
	def _e(self,*args):
		self.shoot(self.shot)
	def _q(self,*args):
		collisions = pygame.sprite.spritecollide(self, collidable, False)
		for other in collisions:
			if other != self and isinstance(other,unit):
				self.pipe("maxdamage","health",-3,other)
	def _i(self,*args):
		self.store("maxregen",1)
	def _k(self,*args):
		self.withdraw("maxregen",3)
	def _u(self,*args):
		self.store("maxspeed",2)
	def _j(self,*args):
		self.withdraw("maxspeed",2)
	def _y(self,*args):
		self.store("firerate",1)
	def _h(self,*args):
		self.withdraw("firerate",10)

default=generic
others={"prototype":prototype}