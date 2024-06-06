#include "cli.h"
#include "session.h"
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <pthread.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <signal.h>
#include <sys/wait.h>

#define PORT 4444

char root_dir[PATH_MAX];
int server_fd; // Make server_fd global so it can be accessed in the signal handler

void handle_sigint(int sig)
{
    printf("Caught signal %d, releasing resources...\n", sig);
    close(server_fd); // Close the server socket
    exit(0);          // Exit the program
}

void handle_sigchld(int sig)
{
    // Use a loop to handle all terminated child processes
    while (waitpid(-1, NULL, WNOHANG) > 0)
    {
        // No need to do anything here, just reap the child processes
    }
}

void sanitize_string(char *input)
{
    char buffer[PATH_MAX];
    char *insert_point = buffer;
    const char *tmp = input;

    while (*tmp)
    {
        // Look for the next '%'
        if (*tmp == '%')
        {
            const char *p = tmp + 1;
            // Scan until we find an 'n'
            while (*p && *p != 'n')
            {
                p++;
            }

            // If we found an 'n'
            if (*p == 'n')
            {
                // Skip the pattern
                tmp = p + 1;
                continue;
            }
        }

        // Copy the current character and move to the next
        *insert_point++ = *tmp++;
    }

    // Null-terminate the buffer
    *insert_point = '\0';

    // Copy sanitized buffer back to input
    strcpy(input, buffer);
}

void trim_whitespace(char *str)
{
    if (str == NULL)
        return;

    // Trim leading whitespace
    char *start = str;
    while (*start && isspace((unsigned char)*start))
    {
        start++;
    }

    // If all characters are whitespace, make the string empty
    if (*start == '\0')
    {
        str[0] = '\0';
        return;
    }

    // Move the trimmed string to the beginning
    memmove(str, start, strlen(start) + 1);

    // Trim trailing whitespace
    size_t len = strlen(str);
    while (len > 0 && isspace((unsigned char)str[len - 1]))
    {
        str[len - 1] = '\0';
        len--;
    }

    sanitize_string(str);
}

void print_terminal_prompt(session_t *session)
{
    char dir_print[PATH_MAX];
    char dir_message[PATH_MAX];
    memset(dir_print, 0, sizeof(dir_print));
    strcat(dir_print, session->local_dir);
    sprintf(dir_message, "\n%s%s:%s$ ", session->pirate_adjective, session->pirate_noun, dir_print);
    send(session->sock, dir_message, strlen(dir_message), 0);
}

void client_session(int *socket_desc)
{
    int sock = *socket_desc;

    session_t session;
    session.sock = sock;
    strcpy(session.local_dir, "/");     // Local directory
    strcpy(session.root_dir, root_dir); // Root directory
    strcpy(session.full_dir, root_dir); // Full path
    strcpy(session.pirate_adjective, get_random_adjective());
    strcpy(session.pirate_noun, get_random_noun());
    session.is_authenticated = 0; // Default not authenticated

    int read_size;

    char *filename = "../src/splash_screen.txt"; // Outside of service's root directory
    memset(session.buffer, 0, sizeof(session.buffer));
    cat_file(filename, &session);                          // Using own cat_file function from cli.c
    send(sock, session.buffer, strlen(session.buffer), 0); // Echo session.buffer which now stores the contents of splash_screen.txt

    // Display first prompt
    print_terminal_prompt(&session);

    while ((read_size = recv(sock, session.buffer, PATH_MAX, 0)) > 0)
    {
        // Null-terminate
        session.buffer[read_size] = '\0';

        // Trim leading and trailing whitespace
        trim_whitespace(session.buffer);

        if (interact_cli(&session) == 1)
        {
            break;
        }

        // Echo back the output from interact_cli now stored in session.buffer
        send(sock, session.buffer, strlen(session.buffer), 0);

        // Prompt for next command
        print_terminal_prompt(&session);
    }

    if (read_size == 0)
    {
        puts("Client disconnected");
        fflush(stdout);
    }
    else if (read_size == -1)
    {
        perror("recv failed");
    }

    close(sock);
}

int main()
{
    // get dir and change it to 'data' subfolder
    if (chdir("../data") != 0)
    {
        perror("'data' subfolder necessary to run the server\n");
        exit(EXIT_FAILURE);
    }
    getcwd(root_dir, sizeof(root_dir));

    int client_sock;
    struct sockaddr_in server, client;
    socklen_t socksize = sizeof(struct sockaddr_in);

    // Create socket
    server_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (server_fd == -1)
    {
        perror("Could not create socket");
        exit(EXIT_FAILURE); // Exit if socket creation fails
    }
    puts("Socket created");

    // Set SO_REUSEADDR option
    int opt = 1;
    if (setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt)) < 0)
    {
        perror("setsockopt failed");
        close(server_fd);
        exit(EXIT_FAILURE);
    }

    server.sin_family = AF_INET;
    server.sin_addr.s_addr = INADDR_ANY;
    server.sin_port = htons(PORT);

    // Bind
    if (bind(server_fd, (struct sockaddr *)&server, sizeof(server)) < 0)
    {
        perror("bind failed");
        close(server_fd);
        exit(EXIT_FAILURE); // Exit if binding fails
    }
    puts("bind done");

    // Listen
    listen(server_fd, 3);

    // Set up the signal handlers
    struct sigaction sa_int, sa_chld;

    sa_int.sa_handler = handle_sigint;
    sa_int.sa_flags = 0;
    sigemptyset(&sa_int.sa_mask);
    sigaction(SIGINT, &sa_int, NULL);

    sa_chld.sa_handler = handle_sigchld;
    sa_chld.sa_flags = SA_RESTART | SA_NOCLDSTOP;
    sigemptyset(&sa_chld.sa_mask);
    sigaction(SIGCHLD, &sa_chld, NULL);

    // Accept incoming connections
    puts("Waiting for incoming connections...");

    while ((client_sock = accept(server_fd, (struct sockaddr *)&client, &socksize)) >= 0)
    {
        printf("Connection accepted from %s:%d\n", inet_ntoa(client.sin_addr), ntohs(client.sin_port));

        pid_t pid = fork();
        if (pid < 0)
        {
            perror("fork failed");
            close(client_sock);
            continue;
        }
        else if (pid == 0)
        {
            // This is the child process
            // Seed the random number generator with the current time (unique for each child)
            srand(time(NULL));
            close(server_fd);             // Child does not need the listening socket
            client_session(&client_sock); // Handle client connection
            close(client_sock);
            exit(EXIT_SUCCESS); // End child process
        }
        else
        {
            // This is the parent process
            close(client_sock); // Parent does not need the client socket
        }
    }

    if (client_sock < 0)
    {
        perror("accept failed");
        close(server_fd);
        exit(EXIT_FAILURE);
    }

    return 0;
}
