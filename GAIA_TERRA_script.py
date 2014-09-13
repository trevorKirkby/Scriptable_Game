account_name = 'GAIA'

def forest(*args):
	return tree((random.randrange(50,1200),random.randrange(3200,4450)),[(120,200,70),(100,150,100),(80,180,70),52,20])

def tropic(*args):
	return tree((random.randrange(50,900),random.randrange(50,1800)),[(100,200,70),(70,180,100),(100,190,100),56,20])

def alpine(*args):
	return tree((random.randrange(3500,4450),random.randrange(2000,4450)),[(120,180,100),(200,200,200),(180,180,200),52,20])

#obviously these trees will end up in different locations on different games, which is why they need spawn points to work...

default=generic
others={"forest":forest,"tropic":tropic,"alpine":alpine}