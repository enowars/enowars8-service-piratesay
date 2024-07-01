# enowars8-service-piratesay

### Testing out the service

1. Clone the repo and run docker compose up for the both service and checker (use the local compose for the checker)
2. Run service/src/generate_content.py to get a clean start
3. Run the checker, put in a flag and check that it is "gettable". Maybe also check that the exploit works for good measure
   1. `enochecker_cli -A http://localhost:14444/ -a piratesay -f ENOFLAGENOFLAG=12345 putflag`
   2. `enochecker_cli -A http://localhost:14444/ -a piratesay -f ENOFLAGENOFLAG=12345 getflag`
   3. `enochecker_cli -A http://localhost:14444/ -a piratesay -f ENOFLAGENOFLAG=12345 --flag_regex ENOFLAGENOFLAG=.+ exploit`
4. Connect to the service with `telnet localhost 4444` and start hunting for the exploits ;)
5. For the solution and more detailed info about the application, look at the readme in the documentation folder

### TODO

See project board on GitHub
