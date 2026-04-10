%{
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "y.tab.h"

int yyline = 1;
%}

%option noyywrap

%%

"@ARTICLE"          { return ARTICLE_KW; }
"@BOOK"             { return BOOK_KW; }
"@INPROCEEDINGS"    { return INPROCEEDINGS_KW; }

"author"            { return AUTHOR_KW; }
"title"             { return TITLE_KW; }
"journal"           { return JOURNAL_KW; }
"year"              { return YEAR_KW; }
"pages"             { return PAGES_KW; }
"page"              { return PAGES_KW; }
"volume"            { return VOLUME_KW; }
"publisher"         { return PUBLISHER_KW; }
"editor"            { return EDITOR_KW; }
"series"            { return SERIES_KW; }

"article"           { return ARTICLE_ID; }
"book"              { return BOOK_ID; }
"inproceedings"     { return INPROC_ID; }

"full"              { yylval.str = strdup(yytext); return REFTEXT; }
"minimal"           { yylval.str = strdup(yytext); return REFTEXT; }
"crossref"          { yylval.str = strdup(yytext); return REFTEXT; }

"{"                 { return LBRACE; }
"}"                 { return RBRACE; }
"="                 { return EQUALS; }
","                 { return COMMA; }
"-"                 { return DASH; }

[0-9]+              { yylval.str = strdup(yytext); return DIGIT; }
[a-zA-Z]+           { yylval.str = strdup(yytext); return TEXT; }

\n                  { yyline++; }
[ \t\r]+            { }

.                   {
    fprintf(stderr, "Lexical error at line %d: unexpected character '%c'\n",
            yyline, yytext[0]);
    exit(1);
}

%%
