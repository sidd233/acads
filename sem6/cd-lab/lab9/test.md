# Test Cases — SDT Parser (Flex + Bison)

## How to Build and Run

```bash
# Step 1: Generate the parser (parser.tab.c and parser.tab.h)
bison -d parser.y

# Step 2: Generate the lexer (lex.yy.c)
flex lexer.l

# Step 3: Compile everything
gcc parser.tab.c lex.yy.c -o parser -lfl

# Step 4: Run interactively (type expression, press Enter)
./parser

# OR pipe an expression directly
echo "a + b * c" | ./parser
```

---

## Valid Test Cases

### Test 1 — Simple precedence (`a + b * c`)

Demonstrates that `*` binds tighter than `+`.

```
$ echo "a + b * c" | ./parser
```

```
--- Postfix ---
a b c * +

--- Inorder (with parentheses) ---
(a + (b * c ))

--- Preorder ---
+ a * b c

--- Three Address Code ---
t1 = b * c
t2 = a + t1
result in: t2
```

**Syntax tree:**
```
    +
   / \
  a   *
     / \
    b   c
```

---

### Test 2 — Parentheses override precedence (`(3+4) * 5`)

Parentheses force addition before multiplication.

```
$ echo "(3+4) * 5" | ./parser
```

```
--- Postfix ---
3 4 + 5 *

--- Inorder (with parentheses) ---
((3 + 4 )* 5 )

--- Preorder ---
* + 3 4 5

--- Three Address Code ---
t1 = 3 + 4
t2 = t1 * 5
result in: t2
```

**Syntax tree:**
```
    *
   / \
  +   5
 / \
3   4
```

---

### Test 3 — Left-associativity (`a - b + c`)

Both `+` and `-` are left-associative, so `a - b` is computed first.

```
$ echo "a - b + c" | ./parser
```

```
--- Postfix ---
a b - c +

--- Inorder (with parentheses) ---
((a - b )+ c )

--- Preorder ---
+ - a b c

--- Three Address Code ---
t1 = a - b
t2 = t1 + c
result in: t2
```

**Syntax tree:**
```
    +
   / \
  -   c
 / \
a   b
```

---

### Test 4 — Mixed operators, numbers (`10 / 2 + 3 * 4`)

Two independent high-precedence sub-expressions, then combined.

```
$ echo "10 / 2 + 3 * 4" | ./parser
```

```
--- Postfix ---
10 2 / 3 4 * +

--- Inorder (with parentheses) ---
((10 / 2 )+ (3 * 4 ))

--- Preorder ---
+ / 10 2 * 3 4

--- Three Address Code ---
t1 = 10 / 2
t2 = 3 * 4
t3 = t1 + t2
result in: t3
```

**Syntax tree:**
```
      +
     / \
    /   *
   / \ / \
  10  2 3  4
```

---

### Test 5 — Parenthesised sub-expressions (`(a + b) * (c - d)`)

Both operands of `*` are parenthesised groups.

```
$ echo "(a + b) * (c - d)" | ./parser
```

```
--- Postfix ---
a b + c d - *

--- Inorder (with parentheses) ---
((a + b )* (c - d ))

--- Preorder ---
* + a b - c d

--- Three Address Code ---
t1 = a + b
t2 = c - d
t3 = t1 * t2
result in: t3
```

**Syntax tree:**
```
      *
     / \
    +   -
   / \ / \
  a  b c  d
```

---

### Test 6 — `x * y + z`

```
$ echo "x * y + z" | ./parser
```

```
--- Postfix ---
x y * z +

--- Inorder (with parentheses) ---
((x * y )+ z )

--- Preorder ---
+ * x y z

--- Three Address Code ---
t1 = x * y
t2 = t1 + z
result in: t2
```

---

## Invalid Test Cases

All invalid inputs produce `Syntax Error: syntax error` and no other output.

| Input       | Reason                          |
|-------------|---------------------------------|
| `a +* b`    | Two consecutive operators       |
| `(3+4`      | Unmatched opening parenthesis   |
| `*5+`       | Expression starts with operator |

```
$ echo "a +* b" | ./parser
Enter expression:
Syntax Error: syntax error

$ echo "(3+4" | ./parser
Enter expression:
Syntax Error: syntax error

$ echo "*5+" | ./parser
Enter expression:
Syntax Error: syntax error
```

---

## Quick Batch Test

Copy and paste this to run all valid cases at once:

```bash
for expr in "a + b * c" "(3+4) * 5" "a - b + c" "10 / 2 + 3 * 4" "(a + b) * (c - d)" "x * y + z"; do
    echo "=== $expr ==="
    echo "$expr" | ./parser
done
```
