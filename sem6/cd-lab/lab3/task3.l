%{
#include <stdio.h>
%}

%x COMMENT

%%

"/*"                    { BEGIN(COMMENT); }
<COMMENT>"*/"           { BEGIN(INITIAL); }
<COMMENT>\n             ;
<COMMENT>.              ; /* Ignore characters inside multi-line comments */
"//".*                  ; /* Ignore single-line comments */
\"(\\.|[^"\\])*\"       { printf("%s", yytext); } /* Preserve string literals */
\'(\\.|[^'\\])*\'       { printf("%s", yytext); } /* Preserve character literals */
.                       { printf("%s", yytext); }
\n                      { printf("\n"); }

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
    
    yylex();
    
    if (argc > 1) {
        fclose(yyin);
    }
    
    return 0;
}