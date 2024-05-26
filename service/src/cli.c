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
#include <sys/stat.h>
#include <time.h>

// Define the macro for formatting messages into the session buffer
#define WRITE_TO_BUFFER(session, format, ...)                   \
    snprintf(session->buffer + strlen(session->buffer),         \
             sizeof(session->buffer) - strlen(session->buffer), \
             format, ##__VA_ARGS__)

int round = 1; // not safe by itself when everyone has the same seed (use flag from server as seed?)

void generate_password(char *password, size_t length)
{
    // Define the characters that we want to use in our password
    char characters[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$^&*()";

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
    if (chdir(session->full_dir) != 0)
    {
        WRITE_TO_BUFFER(session, "Failed to use session's current directory\n");
        return 0;
    }

    // Parse the first word as the command
    sscanf(input, "%255s", command);

    if (strncmp(command, "sail", 255) == 0)
    {
        // Extract directory from input
        char *directory = strchr(input, ' ');
        if (directory && *(directory + 1))
        {
            change_directory(directory + 1, session);
        }
        else
        {
            WRITE_TO_BUFFER(session, "Aye aye, captain, but where to?\n");
            return 0;
        }
    }
    else if (strncmp(command, "bury", 255) == 0)
    {
        char file_path[1024] = "";
        char custom_ID[20] = "";
        char *argument1 = strchr(input, ' ');
        if (argument1 && *(argument1 + 1))
        {
            char *argument2 = strchr(argument1 + 1, ' ');
            if (argument2 && *(argument2 + 1))
            {
                strncpy(file_path, argument1 + 1, argument2 - argument1 - 1);
                file_path[argument2 - argument1 - 1] = '\0';
                strcpy(custom_ID, argument2 + 1);
                trim_whitespace(file_path);
                trim_whitespace(custom_ID);
            }
            else
            {
                strcpy(file_path, argument1 + 1);
                trim_whitespace(file_path);
                generate_password(custom_ID, 16);
            }
        }

        // If at root, can't bury treasure
        if (strcmp(session->full_dir, session->root_dir) == 0)
        {
            WRITE_TO_BUFFER(session, "Can't bury treasure at sea\n");
            return 0;
        }

        // Ask about the scam
        char date[11];
        char time_str[6];
        char content[PATH_MAX];

        // Ask for scam details
        WRITE_TO_BUFFER(session, "What time to save for? (YYYY-MM-DD HH:MM or blank for now): ");
        send(session->sock, session->buffer, strlen(session->buffer), 0);
        memset(session->buffer, 0, sizeof(session->buffer));
        int read_size;
        char time_input[256];
        read_size = recv(session->sock, time_input, 256, 0);
        // Null-terminate and remove newline
        time_input[read_size - 1] = '\0'; // remove newline

        struct tm tm;
        // Using provided date and time
        if (strptime(time_input, "%Y-%m-%d %H:%M", &tm) != NULL)
        {
            sprintf(date, "%04d-%02d-%02d", tm.tm_year + 1900, tm.tm_mon + 1, tm.tm_mday);
            sprintf(time_str, "%02d:%02d", tm.tm_hour, tm.tm_min);
        }
        else
        {
            // Using actual local date and time
            time_t t = time(NULL);
            struct tm *tm = localtime(&t);
            strftime(date, sizeof(date), "%Y-%m-%d", tm);
            strftime(time_str, sizeof(time_str), "%H:%M", tm);
        }

        WRITE_TO_BUFFER(session, "Protect with a parrot? (enter password or blank for nothing): ");
        send(session->sock, session->buffer, strlen(session->buffer), 0);
        memset(session->buffer, 0, sizeof(session->buffer));
        read_size;
        char parrot_input[256];
        read_size = recv(session->sock, parrot_input, 256, 0);
        // Null-terminate and remove newline
        parrot_input[read_size] = '\0';
        trim_whitespace(parrot_input);
        fflush(stdout);
        WRITE_TO_BUFFER(session, "What's your message: ");
        send(session->sock, session->buffer, strlen(session->buffer), 0);
        memset(session->buffer, 0, sizeof(session->buffer));
        char message_input[1024];
        read_size = recv(session->sock, message_input, 1024, 0);
        // Null-terminate and remove newline
        message_input[read_size] = '\0';
        fflush(stdout);

        sprintf(content, "Scam Details:\n----------------\nDate: %s\nTime: %s UTC\nScammer: %s %s\nScammer ID: %s\n\nMessage: %s",
                date,
                time_str, session->pirate_adjective, session->pirate_noun, custom_ID, message_input);

        printf("%s\n", content);

        // Create a new file at the current destination
        char scam_filename[1024];

        // If there is already a second argument, use it as the filename
        if (strlen(file_path) > 0)
        {
            strcpy(scam_filename, file_path);
        }
        else
        {
            sprintf(scam_filename, "%s_%s_scam_%s_%s", session->pirate_adjective, session->pirate_noun, date, time_str);
        }

        // Save as a treasure file with a password
        if (strncmp(parrot_input, "", 255) != 0)
        {
            sprintf(scam_filename, "%s.treasure", scam_filename);
            // add the password to the end of the content
            sprintf(content, "%s\n\nProtected with password:\n%s", content, parrot_input);
            WRITE_TO_BUFFER(session, "Protected with password: %s\n", parrot_input);
        }
        else // or normal log file
        {
            sprintf(scam_filename, "%s.log", scam_filename);
        }

        // If file already exists, creation fails
        if (access(scam_filename, F_OK) != -1)
        {
            // File exists
            WRITE_TO_BUFFER(session, "Something is already burried at '%s'\n", scam_filename);
            return 0;
        }

        printf("Creating file: %s\n", scam_filename);

        FILE *scam_file = fopen(scam_filename, "w");
        if (scam_file == NULL)
        {
            WRITE_TO_BUFFER(session, "Couldn't bury the treasure\n");
            return 0;
        }
        // Write the scam details to the file
        fprintf(scam_file, "%s", content);
        fclose(scam_file);

        WRITE_TO_BUFFER(session, "Treasure burried at '%s'\n", scam_filename);
    }
    else if (strncmp(command, "loot", 255) == 0)
    {
        // Extract filename from input
        char *filename = strchr(input, ' ');
        if (filename && *(filename + 1))
        {
            // If filename include "/", it is not valid, as we can only loot at the current destination
            if (strchr(filename + 1, '/') != NULL)
            {
                WRITE_TO_BUFFER(session, "Can't loot that far from shore\n");
                return 0;
            }
            cat_file(filename + 1, session);
            return 0;
        }
        else
        {
            WRITE_TO_BUFFER(session, "Aye aye, captain, but what item?\n");
            return 0;
        }
    }
    else if (strncmp(command, "scout", 255) == 0)
    {
        // Extract directory from input, if provided
        char *directory_name = strchr(input, ' ');
        char directory_path[1024];

        if (directory_name && *(directory_name + 1))
        {
            strcpy(directory_path, directory_name + 1);
        }
        else
        {
            strcpy(directory_path, ".");
        }

        char resolved_path[PATH_MAX];
        if (realpath(directory_path, resolved_path) == NULL)
        {
            WRITE_TO_BUFFER(session, "Couldn't find any place to scout '%s'\n", directory_path);
            return 0;
        }

        // Check if the resolved path is within the base directory
        if (strncmp(session->root_dir, resolved_path, strlen(session->root_dir)) != 0)
        {
            WRITE_TO_BUFFER(session, "Only blue ocean as far as the eye can see\n");
            return 0;
        }

        DIR *directory = opendir(resolved_path);
        if (directory == NULL)
        {
            WRITE_TO_BUFFER(session, "Scouting '%s' doesn't really work\n", directory_path); // TODO: Consider leaking info here as intentional vuln?
            return 0;
        }

        struct dirent *entry;
        while ((entry = readdir(directory)) != NULL)
        {
            // Calculate the remaining buffer size before writing
            int remaining_buffer_size = sizeof(session->buffer) - strlen(session->buffer) - 1;
            if (remaining_buffer_size > 0)
            {
                WRITE_TO_BUFFER(session, "%s\n", entry->d_name);
            }
            else
            {
                // Buffer full, handle error if needed
                break;
            }
        }
        closedir(directory);
    }

    else if (strncmp(command, "codex", 255) == 0)
    {
        help(session);
    }
    else if (strncmp(command, "dock", 255) == 0)
    {
        return 1; // 1 indicates that the client should be disconnected
    }
    else
    {
        WRITE_TO_BUFFER(session, "Arr! That ain't proper pirate speech. Have you read the codex?\n");
    }

    return 0;
}

int change_directory(char *path, session_t *session)
{
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
        WRITE_TO_BUFFER(session, "Couldn't set course for '%s'\n", path);
        return 0;
    }
    // store the new directory
    char new_path[1024];
    if (getcwd(new_path, sizeof(new_path)) == NULL)
    {
        WRITE_TO_BUFFER(session, "Error getting new directory: %s\n", path);
        return 0;
    }

    // Successfully changed directory, now store the new dir in full_dir if it still includes root_dir
    // then return to original to maintain state
    if (strncmp(session->root_dir, new_path, strlen(session->root_dir)) == 0)
    {
        strcpy(session->full_dir, new_path);
        strcpy(session->local_dir, new_path + strlen(session->root_dir));
        // if session->local_dir is empty, set it to "/"
        if (strlen(session->local_dir) == 0)
        {
            strcpy(session->local_dir, "/");
        }
        chdir(org_path);
    }
    else // we are no longer in the base directory
    {
        chdir(org_path);

        WRITE_TO_BUFFER(session, "The waves are too rough to sail that far!\n");
        return 0;
    }

    return 0;
}

void cat_file(char *filename, session_t *session)
{
    // first of all, check if the file actually exists
    // check that it is not a directory
    struct stat path_stat;
    char file_path[PATH_MAX];
    sprintf(file_path, "%s/%s", session->full_dir, filename);
    if (stat(file_path, &path_stat) != 0)
    {
        WRITE_TO_BUFFER(session, "No treasure '%s' to loot\n", filename);
        return;
    }

    if (S_ISDIR(path_stat.st_mode))
    {
        WRITE_TO_BUFFER(session, "'%s' is a destination, not a treasure\n", filename);
        return;
    }

    // If this is a .treasure file, ask for a password to open
    if (strstr(filename, ".treasure") != NULL)
    {
        char correct_password[256];
        // read the last line of the file, this is the password
        FILE *file = fopen(file_path, "r");
        if (file == NULL)
        {
            WRITE_TO_BUFFER(session, "No treasure '%s' to loot\n", filename);
            return;
        }
        char line[256];
        while (fgets(line, sizeof(line), file))
        {
            strcpy(correct_password, line);
        }
        fclose(file);
        WRITE_TO_BUFFER(session, "A parrot is guarding the treasure tightly\n");
        WRITE_TO_BUFFER(session, "Speak your words: ");
        send(session->sock, session->buffer, strlen(session->buffer), 0);
        memset(session->buffer, 0, sizeof(session->buffer));
        int read_size;
        char password_input[256];
        read_size = recv(session->sock, password_input, 256, 0);
        // Null-terminate and remove newline
        password_input[read_size] = '\0';
        trim_whitespace(password_input);
        fflush(stdout);
        WRITE_TO_BUFFER(session, password_input);
        WRITE_TO_BUFFER(session, ", ");
        WRITE_TO_BUFFER(session, password_input);
        WRITE_TO_BUFFER(session, ", captain!\n");
        if (strncmp(password_input, correct_password, 255) != 0)
        {
            return;
        }

        // Correct password was entered, so generate a new password for the next time
        round++;
    }

    // Open and print the contents of the file
    FILE *file = fopen(filename, "r");
    // print current directory
    if (file == NULL)
    {
        printf("tried opening undefined file: %s\n", filename);
        return;
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
    WRITE_TO_BUFFER(session, "The Official Pirate Codex:\n");
    WRITE_TO_BUFFER(session, "  scout [destination] - Search current or desired destination for items\n");
    WRITE_TO_BUFFER(session, "  sail [destination] - Set sail for a new destination\n");
    WRITE_TO_BUFFER(session, "  bury - bury treasure for others to find at your destination\n");
    WRITE_TO_BUFFER(session, "  loot [item] - Grab the contents of an item at your destination\n");
    WRITE_TO_BUFFER(session, "  codex - Display this pirate codex\n");
    WRITE_TO_BUFFER(session, "  dock - Dock your ship and leave Pirate Prattle\n");
}