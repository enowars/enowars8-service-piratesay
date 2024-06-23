''' Wrapper that connects to the server and provides QoL features such as command history and line editing. '''

import readline
import select
import socket
import sys
import threading

SERVER_IP = '127.0.0.1'
SERVER_PORT = 4444
BUFFER_SIZE = 4096  # Increase buffer size as needed

last_prompt = ''

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

def receive_messages(sock):
    global last_prompt
    while True:
        ready_to_read, _, _ = select.select([sock], [], [], 0.1)
        if ready_to_read:
            response = receive_full_message(sock)
            if response:
                # Save current user input
                saved_line = readline.get_line_buffer()

                # Erase current input line
                sys.stdout.write('\r' + ' ' * (len(saved_line) + len(last_prompt) + 2) + '\r')
                sys.stdout.flush()

                # Remove the last line from the response
                lines = response.split('\n')
                last_prompt = lines[-1]
                response = '\n'.join(lines[:-1])

                # Print the server response
                print(response)

                # Restore user input
                sys.stdout.write(last_prompt + saved_line)
                sys.stdout.flush()
                readline.redisplay()
            
            else:
                print("Empty server response. Exiting...")
                sock.close()
                sys.exit(1)

def handle_input(sock):
    global last_prompt
    while True:
        user_input = input(last_prompt)
        
        # Send the user input to the server, appending a newline character
        sock.sendall(user_input.encode() + b'\n')

def main():
    global last_prompt
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            # Connect to the server
            sock.connect((SERVER_IP, SERVER_PORT))
            
            # Print the initial server message
            initial_msg = receive_full_message(sock)
            print(initial_msg, end='')

            # Start threads for handling input and receiving messages
            input_thread = threading.Thread(target=handle_input, args=(sock,))
            input_thread.daemon = True
            input_thread.start()

            receive_messages(sock)

        except (socket.error, BrokenPipeError) as e:
            print(f"Connection error: {e}")

if __name__ == "__main__":
    main()
