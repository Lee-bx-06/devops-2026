CC ?= cc
CFLAGS ?= -O0

all: app

app: main.o
	$(CC) $(CFLAGS) -o $@ main.o

# Deliberate oracle defects: config.h is used but omitted; unused.h is declared but unused.
main.o: main.c unused.h
	$(CC) $(CFLAGS) -c main.c -o main.o

clean:
	rm -f app main.o

.PHONY: all clean
