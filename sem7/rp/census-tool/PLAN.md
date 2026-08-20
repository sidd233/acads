# PLAN — 2-kernel census tool

## Object

`D = (V, A)` a loopless digraph, `S ⊆ V` is a **2-kernel** iff

1. *independence*: no arc of `A` has both ends in `S` (either direction);
2. *2-domination*: every `v ∉ S` has `|N⁺(v) ∩ S| ≥ 2`.

An undirected graph is its symmetric digraph, so `N⁺(v) = N(v)` and a 2-kernel is the
`(2-d)`-kernel of Włoch, *Australas. J. Combin.* **53** (2012) 273–284. One engine, one
code path, both cases.

Key structural fact used everywhere: **every 2-kernel is a maximal independent set of the
underlying graph** (a vertex outside `S` has out-arcs into `S`, hence is adjacent to `S`).
So "enumerate maximal independent sets, filter by 2-domination" is complete and obviously
correct; it is the ground truth for everything else. Existence is NP-complete (Bednarz,
Hernández-Cruz, Włoch, *Ars Combin.* **121** (2015) 341–351), so the goal is
exponential-but-fast on small instances, not a polynomial exact algorithm.

## Environment

* Python **3.14.6** (newest on this machine; the brief's "3.12" was an oversight).
* venv in `env/`, per the `dl-lab/setup.fish` convention; `env/` is gitignored.
* Deps: `networkx` 3.6.1, `pytest`. No solver dependency on the reference path.
* `pynauty` 2.8.8.1 **is** available (once `python3.14-devel` was installed). It supplies
  canonical labellings and certificates at any size, for digraphs as well as graphs. It
  does *not* ship `geng`, so exhaustive generation past the atlas is done by **canonical
  augmentation** — extend every graph on `n-1` vertices by one vertex in all `2^(n-1)`
  ways and dedup by certificate — which reproduces the known counts and reaches `n = 9`.
* The built-in canonical form (1-WL refinement, then minimise the adjacency bit vector
  over colour-preserving relabellings) is kept as a fallback for environments without
  pynauty, capped at `n <= 7`. The tests check the two backends induce the same
  isomorphism classes, and the exhaustive families give identical class counts under both.

## Modules

| file | contents |
|---|---|
| `twokernel/core.py` | bitmask `Digraph`, `is_2kernel` verifier, Bron–Kerbosch MIS, reference solver, `forced_set`, `forcing_closure` (R0–R4), `solve_dpll` |
| `twokernel/canon.py` | graph6/digraph6 codec, canonical labelling (pynauty, with a self-contained fallback) |
| `twokernel/classes.py` | boolean recognizers, undirected + digraph flags |
| `twokernel/generators.py` | atlas, named families, seeded random families |
| `twokernel/census.py` | sqlite3 store keyed by graph6/digraph6, CLI `run`/`query` |
| `tests/test_core.py` | engine sanity: verifier gate, bitmask round-trips, closure soundness, DPLL vs reference |
| `tests/test_literature.py` | the 16 ground-truth tests from the brief |
| `FINDINGS.md` | E1–E6 results, exact queries, counts, conjectures with ranges |

## Invariants (non-negotiable)

* Every function that returns a set routes it through `is_2kernel` first. No exceptions.
* Every propagation rule is *sound*: it preserves the full solution set. One-line
  justification in each docstring.
* Tests are never weakened. A test believed wrong gets a minimal counterexample in
  FINDINGS.md and is left failing.
* All randomness takes an explicit seed.
* No class or experiment beyond the brief without asking.

## Order of work

1. `PLAN.md`; `core.py` + literature tests 1–4, 11, 14 green. **commit**
2. `classes.py`, `generators.py`, remaining tests (5–10, 12, 13, 15, 16). **commit**
3. `census.py`, then E1–E3. **commit**
4. E4–E6. **commit**
5. `FINDINGS.md` summary + "what surprised me". **commit**

## Interpretation decisions

Recorded here so they are auditable; each is also restated where it is used.

* **Loops** are rejected (`ValueError`). A looped vertex can never lie in an independent
  set, which is a different object; nothing in the brief needs them.
* **Test 6** (Włoch Thm 2.4) does not say which part is `V1`. All pendant vertices lie in
  one part when they are pairwise at even distance, and that part is the one that works
  (the other part then has min degree ≥ 2 only by accident). So `V1 :=` the part
  containing the pendant vertices, either part when there are none. Restricted to
  *connected* bipartite graphs, since "distance" between components is undefined and an
  isolated vertex in `V2` would break the conclusion.
* **Test 9** "simplex" `:=` `N[x]` for a simplicial `x`, as a set (so two simplicial
  vertices with the same closed neighbourhood give *one* simplex containing two simplicial
  vertices, which is what makes `K_n` fail the criterion — consistent with test 3).
* **Test 10** split partitions are not unique. The criterion is checked against the
  partition each graph is *generated* from, and separately against every valid split
  partition with `|C| ≥ 2`; if the predicate is not invariant across partitions that is
  itself a finding and goes in FINDINGS.md.
* **E3** "generate by orienting" yields *oriented* graphs only (no digons); all digraphs
  on 6 vertices is `2^30` labelled and out of reach without nauty. So: exhaustive over all
  orientations of all connected atlas graphs on ≤ 6 vertices (that *is* exhaustive for
  oriented graphs up to isomorphism), plus exhaustive over **all** digraphs including
  digons for n ≤ 4, plus a seeded sample at n = 5, 6. The report states exactly which.
* **E6** DAGs are enumerated as upper-triangular arc sets over a fixed vertex order, which
  covers every isomorphism class; exhaustive while the count is tractable, seeded sample
  above that. Exact ranges reported.

## Status

All five stages are done and all 101 tests pass. Results, the exact queries behind them,
and the three statements that turned out to be provable (the oriented-graph bound `n ≥ 8`,
uniqueness of DAG 2-kernels, and the subdivision family) are in `FINDINGS.md`. No
published expected value disagreed with the implementation, so `FINDINGS.md` records no
counterexample to any cited theorem.
