CC ?= cc
CFLAGS ?= -O0
SOURCES = main.c

all: app

app: main.o
	$(CC) $(CFLAGS) -o $@ main.o

# C1 deliberately adds a real include without updating this declaration.
main.o: $(SOURCES) config.h
	$(CC) $(CFLAGS) -c main.c -o main.o

clean:
	rm -f app main.o

.PHONY: all clean
