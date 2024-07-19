CC=gcc
LDFLAGS=-lssl -lcrypto
DEPS = server.h cli.h session.h
OBJ = server.o cli.o session.o

%.o: %.c $(DEPS)
	$(CC) -c -o $@ $<

piratesay: $(OBJ)
	$(CC) -o $@ $^ $(LDFLAGS)

clean:
	rm -f *.o piratesay
