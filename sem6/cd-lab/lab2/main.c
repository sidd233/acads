#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

#define MAX_LEX 100

/* ================= SYMBOL TABLE ================= */

typedef struct
{
    char name[64];
    char type[32];
    int line;
} Symbol;

Symbol *symbolTable = NULL;
int symbolCount = 0, symbolCapacity = 0;

int lookupSymbol(const char *name)
{
    for (int i = 0; i < symbolCount; i++)
        if (strcmp(symbolTable[i].name, name) == 0)
            return i;
    return -1;
}

void insertSymbol(const char *name, const char *type, int line)
{
    if (lookupSymbol(name) != -1)
        return;

    if (symbolCount == symbolCapacity)
    {
        int newCap = (symbolCapacity == 0) ? 10 : symbolCapacity * 2;
        Symbol *newTable = (Symbol *)realloc(symbolTable, newCap * sizeof(Symbol));
        if (!newTable)
        {
            printf("Memory error\n");
            exit(1);
        }
        symbolTable = newTable;
        symbolCapacity = newCap;
    }

    strcpy(symbolTable[symbolCount].name, name);
    strcpy(symbolTable[symbolCount].type, type);
    symbolTable[symbolCount].line = line;
    symbolCount++;
}

void printSymbolTable()
{
    printf("\n============= SYMBOL TABLE =============\n");
    printf("%-5s %-20s %-10s %-10s\n", "No.", "Name", "Type", "Line");
    for (int i = 0; i < symbolCount; i++)
        printf("%-5d %-20s %-10s %-10d\n",
               i + 1,
               symbolTable[i].name,
               symbolTable[i].type,
               symbolTable[i].line);
}

void freeSymbolTable()
{
    free(symbolTable);
}

/* ================= LEXICAL RULES ================= */

const char *keywords[] = {"if", "else", "while", "int", "float", "return", "begin", "end", "print"};

int isKeyword(char *s)
{
    for (int i = 0; i < 9; i++)
        if (strcmp(s, keywords[i]) == 0)
            return 1;
    return 0;
}

int isDelimiter(char c)
{
    return (c == ' ' || c == '\n' || c == '\t' || c == ';' || c == ',' || c == '(' || c == ')' || c == '{' || c == '}');
}

int isOperator(char c)
{
    return (c == '+' || c == '-' || c == '*' || c == '/' || c == '=');
}

/* ================= LEXICAL ANALYZER ================= */

void lexicalAnalyzer(FILE *fp)
{
    char c, lex[MAX_LEX];
    int i, line = 1;

    while ((c = fgetc(fp)) != EOF)
    {
        if (c == '\n')
        {
            line++;
            continue;
        }
        if (isspace(c))
            continue;

        /* Identifier or Keyword */
        if (isalpha(c))
        {
            i = 0;
            lex[i++] = c;
            while (isalnum(c = fgetc(fp)))
                lex[i++] = c;
            lex[i] = '\0';
            ungetc(c, fp);

            if (isKeyword(lex))
                printf("<KEYWORD, %s>\n", lex);
            else
            {
                printf("<ID, %s>\n", lex);
                insertSymbol(lex, "ID", line);
            }
        }

        /* Number (int or float) */
        else if (isdigit(c))
        {
            i = 0;
            int isFloat = 0;
            lex[i++] = c;

            while (isdigit(c = fgetc(fp)) || c == '.')
            {
                if (c == '.')
                    isFloat = 1;
                lex[i++] = c;
            }
            lex[i] = '\0';
            ungetc(c, fp);

            if (isFloat)
                printf("<NUM_FLOAT, %s>\n", lex);
            else
                printf("<NUM_INT, %s>\n", lex);
        }

        /* Relational operators */
        else if (c == '<' || c == '>' || c == '=' || c == '!')
        {
            char next = fgetc(fp);
            if ((c == '<' && next == '=') || (c == '>' && next == '=') || (c == '=' && next == '=') || (c == '!' && next == '='))
                printf("<RELOP, %c%c>\n", c, next);
            else
            {
                ungetc(next, fp);
                printf("<RELOP, %c>\n", c);
            }
        }

        /* Operators */
        else if (isOperator(c))
            printf("<OPERATOR, %c>\n", c);

        /* Delimiters */
        else if (isDelimiter(c))
            printf("<DELIMITER, %c>\n", c);

        /* Invalid */
        else
            printf("<INVALID, %c>\n", c);
    }
}

/* ================= MAIN ================= */

int main()
{
    FILE *fp = fopen("input.toy", "r");
    if (!fp)
    {
        printf("Cannot open input.toy\n");
        return 1;
    }

    lexicalAnalyzer(fp);
    fclose(fp);

    printSymbolTable();
    freeSymbolTable();
    return 0;
}
