CC=gcc
CFLAGS=-g -pthread
DEPS = server.h cli.h session.h
OBJ = server.o main.o cli.o 

%.o: %.c $(DEPS)
	$(CC) -c -o $@ $< $(CFLAGS)

my_server: $(OBJ)
	$(CC) -o $@ $^ $(CFLAGS)