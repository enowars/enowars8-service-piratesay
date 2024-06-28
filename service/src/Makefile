CC=gcc
CFLAGS=-g -pthread -fno-stack-protector
LDFLAGS=-lssl -lcrypto
DEPS = server.h cli.h session.h
OBJ = server.o cli.o session.o

%.o: %.c $(DEPS)
	$(CC) -c -o $@ $< $(CFLAGS)

piratesay: $(OBJ)
	$(CC) -o $@ $^ $(CFLAGS) $(LDFLAGS)

clean:
	rm -f *.o piratesay
