import socket
from concurrent.futures import ThreadPoolExecutor

host = "localhost"
port = 4444

matching_identities = [i for i in range(0, 100000)]

def connect(identity):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, port))
            s.sendall(f'dock\n'.encode())

# Use ThreadPoolExecutor to parallelize the process_identity function
with ThreadPoolExecutor(max_workers=10) as executor:
    executor.map(connect, matching_identities)