#include "cli.h"
#include "session.h"
#include "server.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <dirent.h>
#include <limits.h>
#include <sys/socket.h>

// Define the macro for formatting messages into the session buffer
#define WRITE_TO_BUFFER(session, format, ...)                   \
    snprintf(session->buffer + strlen(session->buffer),         \
             sizeof(session->buffer) - strlen(session->buffer), \
             format, ##__VA_ARGS__)

int round = 1; // not safe by itself when everyone has the same seed (use flag from server as seed?)

void generate_password(char *password, size_t length)
{
    // Define the characters that we want to use in our password
    char characters[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()";

    // Initialize the random number generator
    srand(round);

    // Generate a random password
    for (size_t i = 0; i < length; i++)
    {
        password[i] = characters[rand() % (sizeof(characters) - 1)];
    }

    // Null-terminate the string
    password[length] = '\0';
}

int interact_cli(session_t *session)
{

    // Define the macro for formatting messages into the session buffer
#define SNPRINTF_TO_BUFFER(format, ...) \
    snprintf(session->buffer, sizeof(session->buffer), format, ##__VA_ARGS__)

    // if buffer is empty, return
    if (strlen(session->buffer) == 0)
    {
        return 0;
    }

    // copy buffer to input
    char input[1024];
    strcpy(input, session->buffer);
    // clearing buffer to use as output
    memset(session->buffer, 0, sizeof(session->buffer));

    char command[1024];
    // chdir to this session's current directory
    if (chdir(session->current_dir) != 0)
    {
        WRITE_TO_BUFFER(session, "Failed to use session's current directory\n");
        return 0;
    }

    // Parse the first word as the command
    sscanf(input, "%255s", command);

    if (strncmp(command, "cd", 255) == 0)
    {
        // Extract directory from input
        char *directory = strchr(input, ' ');
        if (directory && *(directory + 1))
        {
            change_directory(directory + 1, session);
        }
        else
        {
            WRITE_TO_BUFFER(session, "No directory specified.\n");
            return 0;
        }
    }
    else if (strncmp(command, "cat", 255) == 0)
    {
        // Extract filename from input
        char *filename = strchr(input, ' ');
        if (filename && *(filename + 1))
        {
            cat_file(filename + 1, session);
            return 0;
        }
        else
        {
            WRITE_TO_BUFFER(session, "No file specified.\n");
            return 0;
        }
    }
    else if (strncmp(command, "ls", 255) == 0)
    {
        DIR *directory = opendir(".");
        if (directory == NULL)
        {
            WRITE_TO_BUFFER(session, "Failed to open directory.\n");
            return 0;
        }

        struct dirent *entry;
        while ((entry = readdir(directory)) != NULL)
        {
            // Calculate the remaining buffer size before writing
            int remaining_buffer_size = sizeof(session->buffer) - strlen(session->buffer) - 1;
            if (remaining_buffer_size > 0)
            {
                snprintf(session->buffer + strlen(session->buffer), remaining_buffer_size, "%s\n", entry->d_name);
            }
            else
            {
                // Buffer full, handle error if needed
                break;
            }
        }
        closedir(directory);
    }

    else if (strncmp(command, "help", 255) == 0)
    {
        help(session);
    }
    else if (strncmp(command, "exit", 255) == 0)
    {
        return 1; // 1 indicates that the client should be disconnected
    }
    else
    {
        WRITE_TO_BUFFER(session, "Unknown command.\n");
    }

    return 0;
}

int change_directory(char *path, session_t *session)
{
    printf("Received: %s\n", path); // Debugging (remove later
    // Store original path to restore later if needed
    char org_path[1024];
    if (getcwd(org_path, sizeof(org_path)) == NULL)
    {
        WRITE_TO_BUFFER(session, "Error getting old directory: %s\n", path);
        return 0;
    }

    // Try to change to the new directory
    if (chdir(path) != 0)
    {
        // On failure, report the error
        WRITE_TO_BUFFER(session, "Failed to change directory to '%s'\n", path);
        printf("Received: %s\n", path); // Debugging (remove later
        return 0;
    }
    // store the new directory
    char new_path[1024];
    if (getcwd(new_path, sizeof(new_path)) == NULL)
    {
        WRITE_TO_BUFFER(session, "Error getting new directory: %s\n", path);
        return 0;
    }

    // Successfully changed directory, now store the new dir in current_dir if it still includes base_dir
    // then return to original to maintain state
    if (strncmp(session->base_dir, new_path, strlen(session->base_dir)) == 0)
    {
        strcpy(session->current_dir, new_path);
        WRITE_TO_BUFFER(session, "Changed directory to '%s'\n", new_path);
        chdir(org_path);
    }
    else // we are no longer in the base directory
    {
        chdir(org_path);

        WRITE_TO_BUFFER(session, "Failed to change directory to '%s': Not in base directory\n", new_path);
        return 0;
    }

    return 0;
}

void cat_file(char *filename, session_t *session)
{
    // If this is a .scam file, ask for a password to open
    if (strstr(filename, ".scam") != NULL)
    {
        char correct_password[256] = "AAAAAAAA";
        generate_password(correct_password, 16);
        WRITE_TO_BUFFER(session, "You might not be cool enough to view this file. Please enter the top secret scammer's password.\n");
        WRITE_TO_BUFFER(session, "Enter password: ");
        send(session->sock, session->buffer, strlen(session->buffer), 0);
        memset(session->buffer, 0, sizeof(session->buffer));
        int read_size;
        char password_input[256];
        // printf("This is before: %s\n", correct_password);
        read_size = recv(session->sock, password_input, 256, 0);
        // Null-terminate and remove newline
        password_input[read_size] = '\0';
        trim_whitespace(password_input);
        fflush(stdout);
        if (strncmp(password_input, correct_password, 255) != 0)
        {
            WRITE_TO_BUFFER(session, password_input);
            WRITE_TO_BUFFER(session, " is incorrect!");
            return;
        }
    }

    FILE *file = fopen(filename, "r");
    if (file == NULL)
    {
        WRITE_TO_BUFFER(session, "Cannot open file: %s\n", filename);
    }

    char line[256];
    while (fgets(line, sizeof(line), file))
    {
        WRITE_TO_BUFFER(session, "%s", line);
    }

    fclose(file);
}

void help(session_t *session)
{
    WRITE_TO_BUFFER(session, "Available commands:\n");
    WRITE_TO_BUFFER(session, "  ls - List files in the current directory\n");
    WRITE_TO_BUFFER(session, "  cd [directory] - Change current working directory\n");
    WRITE_TO_BUFFER(session, "  cat [file] - Display content of a text file\n");
    WRITE_TO_BUFFER(session, "  help - Display this help message\n");
    WRITE_TO_BUFFER(session, "  exit - Exit the program\n");
}
