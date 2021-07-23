import socket 
import sys

# here we create a socket 
try:
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	print ("Socket successfully created")
except socket.error as err:
	print ("socket creation failed with error %s" %(err))

# default port for socket of DNS
port = 53

try:
    # google DNS server
	host_ip = '8.8.8.8'
except socket.gaierror:
	print ("there was an error resolving the host")
	sys.exit()

# connecting to the server
s.connect((host_ip, port))

print ("the socket has successfully connected")
