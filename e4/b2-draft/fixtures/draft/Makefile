CC ?= cc
CFLAGS ?= -O2 -Wall -Wextra -Werror
TARGET := hello

.PHONY: all clean test

all: $(TARGET)

$(TARGET): main.c
	$(CC) $(CFLAGS) main.c -o $@

clean:
	rm -f $(TARGET)

test: $(TARGET)
	@test "$$($(CURDIR)/$(TARGET))" = "hello E3"
	@printf '%s\n' 'hello E3'
