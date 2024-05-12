#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/personality.h> // Include this header

// gcc -z execstack -z norelro -fno-stack-protector -o format0 format0.c

int main(int argc, char *argv[])
{

    char pass[10] = "AABBCCDD";
    int *ptr = pass;
    char buf[100];

    fgets(buf, 100, stdin);
    buf[strcspn(buf, "\n")] = '\0';

    if (!strncmp(pass, buf, sizeof(pass)))
    {
        printf("Greetings!\n");
        return EXIT_SUCCESS;
    }
    else
    {
        printf(buf);
        printf(" does not have access!\n");
        exit(EXIT_FAILURE);
    }

    return EXIT_SUCCESS;
}