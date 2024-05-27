# enowars8-service-piratesay

### Testing out the service

1. Clone the repo and run docker compose up for the both service and checker (use the local compose for the checker)
2. Run service/src/generate_content.py to get a clean start
3. Run the checker, put in a flag and check that it is "gettable". Maybe also check that the exploit works for good measure
   1. `enochecker_cli -A http://localhost:5008/ -a piratesay -f ENOFLAGENOFLAG=12345 putflag`
   2. `enochecker_cli -A http://localhost:5008/ -a piratesay -f ENOFLAGENOFLAG=12345 getflag`
   3. `enochecker_cli -A http://localhost:5008/ -a piratesay -f ENOFLAGENOFLAG=12345 --flag_regex ENOFLAGENOFLAG=.+ exploit`
4. Connect to the service with `telnet localhost 4444` and start hunting for the exploit ;)
5. For the solution and more detailed info about the application, look at the readme in the documentation folder

### TODO

- [x] Change name of service and commands in command line. This will also somewhat help even out between beginners and advanced players, novel for both.
- [x] Fill with a lot of dummy content. Make sure it is obvious what is related and unrelated to the actual flags.

  - [x] (Should players be able to create fake entries themself?)

- [ ] Implement protected folders from which opening files is not possible. Determine best vuln to implement here (overwrite is_admin thing vs explore race conditions requiring multiple connections vs combining elements from both approaches).
- [x] Implement the checker
- [x] Remove chdir to prevent issues with threads
- [ ] Fix setup the way the slides from the lectures wanted (documention folder, docker compose up should work automatically, .yml file for some CI/CD stuff)
- [ ] Test a whole bunch to make sure there aren't unwanted exploits. Questions so far:

  - [x] How to prevent %n exploit that can change the actual password for the first exploit. This might be bad if it inferes and ruins the experience for the other groups as they can then no longer use the intended exploit.
  - [x] How to prevent arbitrary code execution if the attacker can write an address to the stack and store values in it (Solution: Assuming solved since %n isn't allowed now)
  - [ ] How to solve the potential is_admin problem for the checker. How would it verify itself? (random credentials each round that are cryptographically safe?)
  - [ ] General removel of all warnings and mis-matching of buffer sizes etc. Just use PATH_MAX for everything basically?
  - [x] Implement locks to prevent race conditions and find out how to deal with a potential issue: User 1 is typing in password to open a file while user 2 is changing dir.
    - [ ] NB: Need to test more if concurrent reads can cause issues. Just implement another mutex if that's the case!

### For fun if time

Have a custom pirate tag for each client that joins (pull from a list of 100-ish)
