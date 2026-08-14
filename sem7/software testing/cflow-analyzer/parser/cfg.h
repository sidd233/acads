#ifndef CFG_H
#define CFG_H
#include <stdio.h>
#include "ast.h"

typedef enum { EDGE_UNCOND, EDGE_TRUE, EDGE_FALSE, EDGE_CASE } EdgeType;

typedef struct BasicBlock {
    int id;
    char *label;         /* joined text of statements inside this block, "\n" separated */
    int line_start, line_end;
    int is_entry, is_exit;
    struct BasicBlock *next; /* master list */
} BasicBlock;

typedef struct Edge {
    BasicBlock *from, *to;
    EdgeType type;
    char *label;          /* e.g. case value, or NULL */
    struct Edge *next;
} Edge;

typedef struct CFG {
    char *func_name;
    BasicBlock *blocks;   /* master list, in creation order */
    Edge *edges;          /* master list */
    BasicBlock *entry, *exit;
    int num_blocks, num_edges;
    struct CFG *next;
} CFG;

CFG *build_cfg(FunctionDef *fn);
int cyclomatic_complexity(CFG *cfg);
void cfg_to_json(CFG *cfg_list, FILE *out);

#endif
