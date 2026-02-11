%{
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

int keyword_count = 0;
int identifier_count = 0;
int operator_count = 0;
int constant_count = 0;

/* Symbol table structure */
#define MAX_SYMBOLS 100
typedef struct {
    char name[50];
    int count;
} SymbolEntry;

SymbolEntry symbol_table[MAX_SYMBOLS];
int symbol_count = 0;

/* Function to add identifier to symbol table */
void add_to_symbol_table(char *id) {
    for (int i = 0; i < symbol_count; i++) {
        if (strcmp(symbol_table[i].name, id) == 0) {
            symbol_table[i].count++;
            return;
        }
    }
    if (symbol_count < MAX_SYMBOLS) {
        strcpy(symbol_table[symbol_count].name, id);
        symbol_table[symbol_count].count = 1;
        symbol_count++;
    }
}

/* Function to print symbol table */
void print_symbol_table() {
    printf("\n========== SYMBOL TABLE ==========\n");
    printf("%-20s %s\n", "Identifier", "Occurrences");
    printf("----------------------------------\n");
    for (int i = 0; i < symbol_count; i++) {
        printf("%-20s %d\n", symbol_table[i].name, symbol_table[i].count);
    }
    printf("==================================\n");
}
%}

/* Regular definitions */
delim       [ \t\n]
ws          {delim}+
letter      [a-zA-Z_]
digit       [0-9]
identifier  {letter}({letter}|{digit})*
constant    {digit}+

%%

{ws}                            ;
"auto"                          { keyword_count++; printf("<KEYWORD, %s>\n", yytext); }
"break"                         { keyword_count++; printf("<KEYWORD, %s>\n", yytext); }
"case"                          { keyword_count++; printf("<KEYWORD, %s>\n", yytext); }
"char"                          { keyword_count++; printf("<KEYWORD, %s>\n", yytext); }
"const"                         { keyword_count++; printf("<KEYWORD, %s>\n", yytext); }
"continue"                      { keyword_count++; printf("<KEYWORD, %s>\n", yytext); }
"default"                       { keyword_count++; printf("<KEYWORD, %s>\n", yytext); }
"do"                            { keyword_count++; printf("<KEYWORD, %s>\n", yytext); }
"double"                        { keyword_count++; printf("<KEYWORD, %s>\n", yytext); }
"else"                          { keyword_count++; printf("<KEYWORD, %s>\n", yytext); }
"enum"                          { keyword_count++; printf("<KEYWORD, %s>\n", yytext); }
"extern"                        { keyword_count++; printf("<KEYWORD, %s>\n", yytext); }
"float"                         { keyword_count++; printf("<KEYWORD, %s>\n", yytext); }
"for"                           { keyword_count++; printf("<KEYWORD, %s>\n", yytext); }
"goto"                          { keyword_count++; printf("<KEYWORD, %s>\n", yytext); }
"if"                            { keyword_count++; printf("<KEYWORD, %s>\n", yytext); }
"int"                           { keyword_count++; printf("<KEYWORD, %s>\n", yytext); }
"long"                          { keyword_count++; printf("<KEYWORD, %s>\n", yytext); }
"register"                      { keyword_count++; printf("<KEYWORD, %s>\n", yytext); }
"return"                        { keyword_count++; printf("<KEYWORD, %s>\n", yytext); }
"short"                         { keyword_count++; printf("<KEYWORD, %s>\n", yytext); }
"signed"                        { keyword_count++; printf("<KEYWORD, %s>\n", yytext); }
"sizeof"                        { keyword_count++; printf("<KEYWORD, %s>\n", yytext); }
"static"                        { keyword_count++; printf("<KEYWORD, %s>\n", yytext); }
"struct"                        { keyword_count++; printf("<KEYWORD, %s>\n", yytext); }
"switch"                        { keyword_count++; printf("<KEYWORD, %s>\n", yytext); }
"typedef"                       { keyword_count++; printf("<KEYWORD, %s>\n", yytext); }
"union"                         { keyword_count++; printf("<KEYWORD, %s>\n", yytext); }
"unsigned"                      { keyword_count++; printf("<KEYWORD, %s>\n", yytext); }
"void"                          { keyword_count++; printf("<KEYWORD, %s>\n", yytext); }
"volatile"                      { keyword_count++; printf("<KEYWORD, %s>\n", yytext); }
"while"                         { keyword_count++; printf("<KEYWORD, %s>\n", yytext); }
"+"                             { operator_count++; printf("<OPERATOR, %s>\n", yytext); }
"-"                             { operator_count++; printf("<OPERATOR, %s>\n", yytext); }
"*"                             { operator_count++; printf("<OPERATOR, %s>\n", yytext); }
"/"                             { operator_count++; printf("<OPERATOR, %s>\n", yytext); }
"%"                             { operator_count++; printf("<OPERATOR, %s>\n", yytext); }
"++"                            { operator_count++; printf("<OPERATOR, %s>\n", yytext); }
"--"                            { operator_count++; printf("<OPERATOR, %s>\n", yytext); }
"=="                            { operator_count++; printf("<OPERATOR, %s>\n", yytext); }
"!="                            { operator_count++; printf("<OPERATOR, %s>\n", yytext); }
"<"                             { operator_count++; printf("<OPERATOR, %s>\n", yytext); }
">"                             { operator_count++; printf("<OPERATOR, %s>\n", yytext); }
"<="                            { operator_count++; printf("<OPERATOR, %s>\n", yytext); }
">="                            { operator_count++; printf("<OPERATOR, %s>\n", yytext); }
"&&"                            { operator_count++; printf("<OPERATOR, %s>\n", yytext); }
"||"                            { operator_count++; printf("<OPERATOR, %s>\n", yytext); }
"!"                             { operator_count++; printf("<OPERATOR, %s>\n", yytext); }
"&"                             { operator_count++; printf("<OPERATOR, %s>\n", yytext); }
"|"                             { operator_count++; printf("<OPERATOR, %s>\n", yytext); }
"^"                             { operator_count++; printf("<OPERATOR, %s>\n", yytext); }
"~"                             { operator_count++; printf("<OPERATOR, %s>\n", yytext); }
"<<"                            { operator_count++; printf("<OPERATOR, %s>\n", yytext); }
">>"                            { operator_count++; printf("<OPERATOR, %s>\n", yytext); }
"="                             { operator_count++; printf("<OPERATOR, %s>\n", yytext); }
"+="                            { operator_count++; printf("<OPERATOR, %s>\n", yytext); }
"-="                            { operator_count++; printf("<OPERATOR, %s>\n", yytext); }
"*="                            { operator_count++; printf("<OPERATOR, %s>\n", yytext); }
"/="                            { operator_count++; printf("<OPERATOR, %s>\n", yytext); }
"%="                            { operator_count++; printf("<OPERATOR, %s>\n", yytext); }
"&="                            { operator_count++; printf("<OPERATOR, %s>\n", yytext); }
"|="                            { operator_count++; printf("<OPERATOR, %s>\n", yytext); }
"^="                            { operator_count++; printf("<OPERATOR, %s>\n", yytext); }
"<<="                           { operator_count++; printf("<OPERATOR, %s>\n", yytext); }
">>="                           { operator_count++; printf("<OPERATOR, %s>\n", yytext); }
"?"                             { operator_count++; printf("<OPERATOR, %s>\n", yytext); }
":"                             { operator_count++; printf("<OPERATOR, %s>\n", yytext); }

{identifier}                    { 
                                  identifier_count++; 
                                  printf("<IDENTIFIER, %s>\n", yytext);
                                  add_to_symbol_table(yytext);
                                }
{constant}                      { constant_count++; printf("<CONSTANT, %s>\n", yytext); }
.                               { printf("<SPECIAL, %s>\n", yytext); }

%%

int yywrap() {
    return 1;
}

int main(int argc, char **argv) {
    if (argc > 1) {
        FILE *fp = fopen(argv[1], "r");
        if (!fp) {
            perror(argv[1]);
            return 1;
        }
        yyin = fp;
    }
    
    printf("========== TOKEN STREAM ==========\n");
    yylex();
    
    printf("\n========== TOKEN COUNTS ==========\n");
    printf("Number of keywords    = %d\n", keyword_count);
    printf("Number of identifiers = %d\n", identifier_count);
    printf("Number of operators   = %d\n", operator_count);
    printf("Number of constants   = %d\n", constant_count);
    
    print_symbol_table();
    
    if (argc > 1) {
        fclose(yyin);
    }
    
    return 0;
}