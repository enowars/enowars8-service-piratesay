import ctypes
import re
import socket
import sys
import time

IDENTITY_LENGTH = 64

# Load the C standard library
libc = ctypes.CDLL(None)

# Set argument and return types for rand_r
libc.rand_r.argtypes = [ctypes.POINTER(ctypes.c_uint)]
libc.rand_r.restype = ctypes.c_int

def generate_identity_string(state):
    state_ptr = ctypes.c_uint(state)
    identity_string = ''.join(chr(ord('a') + (libc.rand_r(ctypes.byref(state_ptr)) % 26)) for _ in range(IDENTITY_LENGTH))
    return identity_string, state_ptr.value

def get_unix_time_from_string(date_string):
    # Format of date_string: "2024-07-15 11:35:24"
    return int(time.mktime(time.strptime(date_string, "%Y-%m-%d %H:%M:%S")))

TARGET = sys.argv[1] # The target's ip address is passed as an command line argument
PORT = 4444

def get_seed_and_current_identity(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        
        # Receive the initial server message
        def recv_until_prompt(prompt):
            data = b''
            while not data.endswith(prompt):
                data += s.recv(1024)
            return data

        initial_message = recv_until_prompt(b'$ ').decode()
        # Extract the timestamp from the initial message
        match = re.search(r'\(Pirate Say v1.0.0, up since (.+?)\)', initial_message)
        if match:
            seed_string = match.group(1)
            seed = get_unix_time_from_string(seed_string)
        else:
            print("Failed to extract seed from server message")
            exit(1)

        # Get the current identity
        s.sendall(b'identity\n')
        identity_response = recv_until_prompt(b': ').decode()
        s.sendall(b'\n')  # Keeping current identity
        recv_until_prompt(b'$ ')
        current_identity = identity_response.split("\n")[0].split(":")[1].strip()
        return seed, current_identity
    
# 1. Try to read state.txt if it exists
try:
    with open("state.txt", "r") as f:
        state = int(f.readline())
        match = f.readline().strip()
except FileNotFoundError:
    # 1. Get starting seed and current identity by connecting
    state, match = get_seed_and_current_identity(TARGET, PORT)
    with open("state.txt", "w") as f:
        f.writelines([str(state), "\n", match])

# 2. Generate identity strings until we find the correct one, print every Nth identity
# start_seed = 1721065234
N = 100000
BACK = 10000
i = 1
states = []
while True:
    identity, state = generate_identity_string(state)
    if identity == match:
        print(f"Found matching identity: {identity}")
        break
    if i % N == 0:
        print(f"State at {i}: {state}")
        states.append(state)
    i += 1

# 3. Print the final state
print(f"Match found! State: {state}")
print(f"Storing state {N} steps past, as they might include active flags")
with open("state.txt", "w") as f:
    f.writelines([str(state), "\n", match])
