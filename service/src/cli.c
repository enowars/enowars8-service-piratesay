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
#include <ctype.h>
#include <openssl/sha.h>

// Define the macro for formatting messages into the session buffer
#define WRITE_TO_BUFFER(session, format, ...)                   \
    snprintf(session->buffer + strlen(session->buffer),         \
             sizeof(session->buffer) - strlen(session->buffer), \
             format, ##__VA_ARGS__)

void generate_custom_id(char *password, size_t length)
{
    // Define the characters that we want to use in our password
    char characters[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$^&*()";

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
        char custom_ID[256] = "";
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
            }
            else
            {
                strcpy(file_path, argument1 + 1);
                trim_whitespace(file_path);
                generate_custom_id(custom_ID, 16);
            }
        }

        // If at root, can't bury treasure
        if (strcmp(session->full_dir, session->root_dir) == 0)
        {
            WRITE_TO_BUFFER(session, "Can't bury treasure at sea\n");
            return 0;
        }

        // If file path contains "/", it is not valid
        if (strchr(file_path, '/') != NULL)
        {
            WRITE_TO_BUFFER(session, "Can only bury treasure where your ship is\n");
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

        WRITE_TO_BUFFER(session, "Protect with a parrot? (enter password or leave blank for unprotected): ");
        send(session->sock, session->buffer, strlen(session->buffer), 0);
        memset(session->buffer, 0, sizeof(session->buffer));
        read_size;
        char parrot_input[256];
        read_size = recv(session->sock, parrot_input, 256, 0);
        // Null-terminate and remove newline
        parrot_input[read_size] = '\0';
        trim_whitespace(parrot_input);
        fflush(stdout);

        // If parrot input is empty, ask to save with identity
        int save_with_identity = 0;
        if (strncmp(parrot_input, "", 255) == 0)
        {
            WRITE_TO_BUFFER(session, "Protect with your pirate identity? (y/n): ");
            send(session->sock, session->buffer, strlen(session->buffer), 0);
            memset(session->buffer, 0, sizeof(session->buffer));
            char identity_input[256];
            read_size = recv(session->sock, identity_input, 256, 0);
            // Null-terminate and remove newline
            identity_input[read_size - 1] = '\0';
            trim_whitespace(identity_input);
            fflush(stdout);

            if (strncmp(identity_input, "y", 255) == 0)
            {
                save_with_identity = 1;
            }
        }

        WRITE_TO_BUFFER(session, "What's your message: ");
        send(session->sock, session->buffer, strlen(session->buffer), 0);
        memset(session->buffer, 0, sizeof(session->buffer));
        char message_input[1024];
        read_size = recv(session->sock, message_input, 1024, 0);
        // Null-terminate and remove newline
        message_input[read_size - 1] = '\0';
        fflush(stdout);

        sprintf(content, "Scam Details:\n----------------\nDate: %s\nTime: %s UTC\nScammer: %s %s\nScammer ID: %s\n\nMessage: %s",
                date,
                time_str, session->pirate_adjective, session->pirate_noun, custom_ID, message_input);

        // Create a new file at the current destination
        char scam_filename[1024];

        // If there is already a second argument, use it as the filename
        if (strlen(file_path) > 0)
        {
            strcpy(scam_filename, file_path);
        }
        else
        {
            // Generate a filename based on scam details
            char lower_case_pirate_adjective[sizeof(session->pirate_adjective)];
            char lower_case_pirate_noun[sizeof(session->pirate_noun)];
            strcpy(lower_case_pirate_adjective, session->pirate_adjective);
            strcpy(lower_case_pirate_noun, session->pirate_noun);
            lower_case_pirate_adjective[0] = tolower(lower_case_pirate_adjective[0]);
            lower_case_pirate_noun[0] = tolower(lower_case_pirate_noun[0]);

            int j = 0;
            for (int i = 0; i < strlen(time_str); i++)
            {
                if (time_str[i] != ':')
                {
                    // can modify directly, as it is not re-used later
                    time_str[j++] = time_str[i];
                }
            }
            time_str[j] = '\0'; // Null-terminate the adjusted time string

            sprintf(scam_filename, "%s_%s_scam_%s_%s", lower_case_pirate_adjective, lower_case_pirate_noun, date, time_str);
        }

        // Save as a treasure file with a password
        if (strncmp(parrot_input, "", 255) != 0)
        {
            sprintf(scam_filename, "%s.treasure", scam_filename);
            // add the password to the end of the content
            sprintf(content, "%s\n\nProtected with password:\n%s", content, parrot_input);
        }
        // save as a private file with identity
        else if (save_with_identity)
        {
            sprintf(scam_filename, "%s.private", scam_filename);
            // hash the identity and add it to the end of the content
            unsigned char hash[SHA256_DIGEST_LENGTH];
            compute_sha256(session->pirate_identity, hash);
            sprintf(content, "%s\n\nProtected with identity hash:\n%s", content, hash);
        }
        else // or normal log file
        {
            sprintf(scam_filename, "%s.log", scam_filename);
        }

        // Get absolute path
        char absolute_path[PATH_MAX];
        snprintf(absolute_path, sizeof(absolute_path), "%s/%s", session->full_dir, scam_filename);
        // If file already exists, creation fails
        if (access(absolute_path, F_OK) != -1)
        {
            // File exists
            WRITE_TO_BUFFER(session, "Something is already burried at '%s'\n", scam_filename);
            return 0;
        }

        printf("Creating file: %s\n", scam_filename);

        FILE *scam_file = fopen(absolute_path, "w");
        if (scam_file == NULL)
        {
            WRITE_TO_BUFFER(session, "Unable to bury\n");
            return 0;
        }
        // Write the scam details to the file
        fprintf(scam_file, "%s", content);
        fclose(scam_file);

        WRITE_TO_BUFFER(session, "Burried at '%s'\n", scam_filename);
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
                WRITE_TO_BUFFER(session, "Can only loot where your ship is\n");
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
        char absolute_path[PATH_MAX];
        snprintf(absolute_path, sizeof(absolute_path), "%s/%s", session->full_dir, directory_path);
        char resolved_path[PATH_MAX];
        if (realpath(absolute_path, resolved_path) == NULL)
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
            WRITE_TO_BUFFER(session, "Scouting '%s' doesn't really work\n", directory_path);
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
    else if (strncmp(command, "identity", 255) == 0)
    {
        identity(session);
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
    char absolute_path[PATH_MAX];
    snprintf(absolute_path, sizeof(absolute_path), "%s/%s", session->full_dir, path);
    char resolved_path[PATH_MAX];

    // 1. Resolve the path to an absolute path
    if (realpath(absolute_path, resolved_path) == NULL)
    {
        WRITE_TO_BUFFER(session, "Couldn't set course for '%s'. Path does not exist or is not accessible.\n", path);
        return 0;
    }

    // 2. Check if the resolved path is a directory
    struct stat path_stat;
    if (stat(resolved_path, &path_stat) != 0)
    {
        WRITE_TO_BUFFER(session, "Error getting status of '%s'\n", path);
        return 0;
    }

    if (!S_ISDIR(path_stat.st_mode))
    {
        WRITE_TO_BUFFER(session, "Sailing to '%s' doesn't really work\n", path);
        return 0;
    }

    // 3. Ensure the resolved path is within the root directory
    if (strncmp(session->root_dir, resolved_path, strlen(session->root_dir)) != 0)
    {
        WRITE_TO_BUFFER(session, "You cannot sail beyond the seven seas (root directory)\n");
        return 0;
    }

    // 4. Update the full_dir and local_dir if all checks pass
    strcpy(session->full_dir, resolved_path);

    // Calculate the local directory relative to the root directory
    snprintf(session->local_dir, sizeof(session->local_dir), "%s", resolved_path + strlen(session->root_dir));

    // Ensure local_dir starts with a '/'
    if (session->local_dir[0] != '/')
    {
        char temp_dir[PATH_MAX];
        snprintf(temp_dir, sizeof(temp_dir), "/%s", session->local_dir);
        strcpy(session->local_dir, temp_dir);
    }

    WRITE_TO_BUFFER(session, "Set course for '%s'\n", session->local_dir);
    return 1;
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
        if (strncmp(password_input, correct_password, 255) != 0)
        {
            // Parrot feedback
            char feedback[1024];
            snprintf(feedback, sizeof(feedback), "%s is wrong, %s is wrong, captain!\n", password_input, password_input);
            WRITE_TO_BUFFER(session, feedback);
            return;
        }
    }

    // If this is a .private file, check if the identity matches
    else if (strstr(filename, ".private") != NULL)
    {
        char correct_hash[65];
        // read the last line of the file, this is the identity
        FILE *file = fopen(file_path, "r");
        if (file == NULL)
        {
            WRITE_TO_BUFFER(session, "No treasure '%s' to loot\n", filename);
            return;
        }
        char line[256];
        while (fgets(line, sizeof(line), file))
        {
            strcpy(correct_hash, line);
        }
        fclose(file);

        // Check if the hash of the pirate identity matches the stored identity
        int has_access = 0;
        unsigned char hash[65];
        compute_sha256(session->pirate_identity, hash);
        if (strncmp(correct_hash, (char *)hash, 64) == 0)
        {
            has_access = 1;
        }

        if (!has_access)
        {
            // other users can still access the file if they were given the key by the owner
            char identity_input[65];
            WRITE_TO_BUFFER(session, "This is not your private treasure; prove the owner has entrusted you their code\n");
            WRITE_TO_BUFFER(session, "Identity code: ");
            send(session->sock, session->buffer, strlen(session->buffer), 0);
            memset(session->buffer, 0, sizeof(session->buffer));
            int read_size;
            read_size = recv(session->sock, identity_input, 65, 0);
            // Null-terminate and remove newline
            identity_input[read_size - 1] = '\0';
            trim_whitespace(identity_input);
            fflush(stdout);
            // Check if the hash of the inputed identity matches the stored identity
            compute_sha256(identity_input, hash);
            if (strncmp(correct_hash, (char *)hash, 64) == 0)
            {
                has_access = 1;
            }
            else
            {
                // warn the user to deter them from trying again
                char warning[1024];
                snprintf(warning, sizeof(warning), "Ahoy, trying to steal are we? Your identity %s doesn't match. Keep this up and you'll be forced to walk the plank!\n", session->pirate_identity);
                WRITE_TO_BUFFER(session, warning);
            }
        }

        // if still no access, return
        if (!has_access)
        {
            return;
        }
    }

    // Open and print the contents of the file
    FILE *file = fopen(file_path, "r");
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

    // Write newline for aesthetic reasons
    WRITE_TO_BUFFER(session, "\n");
}

void identity(session_t *session)
{
    // log all the session info
    WRITE_TO_BUFFER(session, "Pirate Identity: %s\n", session->pirate_identity);
    WRITE_TO_BUFFER(session, "Pirate Name: %s %s\n", session->pirate_adjective, session->pirate_noun);

    // Input your new identity (leave blank to keep the same)
    WRITE_TO_BUFFER(session, "Enter your new pirate identity (leave empty to keep current): ");
    send(session->sock, session->buffer, strlen(session->buffer), 0);
    memset(session->buffer, 0, sizeof(session->buffer));
    int read_size;
    char new_identity[256];
    read_size = recv(session->sock, new_identity, 256, 0);
    // Null-terminate and remove newline
    new_identity[read_size - 1] = '\0';
    trim_whitespace(new_identity);
    fflush(stdout);

    if (strlen(new_identity) > 0)
    {
        // Check if the new identity is valid
        if (strlen(new_identity) != 64)
        {
            WRITE_TO_BUFFER(session, "Length must be 64 (not %d)\n", strlen(new_identity));
            return;
        }

        // Update the pirate identity
        strcpy(session->pirate_identity, new_identity);
        strcpy(session->pirate_adjective, get_adjective_from_identity(session->pirate_identity));
        strcpy(session->pirate_noun, get_noun_from_identity(session->pirate_identity));
        WRITE_TO_BUFFER(session, "Pirate identity updated\n");
    }
    else
    {
        WRITE_TO_BUFFER(session, "Pirate identity unchanged\n");
    }
}

void help(session_t *session)
{
    WRITE_TO_BUFFER(session, "The Official Pirate Codex:\n");
    WRITE_TO_BUFFER(session, "  scout [destination] - Search current or desired destination for items\n");
    WRITE_TO_BUFFER(session, "  sail [destination] - Set sail for a new destination\n");
    WRITE_TO_BUFFER(session, "  bury - bury treasure for others to find at your destination\n");
    WRITE_TO_BUFFER(session, "  loot [item] - Grab the contents of an item at your destination\n");
    WRITE_TO_BUFFER(session, "  identity - manage your pirate identity \n");
    WRITE_TO_BUFFER(session, "  codex - Display this pirate codex\n");
    WRITE_TO_BUFFER(session, "  dock - Dock your ship and leave Pirate Say\n");
}

// Checks for a hash