// session.h
#ifndef SESSION_H
#define SESSION_H

#include <limits.h> // For PATH_MAX

typedef struct
{
    int sock;
    char full_dir[PATH_MAX];
    char root_dir[PATH_MAX];
    char local_dir[PATH_MAX];
    char buffer[PATH_MAX];
    int is_authenticated;
} session_t;

#endif // SESSION_H
