#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <openssl/sha.h>
#include <openssl/evp.h>
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
    unsigned char hash[EVP_MAX_MD_SIZE];
    unsigned int lengthOfHash = 0;
    EVP_MD_CTX *mdctx;

    // Create and initialize the context
    if ((mdctx = EVP_MD_CTX_new()) == NULL)
    {
        // Handle error: Set a generic error message and return
        strcpy(outputBuffer, "error");
        return;
    }

    // Initialize the Digest operation
    if (1 != EVP_DigestInit_ex(mdctx, EVP_sha256(), NULL) ||
        1 != EVP_DigestUpdate(mdctx, str, strlen(str)) ||
        1 != EVP_DigestFinal_ex(mdctx, hash, &lengthOfHash))
    {
        // Handle error: Set a generic error message and return
        strcpy(outputBuffer, "error");
        EVP_MD_CTX_free(mdctx);
        return;
    }

    // Clean up
    EVP_MD_CTX_free(mdctx);

    // Convert the binary hash to a hexadecimal string
    for (unsigned int i = 0; i < lengthOfHash; i++)
    {
        sprintf(outputBuffer + (i * 2), "%02x", hash[i]);
    }

    outputBuffer[lengthOfHash * 2] = '\0'; // Null-terminate the string
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
