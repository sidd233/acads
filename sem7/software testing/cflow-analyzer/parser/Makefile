CC = gcc
CFLAGS = -Wall -Wno-unused-function -g
TARGET = cflow-analyzer

all: $(TARGET)

parser.tab.c parser.tab.h: parser.y
	bison -d -o parser.tab.c parser.y

lex.yy.c: lexer.l parser.tab.h
	flex -o lex.yy.c lexer.l

$(TARGET): parser.tab.c lex.yy.c ast.c cfg.c main.c
	$(CC) $(CFLAGS) -o $(TARGET) parser.tab.c lex.yy.c ast.c cfg.c main.c

clean:
	rm -f $(TARGET) parser.tab.c parser.tab.h lex.yy.c *.o

.PHONY: all clean
