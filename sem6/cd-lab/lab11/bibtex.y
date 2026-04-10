%{
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

int yylex(void);
void yyerror(const char *s);
extern int yyline;

FILE *outfile;
%}

%union {
    char *str;
}

%token ARTICLE_KW BOOK_KW INPROCEEDINGS_KW
%token AUTHOR_KW TITLE_KW JOURNAL_KW YEAR_KW PAGES_KW
%token VOLUME_KW PUBLISHER_KW EDITOR_KW SERIES_KW
%token ARTICLE_ID BOOK_ID INPROC_ID
%token LBRACE RBRACE EQUALS COMMA DASH

%token <str> REFTEXT TEXT DIGIT

%type <str> reftext_val text_val alphanumeric_val

%%

program
    : entry_list
    ;

entry_list
    : entry_list entry
    | entry
    ;

entry
    : article_entry
    | book_entry
    | inproc_entry
    ;

article_entry
    : ARTICLE_KW LBRACE ARTICLE_ID DASH reftext_val COMMA
      {
          fprintf(outfile, "\n<ARTICLE>\n");
          fprintf(outfile, "<article>%s</article>\n", $5);
          free($5);
      }
      article_fields RBRACE
      {
          fprintf(outfile, "</ARTICLE>\n");
      }
    ;

article_fields
    : /* empty */
    | article_fields article_field COMMA
    ;

article_field
    : AUTHOR_KW EQUALS LBRACE text_val RBRACE
      { fprintf(outfile, "<author>%s</author>\n", $4); free($4); }
    | TITLE_KW EQUALS LBRACE alphanumeric_val RBRACE
      { fprintf(outfile, "<title>%s</title>\n", $4); free($4); }
    | JOURNAL_KW EQUALS LBRACE text_val RBRACE
      { fprintf(outfile, "<journal>%s</journal>\n", $4); free($4); }
    | YEAR_KW EQUALS DIGIT
      { fprintf(outfile, "<year>%s</year>\n", $3); free($3); }
    | PAGES_KW EQUALS DIGIT
      { fprintf(outfile, "<page>%s</page>\n", $3); free($3); }
    ;

book_entry
    : BOOK_KW LBRACE BOOK_ID DASH reftext_val COMMA
      {
          fprintf(outfile, "\n<BOOK>\n");
          fprintf(outfile, "<book>%s</book>\n", $5);
          free($5);
      }
      book_fields RBRACE
      {
          fprintf(outfile, "</BOOK>\n");
      }
    ;

book_fields
    : /* empty */
    | book_fields book_field COMMA
    ;

book_field
    : AUTHOR_KW EQUALS LBRACE text_val RBRACE
      { fprintf(outfile, "<author>%s</author>\n", $4); free($4); }
    | TITLE_KW EQUALS LBRACE alphanumeric_val RBRACE
      { fprintf(outfile, "<title>%s</title>\n", $4); free($4); }
    | VOLUME_KW EQUALS DIGIT
      { fprintf(outfile, "<volume>%s</volume>\n", $3); free($3); }
    | PUBLISHER_KW EQUALS LBRACE alphanumeric_val RBRACE
      { fprintf(outfile, "<publisher>%s</publisher>\n", $4); free($4); }
    ;

inproc_entry
    : INPROCEEDINGS_KW LBRACE INPROC_ID DASH reftext_val COMMA
      {
          fprintf(outfile, "\n<INPROCEEDINGS>\n");
          fprintf(outfile, "<inproceedings>%s</inproceedings>\n", $5);
          free($5);
      }
      inproc_fields RBRACE
      {
          fprintf(outfile, "</INPROCEEDINGS>\n");
      }
    ;

inproc_fields
    : /* empty */
    | inproc_fields inproc_field COMMA
    ;

inproc_field
    : AUTHOR_KW EQUALS LBRACE text_val RBRACE
      { fprintf(outfile, "<author>%s</author>\n", $4); free($4); }
    | TITLE_KW EQUALS LBRACE alphanumeric_val RBRACE
      { fprintf(outfile, "<title>%s</title>\n", $4); free($4); }
    | EDITOR_KW EQUALS LBRACE text_val RBRACE
      { fprintf(outfile, "<editor>%s</editor>\n", $4); free($4); }
    | SERIES_KW EQUALS LBRACE alphanumeric_val RBRACE
      { fprintf(outfile, "<series>%s</series>\n", $4); free($4); }
    | YEAR_KW EQUALS DIGIT
      { fprintf(outfile, "<year>%s</year>\n", $3); free($3); }
    | PUBLISHER_KW EQUALS LBRACE alphanumeric_val RBRACE
      { fprintf(outfile, "<publisher>%s</publisher>\n", $4); free($4); }
    ;

reftext_val
    : REFTEXT    { $$ = $1; }
    | JOURNAL_KW { $$ = strdup("journal"); }
    | TEXT       { $$ = $1; }
    ;

text_val
    : TEXT
      { $$ = $1; }
    | text_val TEXT
      {
          int len = strlen($1) + strlen($2) + 2;
          $$ = malloc(len);
          sprintf($$, "%s %s", $1, $2);
          free($1); free($2);
      }
    ;

alphanumeric_val
    : TEXT
      { $$ = $1; }
    | DIGIT
      { $$ = $1; }
    | alphanumeric_val TEXT
      {
          int len = strlen($1) + strlen($2) + 2;
          $$ = malloc(len);
          sprintf($$, "%s %s", $1, $2);
          free($1); free($2);
      }
    | alphanumeric_val DIGIT
      {
          int len = strlen($1) + strlen($2) + 2;
          $$ = malloc(len);
          sprintf($$, "%s %s", $1, $2);
          free($1); free($2);
      }
    ;

%%

void yyerror(const char *s) {
    fprintf(stderr, "Syntax error at line %d: %s\n", yyline, s);
    exit(1);
}

int main(int argc, char *argv[]) {
    extern FILE *yyin;
    char outname[512];
    char *dot;

    if (argc < 2) {
        fprintf(stderr, "Usage: %s <input.bib>\n", argv[0]);
        return 1;
    }

    yyin = fopen(argv[1], "r");
    if (!yyin) { perror(argv[1]); return 1; }

    strncpy(outname, argv[1], sizeof(outname) - 5);
    outname[sizeof(outname) - 5] = '\0';
    dot = strrchr(outname, '.');
    if (dot) *dot = '\0';
    strcat(outname, ".xml");

    outfile = fopen(outname, "w");
    if (!outfile) { perror(outname); fclose(yyin); return 1; }

    fprintf(outfile, "<document>\n");
    yyparse();
    fprintf(outfile, "\n</document>\n");

    fclose(yyin);
    fclose(outfile);
    return 0;
}
