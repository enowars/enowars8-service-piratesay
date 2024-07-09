#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <openssl/sha.h>
#include <time.h>

#define NUM_ADJECTIVES 10
#define NUM_NOUNS 10
#define IDENTITY_LENGTH 64

char *pirate_adjectives[NUM_ADJECTIVES] = {
    "Red", "Black", "Silver", "Golden", "Scarlet", "Dark", "White", "Blue", "Rogue", "Stormy"};

char *pirate_nouns[NUM_NOUNS] = {
    "Beard", "Jack", "Bart", "Pete", "Anne", "Patty", "John", "Hook", "Bill", "Bonny"};

// Function to compute SHA-256 hash of a string
void compute_sha256(const char *str, char *outputBuffer)
{
    unsigned char hash[SHA256_DIGEST_LENGTH];
    SHA256_CTX sha256;
    SHA256_Init(&sha256);
    SHA256_Update(&sha256, str, strlen(str));
    SHA256_Final(hash, &sha256);

    // Convert the binary hash to a hexadecimal string
    for (int i = 0; i < SHA256_DIGEST_LENGTH; i++)
    {
        sprintf(outputBuffer + (i * 2), "%02x", hash[i]);
    }

    outputBuffer[SHA256_DIGEST_LENGTH * 2] = '\0'; // Null-terminate the string
}

// Function to generate a random identity string
void generate_random_identity(char *identity_string)
{
    for (int i = 0; i < IDENTITY_LENGTH; i++)
    {
        identity_string[i] = 'a' + (rand() % 26);
    }
    identity_string[IDENTITY_LENGTH] = '\0';
}

char *get_adjective_from_identity(const char *identity_string)
{
    unsigned char hash[SHA256_DIGEST_LENGTH * 2];
    compute_sha256(identity_string, hash);
    int index = hash[0] % NUM_ADJECTIVES;
    return pirate_adjectives[index];
}

// Function to get a noun from the identity string
char *get_noun_from_identity(const char *identity_string)
{
    unsigned char hash[SHA256_DIGEST_LENGTH * 2];
    compute_sha256(identity_string, hash);
    int index = hash[1] % NUM_NOUNS;
    return pirate_nouns[index];
}
