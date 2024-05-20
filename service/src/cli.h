// cli.h
#ifndef CLI_H
#define CLI_H
#include "session.h"

int interact_cli(session_t *session);
int change_directory(char *path, session_t *session);
void cat_file(char *filename, session_t *session);
void help();

#endif // CLI_H
