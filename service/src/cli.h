// cli.h
#ifndef CLI_H
#define CLI_H
#include "session.h"
#include <stdlib.h>

int interact_cli(session_t *session);
int change_directory(char *path, session_t *session);
void cat_file(char *filename, session_t *session);
void help();
void identity(session_t *session);
void safe_snprintf(char *dest, size_t dest_size, const char *format, ...);

#endif // CLI_H
