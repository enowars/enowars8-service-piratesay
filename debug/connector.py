''' Wrapper that connects to the server and provides QoL features such as history, tab completion and line editing. '''

import readline
import socket
import sys

SERVER_IP = sys.argv[1]
SERVER_PORT = 4444
BUFFER_SIZE = 4096

last_prompt = ''
file_list = []

def receive_full_message(sock):
    chunks = []
    while True:
        chunk = sock.recv(BUFFER_SIZE)
        if not chunk:
            break
        chunks.append(chunk)
        if len(chunk) < BUFFER_SIZE:
            break
    return b''.join(chunks).decode()

def receive_until_prompt(sock):
    global last_prompt, file_list
    response = ''
    while True:
        response += receive_full_message(sock)
        last_line = response.split('\n')[-1]
        if last_line.endswith(": ") or ":/" in last_line:
            # Take the last line and use it as last_prompt instead of printing it
            last_prompt = last_line
            response = response.replace(last_line, '')
            
            # If completely finished with a command
            # We run "scout" behind the scene to update the file list for tab completion
            if ":/" in last_line:
                # Run scout in the background to update the file list
                sock.sendall("scout\n".encode())
                # Receive full message until the next prompt
                resp = ''
                while True:
                    resp += receive_full_message(sock)
                    ll = resp.split('\n')[-1]
                    if ":/" in ll:
                        break
                file_list = [line.strip() for line in resp.split('\n')[:-1] if line.strip()]
            break
    return response

def completer(text, state):
    options = [f for f in file_list if f.startswith(text)]
    if state < len(options):
        return options[state]
    else:
        return None

def main():
    global last_prompt, file_list
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            # Connect to the server
            sock.connect((SERVER_IP, SERVER_PORT))
            
            # Print the initial server message
            initial_msg = receive_until_prompt(sock)
            print(initial_msg, end='')

            # Set up readline to use the completer function
            readline.parse_and_bind('tab: complete')
            readline.set_completer(completer)

            while True:
                user_input = input(last_prompt)

                # Send the user input to the server, appending a newline character
                sock.sendall(user_input.encode() + b'\n')

                if user_input.strip() == "dock":
                    print("Disconnecting from the server...")
                    break

                # Receive the server response until the last line ends with ":" or contains ":/"
                response = receive_until_prompt(sock)
                print(response, end='')

        except (socket.error, BrokenPipeError) as e:
            print(f"Connection error: {e}")

if __name__ == "__main__":
    main()
