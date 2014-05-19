from network import *

conn = socket(1340)
conn.connect(raw_input("Please enter the server host: "))
conn.send("new_user")

conn.send(raw_input("enter username: "))
conn.send(raw_input("enter password: "))
conn.send(raw_input("enter email: "))