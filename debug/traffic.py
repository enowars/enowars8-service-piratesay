''' Simulate traffic to the server '''

import socket
import sys
from concurrent.futures import ThreadPoolExecutor

host = sys.argv[1]
connection_count = int(sys.argv[2])
port = 4444

connections = [i for i in range(0, connection_count)]

def connect(_):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, port))
            s.sendall(f'dock\n'.encode())

with ThreadPoolExecutor() as executor:
    executor.map(connect, connections)