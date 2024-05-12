# Open the image file in binary mode
with open('kleinmazama.jpeg', 'rb') as file:
    # Read the binary data
    byte_data = file.read()
    
    # Convert the binary data to hexadecimal format
    hex_data = byte_data.hex()

# Optionally, you can print the hex data
print(hex_data[:512])  # Print the first 512 characters for brevity

# save to file "animal.hex"
with open('kleinmazama.hex', 'w') as file:
    file.write(hex_data)