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
#include <signal.h> // Include signal handling

#define PORT 8082
#define BUFFER_SIZE 1024

char base_dir[PATH_MAX];
int server_fd; // Make server_fd global so it can be accessed in the signal handler

void handle_sigint(int sig)
{
    printf("Caught signal %d, releasing resources...\n", sig);
    close(server_fd); // Close the server socket
    exit(0);          // Exit the program
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
}

void *client_session(void *socket_desc)
{
    int sock = *(int *)socket_desc;
    free(socket_desc);

    session_t session;
    session.sock = sock;
    strcpy(session.base_dir, base_dir);    // Base directory
    strcpy(session.current_dir, base_dir); // Default directory
    session.is_authenticated = 0;          // Default not authenticated

    int read_size;

    char *welcome_msg = "Welcome to the Secure CLI. Type 'help' to see the available commands\n";
    send(sock, welcome_msg, strlen(welcome_msg), 0);

    // Prepare and send the "In dir" message
    char dir_message[1024];
    sprintf(dir_message, "\nIn dir %s: ", session.current_dir);
    send(sock, dir_message, strlen(dir_message), 0);

    while ((read_size = recv(sock, session.buffer, BUFFER_SIZE, 0)) > 0)
    {
        // Null-terminate
        session.buffer[read_size] = '\0';

        // Trim leading and trailing whitespace
        trim_whitespace(session.buffer);

        if (interact_cli(&session) == 1)
        {
            break;
        }

        // Echo back the received message
        send(sock, session.buffer, strlen(session.buffer), 0);

        // Prepare and send the "In dir" message
        sprintf(dir_message, "\nIn dir %s: ", session.current_dir);
        send(sock, dir_message, strlen(dir_message), 0);
    }

    // inform that connection is closed
    char close_msg[] = "Client disconnecting...\n";
    send(sock, close_msg, strlen(close_msg), 0);

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
    return NULL; // Correct return type for pthread function
}

void start_server()
{
    // find the base directory of the server at startup
    getcwd(base_dir, sizeof(base_dir));

    int client_sock, *new_sock;
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

    // Set up the signal handler for SIGINT
    struct sigaction sa;
    sa.sa_handler = handle_sigint;
    sa.sa_flags = 0;
    sigemptyset(&sa.sa_mask);
    sigaction(SIGINT, &sa, NULL);

    // Accept incoming connections
    puts("Waiting for incoming connections...");
    while ((client_sock = accept(server_fd, (struct sockaddr *)&client, &socksize)))
    {
        printf("Connection accepted from %s:%d\n", inet_ntoa(client.sin_addr), ntohs(client.sin_port));

        pthread_t sniffer_thread;
        new_sock = malloc(sizeof(int));
        *new_sock = client_sock;

        if (pthread_create(&sniffer_thread, NULL, client_session, (void *)new_sock) < 0)
        {
            perror("could not create thread");
            free(new_sock);
            continue; // Continue to accept new connections even if thread creation fails
        }

        // Optionally detach the thread
        pthread_detach(sniffer_thread);
    }

    if (client_sock < 0)
    {
        perror("accept failed");
        close(server_fd);
        exit(EXIT_FAILURE); // Exit if accept fails
    }
}
