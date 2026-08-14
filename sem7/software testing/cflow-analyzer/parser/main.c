#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "ast.h"
#include "cfg.h"

extern FILE *yyin;
int yyparse(void);

int main(int argc, char **argv) {
    if (argc < 2) {
        fprintf(stderr, "usage: %s <source.c> [-o output.json]\n", argv[0]);
        return 1;
    }
    const char *infile = argv[1];
    const char *outfile = NULL;
    for (int i = 2; i < argc - 1; i++)
        if (strcmp(argv[i], "-o") == 0) outfile = argv[i + 1];

    /* Stage 1: preprocess with gcc -E (macros and #ifdef are resolved here;
     * our own lexer/parser never sees a preprocessor directive).
     * #include lines are stripped first: we don't parse the C subset well
     * enough for real system headers, and CFG/complexity doesn't need them -
     * only the function bodies in the user's own file matter. */
    char cmd[4096];
    snprintf(cmd, sizeof(cmd),
             "grep -v '^[[:space:]]*#[[:space:]]*include' \"%s\" | gcc -E -P -", infile);
    FILE *pp = popen(cmd, "r");
    if (!pp) { fprintf(stderr, "failed to run gcc -E\n"); return 1; }

    yyin = pp;
    int rc = yyparse();
    pclose(pp);
    if (rc != 0) {
        fprintf(stderr, "parsing failed\n");
        return 1;
    }

    /* Stage 2: build a CFG per function (functions are stored newest-first, reverse for readability) */
    FunctionDef *fns[1024];
    int n = 0;
    for (FunctionDef *f = g_program.functions; f; f = f->next) fns[n++] = f;

    CFG *head = NULL, *tail = NULL;
    for (int i = n - 1; i >= 0; i--) {
        CFG *cfg = build_cfg(fns[i]);
        if (!head) head = tail = cfg;
        else { tail->next = cfg; tail = cfg; }
    }

    FILE *out = outfile ? fopen(outfile, "w") : stdout;
    if (!out) { fprintf(stderr, "cannot open output file %s\n", outfile); return 1; }
    cfg_to_json(head, out);
    if (outfile) fclose(out);

    /* also print a quick human-readable summary to stderr */
    for (CFG *c = head; c; c = c->next)
        fprintf(stderr, "%-20s nodes=%-3d edges=%-3d  cyclomatic complexity = %d\n",
                c->func_name, c->num_blocks, c->num_edges, cyclomatic_complexity(c));

    return 0;
}
