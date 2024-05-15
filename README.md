# enowars8-service-bookkeeper

TODO

- [ ] Change name of service and commands in command line. This will also somewhat help even out between beginners and advanced players, novel for both.
- [ ] Fill with a lot of dummy content. Make sure it is obvious what is related and unrelated to the actual flags. (Should players be able to create fake entries themself?)
- [ ] Implement protected folders from which opening files is not possible. Determine best vuln to implement here (overwrite is_admin thing vs explore race conditions requiring multiple connections vs combining elements from both approaches).
- [ ] Implement the checker
- [ ] Fix setup the way the slides from the lectures wanted (documention folder, docker compose up should work automatically, .yml file for some CI/CD stuff)
- [ ] Test a whole bunch to make sure there aren't unwanted exploits. Questions so far:

  - [ ] How to prevent %n exploit that can change the actual password for the first exploit. This might be bad if it inferes and ruins the experience for the other groups as they can then no longer use the intended exploit.
  - [ ] How to prevent arbitrary code execution if the attacker can write an address to the stack and store values in it. They know a lot more than me, even if I think something would be safe :(
  - [ ] How to solve the potential is_admin problem for the checker. How would it verify itself? (random credentials each round that are cryptographically safe?)
  - [ ] General removel of all warnings and mis-matching of buffer sizes etc. Just use PATH_MAX for everything basically?

### For fun if time

Have a custom pirate tag for each client that joins (pull from a list of 100-ish)
