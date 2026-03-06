%{
#include <stdio.h>
#include <stdlib.h>

int yylex();
int yyerror(const char *s);
%}

%token NUMBER

%%

input:
      | input line
      ;

line:
      expr '\n'  { printf("Parsing successful\n"); }
    | error '\n' { printf("Syntax Error\n"); yyerrok; }
    ;

expr : expr '+' term
     | expr '-' term
     | term
     ;

term : term '*' factor
     | term '/' factor
     | factor
     ;

factor : '(' expr ')'
       | NUMBER
       ;

%%

int main()
{
    yyparse();
    return 0;
}

int yyerror(const char *s)
{
    return 0;
}