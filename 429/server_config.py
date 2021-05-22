import socket
SERVER_IP = socket.gethostbyname(socket.gethostname())
SERVER_PORT = 50000
SERVER_ADDR = (SERVER_IP, SERVER_PORT)
CONN_ADDR = (SERVER_IP, SERVER_PORT-1)
SERVER_DEFAULT_PORT = 50050

FORMAT = 'utf-8'
TITLE = 'Server'
SIZE = '450x300'