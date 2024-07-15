#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <openssl/sha.h>
#include <openssl/evp.h>
#include <time.h>

#define IDENTITY_LENGTH 64
#define NUM_ADJECTIVES 100
#define NUM_NOUNS 100

char *pirate_adjectives[NUM_ADJECTIVES] = {
    "Red", "Black", "Silver", "Golden", "Scarlet", "Dark", "White", "Blue", "Rogue", "Stormy",
    "Fearsome", "Mighty", "Brave", "Savage", "Fiery", "Cunning", "Bold", "Fierce", "Grim", "Vengeful",
    "Merciless", "Wild", "Daring", "Stealthy", "Ferocious", "Deadly", "Bloodthirsty", "Cruel", "Relentless", "Treacherous",
    "Wrathful", "Ruthless", "Sinister", "Ghostly", "Iron", "Steel", "Thunderous", "Shadowy", "Mysterious", "Menacing",
    "Dauntless", "Unyielding", "Reckless", "Savvy", "Fearless", "Intrepid", "Grizzled", "Vigilant", "Crafty", "Sly",
    "Swift", "Dreadful", "Gallant", "Heroic", "Legendary", "Wicked", "Terrorizing", "Formidable", "Chaotic", "Brutal",
    "Perilous", "Noble", "Valiant", "Infernal", "Monstrous", "Raging", "Vicious", "Sinful", "Boldhearted", "Ferocious",
    "Indomitable", "Savage", "Dreaded", "Fabled", "Majestic", "Unstoppable", "Ancient", "Stalwart", "Mythic", "Untamed",
    "Mystic", "Prowling", "Doomed", "Forgotten", "Seafaring", "Wandering", "Shadow", "Deepsea", "Stormborn", "Windrider",
    "Tidal", "Maelstrom", "Typhoon", "Tempest", "Harpooner", "Corsair", "Buccaneer", "Seawolf", "SeaSerpent", "Kraken"};

char *pirate_nouns[NUM_NOUNS] = {
    "Beard", "Jack", "Bart", "Pete", "Anne", "Patty", "John", "Hook", "Bill", "Bonny",
    "Morgan", "Davy", "Blackbeard", "Silver", "LongJohn", "Calico", "Rackham", "Teach", "Drake", "Roberts",
    "Lafitte", "Vane", "Flint", "Kidd", "Bartholomew", "Edward", "Mary", "Jane", "Blood", "Cannon",
    "Cutlass", "Sparrow", "Corsair", "Marooner", "SeaDog", "Scallywag", "Buccaneer", "SeaWolf", "Privateer", "Matey",
    "Swashbuckler", "Skull", "Crossbones", "Treasure", "Galleon", "Parrot", "Pistol", "Rum", "Sloop", "Brig",
    "PirateKing", "Siren", "Corsair", "JollyRoger", "Bounty", "Scourge", "SeaSerpent", "Kraken", "Marauder", "Plunder",
    "Loot", "Booty", "BountyHunter", "Mutineer", "Captain", "Quartermaster", "Gunner", "Boatswain", "Lookout", "Sailor",
    "Navigator", "FirstMate", "Shipwright", "PowderMonkey", "CabinBoy", "Deckhand", "Helmsman", "Longboat", "Cannoneer", "Shipmate",
    "PirateQueen", "SeaRover", "SeaRaider", "SeaCaptain", "Freebooter", "Wench", "Swabber", "Harpooner", "SeaWitch", "Buoy",
    "Gangplank", "Mainmast", "Crowsnest", "Forecastle", "Hold", "Broadside", "Bilge", "Grog", "Anchor", "Tide"};

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
    unsigned int hash = 5381;
    int c;
    while ((c = *identity_string++))
        hash = ((hash << 5) + hash) + c; // hash * 33 + c
    int index = hash % NUM_ADJECTIVES;
    return pirate_adjectives[index];
}

char *get_noun_from_identity(const char *identity_string)
{
    unsigned int hash = 5381;
    int c;
    while ((c = *identity_string++))
        hash = ((hash << 5) + hash) + c;  // hash * 33 + c
    int index = (hash >> 16) % NUM_NOUNS; // Shift to get a different part of the hash
    return pirate_nouns[index];
}
