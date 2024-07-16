// session.h
#ifndef SESSION_H
#define SESSION_H

#include <limits.h> // For PATH_MAX

char *get_adjective_from_identity(const char *identity_string);
char *get_noun_from_identity(const char *identity_string);
void generate_random_identity(char *identity_string);
void compute_sha256(const char *str, unsigned char *outputBuffer);
void slcgrand(unsigned int s);
int lcgrand();

typedef struct
{
    int sock;
    char full_dir[PATH_MAX];
    char root_dir[PATH_MAX];
    char local_dir[PATH_MAX];
    char buffer[PATH_MAX];
    char pirate_identity[65];
    char pirate_adjective[20];
    char pirate_noun[20];
} session_t;

#endif // SESSION_H
