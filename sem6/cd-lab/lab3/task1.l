%{
#include <stdio.h>
int kw = 0, id = 0, op = 0, con = 0;
%}

%%
"int"|"float"|"double"|"char"|"if"|"else"|"while"|"for"|"return"   { kw++; }
[a-zA-Z_][a-zA-Z0-9_]*                                            { id++; }
[0-9]+                                                            { con++; }
"+"|"-"|"*"|"/"|"="|"=="|"<"|">"|"<="|">="                       { op++; }
[ \t\n]+                                                         ;
.                                                                ;
%%

int yywrap() { return 1; }

int main() {
    yylex();
    printf("Keywords   : %d\n", kw);
    printf("Identifiers: %d\n", id);
    printf("Operators  : %d\n", op);
    printf("Constants  : %d\n", con);
    return 0;
}
