#ifndef AST_H
#define AST_H

typedef enum {
    STMT_COMPOUND, STMT_IF, STMT_WHILE, STMT_DO_WHILE, STMT_FOR,
    STMT_SWITCH, STMT_CASE, STMT_DEFAULT, STMT_BREAK, STMT_CONTINUE,
    STMT_RETURN, STMT_GOTO, STMT_LABEL, STMT_EXPR, STMT_DECL, STMT_EMPTY
} StmtType;

typedef struct Stmt {
    StmtType type;
    int line;
    char *text;              /* expr text / cond text / label name / goto target / case value */
    char *text2, *text3;     /* STMT_FOR only: text2=init, text=cond, text3=incr */
    struct Stmt *s1, *s2, *s3, *s4; /* meaning depends on type, see cfg.c comments */
    struct StmtList *body;   /* STMT_COMPOUND: list of statements in the block */
} Stmt;

typedef struct StmtList {
    Stmt *stmt;
    struct StmtList *next;
} StmtList;

typedef struct Param {
    char *name;
    struct Param *next;
} Param;

typedef struct FunctionDef {
    char *name;
    Param *params;
    Stmt *body; /* STMT_COMPOUND */
    int line;
    struct FunctionDef *next;
} FunctionDef;

typedef struct Program {
    FunctionDef *functions;
} Program;

/* constructors */
Stmt *stmt_new(StmtType type, int line);
StmtList *stmtlist_cons(Stmt *s, StmtList *rest);
StmtList *stmtlist_append(StmtList *list, Stmt *s); /* returns head, appends at tail */
Param *param_new(char *name, Param *next);
FunctionDef *funcdef_new(char *name, Param *params, Stmt *body, int line);

extern Program g_program;

#endif
