import socket
import sys
from concurrent.futures import ThreadPoolExecutor

host = sys.argv[1]
connection_count = int(sys.argv[2])
port = 4444

matching_identities = [i for i in range(0, connection_count)]

def connect(identity):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, port))
            s.sendall(f'dock\n'.encode())

# Use ThreadPoolExecutor to parallelize the process_identity function
with ThreadPoolExecutor() as executor:
    executor.map(connect, matching_identities)