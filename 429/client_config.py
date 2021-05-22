import socket
import server_config as sc
import random

CLIENT_IP = socket.gethostbyname(socket.gethostname())
CLIENT_PORT = random.randint(sc.SERVER_PORT + 1, 60000)
CLIENT_ADDR = (CLIENT_IP, CLIENT_PORT)

FORMAT = 'utf-8'
TITLE = 'Chat'
SIZE = '675x430'
DEFAULT_NICKNAME = 'Guest-' + str(random.randint(1, 100))