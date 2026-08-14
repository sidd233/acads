%{
#include <stdlib.h>
#include <string.h>
#include "ast.h"
#include "parser.tab.h"

int yycolumn = 1;
#define YY_USER_ACTION yylloc.first_line = yylloc.last_line = yylineno;
%}

%option noyywrap yylineno

DIGIT       [0-9]
LETTER      [a-zA-Z_]
HEXD        [0-9a-fA-F]

%%

"//".*                                 { /* line comment (also stripped by gcc -E, kept for direct runs) */ }
"/*"([^*]|\*+[^*/])*\*+"/"             { /* block comment */ }

^"#".*\n                               { /* gcc -E linemarkers, e.g. # 1 "file.c" */ }

"if"                                   { return IF; }
"else"                                 { return ELSE; }
"while"                                { return WHILE; }
"do"                                   { return DO; }
"for"                                  { return FOR; }
"switch"                               { return SWITCH; }
"case"                                 { return CASE; }
"default"                              { return DEFAULT; }
"break"                                { return BREAK; }
"continue"                             { return CONTINUE; }
"return"                               { return RETURN; }
"goto"                                 { return GOTO; }
"int"                                  { return INT_KW; }
"char"                                 { return CHAR_KW; }
"float"                                { return FLOAT_KW; }
"double"                               { return DOUBLE_KW; }
"void"                                 { return VOID_KW; }
"long"                                 { return LONG_KW; }
"short"                                { return SHORT_KW; }
"unsigned"                             { return UNSIGNED_KW; }
"signed"                               { return SIGNED_KW; }
"const"                                { return CONST_KW; }
"static"                               { return STATIC_KW; }
"struct"                               { return STRUCT_KW; }

{LETTER}({LETTER}|{DIGIT})*            { yylval.str = strdup(yytext); return IDENTIFIER; }

0[xX]{HEXD}+[uUlL]*                    { yylval.str = strdup(yytext); return CONSTANT; }
{DIGIT}+\.{DIGIT}+([eE][+-]?{DIGIT}+)? { yylval.str = strdup(yytext); return CONSTANT; }
{DIGIT}+[uUlL]*                        { yylval.str = strdup(yytext); return CONSTANT; }
'(\\.|[^'\\])'                         { yylval.str = strdup(yytext); return CONSTANT; }
\"(\\.|[^"\\])*\"                      { yylval.str = strdup(yytext); return STRING_LIT; }

"->"                                   { yylval.str = strdup(yytext); return ARROW; }
"++"                                   { yylval.str = strdup(yytext); return INC_OP; }
"--"                                   { yylval.str = strdup(yytext); return DEC_OP; }
"<<="                                  { yylval.str = strdup(yytext); return LEFT_ASSIGN; }
">>="                                  { yylval.str = strdup(yytext); return RIGHT_ASSIGN; }
"<<"                                   { yylval.str = strdup(yytext); return LEFT_OP; }
">>"                                   { yylval.str = strdup(yytext); return RIGHT_OP; }
"<="                                   { yylval.str = strdup(yytext); return LE_OP; }
">="                                   { yylval.str = strdup(yytext); return GE_OP; }
"=="                                   { yylval.str = strdup(yytext); return EQ_OP; }
"!="                                   { yylval.str = strdup(yytext); return NE_OP; }
"&&"                                   { yylval.str = strdup(yytext); return AND_OP; }
"||"                                   { yylval.str = strdup(yytext); return OR_OP; }
"*="                                   { yylval.str = strdup(yytext); return MUL_ASSIGN; }
"/="                                   { yylval.str = strdup(yytext); return DIV_ASSIGN; }
"%="                                   { yylval.str = strdup(yytext); return MOD_ASSIGN; }
"+="                                   { yylval.str = strdup(yytext); return ADD_ASSIGN; }
"-="                                   { yylval.str = strdup(yytext); return SUB_ASSIGN; }
"&="                                   { yylval.str = strdup(yytext); return AND_ASSIGN; }
"^="                                   { yylval.str = strdup(yytext); return XOR_ASSIGN; }
"|="                                   { yylval.str = strdup(yytext); return OR_ASSIGN; }

[-+*/%=<>!&|^~?:;{}(),.\[\]]           { return yytext[0]; }

[ \t\v\f\r]+                           { /* whitespace */ }
\n                                     { /* newline, yylineno auto-incremented */ }

.                                      { fprintf(stderr, "lexer: unexpected char '%s' at line %d\n", yytext, yylineno); }

%%
