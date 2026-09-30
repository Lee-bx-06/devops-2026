CC ?= cc
CFLAGS ?= -O0 -DMODE=7
SOURCES = main.c

all: app

app: main.o
	$(CC) $(CFLAGS) -o $@ main.o

# Deliberately still omits feature.h.
main.o: $(SOURCES) config.h
	$(CC) $(CFLAGS) -c main.c -o main.o

clean:
	rm -f app main.o

.PHONY: all clean
