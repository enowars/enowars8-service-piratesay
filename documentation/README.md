# Overview

Pirate Say is a TCP-server written in C that presents itself as a pirate-themed dark web forum service. The service contains various logs stating the achievements of scammers. The service contains the following file types:

- .log files: these are standard log files without any password protection
- .treasure files: these files are protected by a password input that contains a format string vulnerability
- .private files: these files are associated with a specific user. However, there is a weakness in using the server's startup time to seed the random numbers. Combined with the option to change your "identity string" when connected, this allows us to pose as other users.

# Vulnerability #1 - Parrot echoes password back

- Category: Format string
- Difficulty: Easy/Medium, high replayability

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

## Exploit

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

## Patch

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

# Vulnerability #2 - Identities are seeded with the startup time

- Category: Pseudorandom number generator
- Difficulty: Medium, no replayability

A linear congruential generator is used to generate a unique _pirate identity_ for each connecting user, but it is insecure as it is seeded with the startup time of the server. This means it is possible to find the identities belonging to the users used by the checker when it posts the flags. Using the `identity` command, users can switch to these identities and this enables them to open the .private files stored by the checker with the flags.

This exploit is rated as more difficult than the first, as it requires recovering a lot of code from the stripped binary (LCG, generation of identity strings, generation of pirate adjectives and nouns). It is also not replayable.

## Exploit

This vuln requires a certain amount of brute force. Upon connecting to the server, the user is told some information regarding the running version of the service as well as its startup time. If we also run `identity`, we will get the identity string of our newly joined user. Assuming some flags have already been posted, we know that there exist some states of the LCG between the one from the startup time and the one used to generate the newly connected user that was used to generate the identity strings for the checker.

Now, at first it might seem like we need to generate identity strings, connect and try to open the files for all states in between. However, the pirate name of a user is also based on their identity string. Since this is also part of the file name saved by the checker, we can locally filter out just the identities with matching names before we even bother to connect. Since there are 100*100 (adjective * noun) combinations of names, we only have to test 0.01% of the identities, assuming pretty even name distribution.

The complete procedure for exploiting is therefore as follows:

1. Connect a user and get the startup time and their identity.
2. Start generating user identities from the startup time until you get this user's identity.
3. Filter the list, by generating the corresponding names of the identity strings and seeing if they match the .private file
4. Try to connect and open the file with each identity in the remaining list. This can be parallelized with an async call.
5. (Optional) Assuming all checker flags was found between startup time and the connected user, set the seed used to generate that connected user's identity as the new startup time. (Speeds up the process for future runs!)

For a complete code implementation, take a look at bambixploit_exploit2.py

## Patch

Given the duration of the CTF, a very simple patch is to hard code a number to seed the LCG instead of using the service's startup time. Without a known starting seed, we can't limit our search space to be between this seed and the newest user.

That being said, using an LCG like this is inherently unsafe and should not be used for cryptographic purposes. The best long-term solution would be to substitute the LCG with a cryptographically secure number generator, but such a substitution might prove difficult and tedious when only working on the binaries and is therefore not the intended patch.
