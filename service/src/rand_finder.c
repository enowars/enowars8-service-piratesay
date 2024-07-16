#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// Linear Congruential Generator parameters
#define A 1103515245
#define C 12345
#define M 2147483648UL // 2^31
#define RAND_MAX 2147483647

// Seed value, initialized to 1
static unsigned long seed = 1;

// Seed the random number generator
void slcgrand(unsigned int s)
{
    seed = s;
}

// Generate a random number using LCG
int lcgrand()
{
    seed = (A * seed + C) % M;
    return (int)seed; // Cast to int to match typical rand function return type
}

// Generate a random identity string of given length
void generate_random_identity(char *identity_string, int length)
{
    for (int i = 0; i < length; i++)
    {
        identity_string[i] = 'a' + (lcgrand() % 26); // Generate a random lowercase letter
    }
    identity_string[length] = '\0'; // Null-terminate the string
}

int main(int argc, char *argv[])
{
    if (argc != 3)
    {
        fprintf(stderr, "Usage: %s <start_seed> <identity_to_match>\n", argv[0]);
        return 1;
    }

    unsigned int start_seed = atoi(argv[1]);
    char *identity_to_match = argv[2];
    int identity_length = strlen(identity_to_match);
    char generated_identity[identity_length + 1];
    unsigned long initial_seed = start_seed;

    slcgrand(start_seed);

    unsigned long offset = 0;
    while (1)
    {
        generate_random_identity(generated_identity, identity_length);
        offset++;
        if (strcmp(generated_identity, identity_to_match) == 0)
        {
            printf("Match found!\n");
            printf("Offset: %lu\n", offset);
            printf("Seed: %lu\n", seed);
            break;
        }
    }

    return 0;
}
