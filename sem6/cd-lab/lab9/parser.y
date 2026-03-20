%{
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* ── Syntax Tree ── */

# Move final PDF to pdf folder
mv build/main.pdf pdf/main.pdf
typedef struct Node {
    char value[20];
    struct Node* left;
    struct Node* right;
} Node;

Node* createLeaf(char* val) {
    Node* n = malloc(sizeof(Node));
    strncpy(n->value, val, 19);
    n->value[19] = '\0';
    n->left = n->right = NULL;
    return n;
}

Node* createNode(char* op, Node* left, Node* right) {
    Node* n = malloc(sizeof(Node));
    strncpy(n->value, op, 19);
    n->value[19] = '\0';
    n->left  = left;
    n->right = right;
    return n;
}

/* ── Tree traversals ── */
void inorder(Node* root) {
    if (!root) return;
    if (root->left || root->right) printf("(");
    inorder(root->left);
    printf("%s ", root->value);
    inorder(root->right);
    if (root->left || root->right) printf(")");
}

void preorder(Node* root) {
    if (!root) return;
    printf("%s ", root->value);
    preorder(root->left);
    preorder(root->right);
}

void postorder(Node* root) {
    if (!root) return;
    postorder(root->left);
    postorder(root->right);
    printf("%s ", root->value);
}

/* ── Three Address Code ── */
int tempCount = 0;

char* newTemp() {
    char* t = malloc(10);
    sprintf(t, "t%d", ++tempCount);
    return t;
}

/* Generate TAC for a subtree; returns the name holding the result */
char* genTAC(Node* root) {
    if (!root) return NULL;

    /* Leaf node */
    if (!root->left && !root->right)
        return strdup(root->value);

    char* left  = genTAC(root->left);
    char* right = genTAC(root->right);
    char* tmp   = newTemp();
    printf("%s = %s %s %s\n", tmp, left, root->value, right);
    free(left);
    free(right);
    return tmp;
}

int yylex(void);
int yyerror(char* s);
%}

%union {
    int   num;
    char* id;
    struct Node* node;
}

%token <num> NUMBER
%token <id>  ID

%type <node> E T F

%left '+' '-'
%left '*' '/'

%%

program
    : E '\n' {
        printf("\n--- Postfix ---\n");
        postorder($1);
        printf("\n");

        printf("\n--- Inorder (with parentheses) ---\n");
        inorder($1);
        printf("\n");

        printf("\n--- Preorder ---\n");
        preorder($1);
        printf("\n");

        printf("\n--- Three Address Code ---\n");
        tempCount = 0;
        char* res = genTAC($1);
        printf("result in: %s\n", res);
        free(res);
    }
    ;

E
    : E '+' T { $$ = createNode("+", $1, $3); }
    | E '-' T { $$ = createNode("-", $1, $3); }
    | T       { $$ = $1; }
    ;

T
    : T '*' F { $$ = createNode("*", $1, $3); }
    | T '/' F { $$ = createNode("/", $1, $3); }
    | F       { $$ = $1; }
    ;

F
    : '(' E ')' { $$ = $2; }
    | NUMBER    { char buf[20]; sprintf(buf, "%d", $1); $$ = createLeaf(buf); }
    | ID        { $$ = createLeaf($1); free($1); }
    ;

%%

int main() {
    printf("Enter expression:\n");
    yyparse();
    return 0;
}

int yyerror(char* s) {
    printf("Syntax Error: %s\n", s);
    return 0;
}
