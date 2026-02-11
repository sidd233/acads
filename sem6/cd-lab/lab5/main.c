#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_ERRORS 256

typedef struct
{
    int line;
    int col;
    char expected[32];
    char found;
} SyntaxError;

SyntaxError errors[MAX_ERRORS];
int error_count = 0;

char input[1024];
int pos;
int line_no;
int col_no;

void E();
void Ep();
void T();
void Tp();
void F();

void log_error(const char *expected)
{
    if (error_count >= MAX_ERRORS)
        return;

    errors[error_count].line = line_no;
    errors[error_count].col = col_no;
    strncpy(errors[error_count].expected, expected, 31);
    errors[error_count].expected[31] = '\0';
    errors[error_count].found =
        (input[pos] == '\0' || input[pos] == '\n') ? '\0' : input[pos];
    error_count++;

    if (input[pos] != '\0' && input[pos] != '\n')
        pos++;
}

void advance()
{
    if (input[pos] == '\n')
    {
        line_no++;
        col_no = 1;
    }
    else
        col_no++;
    pos++;
}

void match(char c)
{
    if (input[pos] == c)
        advance();
    else
    {
        char exp[4] = {'\'', c, '\'', '\0'};
        log_error(exp);
    }
}

void E()
{
    T();
    Ep();
}

void Ep()
{
    if (input[pos] == '+')
    {
        match('+');
        T();
        Ep();
    }
}

void T()
{
    F();
    Tp();
}

void Tp()
{
    if (input[pos] == '*')
    {
        match('*');
        F();
        Tp();
    }
}

void F()
{
    if (input[pos] == '(')
    {
        match('(');
        E();
        match(')');
    }
    else if (input[pos] == 'i' && input[pos + 1] == 'd')
    {
        match('i');
        match('d');
    }
    else
        log_error("'(' or 'id'");
}

int main(int argc, char *argv[])
{
    FILE *fp;

    if (argc != 2)
        return 1;

    fp = fopen(argv[1], "r");
    if (!fp)
        return 1;

    line_no = 1;

    while (fgets(input, sizeof(input), fp))
    {
        pos = 0;
        col_no = 1;

        if (input[0] == '\n')
        {
            line_no++;
            continue;
        }

        E();

        if (input[pos] != '\0' && input[pos] != '\n')
            log_error("end of expression");

        line_no++;
    }

    fclose(fp);

    for (int i = 0; i < error_count; i++)
    {
        if (errors[i].found == '\0')
            printf("Syntax Error at line %d, column %d: expected %s, found end of line\n",
                   errors[i].line, errors[i].col, errors[i].expected);
        else
            printf("Syntax Error at line %d, column %d: expected %s, found '%c'\n",
                   errors[i].line, errors[i].col, errors[i].expected, errors[i].found);
    }

    if (error_count == 0)
        printf("Parsing completed successfully\n");
    else
        printf("Total syntax errors: %d\n", error_count);

    return 0;
}
