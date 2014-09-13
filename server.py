from network import *
import threading
import os

PORT = 1340

event_handlers = {}
characters = {}
senders = {}
games = []
game_events = []
character_data = {}
img_senders = []
img_recv = []
chat_send = {}
chat_recv = []
img_data = {}
players = []
finished = {}

def manage_character(character,handler):
	global characters
	print "managing character", character
	while True:
		data = handler.recv_data(poll=False)
		print "sending to characters", data
		print "characters", characters
		print "data from handler", handler
		try:
			a = unpack("i",data)
		except:
			a = "not applicable, data was not packed"
		print "unpacked data value", a
		for sprite in characters[character][0]:
			sprite.send(data)
			character_data[character].append(data)

def manage_code(character,sender):
	complete = False
	while True:
		header = sender.recv_data(poll=False)
		data = sender.recv_data(poll=False)
		for game in games:
			game.send_data("load code "+character)
			game.send_data(header)
			game.send_data(data)
			game_events.append("load code "+character)
			game_events.append(header)
			game_events.append(data)

def manage_img(sender):
	global img_recv
	while True:
		img = sender.recv_img()
		for receiver in img_recv:
			receiver.send_img(img)
		img_data.update(img)

def handle_account(connection):
	register = connection.recv_data(poll=False)
	if register == "login":
		username = connection.recv_data(poll=False)
		userid = connection.recv_data(poll=False)
		account = open(username+"_"+userid+"_script.py","r")
		bank = open(username+"_"+userid+"_bank.py","r")
	elif register == "new":
		username = connection.recv_data(poll=False)
		userid = connection.recv_data(poll=False)
		email = connection.recv_data(poll=False)
		a = open(username+"_"+userid+"_script.py","w")
		b = open(username+"_"+userid+"_bank.py","w")
		c = open(username+"_"+userid+"_email.txt","w")
		a.write("account_name = '"+username+"'\ndefault=generic\nothers={}")
		b.write("50")
		c.write(email)
		a.close()
		b.close()
		c.close()
		account = open(username+"_"+userid+"_script.py","r")
		bank = open(username+"_"+userid+"_bank.py","r")
	else:
		raise RuntimeError
	connection.send(str(bank.read()))
	connection.recv_data(poll=False)
	for command in game_events:
		connection.send_data(command)
	players.append(account.read())

def manage_adder(connection):
	global players
	done = []
	for player in players:
		connection.send(player)
		done.append(player)
	while True:
		for player in players:
			if player not in done:
				connection.send(player)
				done.append(player)

print get_lan_ip()

try:
	while True:
		print "accepting cycle initiated on port", PORT
		connection = socket(PORT)
		connection.accept()
		print "initial contact made, getting type"
		connection_type = connection.recv_data(poll=False)
		print connection_type
		if connection_type == "account_adder":
			mythreadthing = threading.Thread(target=manage_adder,args=[connection])
			mythreadthing.start()
		if connection_type == "game":
			games.append(connection)
			mythreads = threading.Thread(target=handle_account,args=[connection])
			mythreads.start()
			print "accepted game"
		if connection_type == "sender":
			name = connection.recv_data(poll=False)
			senders.update({name:connection})
			print "accepted sender"
		elif connection_type == "event_handler":
			print "receiving event handler"
			name = connection.recv_data(poll=False)
			who = connection.recv_data(poll=False)
			print "name:", name, "who", who
			event_handlers.update({name:connection})
			print "accepted new event handler for character", name
			for game in games:
				print "sending to", game
				game.send_data("load character "+str(name)+" "+who)
				game_events.append("load character "+str(name)+" "+who)
		elif connection_type == "character":
			name = connection.recv_data(poll=False)
			if name in characters:
				characters[name][0].append(connection)
			else:
				characters.update({name:[[connection],"(100,100)"]})
				character_data.update({name:[]})
			print "accepted new character", name
		elif connection_type == "imagesender":
			img_senders.append(connection)
			mythread = threading.Thread(target=manage_img,args=[connection])
			mythread.start()
		elif connection_type == "imagereceiver":
			img_recv.append(connection)
			for image in img_data.keys():
				connection.send_img({image:img_data[image]})
		if connection_type == "sender" or connection_type == "character":
			for character in characters:
				for sender in senders:
					if character == sender and name == character:
						mythread = threading.Thread(target=manage_code,args=[character,senders[sender]])
						mythread.start()
		if connection_type == "event_handler" or connection_type == "character":
			for character in characters:
				for handler in event_handlers:
					if character == handler and name == character:
						if connection_type == "character":
							for item in character_data[character]:
								characters[character][0][-1:][0].send(item)
		if connection_type == "event_handler":
			mythread = threading.Thread(target=manage_character,args=[name,connection])
			mythread.start()
		#PORT += 1
except KeyboardInterrupt:
	print "\n------\nbye\n------\n"
	raise SystemExit