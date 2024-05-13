#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <dirent.h>
#include <limits.h>

// Function Declarations
void change_directory(char *path);
void cat_file(char *filename);
void help();

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

int command_line_interface()
{
    char command[256];
    char input[256];

    // init an initial directory which is where the script is run from
    char initial_dir[PATH_MAX];
    if (getcwd(initial_dir, sizeof(initial_dir)) == NULL)
    {
        perror("getcwd() error");
        return 1;
    }

    printf("Welcome to the Secure File Viewer!\nType 'help' for a list of commands.\n");

    char cwd[PATH_MAX];
    while (1)
    {
        if (getcwd(cwd, sizeof(cwd)) == NULL)
        {
            perror("getcwd() error");
            return 1;
        }

        printf("\nIn dir %s: ", cwd);
        fflush(stdout); // Flush to print prompt before input
        fgets(input, sizeof(input), stdin);

        // Parse the first word as the command
        sscanf(input, "%255s", command);

        if (strncmp(command, "cd", 255) == 0)
        {
            // Extract directory from input
            char *directory = strchr(input, ' ');
            if (directory && *(directory + 1))
            {
                change_directory(directory + 1);
            }
            else
            {
                printf("No directory specified.\n");
            }
        }
        else if (strncmp(command, "cat", 255) == 0)
        {
            // Extract filename from input
            char *filename = strchr(input, ' ');
            if (filename && *(filename + 1))
            {
                cat_file(filename + 1);
            }
            else
            {
                printf("No file specified.\n");
            }
        }
        else if (strncmp(command, "ls", 255) == 0)
        {
            DIR *directory = opendir(".");
            if (directory == NULL)
            {
                printf("Failed to open directory.\n");
                continue;
            }

            struct dirent *entry;
            while ((entry = readdir(directory)) != NULL)
            {
                printf("%s\n", entry->d_name);
            }
            closedir(directory);
        }
        else if (strncmp(command, "help", 255) == 0)
        {
            help();
        }
        else if (strncmp(command, "exit", 255) == 0)
        {
            break;
        }
        else
        {
            printf("Unknown command.\n");
        }
    }
    return 0;
}

void change_directory(char *path)
{
    // Trim newline
    path[strcspn(path, "\n")] = 0;
    if (chdir(path) == 0)
    {
        printf("Changed directory to %s\n", path);
    }
    else
    {
        printf("Failed to change directory to %s\n", path);
    }
}

void cat_file(char *filename)
{
    // Trim newline
    filename[strcspn(filename, "\n")] = 0;

    // If this is a .scam file, ask for a password to open
    if (strstr(filename, ".scam") != NULL)
    {
        char correct_password[16] = "AAAAAAAA";
        char password[256];
        generate_password(correct_password, 16);
        printf("You might not be cool enough to view this file. Please enter the top secret scammer's password.\n");
        printf("Enter password: ");
        fflush(stdout); // Flush to print prompt before input
        fgets(password, sizeof(password), stdin);
        // printf(password);
        // return;
        password[strcspn(password, "\n")] = 0; // Trim newline
        if (strncmp(password, correct_password, 255) != 0)
        {
            printf(password);
            printf(" is incorrect!");
            return;
        }
    }

    FILE *file = fopen(filename, "r");
    if (file == NULL)
    {
        printf("Cannot open file: %s\n", filename);
        return;
    }

    char line[256];
    while (fgets(line, sizeof(line), file))
    {
        printf("%s", line); // Intentionally omitting format string to introduce vulnerability
    }
    fclose(file);
}

void help()
{
    printf("Available commands:\n");
    printf("  ls - List files in the current directory\n");
    printf("  cd [directory] - Change current working directory\n");
    printf("  cat [file] - Display content of a text file\n");
    printf("  help - Display this help message\n");
    printf("  exit - Exit the program\n");
}
