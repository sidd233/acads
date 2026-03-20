# Lab Report — Experiment 9
## Syntax Directed Translation using Flex and Bison

---

## 1. Objective

Implement a compiler front-end for arithmetic expressions that:

1. **Lexes** (tokenises) the input using Flex
2. **Parses** the token stream using a context-free grammar in Bison
3. **Builds a syntax tree** during parsing using semantic actions (Syntax Directed Translation)
4. **Generates three outputs** from the tree: postfix notation, inorder notation, and Three Address Code (TAC)

---

## 2. Background Concepts

### 2.1 Lexical Analysis (Lexer / Scanner)

The first phase of a compiler. It reads raw characters and groups them into **tokens** — the meaningful units of the language. Examples: the string `"abc"` becomes an `ID` token; `"123"` becomes a `NUMBER` token.

Flex (Fast Lexical Analyser) generates a C function `yylex()` from a set of regular expression rules written in a `.l` file. Every time the parser needs the next token it calls `yylex()`, which:

1. Reads characters from input
2. Matches them against the patterns (rules) in order
3. Returns the token type and stores any associated value in `yylval`

### 2.2 Syntax Analysis (Parser)

The second phase. It takes the flat stream of tokens from the lexer and checks whether they form a valid sentence according to the language's **grammar**, building a hierarchical parse tree in the process.

Bison (GNU's YACC replacement) generates a C function `yyparse()` from grammar rules written in a `.y` file. It uses **LALR(1) parsing** — a bottom-up parsing algorithm that reads one token of lookahead.

### 2.3 Context-Free Grammar (CFG)

A grammar defines the legal structure of sentences in a language. The grammar used in this experiment is:

```
E → E + T          (addition)
E → E - T          (subtraction)
E → T

T → T * F          (multiplication)
T → T / F          (division)
T → F

F → ( E )          (parenthesised expression)
F → NUMBER
F → ID
```

**Why three non-terminals (E, T, F)?**
Each level encodes a different precedence tier:

- `F` (Factor) — the highest precedence: atoms and parenthesised groups
- `T` (Term) — medium precedence: `*` and `/`
- `E` (Expression) — lowest precedence: `+` and `-`

Because `T` can only be reached through `E`, and `F` only through `T`, multiplication and division are always evaluated before addition and subtraction — exactly how normal arithmetic works. This is **precedence encoded directly in the grammar structure**.

**Left recursion for left associativity:**
Rules like `E → E + T` are left-recursive: the `E` on the right-hand side refers back to the same non-terminal on the left. This forces the parser to build the tree left-to-right, making `a - b + c` parse as `(a - b) + c` rather than `a - (b + c)`. Both `+/-` and `*//` are left-associative by this construction.

### 2.4 Syntax Directed Translation (SDT)

SDT attaches **semantic actions** (blocks of C code) to grammar rules. Each grammar symbol can carry a **semantic value** (called an **attribute**). When the parser reduces a rule, it runs the attached action, which typically computes the parent symbol's attribute from the children's attributes.

In Bison:
- `$1`, `$2`, `$3` … refer to the semantic values of the 1st, 2nd, 3rd symbol on the right-hand side of the rule
- `$$` is the semantic value being assigned to the left-hand side (the result)

Example:
```
E : E '+' T { $$ = createNode("+", $1, $3); }
```
Here `$1` is the node for the left `E`, `$3` is the node for `T`, and `$$` becomes a new `+` node with those as children.

### 2.5 Syntax Tree (Abstract Syntax Tree)

A syntax tree is a tree representation of the structure of an expression. Each **internal node** holds an operator; each **leaf node** holds an operand (number or identifier). Parentheses disappear — the structure of the tree itself encodes grouping.

For `a + b * c`:
```
    +
   / \
  a   *
     / \
    b   c
```

The `*` node is deeper (a child of `+`), reflecting that multiplication has higher precedence and is computed first.

### 2.6 Three Address Code (TAC)

TAC is an intermediate representation used by compilers between the front-end and back-end. Each instruction has at most **three addresses** (operands/results) and exactly one operator:

```
result = operand1  op  operand2
```

TAC uses **temporary variables** (`t1`, `t2`, …) to hold intermediate results. These correspond to the intermediate nodes in the syntax tree. Each internal tree node becomes one TAC instruction, and the temporaries form the "wires" connecting instructions.

---

## 3. Tools Used

| Tool | Role |
|------|------|
| **Flex** | Generates the lexer (`lex.yy.c`) from `lexer.l` |
| **Bison** | Generates the parser (`parser.tab.c`, `parser.tab.h`) from `parser.y` |
| **GCC** | Compiles both generated C files into the final `parser` executable |

---

## 4. Implementation

### 4.1 `lexer.l` — The Flex Specification

```c
%{
#include "parser.tab.h"   // gives access to token codes (NUMBER, ID) and yylval
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

[ \t\n]     ;               // whitespace: skip silently

.           { return yytext[0]; }   // anything else: pass the raw character
%%

int yywrap() { return 1; }  // signals end-of-file to the lexer
```

**Key points:**

- `yytext` is a Flex global that holds the matched text as a C string.
- `yylval` is the union where the lexer stores the token's semantic value so the parser can retrieve it.
  - For `NUMBER`, we convert the digit string to an integer with `atoi` and store it in `yylval.num`.
  - For `ID`, we duplicate the string with `strdup` (heap allocation) and store in `yylval.id`. Duplication is necessary because `yytext` is overwritten on the next match.
- Single-character operators are returned as their own ASCII code — Bison treats single-quoted characters as token types directly.
- Whitespace rule has no action body (`{ }` is implicit as empty), so spaces, tabs, and newlines are silently consumed.
- The catch-all `.` rule forwards unknown characters through — this allows `yyerror` to surface them as syntax errors.
- `yywrap()` returning `1` means "do not try to switch to another input file; we are done."

---

### 4.2 `parser.y` — The Bison Specification

The parser file has three sections separated by `%%`: declarations, grammar rules, and auxiliary C code.

#### 4.2.1 Declarations Section

```c
%union {
    int   num;      // used by NUMBER tokens
    char* id;       // used by ID tokens
    struct Node* node;  // used by all non-terminals (E, T, F)
}

%token <num> NUMBER
%token <id>  ID

%type <node> E T F

%left '+' '-'
%left '*' '/'
```

- `%union` defines the type of `yylval` — a C union. Each token or non-terminal carries one of these variants as its semantic value.
- `%token <num> NUMBER` declares `NUMBER` as a terminal whose value is `yylval.num`.
- `%token <id> ID` declares `ID` as a terminal whose value is `yylval.id`.
- `%type <node> E T F` declares that the semantic value of the non-terminals `E`, `T`, `F` is `yylval.node` — a pointer to a `Node` in the syntax tree.
- `%left` declares associativity and (implicitly) precedence. Declarations later in the file have **higher** precedence. So `*` and `/` bind tighter than `+` and `-`. Since these `%left` declarations are present, they act as a secondary disambiguation mechanism alongside the grammar structure.

#### 4.2.2 The Node Structure

```c
typedef struct Node {
    char value[20];     // the operator symbol or operand name/number
    struct Node* left;
    struct Node* right;
} Node;
```

This is a simple **binary tree node**. Every node in the expression tree is one of these:

- **Leaf node**: `left == NULL`, `right == NULL`, `value` holds the operand (`"a"`, `"42"`, etc.)
- **Internal node**: `left` and `right` point to children, `value` holds the operator (`"+"`, `"*"`, etc.)

```c
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
```

`strncpy` with a manual null-terminator is used for safe string copying into the fixed-size buffer.

#### 4.2.3 Grammar Rules and Semantic Actions

```c
E : E '+' T { $$ = createNode("+", $1, $3); }
  | E '-' T { $$ = createNode("-", $1, $3); }
  | T       { $$ = $1; }
  ;

T : T '*' F { $$ = createNode("*", $1, $3); }
  | T '/' F { $$ = createNode("/", $1, $3); }
  | F       { $$ = $1; }
  ;

F : '(' E ')' { $$ = $2; }
  | NUMBER    { char buf[20]; sprintf(buf, "%d", $1); $$ = createLeaf(buf); }
  | ID        { $$ = createLeaf($1); free($1); }
  ;
```

At every reduction, the semantic action builds a piece of the syntax tree:

- `E '+' T` → a new `+` node whose left child is the `E` subtree and right child is the `T` subtree
- `'(' E ')'` → just `$2` (the node for `E`), discarding the parenthesis tokens; this is how parentheses disappear from the tree
- `NUMBER` → a leaf; we convert the integer back to string form so all values are stored uniformly as strings
- `ID` → a leaf from the duplicated string; we `free($1)` here because the tree stores its own copy via `strncpy`

When the `E` rule propagates through `T` (`E : T`), the semantic value is simply forwarded: `$$ = $1`. No new node is created — we just pass the already-built subtree upward.

#### 4.2.4 Tree Traversal Functions

Three standard traversals are implemented:

**Postorder (Left → Right → Root):**
```c
void postorder(Node* root) {
    if (!root) return;
    postorder(root->left);
    postorder(root->right);
    printf("%s ", root->value);
}
```
Printing in postorder gives **postfix (Reverse Polish) notation**. Operators always appear after their operands — this is the order in which a stack-based evaluator would process them. No parentheses are needed because the order of tokens is unambiguous.

**Inorder (Left → Root → Right):**
```c
void inorder(Node* root) {
    if (!root) return;
    if (root->left || root->right) printf("(");
    inorder(root->left);
    printf("%s ", root->value);
    inorder(root->right);
    if (root->left || root->right) printf(")");
}
```
Inorder gives the original **infix notation**. We auto-insert parentheses around every sub-expression that has children so the printed output is unambiguous (even if the original expression had none).

**Preorder (Root → Left → Right):**
```c
void preorder(Node* root) {
    if (!root) return;
    printf("%s ", root->value);
    preorder(root->left);
    preorder(root->right);
}
```
Preorder gives **prefix (Polish) notation** — operators precede their operands. Also unambiguous without parentheses.

#### 4.2.5 Three Address Code Generation

```c
char* genTAC(Node* root) {
    if (!root) return NULL;

    if (!root->left && !root->right)    // leaf: operand, already has a name
        return strdup(root->value);

    char* left  = genTAC(root->left);   // recursively get name for left result
    char* right = genTAC(root->right);  // recursively get name for right result
    char* tmp   = newTemp();            // new temporary for this node's result
    printf("%s = %s %s %s\n", tmp, left, root->value, right);
    free(left);
    free(right);
    return tmp;                         // caller receives this temp's name
}
```

`genTAC` performs a **postorder traversal** (children first, then parent) and generates one TAC instruction per internal node:

1. Recurse left → get the name that holds the left operand's value (either a variable name or a temp like `t1`)
2. Recurse right → same for the right operand
3. Allocate a new temporary `tn`
4. Emit the instruction: `tn = left op right`
5. Return `tn` so the caller can use it as an operand

Leaf nodes just return their own name (`strdup(root->value)`) — they don't emit any instruction because an operand like `a` or `42` already has a value.

`newTemp()` simply increments a global counter and returns `"t1"`, `"t2"`, etc.:
```c
char* newTemp() {
    char* t = malloc(10);
    sprintf(t, "t%d", ++tempCount);
    return t;
}
```

---

## 5. Compilation Steps Explained

```bash
bison -d parser.y
```
- Reads `parser.y`
- Generates `parser.tab.c` (the `yyparse()` function and LALR(1) state tables)
- Generates `parser.tab.h` (token type `#define`s and `YYSTYPE` / `yylval` declarations)
- The `-d` flag is critical: without it the header file is not written, and `lexer.l` cannot include it

```bash
flex lexer.l
```
- Reads `lexer.l`
- Generates `lex.yy.c` (the `yylex()` function)
- Must be run **after** `bison -d` because `lexer.l` includes `parser.tab.h`

```bash
gcc parser.tab.c lex.yy.c -o parser -lfl
```
- Compiles both generated C files into one executable named `parser`
- `-lfl` links the Flex runtime library (provides `yywrap` internals and other support routines)

```bash
./parser
# or
echo "a + b * c" | ./parser
```

---

## 6. End-to-End Walkthrough

### Input: `a + b * c`

**Step 1 — Lexing**

The lexer reads the string and produces this token stream:

```
ID("a")  '+'  ID("b")  '*'  ID("c")  EOF
```

**Step 2 — Parsing (bottom-up reductions)**

The LALR(1) parser shifts tokens and reduces them according to the grammar:

```
"a"    → F(a)   → T(a)   → E(a)
"b"    → F(b)   → T(b)
"c"    → F(c)
T(b) * F(c) → T(b*c)              [T → T * F, creates * node]
E(a) + T(b*c) → E(a+b*c)          [E → E + T, creates + node]
```

Note that `b * c` is reduced to a `T` first, **before** the `+` is processed, because `*` has higher precedence. This is the grammar's precedence tiers at work.

**Step 3 — Tree built by semantic actions**

Each reduction runs its semantic action and builds a node:

```
createLeaf("a")  → leaf a
createLeaf("b")  → leaf b
createLeaf("c")  → leaf c
createNode("*", leaf_b, leaf_c) → * node
createNode("+", leaf_a, star_node) → + node  (root)
```

Resulting tree:
```
    +
   / \
  a   *
     / \
    b   c
```

**Step 4 — Postorder traversal (Postfix)**

Visit: `a`, then `b`, then `c`, then `*`, then `+`

Output: `a b c * +`

**Step 5 — TAC generation**

`genTAC(+_node)`:
- `genTAC(leaf_a)` → returns `"a"` (no instruction emitted)
- `genTAC(*_node)`:
  - `genTAC(leaf_b)` → returns `"b"`
  - `genTAC(leaf_c)` → returns `"c"`
  - Emits: `t1 = b * c`, returns `"t1"`
- Emits: `t2 = a + t1`, returns `"t2"`

Output:
```
t1 = b * c
t2 = a + t1
result in: t2
```

---

## 7. How Precedence and Associativity Work

### Precedence via Grammar Hierarchy

Consider `a + b * c`. Without precedence rules, this could be parsed as either `(a + b) * c` or `a + (b * c)`. The grammar prevents ambiguity structurally:

- `*` can only appear in `T → T * F` rules
- `+` can only appear in `E → E + T` rules
- `T` is "inside" `E` in the derivation chain

So to derive `a + b * c` from `E`, the parser must eventually reduce `b * c` as a `T` before combining with `a` via `+`. The grammar **forces** correct precedence.

### Left Associativity via Left Recursion

For `a - b + c`, the grammar rule `E → E + T` is left-recursive. The parser shifts `a`, reduces to `E`, then shifts `-`, `b`, reduces `b` to `T`, then reduces `E - T` → `E` (getting `a - b`). Only then does it see `+` and combine `(a-b) + c`. The tree becomes:

```
    +
   / \
  -   c
 / \
a   b
```

If the grammar were right-recursive (`E → T + E`), the same input would produce `a - (b + c)` instead — wrong for standard arithmetic.

---

## 8. Sample Outputs

### `a + b * c`
```
--- Postfix ---
a b c * +

--- Inorder ---
(a + (b * c ))

--- Preorder ---
+ a * b c

--- TAC ---
t1 = b * c
t2 = a + t1
```

### `(3+4) * 5`
```
--- Postfix ---
3 4 + 5 *

--- Inorder ---
((3 + 4 )* 5 )

--- Preorder ---
* + 3 4 5

--- TAC ---
t1 = 3 + 4
t2 = t1 * 5
```

### `10 / 2 + 3 * 4`
```
--- Postfix ---
10 2 / 3 4 * +

--- Inorder ---
((10 / 2 )+ (3 * 4 ))

--- Preorder ---
+ / 10 2 * 3 4

--- TAC ---
t1 = 10 / 2
t2 = 3 * 4
t3 = t1 + t2
```

### `(a + b) * (c - d)`
```
--- Postfix ---
a b + c d - *

--- Inorder ---
((a + b )* (c - d ))

--- Preorder ---
* + a b - c d

--- TAC ---
t1 = a + b
t2 = c - d
t3 = t1 * t2
```

---

## 9. Error Handling

When the parser receives a token that does not fit any valid grammar rule, Bison calls `yyerror`:

```c
int yyerror(char* s) {
    printf("Syntax Error: %s\n", s);
    return 0;
}
```

Examples of rejected inputs:

| Input    | Problem                                  |
|----------|------------------------------------------|
| `a +* b` | Two operators in a row — no rule matches `E op op` |
| `(3+4`   | EOF reached while expecting `)`          |
| `*5+`    | An expression cannot begin with `*`      |

---

## 10. Relationship Between Components

```
Source text
    │
    ▼
┌─────────┐   tokens    ┌─────────┐   reduce actions   ┌──────────────┐
│  Flex   │ ──────────► │  Bison  │ ──────────────────► │ Syntax Tree  │
│ (lexer) │             │(parser) │                     │   (in RAM)   │
└─────────┘             └─────────┘                     └──────┬───────┘
                                                               │
                           ┌───────────────────────────────────┤
                           │               │                   │
                           ▼               ▼                   ▼
                        Postfix         Inorder      Three Address Code
                      (postorder)    (inorder)         (postorder +
                                                      temp generation)
```

The syntax tree is the **central data structure**. All three output forms are derived from it by different traversal strategies. This separation of concerns is a key compiler design principle: parse once, derive multiple representations.

---

## 11. Key Design Decisions

| Decision | Reason |
|----------|--------|
| Build a tree instead of printing during parse | Separates parsing from output; allows multiple output formats from one parse |
| Use `%union` with `struct Node*` | Lets each non-terminal carry its subtree as a typed semantic value |
| `strdup` in the lexer for identifiers | `yytext` is a shared buffer overwritten on next match; the tree needs a stable copy |
| `free($1)` in the `ID` rule | The lexer heap-allocated the string with `strdup`; once it's copied into the leaf node via `strncpy`, the original must be freed to avoid a leak |
| Postorder traversal for TAC | Naturally processes children (operands) before parents (operators), matching the evaluation order that TAC encodes |
| Global `tempCount` reset to 0 before `genTAC` | Ensures temporaries are numbered from `t1` regardless of any future extensions |

---

## 12. Conclusion

This experiment demonstrates the complete pipeline of a compiler front-end:

1. **Flex** scans raw text into structured tokens using regular expressions
2. **Bison** uses a CFG with LALR(1) parsing to verify syntax and drive SDT
3. **Semantic actions** build an abstract syntax tree bottom-up during parsing
4. **Tree traversals** derive three equivalent but differently-formatted representations:
   - **Postfix** — operator after operands; useful for stack-based evaluation
   - **Infix with parentheses** — human-readable; explicitly shows grouping the grammar implied
   - **TAC** — machine-friendly intermediate code; each instruction is a single operation on named values

Together, these outputs represent the standard output of a compiler's front-end, ready to be consumed by optimisation passes and code generation in a real compiler.
