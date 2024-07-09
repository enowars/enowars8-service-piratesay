#include <stdio.h>
#include <stdlib.h>

#define IDENTITY_LENGTH 64

int main()
{
    unsigned int seed;
    printf("Enter a seed value: ");
    scanf("%u", &seed);

    srand(seed);

    char identity_string[IDENTITY_LENGTH + 1]; // +1 for the null terminator

    for (int i = 0; i < IDENTITY_LENGTH; i++)
    {
        identity_string[i] = 'a' + (rand() % 26);
    }
    identity_string[IDENTITY_LENGTH] = '\0'; // Null terminate the string

    printf("Generated identity string: %s\n", identity_string);

    return 0;
}
