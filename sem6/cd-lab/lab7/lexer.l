%{
#include "parser.tab.h"
%}

%%

[0-9]+ { return NUMBER; }

"+"    { return '+'; }
"-"    { return '-'; }
"*"    { return '*'; }
"/"    { return '/'; }

"("    { return '('; }
")"    { return ')'; }

\n     { return '\n'; }

[ \t]  ;

. { return yytext[0]; }

%%

int yywrap()
{
    return 1;
}