# This script uses pexpect to interact with the bookkeeper program

import binascii
import re

import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import pexpect

# Start the program
child = pexpect.spawn('./bookkeeper')

# Expect the first password prompt (when trying to cat t.scam)
child.expect('In dir /mnt: ')
# Send the command that triggers the password request
child.sendline('cat kleinmazama.hex')

# Save the outputed hex to an image file that is plotted with matplotlib

child.expect("In dir /mnt: ")
hex_data = child.before.split(b'\n')[1]

# Convert the hexadecimal data back to binary
print(hex_data[-100:1])
binary_data = binascii.unhexlify(hex_data[:-1])
# Write the binary data to an image file
with open('output_image.jpeg', 'wb') as file:
    file.write(binary_data)


from PIL import Image


def image_to_ascii(image_path):
    image = Image.open(image_path)
    image = image.resize((image.width // 8, image.height // 15))
    image = image.convert('L')  # Convert to grayscale

    ascii_chars = '@%#*+=-:. '  # Define the ASCII characters to use
    ascii_image = ''

    for y in range(image.height):
        for x in range(image.width):
            brightness = image.getpixel((x, y))  # Get the brightness of the pixel
            ascii_char = ascii_chars[brightness // 32]  # Map the brightness to an ASCII character
            ascii_image += ascii_char
        ascii_image += '\n'

    print(ascii_image)

image_to_ascii('output_image.jpeg')