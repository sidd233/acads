# Compiler Design Laboratory

## Assignment: Syntax Directed Translation using Flex and Bison

---

## 1. Objective

The objective of this assignment is to:

* Implement a parser using Flex and Bison
* Apply Syntax Directed Translation (SDT)
* Generate:

  * Postfix notation
  * Syntax Tree
  * Three Address Code (TAC)

---

## 2. Problem Statement

Design and implement a compiler front-end for arithmetic expressions using Flex and Bison. The system should:

* Parse arithmetic expressions
* Generate postfix notation
* Construct syntax tree
* Generate three-address intermediate code

---

## 3. Grammar

```
E -> E + T
E -> E - T
E -> T
T -> T * F
T -> T / F
T -> F
F -> ( E )
F -> id
```

---

## 4. Syntax Directed Translation (SDT)

Attach semantic actions to generate:

* Postfix notation
* Temporary variables for TAC

**Example:**

```
E -> E1 + T { print ( E1.code || T.code || '+ ' ) }
```

---

## 5. Flex Specification (`lexer.l`)

```c
%{
#include "parser.tab.h"
%}

%%
[0-9]+      { yylval = atoi(yytext); return NUMBER; }
[a-zA-Z]+   { return ID; }

"+"         { return '+'; }
"-"         { return '-'; }
"*"         { return '*'; }
"/"         { return '/'; }
"("         { return '('; }
")"         { return ')'; }

[ \t\n]     ;

.           { return yytext[0]; }
%%

int yywrap() { return 1; }
```

---

## 6. Bison Specification (`parser.y`)

```c
%{
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int tempCount = 0;

char* newTemp() {
    char* t = malloc(10);
    sprintf(t, "t%d", tempCount++);
    return t;
}
%}

%token NUMBER ID

%%
E : E '+' T { printf("+ "); }
  | E '-' T { printf("- "); }
  | T
  ;

T : T '*' F { printf("* "); }
  | T '/' F { printf("/ "); }
  | F
  ;

F : '(' E ')'
  | NUMBER { printf("%d ", $1); }
  | ID     { printf("id "); }
  ;
%%

int main() {
    printf("Enter expression:\n");
    yyparse();
    return 0;
}

int yyerror(char* s) {
    printf("Syntax Error\n");
    return 0;
}
```

---

## 7. Tasks to Perform

Students must implement:

1. Write `lexer.l` using Flex
2. Write `parser.y` using Bison with SDT rules
3. Modify SDT rules to:

   * Generate postfix notation
   * Generate three-address code
   * Build syntax tree (node-based)
4. Implement temporary variable generation
5. Print syntax tree (preorder or inorder)

---

## 8. Compilation Steps

```bash
bison -d parser.y
flex lexer.l
gcc parser.tab.c lex.yy.c -o parser -lfl
./parser
```

---

## 9. Sample Inputs

### Valid Inputs

```
a + b * c
(3+4) * 5
x * y + z
```

### Invalid Inputs

```
a +* b
(3+4
*5+
```

---

## 10. Expected Output

### Postfix Example

**Input:**

```
a + b * c
```

**Output:**

```
a b c * +
```

---

### Three Address Code Example

```
t1 = b * c
t2 = a + t1
```

---

## 11. Syntax Tree (Node-Based)

### Node Structure

```c
typedef struct Node {
    char value[10];
    struct Node* left;
    struct Node* right;
} Node;
```

---

### Helper Functions

```c
Node* createLeaf(char* val);
Node* createNode(char* op, Node* left, Node* right);
```

---

### Bison Declarations

```c
%union {
    int num;
    char* id;
    struct Node* node;
}

%type <node> E T F
```

---

### Example Semantic Rule

```c
E : E '+' T {
    $$ = createNode("+", $1, $3);
}
```

---

### Leaf Nodes

```c
F : NUMBER {
    $$ = createLeaf("num");
}
  | ID {
    $$ = createLeaf("id");
}
```

---

## 12. Understanding `$1`, `$2`, `$3`, `$$`

Example:

```c
A : B C D {
    $$ = func($1, $2, $3);
}
```

* `$1` → value of B
* `$2` → value of C
* `$3` → value of D
* `$$` → value of A

---

## 13. Tree Traversal

```c
void inorder(Node* root);
void preorder(Node* root);
void postorder(Node* root);
```

---

### Example Tree

For input:

```
a + b * c
```

```
      +
     / \
    a   *
       / \
      b   c
```

---

## 14. Important Notes

* Use `malloc()` for memory allocation
* Maintain proper pointer connections
* Each grammar rule must return a node
* Avoid memory leaks (optional)

---

## 15. Goal

At the end, your parser should:

* Build a syntax tree
* Traverse and print it
* Use it for TAC generation

---

## 16. Advanced Task

* Expression evaluation
* Operator precedence using `%left`
* Extend grammar for unary operators

---

## 17. Submission Requirements

* `lexer.l` file
* `parser.y` file
* Output screenshots
* Explanation of SDT rules

---

## 18. Learning Outcomes

* Apply syntax-directed translation
* Generate intermediate representations
* Build compiler front-end components
* Integrate Flex and Bison effectively
