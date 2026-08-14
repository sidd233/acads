#include <stdlib.h>
#include <string.h>
#include "ast.h"

Program g_program = { NULL };

Stmt *stmt_new(StmtType type, int line) {
    Stmt *s = calloc(1, sizeof(Stmt));
    s->type = type;
    s->line = line;
    return s;
}

StmtList *stmtlist_cons(Stmt *s, StmtList *rest) {
    StmtList *node = malloc(sizeof(StmtList));
    node->stmt = s;
    node->next = rest;
    return node;
}

/* O(n) tail append; fine for typical function sizes in a class project */
StmtList *stmtlist_append(StmtList *list, Stmt *s) {
    StmtList *node = malloc(sizeof(StmtList));
    node->stmt = s;
    node->next = NULL;
    if (!list) return node;
    StmtList *cur = list;
    while (cur->next) cur = cur->next;
    cur->next = node;
    return list;
}

Param *param_new(char *name, Param *next) {
    Param *p = malloc(sizeof(Param));
    p->name = name;
    p->next = next;
    return p;
}

FunctionDef *funcdef_new(char *name, Param *params, Stmt *body, int line) {
    FunctionDef *f = malloc(sizeof(FunctionDef));
    f->name = name;
    f->params = params;
    f->body = body;
    f->line = line;
    f->next = NULL;
    return f;
}
