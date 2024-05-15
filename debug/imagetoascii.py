import sys

from PIL import Image


def image_to_ascii(image_path):
    image = Image.open(image_path)
    image = image.resize((image.width // 16, image.height // 30))
    image = image.convert('L')  # Convert to grayscale

    ascii_chars = '@%#*+=-:. '  # Define the ASCII characters to use
    ascii_image = ''

    for y in range(image.height):
        for x in range(image.width):
            brightness = image.getpixel((x, y))  # Get the brightness of the pixel
            ascii_index = round((brightness / 255) * (len(ascii_chars) - 1)) # Map the brightness to an ASCII character
            ascii_char = ascii_chars[ascii_index]
            ascii_image += ascii_char
        ascii_image += '\n'

    print(ascii_image)

if len(sys.argv) != 2:
    print("Usage: python imagetoascii.py <image_path>")
    sys.exit(1)

image_path = sys.argv[1]
image_to_ascii(image_path)