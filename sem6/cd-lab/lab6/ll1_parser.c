#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

#define MAX_PROD 50
#define MAX_LEN 100
#define MAX_NONTERM 26
#define MAX_TERM 50

typedef struct
{
    char lhs;
    char rhs[MAX_LEN];
} Production;

Production grammar[MAX_PROD];
int prodCount = 0;

char FIRST[MAX_NONTERM][MAX_TERM];
char FOLLOW[MAX_NONTERM][MAX_TERM];
int firstCount[MAX_NONTERM];
int followCount[MAX_NONTERM];

char parsingTable[MAX_NONTERM][MAX_TERM][MAX_LEN];

char stack[MAX_LEN];
int top = -1;

char nonTerminals[MAX_NONTERM];
int ntCount = 0;
char terminals[MAX_TERM];
int tCount = 0;

void push(char c)
{
    stack[++top] = c;
}

char pop()
{
    return stack[top--];
}

void displayStack()
{
    for (int i = 0; i <= top; i++)
        printf("%c", stack[i]);
}

int findNonTerminal(char c)
{
    for (int i = 0; i < ntCount; i++)
        if (nonTerminals[i] == c)
            return i;
    return -1;
}

int findTerminal(char c)
{
    for (int i = 0; i < tCount; i++)
        if (terminals[i] == c)
            return i;
    return -1;
}

void addNonTerminal(char c)
{
    if (findNonTerminal(c) == -1)
        nonTerminals[ntCount++] = c;
}

void addTerminal(char c)
{
    if (c != 'e' && !isupper(c) && findTerminal(c) == -1)
        terminals[tCount++] = c;
}

void readGrammar()
{
    int n;
    printf("Enter number of productions: ");
    scanf("%d", &n);
    getchar();

    for (int i = 0; i < n; i++)
    {
        printf("Enter production (e.g. S->Sa|b): ");
        fgets(grammar[prodCount].rhs, MAX_LEN, stdin);
        grammar[prodCount].rhs[strcspn(grammar[prodCount].rhs, "\n")] = 0;
        grammar[prodCount].lhs = grammar[prodCount].rhs[0];
        prodCount++;
    }
}

void displayGrammar()
{
    for (int i = 0; i < prodCount; i++)
    {
        printf("%c -> ", grammar[i].lhs);
        char *start = strstr(grammar[i].rhs, "->");
        if (start)
            printf("%s\n", start + 2);
    }
}

void removeLeftRecursion()
{
    Production newGrammar[MAX_PROD];
    int newCount = 0;

    for (int i = 0; i < prodCount; i++)
    {
        char lhs = grammar[i].lhs;
        char *rhsStart = strstr(grammar[i].rhs, "->") + 2;

        char alpha[10][30];
        char beta[10][30];
        int alphaCount = 0, betaCount = 0;

        char temp[MAX_LEN];
        strcpy(temp, rhsStart);
        char *token = strtok(temp, "|");

        while (token != NULL)
        {
            if (token[0] == lhs)
            {
                strcpy(alpha[alphaCount++], token + 1);
            }
            else
            {
                strcpy(beta[betaCount++], token);
            }
            token = strtok(NULL, "|");
        }

        if (alphaCount > 0)
        {
            char newNT = lhs + 1;

            for (int j = 0; j < betaCount; j++)
            {
                newGrammar[newCount].lhs = lhs;
                newGrammar[newCount].rhs[0] = lhs;
                newGrammar[newCount].rhs[1] = '-';
                newGrammar[newCount].rhs[2] = '>';
                strcpy(newGrammar[newCount].rhs + 3, beta[j]);
                int len = strlen(newGrammar[newCount].rhs);
                newGrammar[newCount].rhs[len] = newNT;
                newGrammar[newCount].rhs[len + 1] = '\0';
                newCount++;
            }

            for (int j = 0; j < alphaCount; j++)
            {
                newGrammar[newCount].lhs = newNT;
                newGrammar[newCount].rhs[0] = newNT;
                newGrammar[newCount].rhs[1] = '-';
                newGrammar[newCount].rhs[2] = '>';
                strcpy(newGrammar[newCount].rhs + 3, alpha[j]);
                int len = strlen(newGrammar[newCount].rhs);
                newGrammar[newCount].rhs[len] = newNT;
                newGrammar[newCount].rhs[len + 1] = '\0';
                newCount++;
            }

            newGrammar[newCount].lhs = newNT;
            newGrammar[newCount].rhs[0] = newNT;
            newGrammar[newCount].rhs[1] = '-';
            newGrammar[newCount].rhs[2] = '>';
            strcpy(newGrammar[newCount].rhs + 3, "epsilon");
            newCount++;
        }
        else
        {
            newGrammar[newCount++] = grammar[i];
        }
    }

    prodCount = newCount;
    for (int i = 0; i < newCount; i++)
        grammar[i] = newGrammar[i];
}

void leftFactoring()
{
    int changed = 1;

    while (changed)
    {
        changed = 0;
        Production newGrammar[MAX_PROD];
        int newCount = 0;

        for (int i = 0; i < prodCount; i++)
        {
            char lhs = grammar[i].lhs;
            char *rhsStart = strstr(grammar[i].rhs, "->") + 2;

            char alternatives[10][30];
            int altCount = 0;

            char temp[MAX_LEN];
            strcpy(temp, rhsStart);
            char *token = strtok(temp, "|");
            while (token != NULL)
            {
                strcpy(alternatives[altCount++], token);
                token = strtok(NULL, "|");
            }

            int maxPrefix = 0;
            for (int j = 0; j < altCount - 1; j++)
            {
                for (int k = j + 1; k < altCount; k++)
                {
                    int len = 0;
                    while (alternatives[j][len] && alternatives[k][len] &&
                           alternatives[j][len] == alternatives[k][len])
                        len++;
                    if (len > maxPrefix)
                        maxPrefix = len;
                }
            }

            if (maxPrefix > 0)
            {
                changed = 1;
                char prefix[30];
                strncpy(prefix, alternatives[0], maxPrefix);
                prefix[maxPrefix] = '\0';

                char newNT = 'X';

                newGrammar[newCount].lhs = lhs;
                newGrammar[newCount].rhs[0] = lhs;
                newGrammar[newCount].rhs[1] = '-';
                newGrammar[newCount].rhs[2] = '>';
                strcpy(newGrammar[newCount].rhs + 3, prefix);
                int len = strlen(newGrammar[newCount].rhs);
                newGrammar[newCount].rhs[len] = newNT;
                newGrammar[newCount].rhs[len + 1] = '\0';
                newCount++;

                for (int j = 0; j < altCount; j++)
                {
                    if (strncmp(alternatives[j], prefix, maxPrefix) == 0)
                    {
                        newGrammar[newCount].lhs = newNT;
                        newGrammar[newCount].rhs[0] = newNT;
                        newGrammar[newCount].rhs[1] = '-';
                        newGrammar[newCount].rhs[2] = '>';

                        if (strlen(alternatives[j] + maxPrefix) == 0)
                            strcpy(newGrammar[newCount].rhs + 3, "epsilon");
                        else
                            strcpy(newGrammar[newCount].rhs + 3, alternatives[j] + maxPrefix);
                        newCount++;
                    }
                }
            }
            else
            {
                newGrammar[newCount++] = grammar[i];
            }
        }

        prodCount = newCount;
        for (int i = 0; i < newCount; i++)
            grammar[i] = newGrammar[i];
    }
}

void collectSymbols()
{
    ntCount = 0;
    tCount = 0;

    for (int i = 0; i < prodCount; i++)
    {
        addNonTerminal(grammar[i].lhs);

        char *rhsStart = strstr(grammar[i].rhs, "->") + 2;
        for (int j = 0; rhsStart[j]; j++)
        {
            if (isupper(rhsStart[j]))
                addNonTerminal(rhsStart[j]);
            else if (rhsStart[j] != '|' && rhsStart[j] != 'e')
                addTerminal(rhsStart[j]);
        }
    }

    addTerminal('$');
}

int addToFirst(int nt, char c)
{
    for (int i = 0; i < firstCount[nt]; i++)
        if (FIRST[nt][i] == c)
            return 0;
    FIRST[nt][firstCount[nt]++] = c;
    return 1;
}

void computeFirstOf(char symbol)
{
    int idx = findNonTerminal(symbol);
    if (idx == -1)
        return;

    for (int i = 0; i < prodCount; i++)
    {
        if (grammar[i].lhs != symbol)
            continue;

        char *rhsStart = strstr(grammar[i].rhs, "->") + 2;
        char temp[MAX_LEN];
        strcpy(temp, rhsStart);
        char *token = strtok(temp, "|");

        while (token != NULL)
        {
            if (!isupper(token[0]))
            {
                if (token[0] == 'e' && token[1] == 'p')
                    addToFirst(idx, 'e');
                else
                    addToFirst(idx, token[0]);
            }
            else
            {
                computeFirstOf(token[0]);
                int ntIdx = findNonTerminal(token[0]);
                for (int k = 0; k < firstCount[ntIdx]; k++)
                    addToFirst(idx, FIRST[ntIdx][k]);
            }
            token = strtok(NULL, "|");
        }
    }
}

void computeFirst()
{
    memset(firstCount, 0, sizeof(firstCount));
    collectSymbols();

    for (int i = 0; i < ntCount; i++)
        computeFirstOf(nonTerminals[i]);

    printf("\nFIRST Sets:\n");
    for (int i = 0; i < ntCount; i++)
    {
        printf("FIRST(%c) = { ", nonTerminals[i]);
        for (int j = 0; j < firstCount[i]; j++)
        {
            if (FIRST[i][j] == 'e')
                printf("epsilon");
            else
                printf("%c", FIRST[i][j]);
            if (j < firstCount[i] - 1)
                printf(", ");
        }
        printf(" }\n");
    }
}

int addToFollow(int nt, char c)
{
    for (int i = 0; i < followCount[nt]; i++)
        if (FOLLOW[nt][i] == c)
            return 0;
    FOLLOW[nt][followCount[nt]++] = c;
    return 1;
}

void computeFollow()
{
    memset(followCount, 0, sizeof(followCount));
    addToFollow(0, '$');

    int changed = 1;
    while (changed)
    {
        changed = 0;

        for (int i = 0; i < prodCount; i++)
        {
            char *rhsStart = strstr(grammar[i].rhs, "->") + 2;

            for (int j = 0; rhsStart[j]; j++)
            {
                if (isupper(rhsStart[j]))
                {
                    int idx = findNonTerminal(rhsStart[j]);

                    if (rhsStart[j + 1] && rhsStart[j + 1] != '|')
                    {
                        if (isupper(rhsStart[j + 1]))
                        {
                            int nextIdx = findNonTerminal(rhsStart[j + 1]);
                            for (int k = 0; k < firstCount[nextIdx]; k++)
                                if (FIRST[nextIdx][k] != 'e')
                                    changed |= addToFollow(idx, FIRST[nextIdx][k]);
                        }
                        else if (rhsStart[j + 1] != 'e')
                        {
                            changed |= addToFollow(idx, rhsStart[j + 1]);
                        }
                    }
                    else
                    {
                        int lhsIdx = findNonTerminal(grammar[i].lhs);
                        for (int k = 0; k < followCount[lhsIdx]; k++)
                            changed |= addToFollow(idx, FOLLOW[lhsIdx][k]);
                    }
                }
            }
        }
    }

    printf("\nFOLLOW Sets:\n");
    for (int i = 0; i < ntCount; i++)
    {
        printf("FOLLOW(%c) = { ", nonTerminals[i]);
        for (int j = 0; j < followCount[i]; j++)
        {
            printf("%c", FOLLOW[i][j]);
            if (j < followCount[i] - 1)
                printf(", ");
        }
        printf(" }\n");
    }
}

void constructParsingTable()
{
    for (int i = 0; i < MAX_NONTERM; i++)
        for (int j = 0; j < MAX_TERM; j++)
            parsingTable[i][j][0] = '\0';

    for (int i = 0; i < prodCount; i++)
    {
        char lhs = grammar[i].lhs;
        int ntIdx = findNonTerminal(lhs);

        char *rhsStart = strstr(grammar[i].rhs, "->") + 2;

        if (!isupper(rhsStart[0]))
        {
            if (rhsStart[0] == 'e' && rhsStart[1] == 'p')
            {
                for (int j = 0; j < followCount[ntIdx]; j++)
                {
                    int tIdx = findTerminal(FOLLOW[ntIdx][j]);
                    parsingTable[ntIdx][tIdx][0] = lhs;
                    parsingTable[ntIdx][tIdx][1] = '-';
                    parsingTable[ntIdx][tIdx][2] = '>';
                    strcpy(parsingTable[ntIdx][tIdx] + 3, rhsStart);
                }
            }
            else
            {
                int tIdx = findTerminal(rhsStart[0]);
                parsingTable[ntIdx][tIdx][0] = lhs;
                parsingTable[ntIdx][tIdx][1] = '-';
                parsingTable[ntIdx][tIdx][2] = '>';
                strcpy(parsingTable[ntIdx][tIdx] + 3, rhsStart);
            }
        }
        else
        {
            int rhsIdx = findNonTerminal(rhsStart[0]);
            for (int j = 0; j < firstCount[rhsIdx]; j++)
            {
                if (FIRST[rhsIdx][j] != 'e')
                {
                    int tIdx = findTerminal(FIRST[rhsIdx][j]);
                    parsingTable[ntIdx][tIdx][0] = lhs;
                    parsingTable[ntIdx][tIdx][1] = '-';
                    parsingTable[ntIdx][tIdx][2] = '>';
                    strcpy(parsingTable[ntIdx][tIdx] + 3, rhsStart);
                }
            }
        }
    }
}

void displayParsingTable()
{
    printf("\nPredictive Parsing Table:\n");
    printf("     ");
    for (int i = 0; i < tCount; i++)
        printf("%-15c", terminals[i]);
    printf("\n");

    for (int i = 0; i < ntCount; i++)
    {
        printf("%-5c", nonTerminals[i]);
        for (int j = 0; j < tCount; j++)
        {
            if (parsingTable[i][j][0])
                printf("%-15s", parsingTable[i][j]);
            else
                printf("%-15s", " ");
        }
        printf("\n");
    }
}

void parseInputString()
{
    char input[MAX_LEN];
    printf("\nEnter input string (end with $): ");
    scanf("%s", input);

    top = -1;
    push('$');
    push(grammar[0].lhs);

    printf("\nStack\t\tInput\t\tProduction\n");
    printf("------------------------------------------------------------\n");

    int ip = 0;

    while (top != -1)
    {
        displayStack();
        printf("\t\t%s\t\t", &input[ip]);

        char stackTop = stack[top];
        char currentInput = input[ip];

        if (stackTop == currentInput)
        {
            pop();
            ip++;
            printf("Match %c\n", currentInput);

            if (stackTop == '$' && currentInput == '$')
            {
                printf("\nString Accepted\n");
                return;
            }
        }
        else if (isupper(stackTop))
        {
            int ntIdx = findNonTerminal(stackTop);
            int tIdx = findTerminal(currentInput);

            if (parsingTable[ntIdx][tIdx][0])
            {
                printf("%s\n", parsingTable[ntIdx][tIdx]);
                pop();

                char *rhsStart = strstr(parsingTable[ntIdx][tIdx], "->") + 2;

                if (strcmp(rhsStart, "epsilon") != 0 && rhsStart[0] != 'e')
                {
                    for (int j = strlen(rhsStart) - 1; j >= 0; j--)
                        push(rhsStart[j]);
                }
            }
            else
            {
                printf("Syntax Error\n");
                return;
            }
        }
        else
        {
            printf("Syntax Error\n");
            return;
        }
    }

    printf("\nString Accepted\n");
}

int main()
{
    readGrammar();

    printf("\nOriginal Grammar:\n");
    displayGrammar();

    removeLeftRecursion();
    printf("\nAfter Removing Left Recursion:\n");
    displayGrammar();

    leftFactoring();
    printf("\nAfter Left Factoring:\n");
    displayGrammar();

    computeFirst();
    computeFollow();
    constructParsingTable();
    displayParsingTable();
    parseInputString();

    return 0;
}