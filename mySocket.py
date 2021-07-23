import socket               # Import socket module

s = socket.socket()         # Create a socket object
s.connect(('localhost', 12345))
msg = "Hello we coonect"
s.sendall(msg.encode('utf-8'))
s.close()               