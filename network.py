import socket as basic_socket
import pygame
import threading
import subprocess
import time
import os
import select
import pickle
from struct import pack, unpack

if os.name != "nt":
	import fcntl
	import struct
	def get_interface_ip(ifname):
		s = basic_socket.socket(basic_socket.AF_INET, basic_socket.SOCK_DGRAM)
		return socket.inet_ntoa(fcntl.ioctl(s.fileno(), 0x8915, struct.pack('256s',
								ifname[:15]))[20:24])

def get_lan_ip():
	ip = basic_socket.gethostbyname(basic_socket.gethostname())
	if ip.startswith("127.") and os.name != "nt":
		interfaces = [
			"eth0",
			"eth1",
			"eth2",
			"wlan0",
			"wlan1",
			"wifi0",
			"ath0",
			"ath1",
			"ppp0",
			]
		for ifname in interfaces:
			try:
				ip = get_interface_ip(ifname)
				break
			except IOError:
				pass
	return ip

def call(command,io=''):
	command = command.split()
	startupinfo = subprocess.STARTUPINFO()
	startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
	process = subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,startupinfo=startupinfo,shell=True)
	return process.communicate(io)[0]

def recv_fixed(sock,size):
	remaining = size
	mybuffer = str()
	while remaining > 0:
		#print "remaining: ", remaining
		datas = sock.recv(remaining)
		remaining -= len(datas)
		mybuffer += datas
	#print "returning from recv(): ", mybuffer
	#try:
	#	print "unpacked retval: ", unpack("i",mybuffer)
	#except:
	#	pass
	return mybuffer

#make each thread open up their own windows!!!

class socket():
	def __init__(self,port):
		self.port = int(port)
		self.sock = basic_socket.socket(basic_socket.AF_INET, basic_socket.SOCK_STREAM)
		self.sock.setsockopt(basic_socket.SOL_SOCKET, basic_socket.SO_REUSEADDR, 1)
	def connect(self,host):
		connected = False
		while connected == False:
			try:
				self.host = str(host)
				self.sock.connect((self.host,self.port))
				connected = True
				print "connected on port", self.port
				return self.port + 1
			except:
				self.port += 1
	def accept(self,timeout=None):
		if timeout != None:
			self.sock.settimeout(timeout)
		self.sock.bind(("", self.port))
		self.sock.listen(10)
		conn, addr = self.sock.accept()
		self.host = addr
		self.sock = conn
	def send_data(self,data):
		#print "sending", repr(pack("i",int(len(data)))), "(before len, after data)", data
		self.sock.send(pack("i",int(len(data))))
		self.sock.send(data)
	def recv_data(self,poll=True):
		if poll:
			ready = select.select([self.sock], [], [], 0)
			if ready[0]:
				length = recv_fixed(self.sock,4)
				length = unpack("i",length)[0]
				data = recv_fixed(self.sock,int(length))
				#print "receiving polled", length, data
				return data
			else:
				return None
		else:
			length = recv_fixed(self.sock,4)
			length = unpack("i",length)[0]
			data = recv_fixed(self.sock,int(length))
			#print "receiving non-polled", length, data
			return data
	def send_img(self,filename,timeout=None):
		pygame.display.init()
		if type(filename) == str:
			image_file = pygame.image.load(filename).convert_alpha()
		elif type(filename) == dict:
			image_file = list(filename.values())[0]
			filename = list(filename.keys())[0]
		acknowledgement = None
		while acknowledgement == None:
			acknowledgement = self.recv_data()
		if acknowledgement != "receive image":
			print "error: the receiving socket is not expecting an image"
		else:
			self.send_data("image "+filename)
			self.send_data(pack("ii",image_file.get_width(),image_file.get_height()))
			try:
				data = pygame.image.tostring(image_file,"RGBA")
			except:
				pygame.display.set_mode((200,100))
				data = pygame.image.tostring(image_file,"RGBA")
				pygame.display.quit()
			self.send_data(data)
	def recv_img(self,timeout=None):
		pygame.display.init()
		self.send_data("receive image")
		acknowledgement = None
		while acknowledgement == None:
			acknowledgement = self.recv_data()
		if acknowledgement.split()[0] != "image":
			print "error: the socket is not sending an image"
		else:
			imgname = acknowledgement.split()[1]
			dimensions_data = self.recv_data(False)
			#print dimensions_data
			dimensions = unpack("ii",dimensions_data)
			data = self.recv_data(False)
			try:
				image = pygame.image.frombuffer(data,dimensions,"RGBA")
			except:
				pygame.display.set_mode((200,100))
				image = pygame.image.frombuffer(data,dimensions,"RGBA")
				pygame.display.quit()
			return {imgname : image}
		return None
	def send_file(self,filename,timeout=None):
		data_file = open(filename,"rb")
		acknowledgement = None
		while acknowledgement == None:
			acknowledgement = self.recv_data()
		if acknowledgement != "receive file":
			print "error: the receiving socket is not expecting a file"
		else:
			self.send_data("file "+filename)
			self.send_data(data_file.read())
		data_file.close()
	def recv_file(self,timeout=None):
		self.send_data("receive file")
		acknowledgement = None
		while acknowledgement == None:
			acknowledgement = self.recv_data()
		if acknowledgement.split()[0] != "file":
			print "error: the socket is not sending a file"
		else:
			filename = acknowledgement.split()[1]
			data_file = open(filename,"wb")
			data_file.write(self.recv_data(False))
		try:
			data_file.close()
		except:
			pass
	def send_pyobj(self,obj):
		acknowledgement = None
		while acknowledgement == None:
			acknowledgement = self.recv_data()
		if acknowledgement != "receive obj":
			print "error: the receiving socket is not expecting a python object"
		else:
			if hasattr(obj,"__name__"):
				self.send_data("obj "+obj.__name__)
			else:
				self.send_data("obj sent_object")
			myfile = open("sendfile.pkl","wb")
			pickle.dump(obj,myfile)
			myfile.close()
			self.send_file("sendfile.pkl")
			os.remove("sendfile.pkl")
	def recv_pyobj(self):
		self.send_data("receive obj")
		acknowledgement = None
		while acknowledgement == None:
			acknowledgement = self.recv_data()
		if acknowledgement.split()[0] != "obj":
			print "error: the socket is not sending a python object"
		else:
			self.recv_file()
			myfile = open("sendfile.pkl","rb")
			try:
				obj = pickle.load(myfile)
			except AttributeError:
				print "Error: This was caused because an object was sent using send_pyobj that inherited from a class. To send such an object, you need to first send the object it inherits from (the class). You need to do this via sending code (send_code and recv_code functions)"
				raise SystemExit
			myfile.close()
			os.remove("sendfile.pkl")
			return obj
	def send_code(self,string):
		self.send(string)
	def recv_code(self):
		retval = None
		exec self.recv()
		if retval != None:
			return retval
	def send(self,data):
		self.send_data(data)
	def recv(self,poll=True):
		self.recv_data(poll)

class server():
	def __init__(self,port):
		self.port = port
		self.connections = []
		self.new_connections = []
		self.new = False
	def run(self):
		while True:
			new_connection = socket(self.port)
			self.connections.append(new_connection)
			new_connection.accept()
			self.new_connections.append(new_connection)
			self.new = True
	def newest(self):
		if self.new == True:
			self.new = False
			returnval = self.new_connections
			self.new_connections = []
			return returnval

def portscan(host):
	output = str()
	for port in range(1,3000):
		sock = basic_socket.socket(basic_socket.AF_INET, basic_socket.SOCK_STREAM)
		result = sock.connect_ex((remoteServerIP, port))
		if result == 0:
			output += "Port {}: \t Open".format(port)
		sock.close()
	return output

def connect_wifi(name):
    call("netsh wlan connect interface=\"Wireless Network Connection\" name=\""+name+"\"")

def disconnect_wifi():
	call("netsh wlan disconnect interface=\"Wireless Network Connection\"")