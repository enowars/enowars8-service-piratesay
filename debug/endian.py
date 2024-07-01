# convert input like this to little endian string 0xbffff6ac -> \xac\xf6\xff\xbf

def convert_to_little_endian(hex_string):
    # Remove the leading '0x' from the hex string
    hex_string = hex_string[2:]

    # Reverse the hex string in pairs
    hex_pairs = [hex_string[i:i+2] for i in range(0, len(hex_string), 2)]
    hex_pairs.reverse()

    # Convert the hex pairs to bytes and join them
    little_endian = ''.join([f'\\x{pair}' for pair in hex_pairs])

    return little_endian


print(convert_to_little_endian('0x0000ffffffff81c8'))

