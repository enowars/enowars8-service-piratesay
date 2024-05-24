#include <time.h>

#define NUM_ADJECTIVES 10
#define NUM_NOUNS 10

char *pirate_adjectives[NUM_ADJECTIVES] = {
    "Red", "Black", "Silver", "Golden", "Scarlet", "Dark", "White", "Blue", "Rogue", "Stormy"};

char *pirate_nouns[NUM_NOUNS] = {
    "Beard", "Jack", "Bart", "Pete", "Anne", "Patty", "John", "Hook", "Bill", "Bonny"};

char *get_random_adjective()
{
    return pirate_adjectives[rand() % NUM_ADJECTIVES];
}

char *get_random_noun()
{
    return pirate_nouns[rand() % NUM_NOUNS];
}