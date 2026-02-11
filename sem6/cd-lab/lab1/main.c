#include <stdio.h>
#include <string.h>

#define MAX 20
#define STR 1024

char R[MAX][MAX][MAX][STR];
int N, M, start, T, Fcount;
int final[MAX];

void u(char *r, const char *a, const char *b)
{
    if (!a[0])
        strcpy(r, b);
    else if (!b[0])
        strcpy(r, a);
    else if (!strcmp(a, b))
        strcpy(r, a);
    else
    {
        strncpy(r, a, STR - 1);
        r[STR - 1] = 0;
        strncat(r, "|", STR - strlen(r) - 1);
        strncat(r, b, STR - strlen(r) - 1);
    }
}

void c(char *r, const char *a, const char *b)
{
    if (!a[0] || !b[0])
    {
        r[0] = 0;
        return;
    }
    if (!strcmp(a, "e"))
        strcpy(r, b);
    else if (!strcmp(b, "e"))
        strcpy(r, a);
    else
    {
        strncpy(r, a, STR - 1);
        r[STR - 1] = 0;
        strncat(r, b, STR - strlen(r) - 1);
    }
}

void s(char *r, const char *a)
{
    if (!a[0] || !strcmp(a, "e"))
        strcpy(r, "e");
    else
    {
        strncpy(r, "(", STR - 1);
        r[STR - 1] = 0;
        strncat(r, a, STR - strlen(r) - 1);
        strncat(r, ")*", STR - strlen(r) - 1);
    }
}

int main(int argc, char **argv)
{
    FILE *fp = fopen(argv[1], "r");
    if (argc != 2)
    {
        printf("Please specify input file.");
        return 0;
    }

    fscanf(fp, "%d", &N);
    fscanf(fp, "%d %d %d %d", &M, &start, &T, &Fcount);

    int trans[MAX][MAX];
    memset(trans, -1, sizeof(trans));

    for (int i = 0; i < T; i++)
    {
        int p, sym, q;
        fscanf(fp, "%d %d %d", &p, &sym, &q);
        trans[p][sym] = q;
    }

    for (int i = 0; i < Fcount; i++)
        fscanf(fp, "%d", &final[i]);

    fclose(fp);

    for (int i = 1; i <= N; i++)
        for (int j = 1; j <= N; j++)
            R[i][j][0][0] = 0;

    for (int i = 1; i <= N; i++)
    {
        for (int j = 1; j <= N; j++)
        {
            for (int s1 = 1; s1 <= M; s1++)
            {
                if (trans[i][s1] == j)
                {
                    char c1[2] = {'a' + s1 - 1, 0};
                    u(R[i][j][0], R[i][j][0], c1);
                }
            }
            if (i == j)
                u(R[i][j][0], R[i][j][0], "e");
        }
    }

    for (int k = 1; k <= N; k++)
    {
        for (int i = 1; i <= N; i++)
        {
            for (int j = 1; j <= N; j++)
            {
                char t1[STR], t2[STR], st[STR];
                s(st, R[k][k][k - 1]);
                c(t1, R[i][k][k - 1], st);
                c(t2, t1, R[k][j][k - 1]);
                u(R[i][j][k], t2, R[i][j][k - 1]);
            }
        }
    }

    char res[STR] = "";
    for (int i = 0; i < Fcount; i++)
        u(res, res, R[start][final[i]][N]);

    printf("Regular Expression: %s\n", res);
    return 0;
}
