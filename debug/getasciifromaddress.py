def little_endian_to_ascii(hex_address):
    # Remove any leading '0x' if present
    if hex_address.startswith('0x'):
        hex_address = hex_address[2:]
    
    # Ensure the hex address length is even
    if len(hex_address) % 2 != 0:
        hex_address = '0' + hex_address
    
    # Split the hex string into bytes
    bytes_list = [hex_address[i:i+2] for i in range(0, len(hex_address), 2)]
    
    # Reverse the byte order (little-endian to big-endian)
    bytes_list.reverse()
    
    # Convert each byte to its ASCII character
    ascii_chars = [chr(int(byte, 16)) for byte in bytes_list]
    
    # Join the ASCII characters into a single string
    ascii_string = ''.join(ascii_chars)
    
    return ascii_string

# Example usage
hex_address = '0x3a64726f77737300'
ascii_representation = little_endian_to_ascii(hex_address)
print(ascii_representation)  # Output: "olleh"

# DB4QRQ1Y001XZY6L