/*
 * LL(1) Parser Generator in C
 * Compiler Design Lab - Assignment 6
 *
 * CONVENTION:
 *   - In a STANDALONE production (S->e alone), 'e' = epsilon (empty string)
 *   - In a MIXED production (S->eA), 'e' = real terminal character 'e'
 *   - We use '#' internally to mean epsilon to avoid confusion
 *
 * Input Grammar: S -> Sa | bSc | bSd | e
 * (Here the last alternative 'e' is standalone, so it IS epsilon in logic
 *  BUT 'e' is also the terminal that S directly derives — the assignment
 *  treats them consistently: FIRST(S)={b,e} where e is the terminal 'e'.)
 *
 * SIMPLEST CORRECT APPROACH:
 *   Treat 'e' as ALWAYS the terminal 'e'.
 *   Represent epsilon with '#' internally.
 *   When user types "S->e" alone, we treat S->e as deriving terminal 'e'.
 *   When A->epsilon we write A->#.
 *   After LR removal, A'->epsilon becomes A'-># internally.
 *
 * This matches the ASSIGNMENT exactly: FIRST(S)={b,e} FIRST(S')={a,epsilon}
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

#define MAX_PROD 50
#define MAX_LEN 100
#define MAX_NONTERM 26
#define MAX_TERM 50
#define EPSILON '#' /* internal epsilon symbol */

typedef struct
{
    char lhs;
    char rhs[MAX_LEN];
} Production;
Production grammar[MAX_PROD];
int prodCount = 0;

char FIRST[MAX_NONTERM][MAX_TERM];
char FOLLOW[MAX_NONTERM][MAX_TERM];
char parsingTable[MAX_NONTERM][MAX_TERM][MAX_LEN];

char terminals[MAX_TERM];
int termCount = 0;
char nonTerminals[MAX_NONTERM];
int ntCount = 0;

char stack[MAX_LEN];
int top = -1;
void push(char c) { stack[++top] = c; }
char pop() { return stack[top--]; }
char peek() { return stack[top]; }

/* --- Set helpers ------------------------------------------------ */
void addToSet(char *set, char c)
{
    for (int i = 0; set[i]; i++)
        if (set[i] == c)
            return;
    int l = strlen(set);
    set[l] = c;
    set[l + 1] = '\0';
}
int inSet(char *set, char c)
{
    for (int i = 0; set[i]; i++)
        if (set[i] == c)
            return 1;
    return 0;
}

/* --- Collect symbols -------------------------------------------- */
void collectSymbols()
{
    ntCount = 0;
    termCount = 0;
    memset(nonTerminals, 0, sizeof(nonTerminals));
    memset(terminals, 0, sizeof(terminals));
    for (int i = 0; i < prodCount; i++)
    {
        char nt = grammar[i].lhs;
        if (!inSet(nonTerminals, nt))
            nonTerminals[ntCount++] = nt;
        for (int j = 0; grammar[i].rhs[j]; j++)
        {
            char c = grammar[i].rhs[j];
            if (islower(c) && c != EPSILON)
                if (!inSet(terminals, c))
                    terminals[termCount++] = c;
        }
    }
    if (!inSet(terminals, '$'))
        terminals[termCount++] = '$';
}
int ntIndex(char c) { return c - 'A'; }
int termIndex(char c)
{
    for (int i = 0; i < termCount; i++)
        if (terminals[i] == c)
            return i;
    return -1;
}

/* ================================================================
   READ GRAMMAR
   Input: "S->Sa|bSc|bSd|e"
   We treat 'e' as the terminal letter 'e' (NOT epsilon).
   Epsilon productions created internally use '#'.
   ================================================================ */
void readGrammar()
{
    int n;
    printf("Enter number of productions: ");
    scanf("%d", &n);
    getchar();
    for (int i = 0; i < n; i++)
    {
        char line[MAX_LEN];
        printf("Enter production (e.g. S->Sa|bSc|bSd|e): ");
        fgets(line, MAX_LEN, stdin);
        line[strcspn(line, "\n")] = '\0';
        char lhs = line[0];
        char *arrow = strstr(line, "->");
        if (!arrow)
        {
            printf("Bad format!\n");
            i--;
            continue;
        }
        char *rhsPart = arrow + 2;
        char *tok = strtok(rhsPart, "|");
        while (tok)
        {
            grammar[prodCount].lhs = lhs;
            strcpy(grammar[prodCount].rhs, tok);
            prodCount++;
            tok = strtok(NULL, "|");
        }
    }
}
void displayGrammar()
{
    for (int i = 0; i < prodCount; i++)
    {
        if (strcmp(grammar[i].rhs, "#") == 0)
            printf("  %c -> epsilon\n", grammar[i].lhs);
        else
            printf("  %c -> %s\n", grammar[i].lhs, grammar[i].rhs);
    }
}

/* ================================================================
   REMOVE IMMEDIATE LEFT RECURSION
   A->Aalpha|beta  =>  A->betaA'  A'->alphaA'|#
   ================================================================ */
void removeLeftRecursion()
{
    Production ng[MAX_PROD];
    int nc = 0;
    int usedPrimes[26] = {0}; // Track which primes are already used

    for (int nt = 0; nt < 26; nt++)
    {
        char A = 'A' + nt;
        char alphas[MAX_PROD][MAX_LEN];
        int aC = 0;
        char betas[MAX_PROD][MAX_LEN];
        int bC = 0;
        int found = 0;

        for (int i = 0; i < prodCount; i++)
        {
            if (grammar[i].lhs == A)
            {
                found = 1;
                if (grammar[i].rhs[0] == A)
                    strcpy(alphas[aC++], grammar[i].rhs + 1);
                else
                    strcpy(betas[bC++], grammar[i].rhs);
            }
        }

        if (!found)
            continue;

        if (aC == 0)
        {
            // No left recursion for this non-terminal
            for (int i = 0; i < prodCount; i++)
                if (grammar[i].lhs == A)
                    ng[nc++] = grammar[i];
        }
        else
        {
            // Has left recursion, need A'
            // Find next available prime symbol
            char prime = 'A';
            for (int i = 0; i < 26; i++)
            {
                if (!usedPrimes[i])
                {
                    // Check if this letter is already used as a non-terminal in original grammar
                    int alreadyUsed = 0;
                    for (int j = 0; j < prodCount; j++)
                    {
                        if (grammar[j].lhs == ('A' + i))
                        {
                            alreadyUsed = 1;
                            break;
                        }
                    }
                    // Also check in new grammar being built
                    for (int j = 0; j < nc; j++)
                    {
                        if (ng[j].lhs == ('A' + i))
                        {
                            alreadyUsed = 1;
                            break;
                        }
                    }
                    if (!alreadyUsed)
                    {
                        prime = 'A' + i;
                        usedPrimes[i] = 1;
                        break;
                    }
                }
            }

            // A -> beta A'
            for (int b = 0; b < bC; b++)
            {
                ng[nc].lhs = A;
                sprintf(ng[nc].rhs, "%s%c", betas[b], prime);
                nc++;
            }

            // A' -> alpha A' | #
            for (int a = 0; a < aC; a++)
            {
                ng[nc].lhs = prime;
                sprintf(ng[nc].rhs, "%s%c", alphas[a], prime);
                nc++;
            }
            ng[nc].lhs = prime;
            strcpy(ng[nc].rhs, "#");
            nc++;
        }
    }

    prodCount = nc;
    memcpy(grammar, ng, sizeof(ng));
}
/* ================================================================
   LEFT FACTORING
   ================================================================ */
void leftFactoring()
{
    Production ng[MAX_PROD];
    int nc = 0;
    int changed = 1;

    while (changed)
    {
        changed = 0;
        for (int nt = 0; nt < 26; nt++)
        {
            char A = 'A' + nt;
            char prods[MAX_PROD][MAX_LEN];
            int pC = 0;
            int found = 0;

            for (int i = 0; i < prodCount; i++)
                if (grammar[i].lhs == A)
                {
                    strcpy(prods[pC++], grammar[i].rhs);
                    found = 1;
                }
            if (!found || pC < 2)
                continue;

            int bestLen = 0, bestI = -1, bestJ = -1;

            for (int i = 0; i < pC - 1; i++)
            {
                // Skip epsilon productions
                if (strcmp(prods[i], "#") == 0)
                    continue;

                for (int j = i + 1; j < pC; j++)
                {
                    // Skip epsilon productions
                    if (strcmp(prods[j], "#") == 0)
                        continue;

                    int maxCmp = strlen(prods[i]);
                    if (strlen(prods[j]) < maxCmp)
                        maxCmp = strlen(prods[j]);

                    // Find actual common prefix length
                    int commonLen = 0;
                    while (commonLen < maxCmp &&
                           prods[i][commonLen] == prods[j][commonLen])
                    {
                        commonLen++;
                    }

                    // Only consider it if there's at least 1 character in common
                    if (commonLen > 0 && commonLen > bestLen)
                    {
                        bestLen = commonLen;
                        bestI = i;
                        bestJ = j;
                    }
                }
            }

            if (bestLen == 0)
                continue;

            changed = 1;

            // Find prime symbol
            char prime = 'A';
            int used[26] = {0};
            for (int i = 0; i < prodCount; i++)
                if (isupper(grammar[i].lhs))
                    used[grammar[i].lhs - 'A'] = 1;
            for (int i = 0; i < 26; i++)
                if (!used[i])
                {
                    prime = 'A' + i;
                    break;
                }

            // Rebuild grammar with factoring
            for (int i = 0; i < prodCount; i++)
                if (grammar[i].lhs != A)
                    ng[nc++] = grammar[i];

            // Group all productions with the common prefix
            char prefix[MAX_LEN];
            strncpy(prefix, prods[bestI], bestLen);
            prefix[bestLen] = '\0';

            // A -> prefix A'
            ng[nc].lhs = A;
            sprintf(ng[nc].rhs, "%s%c", prefix, prime);
            nc++;

            // Create A' productions
            for (int i = 0; i < pC; i++)
            {
                if (strncmp(prods[i], prefix, bestLen) == 0)
                {
                    // This production has the common prefix
                    ng[nc].lhs = prime;
                    strcpy(ng[nc].rhs, prods[i] + bestLen);
                    if (strlen(ng[nc].rhs) == 0)
                        strcpy(ng[nc].rhs, "#");
                    nc++;
                }
                else
                {
                    // This production doesn't have the prefix, keep as-is
                    ng[nc].lhs = A;
                    strcpy(ng[nc].rhs, prods[i]);
                    nc++;
                }
            }

            prodCount = nc;
            memcpy(grammar, ng, sizeof(ng));
            break;
        }
    }
}
/* ================================================================
   FIRST sets (fixed-point iteration)
   '#' = epsilon
   ================================================================ */
void computeFirst()
{
    for (int i = 0; i < MAX_NONTERM; i++)
        memset(FIRST[i], 0, MAX_TERM);
    int changed = 1;
    while (changed)
    {
        changed = 0;
        for (int i = 0; i < prodCount; i++)
        {
            char A = grammar[i].lhs;
            char *rhs = grammar[i].rhs;
            int ai = ntIndex(A);
            int oldLen = strlen(FIRST[ai]);
            if (strcmp(rhs, "#") == 0)
            {
                addToSet(FIRST[ai], EPSILON);
            }
            else
            {
                int allEps = 1;
                for (int j = 0; rhs[j]; j++)
                {
                    char sym = rhs[j];
                    if (isupper(sym))
                    {
                        int si = ntIndex(sym);
                        for (int k = 0; FIRST[si][k]; k++)
                            if (FIRST[si][k] != EPSILON)
                                addToSet(FIRST[ai], FIRST[si][k]);
                        if (!inSet(FIRST[si], EPSILON))
                        {
                            allEps = 0;
                            break;
                        }
                    }
                    else
                    {
                        addToSet(FIRST[ai], sym);
                        allEps = 0;
                        break;
                    }
                }
                if (allEps)
                    addToSet(FIRST[ai], EPSILON);
            }
            if ((int)strlen(FIRST[ai]) != oldLen)
                changed = 1;
        }
    }
}

/* ================================================================
   FOLLOW sets
   ================================================================ */
void computeFollow()
{
    for (int i = 0; i < MAX_NONTERM; i++)
        memset(FOLLOW[i], 0, MAX_TERM);
    addToSet(FOLLOW[ntIndex(grammar[0].lhs)], '$');
    int changed = 1;
    while (changed)
    {
        changed = 0;
        for (int i = 0; i < prodCount; i++)
        {
            char B = grammar[i].lhs;
            char *rhs = grammar[i].rhs;
            int len = strlen(rhs);
            for (int j = 0; j < len; j++)
            {
                char A = rhs[j];
                if (!isupper(A))
                    continue;
                int ai = ntIndex(A), bi = ntIndex(B), oldLen = strlen(FOLLOW[ai]);
                int allEps = 1;
                for (int k = j + 1; k < len; k++)
                {
                    char beta = rhs[k];
                    if (isupper(beta))
                    {
                        int bi2 = ntIndex(beta);
                        for (int m = 0; FIRST[bi2][m]; m++)
                            if (FIRST[bi2][m] != EPSILON)
                                addToSet(FOLLOW[ai], FIRST[bi2][m]);
                        if (!inSet(FIRST[bi2], EPSILON))
                        {
                            allEps = 0;
                            break;
                        }
                    }
                    else
                    {
                        addToSet(FOLLOW[ai], beta);
                        allEps = 0;
                        break;
                    }
                }
                if (allEps)
                    for (int m = 0; FOLLOW[bi][m]; m++)
                        addToSet(FOLLOW[ai], FOLLOW[bi][m]);
                if ((int)strlen(FOLLOW[ai]) != oldLen)
                    changed = 1;
            }
        }
    }
}

/* ================================================================
   PARSING TABLE
   ================================================================ */
void firstOfString(char *str, char *result)
{
    result[0] = '\0';
    if (strcmp(str, "#") == 0)
    {
        addToSet(result, EPSILON);
        return;
    }
    int allEps = 1;
    for (int i = 0; str[i]; i++)
    {
        char c = str[i];
        if (isupper(c))
        {
            int ci = ntIndex(c);
            for (int k = 0; FIRST[ci][k]; k++)
                if (FIRST[ci][k] != EPSILON)
                    addToSet(result, FIRST[ci][k]);
            if (!inSet(FIRST[ci], EPSILON))
            {
                allEps = 0;
                break;
            }
        }
        else
        {
            addToSet(result, c);
            allEps = 0;
            break;
        }
    }
    if (allEps)
        addToSet(result, EPSILON);
}
void constructParsingTable()
{
    for (int i = 0; i < MAX_NONTERM; i++)
        for (int j = 0; j < MAX_TERM; j++)
            memset(parsingTable[i][j], 0, MAX_LEN);
    for (int i = 0; i < prodCount; i++)
    {
        char A = grammar[i].lhs;
        char *rhs = grammar[i].rhs;
        int ai = ntIndex(A);
        char fa[MAX_TERM] = {0};
        firstOfString(rhs, fa);
        for (int k = 0; fa[k]; k++)
        {
            char a = fa[k];
            if (a == EPSILON)
                continue;
            int ti = termIndex(a);
            if (ti < 0)
            {
                terminals[termCount++] = a;
                ti = termCount - 1;
            }
            if (parsingTable[ai][ti][0])
                printf("  [Conflict at M[%c,%c]]\n", A, a);
            snprintf(parsingTable[ai][ti], MAX_LEN, "%c->%s", A, rhs);
        }
        if (inSet(fa, EPSILON))
        {
            for (int k = 0; FOLLOW[ai][k]; k++)
            {
                char b = FOLLOW[ai][k];
                int ti = termIndex(b);
                if (ti < 0)
                {
                    terminals[termCount++] = b;
                    ti = termCount - 1;
                }
                if (parsingTable[ai][ti][0])
                    printf("  [Conflict at M[%c,%c]]\n", A, b);
                snprintf(parsingTable[ai][ti], MAX_LEN, "%c->%s", A, rhs);
            }
        }
    }
}
void displayFirstFollow()
{
    printf("\nFIRST Sets:\n");
    for (int i = 0; i < ntCount; i++)
    {
        char A = nonTerminals[i];
        printf("  FIRST(%c)  = { ", A);
        char *fs = FIRST[ntIndex(A)];
        for (int j = 0; fs[j]; j++)
        {
            if (fs[j] == EPSILON)
                printf("epsilon");
            else
                printf("%c", fs[j]);
            if (fs[j + 1])
                printf(", ");
        }
        printf(" }\n");
    }
    printf("\nFOLLOW Sets:\n");
    for (int i = 0; i < ntCount; i++)
    {
        char A = nonTerminals[i];
        printf("  FOLLOW(%c) = { ", A);
        char *fl = FOLLOW[ntIndex(A)];
        for (int j = 0; fl[j]; j++)
        {
            printf("%c", fl[j]);
            if (fl[j + 1])
                printf(", ");
        }
        printf(" }\n");
    }
}
void displayParsingTable()
{
    printf("\nPredictive Parsing Table:\n");
    printf("   %-5s", "");
    for (int t = 0; t < termCount; t++)
        printf("  %-12c", terminals[t]);
    printf("\n   ");
    for (int t = 0; t <= termCount; t++)
        printf("-------------");
    printf("\n");
    for (int i = 0; i < ntCount; i++)
    {
        char A = nonTerminals[i];
        int ai = ntIndex(A);
        printf("  %c |", A);
        for (int t = 0; t < termCount; t++)
        {
            if (parsingTable[ai][t][0])
            {
                /* replace internal '#' with 'epsilon' for display */
                char disp[MAX_LEN];
                strcpy(disp, parsingTable[ai][t]);
                char *hp = strchr(disp, '#');
                if (hp)
                {
                    memmove(hp + 7, hp + 1, strlen(hp));
                    memcpy(hp, "epsilon", 7);
                }
                printf("  %-12s", disp);
            }
            else
                printf("  %-12s", "");
        }
        printf("\n");
    }
}

/* ================================================================
   LL(1) PARSER
   ================================================================ */
void parseInputString()
{
    char input[MAX_LEN];
    printf("\nEnter input string (end with $): ");
    scanf("%s", input);
    top = -1;
    push('$');
    push(grammar[0].lhs);
    int ip = 0;
    printf("\nParsing Trace:\n");
    printf("%-22s %-16s %s\n", "Stack", "Input", "Production/Action");
    printf("-----------------------------------------------------------\n");
    while (top >= 0)
    {
        char stackStr[MAX_LEN] = {0};
        for (int i = 0; i <= top; i++)
            stackStr[i] = stack[i];
        printf("%-22s %-16s ", stackStr, input + ip);
        char X = peek(), a = input[ip];
        if (X == '$' && a == '$')
        {
            printf("Match $\n");
            break;
        }
        if (X == a)
        {
            pop();
            ip++;
            printf("Match %c\n", a);
        }
        else if (isupper(X))
        {
            int xi = ntIndex(X), ti = termIndex(a);
            if (ti < 0 || parsingTable[xi][ti][0] == '\0')
            {
                printf("Syntax Error at symbol '%c'\n", a);
                return;
            }
            char *prod = parsingTable[xi][ti];
            /* Display with epsilon label */
            char disp[MAX_LEN];
            strcpy(disp, prod);
            char *hp = strchr(disp, '#');
            if (hp)
            {
                memmove(hp + 7, hp + 1, strlen(hp));
                memcpy(hp, "epsilon", 7);
            }
            printf("%s\n", disp);
            char *arrowPos = strstr(prod, "->");
            char *rhs = arrowPos + 2;
            pop();
            if (strcmp(rhs, "#") != 0)
            {
                int rhsLen = strlen(rhs);
                for (int k = rhsLen - 1; k >= 0; k--)
                    push(rhs[k]);
            }
        }
        else
        {
            printf("Syntax Error: expected '%c' got '%c'\n", X, a);
            return;
        }
    }
    printf("\nString Accepted!\n");
}

/* ================================================================
   MAIN
   ================================================================ */
int main()
{
    printf("==============================================\n");
    printf("        LL(1) Parser Generator in C          \n");
    printf("==============================================\n");
    readGrammar();
    printf("\nOriginal Grammar:\n");
    displayGrammar();
    removeLeftRecursion();
    collectSymbols();
    printf("\nAfter Removing Left Recursion:\n");
    displayGrammar();
    leftFactoring();
    collectSymbols();
    printf("\nAfter Left Factoring:\n");
    displayGrammar();
    computeFirst();
    computeFollow();
    displayFirstFollow();
    constructParsingTable();
    displayParsingTable();
    parseInputString();
    return 0;
}