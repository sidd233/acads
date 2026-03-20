%{
#include "parser.tab.h"
#include <string.h>
%}

%%
[0-9]+      { yylval.num = atoi(yytext); return NUMBER; }
[a-zA-Z]+   { yylval.id = strdup(yytext); return ID; }

"+"         { return '+'; }
"-"         { return '-'; }
"*"         { return '*'; }
"/"         { return '/'; }
"("         { return '('; }
")"         { return ')'; }

[ \t]       ;
\n          { return '\n'; }

.           { return yytext[0]; }
%%

int yywrap() { return 1; }
