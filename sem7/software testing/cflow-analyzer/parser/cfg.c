#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "cfg.h"

/* ---- small dynamic stacks for break/continue targets ---- */
#define MAX_NEST 256
static BasicBlock *break_stack[MAX_NEST];
static BasicBlock *continue_stack[MAX_NEST];
static int break_top = 0, continue_top = 0;

/* ---- label bookkeeping for goto, resolved in a second pass ---- */
typedef struct LabelDef { char *name; BasicBlock *block; struct LabelDef *next; } LabelDef;
typedef struct PendingGoto { BasicBlock *from; char *target; struct PendingGoto *next; } PendingGoto;
static LabelDef *g_labels = NULL;
static PendingGoto *g_pending_gotos = NULL;

static CFG *g_cfg = NULL;
static int g_next_id = 0;

static BasicBlock *new_block(const char *label) {
    BasicBlock *b = calloc(1, sizeof(BasicBlock));
    b->id = g_next_id++;
    b->label = label ? strdup(label) : strdup("");
    b->next = NULL;
    if (!g_cfg->blocks) g_cfg->blocks = b;
    else {
        BasicBlock *cur = g_cfg->blocks;
        while (cur->next) cur = cur->next;
        cur->next = b;
    }
    g_cfg->num_blocks++;
    return b;
}

static void append_text(BasicBlock *b, const char *text, int line) {
    if (!text || !text[0]) return;
    size_t n = strlen(b->label) + strlen(text) + 2;
    char *joined = malloc(n);
    if (b->label[0]) snprintf(joined, n, "%s\n%s", b->label, text);
    else snprintf(joined, n, "%s", text);
    free(b->label);
    b->label = joined;
    if (b->line_start == 0 || line < b->line_start) b->line_start = line;
    if (line > b->line_end) b->line_end = line;
}

static void add_edge(BasicBlock *from, BasicBlock *to, EdgeType type, const char *label) {
    if (!from || !to) return;
    Edge *e = calloc(1, sizeof(Edge));
    e->from = from; e->to = to; e->type = type;
    e->label = label ? strdup(label) : NULL;
    e->next = NULL;
    if (!g_cfg->edges) g_cfg->edges = e;
    else {
        Edge *cur = g_cfg->edges;
        while (cur->next) cur = cur->next;
        cur->next = e;
    }
    g_cfg->num_edges++;
}

static void push_loop(BasicBlock *cont, BasicBlock *brk) {
    continue_stack[continue_top++] = cont;
    break_stack[break_top++] = brk;
}
static void pop_loop(void) { continue_top--; break_top--; }

/* switch establishes a break target but does NOT catch `continue` -
 * a continue inside a switch inside a loop must still reach the loop */
static void push_switch(BasicBlock *brk) { break_stack[break_top++] = brk; }
static void pop_switch(void) { break_top--; }

static char *wrap(const char *prefix, const char *inner, const char *suffix) {
    size_t n = strlen(prefix) + strlen(inner) + strlen(suffix) + 1;
    char *buf = malloc(n);
    snprintf(buf, n, "%s%s%s", prefix, inner, suffix);
    return buf;
}

/* forward decl */
static BasicBlock *emit_stmt(Stmt *s, BasicBlock *cur);

static BasicBlock *emit_compound(StmtList *list, BasicBlock *cur) {
    for (StmtList *it = list; it; it = it->next) {
        if (!cur) cur = new_block(NULL); /* reachable only via a later jump/label */
        cur = emit_stmt(it->stmt, cur);
    }
    return cur;
}

/* Switch bodies are handled specially: `case`/`default` are flat markers that
 * start a new block reachable from the switch condition block, and normal
 * fallthrough between cases happens exactly like sequential statements. */
static BasicBlock *emit_switch_body(StmtList *list, BasicBlock *switchBlock, BasicBlock *exitBlock) {
    BasicBlock *cur = NULL;
    for (StmtList *it = list; it; it = it->next) {
        Stmt *s = it->stmt;
        if (s->type == STMT_CASE || s->type == STMT_DEFAULT) {
            char *caseLabel = s->type == STMT_CASE ? wrap("case ", s->text, ":") : strdup("default:");
            BasicBlock *caseBlock = new_block(caseLabel);
            add_edge(switchBlock, caseBlock, EDGE_CASE, s->type == STMT_CASE ? s->text : "default");
            free(caseLabel);
            if (cur) add_edge(cur, caseBlock, EDGE_UNCOND, NULL); /* fallthrough from prev case */
            cur = caseBlock;
        } else {
            if (!cur) cur = new_block(NULL);
            cur = emit_stmt(s, cur);
        }
    }
    if (cur) add_edge(cur, exitBlock, EDGE_UNCOND, NULL); /* fell off the end without break */
    return exitBlock;
}

static BasicBlock *emit_stmt(Stmt *s, BasicBlock *cur) {
    switch (s->type) {
    case STMT_COMPOUND:
        return emit_compound(s->body, cur);

    case STMT_EXPR:
    case STMT_DECL:
        append_text(cur, s->type == STMT_DECL ? s->text : s->text, s->line);
        return cur;

    case STMT_EMPTY:
        return cur;

    case STMT_IF: {
        char *label = wrap("if (", s->text, ")");
        append_text(cur, label, s->line);
        free(label);
        BasicBlock *condBlock = cur;
        BasicBlock *thenEntry = new_block(NULL);
        add_edge(condBlock, thenEntry, EDGE_TRUE, NULL);
        BasicBlock *thenExit = emit_stmt(s->s1, thenEntry);

        BasicBlock *elseExit = NULL;
        int hasElse = s->s2 != NULL;
        if (hasElse) {
            BasicBlock *elseEntry = new_block(NULL);
            add_edge(condBlock, elseEntry, EDGE_FALSE, NULL);
            elseExit = emit_stmt(s->s2, elseEntry);
        }

        BasicBlock *join = new_block(NULL);
        int joinReachable = 0;
        if (thenExit) { add_edge(thenExit, join, EDGE_UNCOND, NULL); joinReachable = 1; }
        if (hasElse) {
            if (elseExit) { add_edge(elseExit, join, EDGE_UNCOND, NULL); joinReachable = 1; }
        } else {
            add_edge(condBlock, join, EDGE_FALSE, NULL);
            joinReachable = 1;
        }
        return joinReachable ? join : NULL;
    }

    case STMT_WHILE: {
        BasicBlock *head = new_block(NULL);
        add_edge(cur, head, EDGE_UNCOND, NULL);
        char *label = wrap("while (", s->text, ")");
        append_text(head, label, s->line);
        free(label);
        BasicBlock *exitB = new_block(NULL);
        add_edge(head, exitB, EDGE_FALSE, NULL);
        push_loop(head, exitB);
        BasicBlock *bodyEntry = new_block(NULL);
        add_edge(head, bodyEntry, EDGE_TRUE, NULL);
        BasicBlock *bodyExit = emit_stmt(s->s1, bodyEntry);
        if (bodyExit) add_edge(bodyExit, head, EDGE_UNCOND, NULL);
        pop_loop();
        return exitB;
    }

    case STMT_DO_WHILE: {
        BasicBlock *bodyEntry = new_block(NULL);
        add_edge(cur, bodyEntry, EDGE_UNCOND, NULL);
        BasicBlock *condBlock = new_block(NULL);
        BasicBlock *exitB = new_block(NULL);
        push_loop(condBlock, exitB);
        BasicBlock *bodyExit = emit_stmt(s->s1, bodyEntry);
        pop_loop();
        if (bodyExit) add_edge(bodyExit, condBlock, EDGE_UNCOND, NULL);
        char *label = wrap("while (", s->text, ")");
        append_text(condBlock, label, s->line);
        free(label);
        add_edge(condBlock, bodyEntry, EDGE_TRUE, NULL);
        add_edge(condBlock, exitB, EDGE_FALSE, NULL);
        return exitB;
    }

    case STMT_FOR: {
        append_text(cur, s->text2, s->line); /* init */
        BasicBlock *condBlock = new_block(NULL);
        add_edge(cur, condBlock, EDGE_UNCOND, NULL);
        append_text(condBlock, s->text, s->line); /* cond */
        BasicBlock *exitB = new_block(NULL);
        add_edge(condBlock, exitB, EDGE_FALSE, NULL);
        BasicBlock *incrBlock = new_block(NULL);
        append_text(incrBlock, s->text3, s->line); /* incr */
        push_loop(incrBlock, exitB);
        BasicBlock *bodyEntry = new_block(NULL);
        add_edge(condBlock, bodyEntry, EDGE_TRUE, NULL);
        BasicBlock *bodyExit = emit_stmt(s->s1, bodyEntry);
        pop_loop();
        if (bodyExit) add_edge(bodyExit, incrBlock, EDGE_UNCOND, NULL);
        add_edge(incrBlock, condBlock, EDGE_UNCOND, NULL);
        return exitB;
    }

    case STMT_SWITCH: {
        char *label = wrap("switch (", s->text, ")");
        append_text(cur, label, s->line);
        free(label);
        BasicBlock *exitB = new_block(NULL);
        push_switch(exitB);
        emit_switch_body(s->s2->body, cur, exitB);
        pop_switch();
        return exitB;
    }

    case STMT_BREAK:
        if (break_top > 0) add_edge(cur, break_stack[break_top - 1], EDGE_UNCOND, NULL);
        return NULL;

    case STMT_CONTINUE:
        if (continue_top > 0) add_edge(cur, continue_stack[continue_top - 1], EDGE_UNCOND, NULL);
        return NULL;

    case STMT_RETURN:
        append_text(cur, s->text ? s->text : "return", s->line);
        add_edge(cur, g_cfg->exit, EDGE_UNCOND, NULL);
        return NULL;

    case STMT_GOTO: {
        PendingGoto *pg = malloc(sizeof(PendingGoto));
        pg->from = cur; pg->target = s->text; pg->next = g_pending_gotos;
        g_pending_gotos = pg;
        return NULL;
    }

    case STMT_LABEL: {
        BasicBlock *lb = new_block(s->text);
        add_edge(cur, lb, EDGE_UNCOND, NULL);
        LabelDef *ld = malloc(sizeof(LabelDef));
        ld->name = s->text; ld->block = lb; ld->next = g_labels;
        g_labels = ld;
        return emit_stmt(s->s1, lb);
    }

    case STMT_CASE:
    case STMT_DEFAULT:
        /* only meaningful inside emit_switch_body; if reached elsewhere, ignore */
        return cur;
    }
    return cur;
}

CFG *build_cfg(FunctionDef *fn) {
    CFG *cfg = calloc(1, sizeof(CFG));
    cfg->func_name = strdup(fn->name);
    g_cfg = cfg;
    g_next_id = 0;
    break_top = continue_top = 0;
    g_labels = NULL;
    g_pending_gotos = NULL;

    BasicBlock *entry = new_block("ENTRY");
    entry->is_entry = 1;
    BasicBlock *exit = new_block("EXIT");
    exit->is_exit = 1;
    cfg->entry = entry;
    cfg->exit = exit;

    BasicBlock *last = emit_compound(fn->body->body, entry);
    if (last) add_edge(last, exit, EDGE_UNCOND, NULL); /* implicit fallthrough return */

    /* resolve gotos now that all labels in the function have been seen */
    for (PendingGoto *pg = g_pending_gotos; pg; pg = pg->next) {
        BasicBlock *target = NULL;
        for (LabelDef *ld = g_labels; ld; ld = ld->next) {
            if (strcmp(ld->name, pg->target) == 0) { target = ld->block; break; }
        }
        if (target) add_edge(pg->from, target, EDGE_UNCOND, NULL);
        else fprintf(stderr, "warning: undefined label '%s' in function %s\n", pg->target, fn->name);
    }

    return cfg;
}

int cyclomatic_complexity(CFG *cfg) {
    /* M = E - N + 2P, P = 1 (single entry/exit per function) */
    return cfg->num_edges - cfg->num_blocks + 2;
}

static void json_escape(FILE *out, const char *s) {
    for (const char *p = s; *p; p++) {
        switch (*p) {
        case '"': fputs("\\\"", out); break;
        case '\\': fputs("\\\\", out); break;
        case '\n': fputs("\\n", out); break;
        case '\t': fputs("\\t", out); break;
        default: fputc(*p, out);
        }
    }
}

static const char *edge_type_str(EdgeType t) {
    switch (t) {
    case EDGE_TRUE: return "true";
    case EDGE_FALSE: return "false";
    case EDGE_CASE: return "case";
    default: return "uncond";
    }
}

void cfg_to_json(CFG *cfg_list, FILE *out) {
    fprintf(out, "{\n  \"functions\": [\n");
    for (CFG *cfg = cfg_list; cfg; cfg = cfg->next) {
        fprintf(out, "    {\n");
        fprintf(out, "      \"name\": \""); json_escape(out, cfg->func_name); fprintf(out, "\",\n");
        fprintf(out, "      \"complexity\": %d,\n", cyclomatic_complexity(cfg));
        fprintf(out, "      \"num_nodes\": %d,\n", cfg->num_blocks);
        fprintf(out, "      \"num_edges\": %d,\n", cfg->num_edges);
        fprintf(out, "      \"nodes\": [\n");
        for (BasicBlock *b = cfg->blocks; b; b = b->next) {
            fprintf(out, "        {\"id\": \"B%d\", \"label\": \"", b->id);
            json_escape(out, b->label[0] ? b->label : (b->is_entry ? "ENTRY" : b->is_exit ? "EXIT" : ""));
            fprintf(out, "\", \"line_start\": %d, \"line_end\": %d, \"is_entry\": %s, \"is_exit\": %s}%s\n",
                    b->line_start, b->line_end, b->is_entry ? "true" : "false",
                    b->is_exit ? "true" : "false", b->next ? "," : "");
        }
        fprintf(out, "      ],\n      \"edges\": [\n");
        for (Edge *e = cfg->edges; e; e = e->next) {
            fprintf(out, "        {\"from\": \"B%d\", \"to\": \"B%d\", \"type\": \"%s\"",
                    e->from->id, e->to->id, edge_type_str(e->type));
            if (e->label) { fprintf(out, ", \"label\": \""); json_escape(out, e->label); fprintf(out, "\""); }
            fprintf(out, "}%s\n", e->next ? "," : "");
        }
        fprintf(out, "      ]\n    }%s\n", cfg->next ? "," : "");
    }
    fprintf(out, "  ]\n}\n");
}
