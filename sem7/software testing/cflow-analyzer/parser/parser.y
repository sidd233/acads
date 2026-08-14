%{
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>
#include "ast.h"

int yylex(void);
void yyerror(const char *s);
extern int yylineno;

static char *strf(const char *fmt, ...) {
    va_list ap, ap2;
    va_start(ap, fmt);
    va_copy(ap2, ap);
    int n = vsnprintf(NULL, 0, fmt, ap);
    va_end(ap);
    char *buf = malloc(n + 1);
    vsnprintf(buf, n + 1, fmt, ap2);
    va_end(ap2);
    return buf;
}
%}

%locations

%union {
    char *str;
    struct Stmt *stmt;
    struct StmtList *stmtlist;
    struct Param *param;
}

%token IF ELSE WHILE DO FOR SWITCH CASE DEFAULT BREAK CONTINUE RETURN GOTO
%token INT_KW CHAR_KW FLOAT_KW DOUBLE_KW VOID_KW LONG_KW SHORT_KW UNSIGNED_KW SIGNED_KW CONST_KW STATIC_KW STRUCT_KW
%token <str> IDENTIFIER CONSTANT STRING_LIT
%token <str> ARROW INC_OP DEC_OP LEFT_ASSIGN RIGHT_ASSIGN LEFT_OP RIGHT_OP LE_OP GE_OP EQ_OP NE_OP AND_OP OR_OP
%token <str> MUL_ASSIGN DIV_ASSIGN MOD_ASSIGN ADD_ASSIGN SUB_ASSIGN AND_ASSIGN XOR_ASSIGN OR_ASSIGN

%type <str> expr expr_opt assignment_expr cond_expr lor_expr land_expr or_expr xor_expr and_expr
%type <str> equality_expr relational_expr shift_expr additive_expr multiplicative_expr
%type <str> unary_expr postfix_expr primary_expr unary_op assign_op const_expr arg_list arg_list_opt
%type <str> init_declarator init_declarator_list array_suffix_opt global_init_opt
%type <stmt> statement compound_stmt if_stmt while_stmt do_while_stmt for_stmt switch_stmt decl_stmt expr_stmt
%type <stmtlist> stmt_list stmt_list_opt
%type <param> param_list param_list_opt param_decl

%nonassoc LOWER_THAN_ELSE
%nonassoc ELSE

%start translation_unit

%%

translation_unit
    : external_decl
    | translation_unit external_decl
    ;

external_decl
    : function_def
    | type_spec_list pointer_opt IDENTIFIER array_suffix_opt global_init_opt ';' { free($3); }
    ;

function_def
    : type_spec_list pointer_opt IDENTIFIER '(' param_list_opt ')' compound_stmt {
        FunctionDef *f = funcdef_new($3, $5, $7, @3.first_line);
        f->next = g_program.functions;
        g_program.functions = f;
      }
    ;

pointer_opt
    : /* empty */
    | pointer_opt '*'
    ;

param_list_opt
    : /* empty */ { $$ = NULL; }
    | VOID_KW     { $$ = NULL; }
    | param_list  { $$ = $1; }
    ;

param_list
    : param_decl                    { $$ = $1; }
    | param_list ',' param_decl     {
        Param *cur = $1;
        while (cur->next) cur = cur->next;
        cur->next = $3;
        $$ = $1;
      }
    ;

param_decl
    : type_spec_list pointer_opt IDENTIFIER array_suffix_opt { $$ = param_new($3, NULL); }
    ;

type_spec_list
    : type_spec
    | type_spec_list type_spec
    ;

type_spec
    : INT_KW | CHAR_KW | FLOAT_KW | DOUBLE_KW | VOID_KW | LONG_KW | SHORT_KW
    | UNSIGNED_KW | SIGNED_KW | CONST_KW | STATIC_KW
    | STRUCT_KW IDENTIFIER { free($2); }
    ;

array_suffix_opt
    : /* empty */                       { $$ = strdup(""); }
    | array_suffix_opt '[' ']'          { $$ = $1; }
    | array_suffix_opt '[' CONSTANT ']' { $$ = $1; free($3); }
    ;

global_init_opt
    : /* empty */    { $$ = strdup(""); }
    | '=' expr       { $$ = $2; }
    ;

/* ---------------- statements ---------------- */

compound_stmt
    : '{' stmt_list_opt '}' {
        Stmt *s = stmt_new(STMT_COMPOUND, @1.first_line);
        s->body = $2;
        $$ = s;
      }
    ;

stmt_list_opt
    : /* empty */ { $$ = NULL; }
    | stmt_list   { $$ = $1; }
    ;

stmt_list
    : statement              { $$ = stmtlist_cons($1, NULL); }
    | stmt_list statement    { $$ = stmtlist_append($1, $2); }
    ;

statement
    : compound_stmt
    | if_stmt
    | while_stmt
    | do_while_stmt
    | for_stmt
    | switch_stmt
    | decl_stmt
    | expr_stmt
    | BREAK ';'                { $$ = stmt_new(STMT_BREAK, @1.first_line); }
    | CONTINUE ';'              { $$ = stmt_new(STMT_CONTINUE, @1.first_line); }
    | RETURN ';'                { $$ = stmt_new(STMT_RETURN, @1.first_line); }
    | RETURN expr ';'           { Stmt *s = stmt_new(STMT_RETURN, @1.first_line); s->text = $2; $$ = s; }
    | GOTO IDENTIFIER ';'       { Stmt *s = stmt_new(STMT_GOTO, @1.first_line); s->text = $2; $$ = s; }
    | IDENTIFIER ':' statement  { Stmt *s = stmt_new(STMT_LABEL, @1.first_line); s->text = $1; s->s1 = $3; $$ = s; }
    | CASE const_expr ':'       { Stmt *s = stmt_new(STMT_CASE, @1.first_line); s->text = $2; $$ = s; }
    | DEFAULT ':'                { $$ = stmt_new(STMT_DEFAULT, @1.first_line); }
    | ';'                        { $$ = stmt_new(STMT_EMPTY, @1.first_line); }
    ;

if_stmt
    : IF '(' expr ')' statement %prec LOWER_THAN_ELSE {
        Stmt *s = stmt_new(STMT_IF, @1.first_line);
        s->text = $3; s->s1 = $5; s->s2 = NULL;
        $$ = s;
      }
    | IF '(' expr ')' statement ELSE statement {
        Stmt *s = stmt_new(STMT_IF, @1.first_line);
        s->text = $3; s->s1 = $5; s->s2 = $7;
        $$ = s;
      }
    ;

while_stmt
    : WHILE '(' expr ')' statement {
        Stmt *s = stmt_new(STMT_WHILE, @1.first_line);
        s->text = $3; s->s1 = $5;
        $$ = s;
      }
    ;

do_while_stmt
    : DO statement WHILE '(' expr ')' ';' {
        Stmt *s = stmt_new(STMT_DO_WHILE, @1.first_line);
        s->s1 = $2; s->text = $5;
        $$ = s;
      }
    ;

for_stmt
    : FOR '(' expr_opt ';' expr_opt ';' expr_opt ')' statement {
        Stmt *s = stmt_new(STMT_FOR, @1.first_line);
        s->text2 = $3; s->text = $5; s->text3 = $7; s->s1 = $9;
        $$ = s;
      }
    ;

switch_stmt
    : SWITCH '(' expr ')' compound_stmt {
        Stmt *s = stmt_new(STMT_SWITCH, @1.first_line);
        s->text = $3; s->s2 = $5;
        $$ = s;
      }
    ;

decl_stmt
    : type_spec_list init_declarator_list ';' {
        Stmt *s = stmt_new(STMT_DECL, @1.first_line);
        s->text = $2;
        $$ = s;
      }
    ;

init_declarator_list
    : init_declarator                             { $$ = $1; }
    | init_declarator_list ',' init_declarator     { $$ = strf("%s, %s", $1, $3); }
    ;

init_declarator
    : pointer_opt IDENTIFIER array_suffix_opt                 { $$ = strf("%s%s", $2, $3); }
    | pointer_opt IDENTIFIER array_suffix_opt '=' assignment_expr { $$ = strf("%s%s = %s", $2, $3, $5); }
    ;

expr_stmt
    : expr ';' { Stmt *s = stmt_new(STMT_EXPR, @1.first_line); s->text = $1; $$ = s; }
    ;

/* ---------------- expressions (return reconstructed source text) ---------------- */

primary_expr
    : IDENTIFIER      { $$ = $1; }
    | CONSTANT        { $$ = $1; }
    | STRING_LIT      { $$ = $1; }
    | '(' expr ')'    { $$ = strf("(%s)", $2); }
    ;

postfix_expr
    : primary_expr
    | postfix_expr '[' expr ']'         { $$ = strf("%s[%s]", $1, $3); }
    | postfix_expr '(' arg_list_opt ')' { $$ = strf("%s(%s)", $1, $3); }
    | postfix_expr '.' IDENTIFIER       { $$ = strf("%s.%s", $1, $3); }
    | postfix_expr ARROW IDENTIFIER     { $$ = strf("%s->%s", $1, $3); }
    | postfix_expr INC_OP               { $$ = strf("%s++", $1); }
    | postfix_expr DEC_OP               { $$ = strf("%s--", $1); }
    ;

arg_list_opt
    : /* empty */ { $$ = strdup(""); }
    | arg_list    { $$ = $1; }
    ;

arg_list
    : assignment_expr                  { $$ = $1; }
    | arg_list ',' assignment_expr     { $$ = strf("%s, %s", $1, $3); }
    ;

unary_expr
    : postfix_expr
    | INC_OP unary_expr   { $$ = strf("++%s", $2); }
    | DEC_OP unary_expr   { $$ = strf("--%s", $2); }
    | unary_op unary_expr { $$ = strf("%s%s", $1, $2); }
    ;

unary_op
    : '&' { $$ = strdup("&"); } | '*' { $$ = strdup("*"); } | '+' { $$ = strdup("+"); }
    | '-' { $$ = strdup("-"); } | '~' { $$ = strdup("~"); } | '!' { $$ = strdup("!"); }
    ;

multiplicative_expr
    : unary_expr
    | multiplicative_expr '*' unary_expr { $$ = strf("%s * %s", $1, $3); }
    | multiplicative_expr '/' unary_expr { $$ = strf("%s / %s", $1, $3); }
    | multiplicative_expr '%' unary_expr { $$ = strf("%s %% %s", $1, $3); }
    ;

additive_expr
    : multiplicative_expr
    | additive_expr '+' multiplicative_expr { $$ = strf("%s + %s", $1, $3); }
    | additive_expr '-' multiplicative_expr { $$ = strf("%s - %s", $1, $3); }
    ;

shift_expr
    : additive_expr
    | shift_expr LEFT_OP additive_expr  { $$ = strf("%s << %s", $1, $3); }
    | shift_expr RIGHT_OP additive_expr { $$ = strf("%s >> %s", $1, $3); }
    ;

relational_expr
    : shift_expr
    | relational_expr '<' shift_expr  { $$ = strf("%s < %s", $1, $3); }
    | relational_expr '>' shift_expr  { $$ = strf("%s > %s", $1, $3); }
    | relational_expr LE_OP shift_expr { $$ = strf("%s <= %s", $1, $3); }
    | relational_expr GE_OP shift_expr { $$ = strf("%s >= %s", $1, $3); }
    ;

equality_expr
    : relational_expr
    | equality_expr EQ_OP relational_expr { $$ = strf("%s == %s", $1, $3); }
    | equality_expr NE_OP relational_expr { $$ = strf("%s != %s", $1, $3); }
    ;

and_expr
    : equality_expr
    | and_expr '&' equality_expr { $$ = strf("%s & %s", $1, $3); }
    ;

xor_expr
    : and_expr
    | xor_expr '^' and_expr { $$ = strf("%s ^ %s", $1, $3); }
    ;

or_expr
    : xor_expr
    | or_expr '|' xor_expr { $$ = strf("%s | %s", $1, $3); }
    ;

land_expr
    : or_expr
    | land_expr AND_OP or_expr { $$ = strf("%s && %s", $1, $3); }
    ;

lor_expr
    : land_expr
    | lor_expr OR_OP land_expr { $$ = strf("%s || %s", $1, $3); }
    ;

cond_expr
    : lor_expr
    | lor_expr '?' expr ':' cond_expr { $$ = strf("%s ? %s : %s", $1, $3, $5); }
    ;

assign_op
    : '='            { $$ = strdup("="); }
    | MUL_ASSIGN | DIV_ASSIGN | MOD_ASSIGN | ADD_ASSIGN | SUB_ASSIGN
    | LEFT_ASSIGN | RIGHT_ASSIGN | AND_ASSIGN | XOR_ASSIGN | OR_ASSIGN
    ;

assignment_expr
    : cond_expr
    | unary_expr assign_op assignment_expr { $$ = strf("%s %s %s", $1, $2, $3); }
    ;

expr
    : assignment_expr
    | expr ',' assignment_expr { $$ = strf("%s, %s", $1, $3); }
    ;

expr_opt
    : /* empty */ { $$ = strdup(""); }
    | expr        { $$ = $1; }
    ;

const_expr
    : cond_expr
    ;

%%

void yyerror(const char *s) {
    fprintf(stderr, "parse error: %s at line %d\n", s, yylineno);
}
