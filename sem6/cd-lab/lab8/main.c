#include <stdio.h>
#include <string.h>
#include <ctype.h>
#include <math.h>

int isVariable(char c)
{
    if (isalpha(c) && c != 'T' && c != 'F' && c != 't' && c != 'f')
        return 1;
    return 0;
}

int isOperand(char c)
{
    return isVariable(c) || c == 'T' || c == 'F' || c == 't' || c == 'f';
}

int lexicalCheck(char *s)
{

    int len = strlen(s);

    for (int i = 0; i < len; i++)
    {

        char c = s[i];

        if (isalpha(c) || c == 'T' || c == 'F' || c == 't' || c == 'f' || c == '(' || c == ')')
            continue;

        if (c == '~')
            continue;

        if (i + 1 < len && s[i] == '/' && s[i + 1] == '\\')
        {
            i++;
            continue;
        }

        if (i + 1 < len && s[i] == '\\' && s[i + 1] == '/')
        {
            i++;
            continue;
        }

        if (i + 1 < len && s[i] == '-' && s[i + 1] == '>')
        {
            i++;
            continue;
        }

        if (i + 2 < len && s[i] == '<' && s[i + 1] == '-' && s[i + 2] == '>')
        {
            i += 2;
            continue;
        }

        printf("Lexical Error: Invalid token '%c' at position %d\n", c, i + 1);
        return 0;
    }

    return 1;
}

int syntaxCheck(char *s)
{

    int len = strlen(s);

    /* (i) Incomplete expression */
    if (len == 0)
    {
        printf("Syntax Error: Incomplete expression\n");
        return 0;
    }

    for (int i = 0; i < len; i++)
    {

        char c = s[i];

        /* (ii) two operands consecutive */
        if (isOperand(c) && i + 1 < len && isOperand(s[i + 1]))
        {
            printf("Syntax Error: Operator missing between operands at position %d\n", i + 1);
            return 0;
        }

        /* (iii) () empty parentheses */
        if (c == '(' && i + 1 < len && s[i + 1] == ')')
        {
            printf("Syntax Error: Expression missing between parentheses at position %d\n", i + 1);
            return 0;
        }

        if (s[i] == ')' && i + 1 < len && s[i + 1] == '(')
        {
            printf("Syntax Error: Operator missing between ')' and '(' at position %d\n", i + 1);
            return 0;
        }

        /* (iv) binary operator missing operand */

        if (i + 1 < len && s[i] == '/' && s[i + 1] == '\\')
        {

            if (i == 0 || i + 2 >= len || s[i + 2] == ')')
            {
                printf("Syntax Error: Operand missing for binary operator '/\\' at position %d\n", i + 1);
                return 0;
            }

            i++;
        }

        if (i + 1 < len && s[i] == '\\' && s[i + 1] == '/')
        {

            if (i == 0 || i + 2 >= len || s[i + 2] == ')')
            {
                printf("Syntax Error: Operand missing for binary operator '\\/' at position %d\n", i + 1);
                return 0;
            }

            i++;
        }

        if (i + 1 < len && s[i] == '-' && s[i + 1] == '>')
        {

            if (i == 0 || i + 2 >= len)
            {
                printf("Syntax Error: Operand missing for binary operator '->' at position %d\n", i + 1);
                return 0;
            }

            i++;
        }

        if (i + 2 < len && s[i] == '<' && s[i + 1] == '-' && s[i + 2] == '>')
        {

            if (i == 0 || i + 3 >= len)
            {
                printf("Syntax Error: Operand missing for binary operator '<->' at position %d\n", i + 1);
                return 0;
            }

            i += 2;
        }

        /* (v) unary operator missing operand */

        if (c == '~' && (i + 1 >= len || s[i + 1] == ')'))
        {
            printf("Syntax Error: Operand missing for unary operator '~' at position %d\n", i + 1);
            return 0;
        }

        /* (vi) consecutive binary operators */

        if (i + 1 < len)
        {

            if ((s[i] == '/' && s[i + 1] == '\\') &&
                (s[i + 2] == '/' || s[i + 2] == '\\' || s[i + 2] == '-' || s[i + 2] == '<'))
            {
                printf("Syntax Error: Consecutive binary operators at position %d\n", i + 1);
                return 0;
            }
        }
    }

    /* (vii) missing '(' for ')' */

    char stack[100];
    int top = -1;

    for (int i = 0; i < len; i++)
    {

        if (s[i] == '(')
            stack[++top] = '(';

        if (s[i] == ')')
        {

            if (top == -1)
            {
                printf("Syntax Error: Missing '(' for ')' at position %d\n", i + 1);
                return 0;
            }

            top--;
        }
    }

    if (top != -1)
    {
        printf("Syntax Error: Missing ')' for '('\n");
        return 0;
    }

    return 1;
}
int implication(int a, int b)
{
    return (!a) || b;
}

int bicond(int a, int b)
{
    return a == b;
}

int precedence(char *op)
{
    if (strcmp(op, "~") == 0)
        return 6;
    if (strcmp(op, "<->") == 0)
        return 5;
    if (strcmp(op, "->") == 0)
        return 4;
    if (strcmp(op, "/\\") == 0)
        return 3;
    if (strcmp(op, "\\/") == 0)
        return 2;
    return 0;
}

void infixToPostfix(char *expr, char postfix[][10], int *k)
{
    char stack[100][10];
    int top = -1;

    int len = strlen(expr);

    for (int i = 0; i < len; i++)
    {
        if (isOperand(expr[i]))
        {
            postfix[*k][0] = expr[i];
            postfix[*k][1] = '\0';
            (*k)++;
        }

        else if (expr[i] == '(')
        {
            strcpy(stack[++top], "(");
        }

        else if (expr[i] == ')')
        {
            while (top != -1 && strcmp(stack[top], "(") != 0)
                strcpy(postfix[(*k)++], stack[top--]);

            top--;
        }

        else
        {
            char op[10];

            if (expr[i] == '~')
                strcpy(op, "~");

            else if (expr[i] == '/' && expr[i + 1] == '\\')
            {
                strcpy(op, "/\\");
                i++;
            }

            else if (expr[i] == '\\' && expr[i + 1] == '/')
            {
                strcpy(op, "\\/");
                i++;
            }

            else if (expr[i] == '-' && expr[i + 1] == '>')
            {
                strcpy(op, "->");
                i++;
            }

            else if (expr[i] == '<' && expr[i + 1] == '-' && expr[i + 2] == '>')
            {
                strcpy(op, "<->");
                i += 2;
            }

            while (top != -1 && (precedence(stack[top]) > precedence(op) || (precedence(stack[top]) == precedence(op) && strcmp(op, "~") != 0)))
            {
                strcpy(postfix[(*k)++], stack[top--]);
            }
            strcpy(stack[++top], op);
        }
    }

    while (top != -1)
        strcpy(postfix[(*k)++], stack[top--]);
}

int evaluatePostfix(char postfix[][10], int k, int values[256])
{
    int stack[100];
    int top = -1;

    for (int i = 0; i < k; i++)
    {
        char *op = postfix[i];

        if (strlen(op) == 1 && isOperand(op[0]))
        {
            char c = op[0];

            if (c == 'T' || c == 't')
                stack[++top] = 1;

            else if (c == 'F' || c == 'f')
                stack[++top] = 0;

            else
                stack[++top] = values[c];
        }

        else if (strcmp(op, "~") == 0)
        {
            int a = stack[top--];
            stack[++top] = !a;
        }

        else
        {
            int b = stack[top--];
            int a = stack[top--];

            if (strcmp(op, "/\\") == 0)
                stack[++top] = a && b;

            else if (strcmp(op, "\\/") == 0)
                stack[++top] = a || b;

            else if (strcmp(op, "->") == 0)
                stack[++top] = (!a) || b;

            else if (strcmp(op, "<->") == 0)
                stack[++top] = (a == b);
        }
    }

    return stack[top];
}
void parsingTrace(char *expr)
{

    char stack[100];
    int top = -1;

    char input[200];
    strcpy(input, expr);
    strcat(input, "$");

    printf("\nParsing Trace\n");
    printf("Stack\tInput\tAction\n");

    for (int i = 0; i < strlen(input); i++)
    {

        for (int j = 0; j <= top; j++)
            printf("%c", stack[j]);

        printf("\t%s\t", input + i);

        if (isOperand(input[i]) || input[i] == '(')
        {

            printf("SHIFT\n");
            stack[++top] = input[i];
        }

        else if (input[i] == ')')
        {

            printf("REDUCE\n");

            if (top != -1)
                top--;
        }

        else if (input[i] == '$')
        {

            printf("ACCEPT\n");
        }

        else
        {

            printf("SHIFT\n");
        }
    }
}

int main()
{

    char expr[200];

    printf("Enter logical expression:\n");
    scanf("%s", expr);

    if (!lexicalCheck(expr))
        return 0;

    if (!syntaxCheck(expr))
        return 0;

    parsingTrace(expr);

    char vars[50];
    int n = 0;

    for (int i = 0; i < strlen(expr); i++)
    {

        if (isVariable(expr[i]))
        {

            int found = 0;

            for (int j = 0; j < n; j++)
                if (vars[j] == expr[i])
                    found = 1;

            if (!found)
                vars[n++] = expr[i];
        }
    }

    int rows = pow(2, n);

    printf("\nTruth Table\n");

    for (int i = 0; i < n; i++)
        printf("%c ", vars[i]);

    printf("Result\n");

    int trueCount = 0;
    char postfix[200][10];
    int k = 0;
    infixToPostfix(expr, postfix, &k);

    for (int i = 0; i < rows; i++)
    {

        int values[256] = {0};

        for (int j = 0; j < n; j++)
        {

            int bit = (i >> j) & 1;

            values[vars[j]] = bit;

            printf("%d ", bit);
        }

        int result = evaluatePostfix(postfix, k, values);

        printf("%d\n", result);

        if (result)
            trueCount++;
    }

    if (trueCount == rows)
        printf("\nExpression is TAUTOLOGY\n");

    else if (trueCount == 0)
        printf("\nExpression is FALLACY\n");

    else
        printf("\nExpression is SATISFIABLE\n");

    return 0;
}