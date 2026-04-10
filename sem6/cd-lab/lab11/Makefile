CC     = gcc
FLEX   = flex
YACC   = yacc

all: bibtex_parser

bibtex_parser: lex.yy.c y.tab.c y.tab.h
	$(CC) -o bibtex_parser lex.yy.c y.tab.c

y.tab.c y.tab.h: bibtex.y
	$(YACC) -d bibtex.y

lex.yy.c: bibtex.l y.tab.h
	$(FLEX) bibtex.l

run: bibtex_parser
	./bibtex_parser sample.bib

clean:
	rm -f lex.yy.c y.tab.c y.tab.h bibtex_parser
