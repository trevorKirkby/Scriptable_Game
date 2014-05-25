account_name = 'trevor'

class prototype(character):
	def __init__(self,sockets,pos):
		self.aim = [0,0]
		character.__init__(self,pos,"generic.png","",sockets)
		self.pipe("maxhealth","health","all",self)
		self.upgrade("maxdamage",1)
		self.upgrade("maxspeed",1)
		imgsend = socket(PORT)
		imgsend.connect(serverhost)
		imgsend.send_data("imagesender")
		imgsend.send_img("wolf.png")
		imgsend.send_img("gun.png")
		pos = self.rect.center
		self.right = images["wolf.png"]
		self.left = pygame.transform.flip(self.right,True,False)
		self.vertical = pygame.transform.rotate(self.right,90)
		self.image = self.right
		if self not in projectiles:
			self.direction = "right"
		self.rect = self.image.get_rect()
		self.rect.center = pos
		class bigbolt(projectile):
			def __init__(self,pos,direction,parent):
				projectile.__init__(self,pos,direction,"pulse.png",30,damager=False,boomtrigger=False,simple=True,parent=parent)
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
						self.pipe("maxdamage","health",-2,other)
		self.shot = bigbolt
	def manage(self):
		#print self.realattributes["health"]
		self.store("maxhealth",2)
		self.pipe("maxhealth","health","all",self)
		self.pipe("maxregen","health","all",self)
		self.pipe("firerate","firetime",-5,self)
		self.pipe("maxspeed","speed","all",self)
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
		self.shoot(self.shot)
	def _q(self,*args):
		collisions = pygame.sprite.spritecollide(self, collidable, False)
		for other in collisions:
			if other != self and isinstance(other,unit):
				self.pipe("maxdamage","health",-3,other)
	def _i(self,*args):
		self.store("maxregen",2)
	def _k(self,*args):
		self.withdraw("maxregen",2)
	def _u(self,*args):
		self.store("maxspeed",2)
	def _j(self,*args):
		self.withdraw("maxspeed",2)

default=generic
others={"prototype":prototype}