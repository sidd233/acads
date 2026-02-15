#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

// Assuming e as a terminal not as epsilon. ALso the program dosn't consider spaces.
#define MAX_PROD 200
#define MAX_LEN 200
#define MAX_TERM 128
#define MAX_NONTERM 26

// Internal epsilon marker (NOT the terminal 'e')
#define EPS '@'
typedef struct
{
    char lhs;          // Non-terminal (A..Z)
    char rhs[MAX_LEN]; // Sequence of symbols (terminals/nonterminals), EPS allowed as single char
} Production;

static Production grammar[MAX_PROD];
static int prodCount = 0;

// Non-terminal alias for printing primes (e.g., Z represents S')
static char aliasOf[256][16]; // aliasOf['Z']="S'" etc.

// Terminals list for table columns
static char terminals[MAX_TERM];
static int termCount = 0;

// Sets as boolean tables over ASCII
static int FIRSTset[256][256];
static int FOLLOWset[256][256];

// Parsing table: for each [NonTerm][Terminal] store RHS string; empty if none
static char parsingTable[256][256][MAX_LEN];

// Stack for parsing
static char stackArr[MAX_LEN];
static int top = -1;

/* -----------------------------
   Stack utilities
----------------------------- */
static void push(char c) { stackArr[++top] = c; }
static char popStack(void) { return stackArr[top--]; }
static char peekStack(void) { return stackArr[top]; }

static void displayStack(void)
{
    for (int i = 0; i <= top; i++)
    {
        char c = stackArr[i];
        if (aliasOf[(unsigned char)c][0])
            printf("%s", aliasOf[(unsigned char)c]);
        else
            printf("%c", c);
    }
}

/* -----------------------------
   Helper utilities
----------------------------- */
static int isNonTerm(char c) { return (c >= 'A' && c <= 'Z'); }
static int isEpsStr(const char *s)
{
    return (!strcmp(s, "epsilon") || !strcmp(s, "eps") || !strcmp(s, "@") || !strcmp(s, "#"));
}

static void printSymbol(char c)
{
    if (c == EPS)
    {
        printf("epsilon");
        return;
    }
    if (aliasOf[(unsigned char)c][0])
    {
        printf("%s", aliasOf[(unsigned char)c]);
        return;
    }
    printf("%c", c);
}

static void printRHS(const char *rhs)
{
    if (rhs[0] == EPS && rhs[1] == '\0')
    {
        printf("epsilon");
        return;
    }
    for (int i = 0; rhs[i]; i++)
    {
        if (rhs[i] == EPS)
            printf("epsilon");
        else
            printSymbol(rhs[i]);
    }
}

static void addProduction(char lhs, const char *rhs)
{
    if (prodCount >= MAX_PROD)
    {
        fprintf(stderr, "Too many productions.\n");
        exit(1);
    }
    grammar[prodCount].lhs = lhs;
    strncpy(grammar[prodCount].rhs, rhs, MAX_LEN - 1);
    grammar[prodCount].rhs[MAX_LEN - 1] = '\0';
    prodCount++;
}

static void rebuildTerminals(void)
{
    int seen[256] = {0};
    termCount = 0;

    // Collect terminals from RHS
    for (int i = 0; i < prodCount; i++)
    {
        for (int j = 0; grammar[i].rhs[j]; j++)
        {
            unsigned char c = (unsigned char)grammar[i].rhs[j];
            if (c == (unsigned char)EPS)
                continue;
            if (!isNonTerm((char)c) && c != '|')
            {
                if (!seen[c])
                {
                    terminals[termCount++] = (char)c;
                    seen[c] = 1;
                }
            }
        }
    }
    // Ensure '$' is present
    if (!seen[(unsigned char)'$'])
        terminals[termCount++] = '$';

    // Sort terminals for pretty printing
    for (int i = 0; i < termCount; i++)
    {
        for (int j = i + 1; j < termCount; j++)
        {
            if (terminals[j] < terminals[i])
            {
                char t = terminals[i];
                terminals[i] = terminals[j];
                terminals[j] = t;
            }
        }
    }
}

static void clearAllSets(void)
{
    memset(FIRSTset, 0, sizeof(FIRSTset));
    memset(FOLLOWset, 0, sizeof(FOLLOWset));
}

static void clearParsingTable(void)
{
    for (int A = 0; A < 256; A++)
        for (int t = 0; t < 256; t++)
            parsingTable[A][t][0] = '\0';
}

static int addToSet(int setTable[256][256], char X, char a)
{
    if (!setTable[(unsigned char)X][(unsigned char)a])
    {
        setTable[(unsigned char)X][(unsigned char)a] = 1;
        return 1;
    }
    return 0;
}

static int addSetMinusEps(int setTable[256][256], char dest, int srcSet[256])
{
    int changed = 0;
    for (int c = 0; c < 256; c++)
    {
        if (c == EPS)
            continue;
        if (srcSet[c])
            changed |= addToSet(setTable, dest, (char)c);
    }
    return changed;
}

/* -----------------------------
   Grammar IO
----------------------------- */
static void displayGrammar(void)
{
    // Print grouped by lhs (like A -> ... | ...)
    int printed[256] = {0};

    for (int i = 0; i < prodCount; i++)
    {
        char A = grammar[i].lhs;
        if (printed[(unsigned char)A])
            continue;

        printed[(unsigned char)A] = 1;

        printSymbol(A);
        printf(" -> ");

        int firstAlt = 1;
        for (int j = 0; j < prodCount; j++)
        {
            if (grammar[j].lhs == A)
            {
                if (!firstAlt)
                    printf(" | ");
                printRHS(grammar[j].rhs);
                firstAlt = 0;
            }
        }
        printf("\n");
    }
}

static void parseAndAddLine(const char *lineRaw)
{
    // Expect something like: S->Sa|bSc|epsilon
    char line[MAX_LEN];
    strncpy(line, lineRaw, MAX_LEN - 1);
    line[MAX_LEN - 1] = '\0';

    // remove spaces
    char tmp[MAX_LEN];
    int k = 0;
    for (int i = 0; line[i] && k < MAX_LEN - 1; i++)
    {
        if (!isspace((unsigned char)line[i]))
            tmp[k++] = line[i];
    }
    tmp[k] = '\0';

    if ((int)strlen(tmp) < 4 || tmp[1] != '-' || tmp[2] != '>')
    {
        fprintf(stderr, "Invalid production format: %s\n", tmp);
        exit(1);
    }

    char lhs = tmp[0];
    if (!isNonTerm(lhs))
    {
        fprintf(stderr, "LHS must be a single uppercase non-terminal: %s\n", tmp);
        exit(1);
    }

    const char *rhsAll = tmp + 3;

    // split by '|'
    char buf[MAX_LEN];
    int bi = 0;
    for (int i = 0;; i++)
    {
        char c = rhsAll[i];
        if (c == '|' || c == '\0')
        {
            buf[bi] = '\0';

            if (buf[0] == '\0')
            {
                // empty alternative treated as epsilon
                char epsRhs[2] = {EPS, '\0'};
                addProduction(lhs, epsRhs);
            }
            else if (isEpsStr(buf))
            {
                char epsRhs[2] = {EPS, '\0'};
                addProduction(lhs, epsRhs);
            }
            else
            {
                addProduction(lhs, buf);
            }

            bi = 0;
            if (c == '\0')
                break;
        }
        else
        {
            if (bi < MAX_LEN - 1)
                buf[bi++] = c;
        }
    }
}

static void readGrammar(void)
{
    int n;
    printf("Enter number of productions: ");
    if (scanf("%d", &n) != 1)
        exit(1);

    // consume newline
    int ch;
    while ((ch = getchar()) != '\n' && ch != EOF)
    {
    }

    prodCount = 0;
    memset(aliasOf, 0, sizeof(aliasOf));

    for (int i = 0; i < n; i++)
    {
        char line[MAX_LEN];
        printf("Enter production (e.g., S->Sa|bSc|epsilon): ");
        if (!fgets(line, sizeof(line), stdin))
            exit(1);
        // strip newline
        line[strcspn(line, "\r\n")] = '\0';
        parseAndAddLine(line);
    }

    rebuildTerminals();
}

/* -----------------------------
   Fresh new non-terminal selection
----------------------------- */
static char newNonTerminal(void)
{
    // Find unused uppercase letter
    int used[256] = {0};
    for (int i = 0; i < prodCount; i++)
        used[(unsigned char)grammar[i].lhs] = 1;
    for (int i = 0; i < prodCount; i++)
    {
        for (int j = 0; grammar[i].rhs[j]; j++)
        {
            char c = grammar[i].rhs[j];
            if (isNonTerm(c))
                used[(unsigned char)c] = 1;
        }
    }
    for (char c = 'A'; c <= 'Z'; c++)
    {
        if (!used[(unsigned char)c])
            return c;
    }
    fprintf(stderr, "No free non-terminals left (A-Z exhausted).\n");
    exit(1);
}

/* -----------------------------
   Task 1: Remove immediate left recursion
----------------------------- */
static void removeLeftRecursion(void)
{
    // For each non-terminal A:
    // Partition A-productions into:
    //   A -> Aα  (alpha list)
    //   A -> β   (beta list)
    // Transform if alpha exists.

    int i = 0;
    while (i < prodCount)
    {
        char A = grammar[i].lhs;

        // collect indices for this A
        int idx[MAX_PROD], cnt = 0;
        for (int j = 0; j < prodCount; j++)
            if (grammar[j].lhs == A)
                idx[cnt++] = j;

        // alpha/beta rhs arrays
        char alpha[MAX_PROD][MAX_LEN];
        int aCnt = 0;
        char beta[MAX_PROD][MAX_LEN];
        int bCnt = 0;

        for (int k = 0; k < cnt; k++)
        {
            const char *rhs = grammar[idx[k]].rhs;
            if (rhs[0] == A)
            {
                // alpha is rhs[1..]
                if (rhs[1] == '\0')
                {
                    // A -> A (alpha empty) treat as epsilon alpha
                    alpha[aCnt][0] = EPS;
                    alpha[aCnt][1] = '\0';
                }
                else
                {
                    strncpy(alpha[aCnt], rhs + 1, MAX_LEN - 1);
                    alpha[aCnt][MAX_LEN - 1] = '\0';
                }
                aCnt++;
            }
            else
            {
                strncpy(beta[bCnt], rhs, MAX_LEN - 1);
                beta[bCnt][MAX_LEN - 1] = '\0';
                bCnt++;
            }
        }

        if (aCnt > 0)
        {
            if (bCnt == 0)
            {
                // If no beta, grammar is problematic for immediate LR removal
                // We can add epsilon as beta to proceed.
                beta[bCnt][0] = EPS;
                beta[bCnt][1] = '\0';
                bCnt++;
            }

            char Aprime = newNonTerminal();

            // alias Aprime as A'
            char alias[16];
            snprintf(alias, sizeof(alias), "%c'", A);
            strncpy(aliasOf[(unsigned char)Aprime], alias, sizeof(aliasOf[0]) - 1);

            // Remove all productions with lhs A from grammar by rebuilding list
            Production newG[MAX_PROD];
            int newCount = 0;
            for (int j = 0; j < prodCount; j++)
            {
                if (grammar[j].lhs != A)
                    newG[newCount++] = grammar[j];
            }
            // write back
            memcpy(grammar, newG, sizeof(Production) * newCount);
            prodCount = newCount;

            // Add A -> beta Aprime
            for (int k = 0; k < bCnt; k++)
            {
                char rhsNew[MAX_LEN] = {0};
                if (beta[k][0] == EPS && beta[k][1] == '\0')
                {
                    // A -> Aprime
                    rhsNew[0] = Aprime;
                    rhsNew[1] = '\0';
                }
                else
                {
                    snprintf(rhsNew, sizeof(rhsNew), "%s%c", beta[k], Aprime);
                }
                addProduction(A, rhsNew);
            }

            // Add Aprime -> alpha Aprime
            for (int k = 0; k < aCnt; k++)
            {
                char rhsNew[MAX_LEN] = {0};
                if (alpha[k][0] == EPS && alpha[k][1] == '\0')
                {
                    // alpha is epsilon => Aprime -> Aprime (useless); skip
                    // Better: keep only epsilon production below
                }
                else
                {
                    snprintf(rhsNew, sizeof(rhsNew), "%s%c", alpha[k], Aprime);
                    addProduction(Aprime, rhsNew);
                }
            }

            // Add Aprime -> epsilon
            char epsRhs[2] = {EPS, '\0'};
            addProduction(Aprime, epsRhs);

            rebuildTerminals();
            // Restart scan because grammar changed
            i = 0;
            continue;
        }

        // move i forward to next different lhs
        while (i < prodCount && grammar[i].lhs == A)
            i++;
    }
}

/* -----------------------------
   Task 2: Left factoring
----------------------------- */
static int longestCommonPrefix(const char *a, const char *b)
{
    int i = 0;
    while (a[i] && b[i] && a[i] == b[i] && a[i] != EPS && b[i] != EPS)
        i++;
    return i;
}

static int leftFactorOnceFor(char A)
{
    // Find the best (longest) common prefix among productions of A
    int idx[MAX_PROD], cnt = 0;
    for (int i = 0; i < prodCount; i++)
        if (grammar[i].lhs == A)
            idx[cnt++] = i;
    if (cnt < 2)
        return 0;

    int bestLen = 0;
    char bestPrefix[MAX_LEN] = {0};

    for (int i = 0; i < cnt; i++)
    {
        for (int j = i + 1; j < cnt; j++)
        {
            int l = longestCommonPrefix(grammar[idx[i]].rhs, grammar[idx[j]].rhs);
            if (l > bestLen)
            {
                bestLen = l;
                strncpy(bestPrefix, grammar[idx[i]].rhs, l);
                bestPrefix[l] = '\0';
            }
        }
    }
    if (bestLen <= 0)
        return 0;

    // Create new non-terminal X for the factored part
    char X = newNonTerminal();

    // Rewrite:
    // A -> prefix X
    // X -> suffixes...
    // for all A-productions that start with prefix

    // Collect suffixes for those productions
    char suffixes[MAX_PROD][MAX_LEN];
    int sCnt = 0;

    // Rebuild grammar excluding the matching productions
    Production newG[MAX_PROD];
    int newCount = 0;

    int removedAny = 0;
    for (int i = 0; i < prodCount; i++)
    {
        if (grammar[i].lhs == A && strncmp(grammar[i].rhs, bestPrefix, bestLen) == 0)
        {
            removedAny = 1;
            const char *old = grammar[i].rhs;
            const char *suf = old + bestLen;
            if (*suf == '\0')
            {
                suffixes[sCnt][0] = EPS;
                suffixes[sCnt][1] = '\0';
            }
            else
            {
                strncpy(suffixes[sCnt], suf, MAX_LEN - 1);
                suffixes[sCnt][MAX_LEN - 1] = '\0';
            }
            sCnt++;
        }
        else
        {
            newG[newCount++] = grammar[i];
        }
    }
    if (!removedAny || sCnt < 2)
        return 0;

    memcpy(grammar, newG, sizeof(Production) * newCount);
    prodCount = newCount;

    // Add factored A -> prefix X
    char rhsNew[MAX_LEN] = {0};
    snprintf(rhsNew, sizeof(rhsNew), "%s%c", bestPrefix, X);
    addProduction(A, rhsNew);

    // Add X -> suffixes
    for (int i = 0; i < sCnt; i++)
        addProduction(X, suffixes[i]);

    rebuildTerminals();
    return 1;
}

static void leftFactoring(void)
{
    int changed = 1;
    while (changed)
    {
        changed = 0;

        // Get current set of non-terminals
        int seen[256] = {0};
        char nts[64];
        int ntc = 0;

        for (int i = 0; i < prodCount; i++)
        {
            char A = grammar[i].lhs;
            if (!seen[(unsigned char)A])
            {
                nts[ntc++] = A;
                seen[(unsigned char)A] = 1;
            }
        }

        for (int i = 0; i < ntc; i++)
        {
            char A = nts[i];
            if (leftFactorOnceFor(A))
            {
                changed = 1;
                break; // restart scanning after a successful factoring
            }
        }
    }
}

/* -----------------------------
   FIRST/FOLLOW helpers
----------------------------- */
static int firstOfStringToSet(const char *alpha, int outSet[256])
{
    // outSet filled with FIRST(alpha); returns whether epsilon is in FIRST(alpha)
    memset(outSet, 0, sizeof(int) * 256);

    if (alpha[0] == '\0')
    {
        outSet[(unsigned char)EPS] = 1;
        return 1;
    }

    int allCanBeEps = 1;

    for (int i = 0; alpha[i]; i++)
    {
        char X = alpha[i];

        if (X == EPS)
        {
            outSet[(unsigned char)EPS] = 1;
            return 1;
        }

        if (!isNonTerm(X))
        {
            outSet[(unsigned char)X] = 1;
            allCanBeEps = 0;
            break;
        }

        // X is non-terminal
        for (int c = 0; c < 256; c++)
        {
            if (c == EPS)
                continue;
            if (FIRSTset[(unsigned char)X][c])
                outSet[c] = 1;
        }

        if (!FIRSTset[(unsigned char)X][(unsigned char)EPS])
        {
            allCanBeEps = 0;
            break;
        }
    }

    if (allCanBeEps)
        outSet[(unsigned char)EPS] = 1;
    return outSet[(unsigned char)EPS];
}

/* -----------------------------
   Task 3: Compute FIRST
----------------------------- */
static void computeFirst(void)
{
    clearAllSets();

    // Initialize FIRST of terminals (optional; we only store for nonterminals, but keeping is fine)
    for (int t = 0; t < termCount; t++)
    {
        char a = terminals[t];
        FIRSTset[(unsigned char)a][(unsigned char)a] = 1;
    }
    FIRSTset[(unsigned char)EPS][(unsigned char)EPS] = 1;

    int changed = 1;
    while (changed)
    {
        changed = 0;

        for (int i = 0; i < prodCount; i++)
        {
            char A = grammar[i].lhs;
            const char *rhs = grammar[i].rhs;

            int firstAlpha[256];
            firstOfStringToSet(rhs, firstAlpha);

            // Add FIRST(rhs) - {eps} to FIRST(A)
            changed |= addSetMinusEps(FIRSTset, A, firstAlpha);

            // If eps in FIRST(rhs), add eps to FIRST(A)
            if (firstAlpha[(unsigned char)EPS])
                changed |= addToSet(FIRSTset, A, EPS);
        }
    }

    printf("\nFIRST Sets:\n");
    // Print FIRST for each non-terminal present
    int seen[256] = {0};
    for (int i = 0; i < prodCount; i++)
    {
        char A = grammar[i].lhs;
        if (seen[(unsigned char)A])
            continue;
        seen[(unsigned char)A] = 1;

        printf("FIRST ( ");
        printSymbol(A);
        printf(" ) = { ");

        int firstPrinted = 0;
        for (int c = 0; c < 256; c++)
        {
            if (FIRSTset[(unsigned char)A][c])
            {
                if (firstPrinted)
                    printf(" , ");
                if ((char)c == EPS)
                    printf("epsilon");
                else
                    printSymbol((char)c);
                firstPrinted = 1;
            }
        }
        printf(" }\n");
    }
}

/* -----------------------------
   Task 3: Compute FOLLOW
----------------------------- */
static void computeFollow(void)
{
    // start symbol is grammar[0].lhs as in PDF skeleton
    char start = grammar[0].lhs;
    addToSet(FOLLOWset, start, '$');

    int changed = 1;
    while (changed)
    {
        changed = 0;

        for (int i = 0; i < prodCount; i++)
        {
            char A = grammar[i].lhs;
            const char *rhs = grammar[i].rhs;
            int n = (int)strlen(rhs);

            for (int p = 0; p < n; p++)
            {
                char B = rhs[p];
                if (!isNonTerm(B))
                    continue;

                // beta = rhs[p+1..]
                char beta[MAX_LEN];
                strncpy(beta, rhs + p + 1, MAX_LEN - 1);
                beta[MAX_LEN - 1] = '\0';

                int firstBeta[256];
                int betaHasEps = firstOfStringToSet(beta, firstBeta);

                // FOLLOW(B) += FIRST(beta) - {eps}
                for (int c = 0; c < 256; c++)
                {
                    if (c == EPS)
                        continue;
                    if (firstBeta[c])
                        changed |= addToSet(FOLLOWset, B, (char)c);
                }

                // If beta can be epsilon OR beta is empty: FOLLOW(B) += FOLLOW(A)
                if (betaHasEps || beta[0] == '\0')
                {
                    for (int c = 0; c < 256; c++)
                    {
                        if (FOLLOWset[(unsigned char)A][c])
                            changed |= addToSet(FOLLOWset, B, (char)c);
                    }
                }
            }
        }
    }

    printf("\nFOLLOW Sets:\n");
    int seen[256] = {0};
    for (int i = 0; i < prodCount; i++)
    {
        char A = grammar[i].lhs;
        if (seen[(unsigned char)A])
            continue;
        seen[(unsigned char)A] = 1;

        printf("FOLLOW ( ");
        printSymbol(A);
        printf(" ) = { ");

        int firstPrinted = 0;
        for (int c = 0; c < 256; c++)
        {
            if (FOLLOWset[(unsigned char)A][c])
            {
                if (firstPrinted)
                    printf(" , ");
                printSymbol((char)c);
                firstPrinted = 1;
            }
        }
        printf(" }\n");
    }
}

/* -----------------------------
   Task 4: Construct parsing table
----------------------------- */
static void constructParsingTable(void)
{
    clearParsingTable();

    int conflict = 0;

    for (int i = 0; i < prodCount; i++)
    {
        char A = grammar[i].lhs;
        const char *alpha = grammar[i].rhs;

        int firstAlpha[256];
        int hasEps = firstOfStringToSet(alpha, firstAlpha);

        // For each terminal a in FIRST(alpha) - {eps}: M[A,a] = A->alpha
        for (int c = 0; c < 256; c++)
        {
            if (c == EPS)
                continue;
            if (firstAlpha[c])
            {
                if (parsingTable[(unsigned char)A][c][0] != '\0' &&
                    strcmp(parsingTable[(unsigned char)A][c], alpha) != 0)
                {
                    conflict = 1;
                }
                else
                {
                    strncpy(parsingTable[(unsigned char)A][c], alpha, MAX_LEN - 1);
                    parsingTable[(unsigned char)A][c][MAX_LEN - 1] = '\0';
                }
            }
        }

        // If eps in FIRST(alpha): for each b in FOLLOW(A), M[A,b]=A->alpha
        if (hasEps)
        {
            for (int c = 0; c < 256; c++)
            {
                if (FOLLOWset[(unsigned char)A][c])
                {
                    if (parsingTable[(unsigned char)A][c][0] != '\0' &&
                        strcmp(parsingTable[(unsigned char)A][c], alpha) != 0)
                    {
                        conflict = 1;
                    }
                    else
                    {
                        strncpy(parsingTable[(unsigned char)A][c], alpha, MAX_LEN - 1);
                        parsingTable[(unsigned char)A][c][MAX_LEN - 1] = '\0';
                    }
                }
            }
        }
    }

    if (conflict)
    {
        printf("\n[Warning] Conflicts detected: grammar may NOT be LL(1).\n");
    }
}

static void displayParsingTable(void)
{
    printf("\nPredictive Parsing Table:\n");

    rebuildTerminals();

    // header
    printf("%-8s", "");
    for (int t = 0; t < termCount; t++)
    {
        printf("%-12c", terminals[t]);
    }
    printf("\n");

    // gather non-terminals
    int seen[256] = {0};
    char nts[64];
    int ntc = 0;
    for (int i = 0; i < prodCount; i++)
    {
        char A = grammar[i].lhs;
        if (!seen[(unsigned char)A])
        {
            nts[ntc++] = A;
            seen[(unsigned char)A] = 1;
        }
    }
    // sort nts
    for (int i = 0; i < ntc; i++)
        for (int j = i + 1; j < ntc; j++)
            if (nts[j] < nts[i])
            {
                char tmp = nts[i];
                nts[i] = nts[j];
                nts[j] = tmp;
            }

    // rows
    for (int i = 0; i < ntc; i++)
    {
        char A = nts[i];
        char rowName[16] = {0};
        if (aliasOf[(unsigned char)A][0])
            snprintf(rowName, sizeof(rowName), "%s", aliasOf[(unsigned char)A]);
        else
            snprintf(rowName, sizeof(rowName), "%c", A);

        printf("%-8s", rowName);

        for (int t = 0; t < termCount; t++)
        {
            char a = terminals[t];
            if (parsingTable[(unsigned char)A][(unsigned char)a][0] == '\0')
            {
                printf("%-12s", "");
            }
            else
            {
                // print "A->rhs" compactly
                char cell[64];
                snprintf(cell, sizeof(cell), "->");
                // to keep table readable, only show RHS in cell
                char rhsStr[48] = {0};
                // build RHS string for display (epsilon handled)
                if (parsingTable[(unsigned char)A][(unsigned char)a][0] == EPS &&
                    parsingTable[(unsigned char)A][(unsigned char)a][1] == '\0')
                {
                    snprintf(rhsStr, sizeof(rhsStr), "epsilon");
                }
                else
                {
                    // raw rhs (may include alias nonterm letters)
                    snprintf(rhsStr, sizeof(rhsStr), "%s", parsingTable[(unsigned char)A][(unsigned char)a]);
                }
                char out[64];
                snprintf(out, sizeof(out), "%s%s", cell, rhsStr);
                printf("%-12s", out);
            }
        }
        printf("\n");
    }
}

/* -----------------------------
   Task 5: LL(1) parsing
----------------------------- */
static void pushRHSReversed(const char *rhs)
{
    // Push RHS to stack in reverse order; skip epsilon
    int n = (int)strlen(rhs);
    if (n == 1 && rhs[0] == EPS)
        return;
    for (int i = n - 1; i >= 0; i--)
    {
        if (rhs[i] == EPS)
            continue;
        push(rhs[i]);
    }
}

static void parseInputString(void)
{
    char input[MAX_LEN];
    printf("\nEnter input string (end with $): ");
    if (scanf("%s", input) != 1)
        return;

    // init stack
    top = -1;
    push('$');
    push(grammar[0].lhs);

    int ip = 0;

    printf("\nStack\t\tInput\t\tProduction\n");
    printf("-------------------------------------------------------------\n");

    while (top != -1)
    {
        // display current stack
        displayStack();
        printf("\t\t%s\t\t", &input[ip]);

        char X = peekStack();
        char a = input[ip];

        if (X == '$' && a == '$')
        {
            printf("Match $\n");
            break;
        }

        if (!isNonTerm(X))
        {
            // terminal
            if (X == a)
            {
                popStack();
                ip++;
                printf("Match %c\n", a);
            }
            else
            {
                printf("Syntax Error at symbol %c (expected %c)\n", a, X);
                return;
            }
        }
        else
        {
            // non-terminal: consult table
            const char *rhs = parsingTable[(unsigned char)X][(unsigned char)a];
            if (rhs[0] == '\0')
            {
                printf("Syntax Error at symbol %c (no rule)\n", a);
                return;
            }

            // Apply production X -> rhs
            popStack();

            // Print production nicely
            printSymbol(X);
            printf(" -> ");
            printRHS(rhs);
            printf("\n");

            pushRHSReversed(rhs);
        }
    }

    printf("\nString Accepted\n");
}

/* -----------------------------
   MAIN (matches PDF flow)
----------------------------- */
int main(void)
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