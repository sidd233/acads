%{
#include <stdio.h>
int line_no = 1, keyword_count = 0, id_count = 0, num_count = 0, separator_count = 0, operator_count = 0;

#define MAX_SYMBOLS 100
typedef struct {
    char name[50];
    int count;
} SymbolEntry;

SymbolEntry symbol_table[MAX_SYMBOLS];
int symbol_count = 0;

void add_to_symbol_table(char *id) {
    for (int i = 0; i <  symbol_count; i++) {
        if (strcmp(symbol_table[i].name, id) == 0) {
            symbol_table[i].count++;
            return;
        }
    }
    if (symbol_count <  MAX_SYMBOLS) {
        strcpy(symbol_table[symbol_count].name, id);
        symbol_table[symbol_count].count = 1;
        symbol_count++;
    }
}

void print_symbol_table() {
    printf("\nSYMBOL TABLE\n");
    printf("%-10s %s\n", "Identifier", "Occurrences");
    for (int i = 0; i <  symbol_count; i++) {
        printf("%-10s %d\n", symbol_table[i].name, symbol_table[i].count);
    }
}
%}

%x COMMENT

%%
"int"|"if"|"else"|"while"|"return" {
    keyword_count++;
    printf("< KEYWORD , %s >\n", yytext);
}

[a-zA-Z_][a-zA-Z0-9_]* {
    id_count++;
    printf("< ID , %s >\n", yytext);
    add_to_symbol_table(yytext);
}

[0-9]+ {
    num_count++;
    printf("< NUM , %s >\n", yytext);
}

"=="|"!="|"<="|">="|"<"|">" {
    operator_count++;
    printf("< RELOP , %s >\n", yytext);
}

"+"|"-"|"*"|"/"|"=" {
    operator_count++;
    printf("< OP , %s >\n", yytext);
}

";"|","|"("|")"|"{"|"}" {
    separator_count++;
    printf("< SEP , %s >\n", yytext);
}

\n {
    line_no++;
}

[ \t]+ ;

"/*"                    { BEGIN(COMMENT); }
<COMMENT>"*/"           { BEGIN(INITIAL); }
<COMMENT>\n             ;
<COMMENT>.              ;
"//".*                  ;

. {
    printf("< INVALID , %s > at line %d\n", yytext, line_no);
}
%%

int main() {
    yylex();
    printf("Number of keywords = %d\nNumber of identifiers = %d\nNumber of numbers = %d\nNumber of operators = %d\nNumber of separators = %d\n",
            keyword_count, id_count, num_count, operator_count, separator_count);
    print_symbol_table();
    return 0;
}
