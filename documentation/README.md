# Pirate Say

Pirate Say is a TCP-server written in C that presents itself as a pirate-themed dark web forum service. The service contains various logs dictating/accounting the achievements of scammers. The service contains the following file types:

- .log files: these are standard log files without any password protection
- .treasure files: these files are protected by a password input that contain a format string vulnerability
- .private files: these files are associated with a specific user. However, there is a weekness in using the server's startup time to seed the random numbers. Combined with the option to change your "identity string" when connected, this allows us to pose as other users.

# Vulnerabilities

## Vulnerability #1 - Parrot echoes password back

- Category: Format string
- Difficulty: Easy/Medium

When trying to access .treasure files, the guarding parrot echoing back your words after each attempt is vulnerable to format string attacks. Each inputed string is sanitized with special code to remove patterns with %n (as multiple writes to the stack might lead to RCE), and also %p, %x and other common format specifiers (to increase the difficulty of the vuln). The lesser used %o is among the few specifiers that aren't sanitized (the only not using floating point numbers), meaning the attempted password "%o" would leak an octal address from the stack.

```
cli.c:482
// Parrot feedback
char feedback[1024];
safe_snprintf(feedback, sizeof(feedback), "%s is wrong, %s is wrong, captain!\n", password_input, password_input);
WRITE_TO_BUFFER(session, feedback);
fclose(file);
return;
```

The `WRITE_TO_BUFFER(session, feedback);` gives us a custom `safe_snprintf`, which is susceptible to format string attacks.

## Vulnerability #2 - Identities are seeded with the startup time

# Exploits

## Vulnerability #1 - Parrot echoes password back

```
cli.c:459
// If this is a .treasure file, ask for a password to open
    if (strstr(filename, ".treasure") != NULL)
    {
        char correct_password[256];
        // read the last line of the file, this is the password
        char line[256];
        while (fgets(line, sizeof(line), file))
        {
            strcpy(correct_password, line);
        }
        WRITE_TO_BUFFER(session, "A parrot is guarding the treasure tightly\n");
        WRITE_TO_BUFFER(session, "Speak your words: ");
        send(session->sock, session->buffer, strlen(session->buffer), 0);
        memset(session->buffer, 0, sizeof(session->buffer));
        int read_size;
        char password_input[256];
        read_size = recv(session->sock, password_input, 256, 0);
        // Null-terminate and remove newline
        password_input[read_size] = '\0';
        trim_whitespace(password_input, sizeof(password_input));
        fflush(stdout);
        if (strncmp(password_input, correct_password, 255) != 0)
```

Looking at the code directly above the "feedback" code, we can see that the file's password is stored within the file itself and already read onto the stack for comparision with the user input.

Using a debugger like GDB or similar tools, we can see that the password is stored with the offset 26 and 27 on the stack (each password from the checker is 16 bytes long). [NOTE: the offset might differ for non-x86 architecture]

The input `%26$lo %27$lo` will therefore give us the password outputed as octals, which we can then convert to ASCII characters.

Step-by-step:

1. `loot x.treasure`
2. `%26$lo %27$lo`
3. Convert the octals to ASCII characters
4. `loot x.treasure`
5. `[ASCII]`
6. File has been accessed

# Patches

## Vulnerability #1 - Parrot echoes password back

```
WRITE_TO_BUFFER(session, feedback);
```

Converting the code above to the one below effectively fixes the issue.

```
WRITE_TO_BUFFER(session, "%s", feedback);
```

When working on binary files, we can use a tool like Ghidra to decompile the source code and see the corresponding updates in the decompiled code as we try to modify the registers in the assembly code.
Essentially, what we need to do is the following:

1. Locate the string "%s" in the source code
2. Make sure the value corresponding to its position is passed into the register that takes the second argument before calling safe_snprintf
3. Make sure feedback is passed into the register carrying the value of the third argument, instead of the second.

This should lead to the parrot replying with the literal string "%26$lo %27$lo" when users try to exploit.
