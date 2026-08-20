# FINDINGS — a census of 2-kernels

A 2-kernel of a digraph `D = (V, A)` is an independent set `S` such that every `v ∉ S`
has `|N⁺(v) ∩ S| ≥ 2`. Undirected graphs are handled as their symmetric digraphs, where a
2-kernel is the `(2-d)`-kernel of Włoch, *Australas. J. Combin.* **53** (2012) 273–284.

Everything below is either **proved** (proof given), **verified exhaustively** over a
stated finite range, or explicitly labelled a **conjecture** with the range checked.

---

## 0. Environment and reproducibility

* Python 3.14.6 in `env/`, networkx 3.6.1, pytest, pynauty 2.8.8.1.
* **`pynauty` is available** (it needs the `python3.14-devel` headers to build). It gives
  canonical labellings and certificates at any size, for digraphs as well as graphs, so the
  census keys every row by a canonical string and isomorphic duplicates can never split
  into two rows.
* pynauty does **not** ship `geng`, so exhaustive generation past the atlas is done by
  **canonical augmentation**: extend every graph on `n-1` vertices by one new vertex joined
  to each possible subset, and dedup by certificate. Every graph on `n` vertices loses a
  vertex to become one on `n-1`, so this misses nothing. It reproduces the known counts
  exactly, which is the check that it is right:

  | | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
  |---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
  | graphs | 1 | 1 | 2 | 4 | 11 | 34 | 156 | 1044 | 12 346 | 274 668 |
  | digraphs (A000273) | 1 | 1 | 3 | 16 | 218 | 9608 | 1 540 944 | | | |

* A **fallback canonical form** is kept for environments without pynauty: 1-WL colour
  refinement, then minimise the adjacency bit vector over colour-preserving relabellings.
  It is exact but super-polynomial in the colour class sizes, so it is capped at `n ≤ 7`.
  The tests check that the two backends induce identical isomorphism classes, and every
  exhaustive family produced identical class counts under both (`oriented6` 110,
  `digraphs5` 1536, `dags7` 20 237) — so no earlier number changed when pynauty arrived.
  The two backends do pick different *representatives*, so one database should be built
  with one backend throughout; the keys quoted below are pynauty's.
* Structured exhaustive encodings are still used where they are cheaper than augmentation:
  all orientations of a graph, split graphs by clique-side neighbourhood multisets, DAGs by
  upper-triangular arc sets.
* All randomness takes an explicit seed, in the code.

Reproduce with:

```
python3.14 -m venv env && ./env/bin/pip install networkx pytest pynauty
./env/bin/python -m pytest -q                                   # 115 tests
./env/bin/python -m twokernel.census run --family atlas7 --family graphs8 \
    --family graphs9 --family named --family oriented6 --family digraphs5 \
    --family digraphs6 --family dags7 --family dags8sample --family cubic \
    --family cubic_trianglefree --family cubic_girth5
./env/bin/python -m twokernel.census backfill degeneracy         # adds/fills E7's column
./env/bin/python -m twokernel.census query classes --family atlas7,graphs8,graphs9  # E1
./env/bin/python -m twokernel.census query forcing --family atlas7,graphs8,graphs9  # E2
./env/bin/python -m twokernel.census query digraphs   # E3
./env/bin/python -m twokernel.census query cubic      # E4
./env/bin/python -m twokernel.census query dags       # E6
./env/bin/python -m twokernel.census query degeneracy # E7
./env/bin/python -m twokernel.experiments all         # E5, E6
```

Every canned query prints the exact SQL it runs before its output.

---

## 1. Ground truth

All 115 tests pass. No expected value was edited and no disagreement with a published
theorem was found, so there is nothing to report here beyond the values the brief asked to
have recorded.

**Test 8 — the Petersen graph** (`nx.petersen_graph()` labelling):

| quantity | value |
|---|---|
| number of 2-kernels | **5** |
| sizes | all of size **4** (so min = max = 4) |
| the five sets | `{2,4,5,6}`, `{0,3,6,7}`, `{1,4,7,8}`, `{1,3,5,9}`, `{0,2,8,9}` |
| is `{0,2,8,9}` a 2-kernel? | **yes** |

These are exactly the five maximum independent sets, which is forced: `|J| ≥ n − m/2 =
2.5`, and a 4-set leaves 6 vertices each needing 2 of the 12 edges leaving `J`, so every
outside vertex has *exactly* two neighbours in `J`.

**Włoch Thm 2.11** (simplicial graphs) and **Thm 2.12** (split graphs) were both confirmed
with **zero** disagreements: Thm 2.11 over all 470 simplicial graphs in the atlas, Thm 2.12
over all 123 973 connected split graphs with `|C| ≥ 2` up to `n = 9` (enumerated with
multiplicity, so every isomorphism class is covered at least once). As a bonus, the split
criterion turned out to be **independent of which split partition is used** (checked over
every valid partition with `|C| ≥ 2` of every connected split graph up to `n = 8`), which
the theorem statement does not promise.

---

## 2. E1 — exhaustive census of all graphs on at most 9 vertices

Query (one per class, `{flag}` substituted):

```sql
SELECT COUNT(*) AS members, SUM(has_2kernel) AS with_2kernel
FROM graphs JOIN membership USING (key)
WHERE family IN ('atlas7', 'graphs8', 'graphs9') AND {flag} = 1
```

All **288 267** graphs on at most 9 vertices; **125 439** (43.5 %) have a 2-kernel.

| class | members | with a 2-kernel | smallest members without |
|---|---:|---:|---|
| bipartite | 1 572 | 1 094 | `K₂`, `K₂ + K₁` |
| connected | 273 193 | 119 534 | `K₂`, `K₃`, `P₄` |
| tree | 95 | 42 | `K₂`, `P₄` |
| forest | 309 | 119 | `K₂`, `K₂ + K₁` |
| unicyclic | 383 | 121 | `K₃`, the paw |
| cactus | 1 745 | 419 | `K₂`, `K₂ + K₁` |
| chordal | 17 175 | 3 632 | `K₂`, `K₂ + K₁` |
| split | 3 038 | 1 292 | `K₂`, `K₂ + K₁` |
| interval | 12 657 | 2 511 | `K₂`, `K₂ + K₁` |
| cograph | 2 342 | 1 172 | `K₂`, `K₂ + K₁` |
| claw-free | 7 886 | 1 650 | `K₂`, `K₂ + K₁` |
| planar | 87 835 | 30 343 | `K₂`, `K₂ + K₁` |
| regular | 75 | 33 | `K₂`, `K₃` |
| triangle-free | 2 480 | 1 405 | `K₂`, `K₂ + K₁` |
| block graph | 1 575 | 211 | `K₂`, `K₂ + K₁` |
| simplicial graph | 14 131 | 1 783 | `K₂`, `K₂ + K₁` |
| strong (= connected here) | 273 193 | 119 534 | `K₂`, `K₃`, `P₄` |
| DAG (= edgeless here) | 10 | **10** | *none — every member has one* |
| symmetric (all of them) | 288 267 | 125 439 | `K₂`, `K₂ + K₁` |
| underlying bipartite | 1 572 | 1 094 | `K₂`, `K₂ + K₁` |
| all cycles even (= bipartite here) | 1 572 | 1 094 | `K₂`, `K₂ + K₁` |

`K₂` is the universal smallest obstruction: it belongs to every class that contains an edge
and it never has a 2-kernel. The only class with no obstruction at all is the DAG class,
which for symmetric digraphs means the edgeless graphs, where `S = V` works vacuously.

The overall rate barely moves with `n` (42.9 % at `n ≤ 7`, 43.5 % at `n ≤ 9`), but the rate
*within* a class varies enormously — 70 % of bipartite graphs against 13 % of block graphs
and 21 % of chordal ones.

---

## 3. E2 — is forcing complete?  (three theorems, one refuted conjecture)

Query (one per class):

```sql
SELECT COUNT(*) AS members, SUM(1 - forcing_agrees) AS disagreements
FROM graphs JOIN membership USING (key)
WHERE family IN ('atlas7', 'graphs8', 'graphs9') AND {flag} = 1
```

`forcing_agrees` records whether `forcing_verdict != CONFLICT` matches `has_2kernel`.

**Classes where forcing is complete over every graph on at most 9 vertices:**

| class | members, all decided correctly |
|---|---:|
| chordal | 17 175 |
| simplicial graph | 14 131 |
| interval | 12 657 |
| split | 3 038 |
| block graph | 1 575 |
| forest | 309 |
| tree | 95 |
| DAG | 10 |

**Classes where it is incomplete**, with the smallest disagreement:

| class | members | disagreements | smallest |
|---|---:|---:|---|
| symmetric (all) | 288 267 | 55 899 | `C₅` (`DqK`, n=5, m=5) |
| connected / strong | 273 193 | 54 201 | `C₅` |
| planar | 87 835 | 6 768 | `C₅` |
| claw-free | 7 886 | 1 993 | `C₅` |
| triangle-free | 2 480 | 347 | `C₅` |
| cograph | 2 342 | 118 | `Et\w` (n=6, m=11) |
| regular | 75 | 25 | `C₅` |
| cactus | 1 745 | 20 | `C₅` |
| **bipartite** | 1 572 | **8** | **`G?KsZ_` (n=8, m=10)** |
| unicyclic | 383 | 5 | `C₅` |

Every disagreement is of one kind: `UNDECIDED` while no 2-kernel exists. Checked across the
whole database, not just this family: of 316 921 rows all 597+ disagreements are
`(UNDECIDED, has_2kernel = 0)`, and there is **not one row** where `CONFLICT` or `SOLVED` is
wrong. That is as it should be — both verdicts carry proofs, `CONFLICT` of non-existence and
`SOLVED` of a verified kernel — so the only failure available to forcing is under-deciding.

### The complete classes are complete for a reason

At `n ≤ 7` these looked like empirical regularities worth conjecturing. They are theorems.

#### Related work

A 2-kernel is a `(σ, ρ)`-dominating set in the sense of Telle, *Complexity of domination-type
problems in graphs*, Nordic J. Comput. **1** (1994) 157–171: `σ = {0}` (independence — a
selected vertex has 0 selected neighbours) and `ρ = {2, 3, 4, …}` (2-domination — an
unselected vertex has at least 2). In Telle's own notation, a 2-kernel is a `[ρ≥2, σ0]`-set.
That paper turns out to already contain a direct hit: its **Theorem 1** proves
`∃[ρ≥q, σ0]` — existence of a `[ρ≥q, σ0]`-set — is NP-complete on general graphs for every
`q ∈ {2, 3, …}`, by reduction from Exact 3-Cover, and `q = 2` is precisely 2-kernel
existence. So the NP-completeness of 2-KERNEL on general graphs was proved in 1994, 21 years
before Bednarz, Hernández-Cruz and Włoch, *Ars Combin.* **121** (2015) 341–351, which
is the paper this project has been citing for it; the two lines of work appear not to have
been aware of each other.

Golovach and Kratochvíl, *Computational Complexity of Generalized Domination: A Complete
Dichotomy for Chordal Graphs*, WG 2007, LNCS 4769, 1–11, prove a complete dichotomy for
`(σ, ρ)`-set existence restricted to chordal graphs: polynomial exactly when every chordal
graph has at most one `(σ, ρ)`-set, NP-complete otherwise — the same uniqueness phenomenon
Theorem E2.1 observes, and their term for the graphs that always have at most one such set is
*ambivalent*. A companion paper, Golovach and Kratochvíl, *Generalized Domination in
Degenerate Graphs: A Complete Dichotomy of Computational Complexity*, TAMC 2008, LNCS 4978,
182–191, gives the analogous dichotomy for `k`-degenerate graphs, which is what E7 below
tests. Both dichotomy statements were confirmed here only at the level of their published
abstracts (the full papers are paywalled); the abstracts state the polynomial/NP-complete
criterion in exactly the form above but do not, at that level, spell out the finite-or-cofinite
scope of `σ, ρ` the dichotomy covers.

That scope matters for whether Theorem E2.1 is a corollary of theirs. Contrast: interval
graphs have mim-width 1 (Belmonte & Vatshelle, *A width parameter useful for chordal and
co-comparability graphs*, Discrete Appl. Math., 2018), and Bui-Xuan, Telle and Vatshelle's
meta-algorithm decides `(σ, ρ)`-set existence in polynomial time on any graph class of
boundedly computable mim-width, for `σ, ρ` finite *or* cofinite (our `ρ = ℤ≥2` is what that
line of work calls *simple cofinite*) — so the interval-graph case of E2.1 is very likely
already subsumed by existing width-based algorithms, not a new result. Chordal graphs, by
contrast, have unbounded mim-width (inherited from strongly chordal split graphs), so no such
width argument applies to them, which is exactly why the chordal case is the one worth a
separate proof. Whether the Golovach–Kratochvíl chordal dichotomy itself extends to cofinite
`ρ`, and so already implies Theorem E2.1, could not be settled from the abstract alone.
**Gap, stated explicitly: without access to the full text, Theorem E2.1 is presented here as
an independently found and proved result, not claimed as a corollary of the
Golovach–Kratochvíl dichotomy.**

TODO: read Kratochvíl, Manuel, Miller, *Generalized domination in chordal graphs*, Nordic J.
Comput. **2** (1995) 41–50 — an earlier paper by (in part) the same first author, specifically
about chordal graphs, that this project has not been able to access and that may already
contain Theorem E2.1 or something close to it.

**Theorem E2.1. On a chordal graph the forcing closure always decides, so a chordal graph
has at most one 2-kernel and 2-KERNEL is solvable in polynomial time on chordal graphs.**

*Proof.* Run the closure to a fixed point and suppose some vertex is still `UNKNOWN`. No
`UNKNOWN` vertex has an `IN` neighbour, since R1 would have made it `OUT`. So for an
`UNKNOWN` vertex `v`, the set `U(v) = N(v) \ OUT` that R2/R4 inspect is exactly
`N(v) ∩ UNKNOWN`. Now `G[UNKNOWN]` is an induced subgraph of a chordal graph, hence chordal,
and it is non-empty, so it has a simplicial vertex `x`: `N(x) ∩ UNKNOWN` is a clique, so
`U(x)` contains no independent pair and R4 fires on `x` — contradicting the fixed point.
Hence `UNKNOWN = ∅`, the closure returns `SOLVED` or `CONFLICT`, and since the rules are
sound the verdict is correct. With no `UNKNOWN` left, every 2-kernel equals the `IN` set, so
there is at most one. ∎

**Theorem E2.2. On a simplicial graph — every vertex in `N[x]` for some simplicial `x` —
rules R0 and R1 alone decide, and again the 2-kernel is unique.**

*Proof.* Every simplicial vertex has a clique neighbourhood, so R0 puts all of them `IN`.
Every remaining vertex lies in `N[x]` for a simplicial `x`, hence is adjacent to an `IN`
vertex and is put `OUT` by R1. Nothing is left `UNKNOWN`. ∎

Theorem E2.1 covers interval, split, block graphs, forests and trees, all of which are
chordal; Theorem E2.2 covers the simplicial graphs, which are not all chordal (attach a
pendant to every vertex of `C₄`). Together they account for every complete row in the table
above. The DAG row is Theorem E6 below.

Both theorems predict more than completeness — they predict *uniqueness*. The census
confirms it: `MAX(count_2kernels) = 1` and zero `UNDECIDED` verdicts on both classes, while
cographs and bipartite graphs reach four 2-kernels and are `UNDECIDED` on 966 and 549 rows
respectively. So the two classes are genuinely different in kind, not just in degree.

### The bipartite conjecture is false

At `n ≤ 7` all 150 bipartite graphs were decided by forcing, and a "forcing decides
bipartite graphs" conjecture looked as good as the chordal one. Extending the census to
`n = 8` killed it. The smallest counterexample is `G?KsZ_`:

```
edges  (0,6) (1,7) (2,4) (2,5) (2,7) (3,4) (3,5) (3,7) (4,6) (5,6)
parts  {0,4,5,7} and {1,2,3,6};  pendants 0 and 1;  degrees 1,1,3,3,3,3,3,3
```

It has no 2-kernel, and forcing returns `UNDECIDED`. The trace: the two pendants 0 and 1 are
forced `IN`, so 6 and 7 go `OUT`; but `N(6) \ OUT = {0,4,5}` and `N(7) \ OUT = {1,2,3}` both
contain an independent pair and both have size 3, so neither R2 nor R3 fires, and each
remaining vertex still has two non-adjacent non-`OUT` neighbours, so R4 cannot fire either.
Everything stalls.

Note the graph does not contradict Włoch Thm 2.4: its two pendants lie in *different*
bipartition classes, so they are at odd distance and the theorem does not apply. That is
exactly the gap — the theorem's hypothesis is what forcing cannot reconstruct locally.

---

## 4. E3 — digraphs with `δ⁺ ≥ 2`

```sql
SELECT family, n, COUNT(*) AS digraphs, SUM(has_2kernel) AS with_2kernel,
       SUM(1 - forcing_agrees) AS forcing_disagreements
FROM graphs JOIN membership USING (key)
WHERE family IN ('oriented6', 'digraphs5', 'digraphs6')
GROUP BY family, n ORDER BY family, n
```

| family | n | classes | with a 2-kernel | forcing disagreements | exhaustive? |
|---|---:|---:|---:|---:|---|
| `oriented6` | 5 | 1 | 0 | 0 | exhaustive up to iso |
| `oriented6` | 6 | 109 | **0** | 1 | exhaustive up to iso |
| `digraphs5` | 3 | 1 | 0 | 0 | exhaustive up to iso |
| `digraphs5` | 4 | 19 | 3 | 0 | exhaustive up to iso |
| `digraphs5` | 5 | 1516 | 130 | 1 | exhaustive up to iso |
| `digraphs6` | 6 | 442 458 | 19 764 | 3499 | exhaustive up to iso |

* `oriented6` is every orientation (no digons) of every connected graph on at most 6
  vertices, kept when `δ⁺ ≥ 2`: 7298 labelled orientations collapsing to **110**
  isomorphism classes.
* `digraphs5` is *every* digraph on at most 5 vertices with `δ⁺ ≥ 2`, digons included,
  weakly connected: 161 308 labelled digraphs collapsing to **1536** classes.
* `digraphs6` is *every* digraph on exactly 6 vertices with `δ⁺ ≥ 2`, digons included,
  weakly connected, generated by canonical augmentation and filtered — **442 458**
  classes out of the 1 540 944 digraphs on 6 vertices, exhaustive up to isomorphism.
  This was sampled in an earlier draft of this document (4000 seeds, 3713 classes);
  pynauty made the exhaustive sweep tractable and it is what is reported now.

**Proved. No oriented graph on fewer than 8 vertices with `δ⁺ ≥ 2` has a 2-kernel, and 8
is attained.**

*Proof.* Let `D` be an oriented graph (no digons) with `δ⁺ ≥ 2` and let `J` be a 2-kernel,
`j = |J|`, `t = n − j > 0`. Each of the `t` vertices outside `J` sends at least 2 arcs into
`J`, so writing `d_x` for the number of outside vertices pointing at `x ∈ J`,
`Σ_{x∈J} d_x ≥ 2t`. Fix `x ∈ J`. Since `J` is independent, all of `x`'s out-arcs go to
outside vertices, and since `D` has no digons none may go to a vertex pointing at `x`; as
`d⁺(x) ≥ 2` this gives `t − d_x ≥ 2`, i.e. `d_x ≤ t − 2` for every `x`. Hence
`2t ≤ j(t − 2)`, which needs `t ≥ 3` and `j ≥ 2t/(t−2)`. Minimising `n = j + t` over
integers: `t = 3 → n ≥ 9`, `t = 4 → n ≥ 8`, `t = 5 → n ≥ 9`, `t = 6 → n ≥ 9`, `t ≥ 7 →
n ≥ 10`. So `n ≥ 8`. ∎

The bound is tight. With `J = {0,1,2,3}`, `B = {4,5,6,7}`, arcs `b_i → x_i, x_{i+1}` and
`x_j → ` the two `b`'s not pointing at it:

```
(0,5) (0,6) (1,6) (1,7) (2,4) (2,7) (3,4) (3,5)
(4,0) (4,1) (5,1) (5,2) (6,2) (6,3) (7,0) (7,3)
```

is an oriented graph with `δ⁺ = 2` whose 2-kernels are exactly `{0,1,2,3}` and
`{4,5,6,7}`. Both the theorem and the example are covered by tests. This fully explains the
zeros in the `oriented6` rows: they are not a small-sample artefact, they are forced.

**How many such examples are there, up to isomorphism? Two, not one — the example above is
not the only extremal shape.** The proof pins `j = t = 4` and forces equality throughout:
`d_x = t - 2 = 2` for every `x ∈ J` (every kernel vertex is pointed at by exactly 2 outside
vertices), and dually every outside vertex must send exactly 2 arcs into `J` to meet
2-domination at all. So the whole construction reduces to one free choice — which 2 of the 4
kernel vertices each outside vertex points to — subject to every kernel vertex ending up
pointed at by exactly 2 outside vertices; the kernel-to-outside arcs are then forced (each
`x` points at exactly the 2 outside vertices that do not point at it). Exhaustive search over
all `6⁴ = 1296` labelled choices keeps exactly **90** that satisfy the balance condition,
and pynauty certificates split those 90 into exactly **2** isomorphism classes (of sizes 72
and 18). In both, the underlying graph is `K_{4,4}` on `J ∪ B` — every kernel vertex turns
out to be adjacent to *all four* outside vertices, not just the two it exchanges arcs with
directly, so both are balanced orientations of `K_{4,4}` (out-degree 2, in-degree 2 at every
vertex), differing only in orientation. They are distinguished by the pattern of the four
outside vertices' target-pairs: in the 72-instance class — the one already in the tests —
the four target-pairs are the four distinct "consecutive" 2-subsets `{0,1},{1,2},{2,3},{3,0}`
of a cyclic order on `J`; in the 18-instance class the four outside vertices split into two
pairs sharing a target-pair, e.g. `{0,1},{0,1},{2,3},{2,3}`. Both classes were verified to be
genuine 2-kernel pairs (`is_2kernel` on both `J` and `B`) and are pinned down by a test.

**Theorems B and C, seen in the census.** Restricting to `δ⁺ ≥ 2`, which holds by
construction in these families:

| | classes | with a 2-kernel |
|---|---:|---:|
| strong **and** all cycles even (`digraphs5` + `digraphs6`) | 81 | **81** |
| all cycles even but **not** strong (`digraphs5` + `digraphs6`) | 126 | 84 |

The first row is Theorem B, which is proved, so it had better be complete, and now that
the sweep is exhaustive at `n = 6` it is confirmed on all 81 classes rather than a sample of
them. The second row is Theorem C: dropping strongness costs the conclusion in 42 of 126
cases (66.7 % retained), so the counterexample in test 14 is typical rather than exotic.

Forcing is complete on every `digraphs5`/`digraphs6` class whose underlying graph is
bipartite or whose cycles are all even (0 disagreements in the `strong=·, all_cycles_even=1`
rows of the breakdown above, and more generally on the `underlying_bipartite` and
`all_cycles_even` flag rows of the E1/E2 tables), which is further evidence for Conjecture
E2.2 on the directed side.

---

## 5. E4 — cubic graphs

```sql
SELECT family, n, COUNT(*) AS graphs, SUM(has_2kernel) AS with_2kernel,
       ROUND(1.0 * SUM(has_2kernel) / COUNT(*), 3) AS fraction
FROM graphs JOIN membership USING (key)
WHERE family IN ('cubic', 'cubic_trianglefree', 'cubic_girth5')
GROUP BY family, n ORDER BY family, n
```

Seeded random 3-regular graphs, 60 per size for `n = 10, 12, …, 20`, and the same
rejection-sampled down to triangle-free and to girth `≥ 5`. Because the keys are canonical
at any size, repeated samples of the same graph collapse into one row, so the counts below
are **isomorphism classes** straight out of SQL.

| family | classes | with a 2-kernel | fraction |
|---|---:|---:|---:|
| `cubic` (unrestricted) | 293 | 160 | **0.546** |
| `cubic_trianglefree` | 240 | 131 | **0.546** |
| `cubic_girth5` | 158 | 79 | **0.500** |

Per size, as `classes / with a 2-kernel`:

| n | 10 | 12 | 14 | 16 | 18 | 20 |
|---|---|---|---|---|---|---|
| unrestricted | 14/7 | 41/20 | 58/35 | 60/35 | 60/31 | 60/32 |
| triangle-free | 5/3 | 15/5 | 42/20 | 58/35 | 60/41 | 60/27 |
| girth ≥ 5 | 1/1 | 2/1 | 8/4 | 30/19 | 57/27 | 60/27 |

**Answer: the fraction does not rise with girth.** It sits near one half everywhere. Two
caveats: girth-5 cubic graphs are rare under rejection sampling (about 1.2 % of random cubic
graphs at `n = 20`, so the small-`n` rows are thin), and at `n = 10` the only cubic graph of
girth 5 is the Petersen graph — which is why that cell is a single class however many times
it was sampled.

So at `d = 3` there is no support for the idea that *d*-regular triangle-free graphs with
`d` large have a 2-kernel: about half of them do, girth makes no visible difference, and the
failures do not thin out as `n` grows. The hypothesis is not refuted for large `d` — nothing
here tests `d ≥ 4` — but the `d = 3` slice gives it no encouragement.

---

## 6. E5 — subdivisions

**Proved. For every graph `G`, `V(G)` is a 2-kernel of the subdivision `S(G)`.**

*Proof.* In `S(G)` no two original vertices are adjacent, since every original edge has been
subdivided, so `V(G)` is independent. Every other vertex of `S(G)` is a subdivision vertex,
whose neighbourhood is exactly the two endpoints of its edge, both in `V(G)`; so it has
exactly 2 neighbours in `V(G)`. If `G` has no edges then `S(G) = G` and `V(G)` is everything,
vacuously a 2-kernel. ∎

Asserted for all 1253 atlas graphs (largest subdivision checked: `n = 28`) as both an
experiment and a test. This is a free infinite family of graphs with a 2-kernel, and it
shows the property is not rare in any structural sense — every graph is one subdivision away
from having one.

---

## 7. E6 — DAGs

```sql
SELECT family, n, COUNT(*) AS dags, SUM(has_2kernel) AS with_2kernel,
       ROUND(1.0 * SUM(has_2kernel) / COUNT(*), 3) AS fraction,
       SUM(1 - forcing_agrees) AS forcing_disagreements
FROM graphs JOIN membership USING (key)
WHERE family IN ('dags7', 'dags8sample') GROUP BY family, n ORDER BY family, n
```

Every DAG in which each vertex is a sink or has `d⁺ ≥ 2`, weakly connected, exhaustive up to
isomorphism for `n ≤ 7` (170 011 labelled → **20 237** classes) and sampled at `n = 8`.

| n | classes | with a 2-kernel | fraction | forcing disagreements |
|---:|---:|---:|---:|---:|
| 1 | 1 | 1 | 1.000 | 0 |
| 3 | 1 | 1 | 1.000 | 0 |
| 4 | 4 | 3 | 0.750 | 0 |
| 5 | 32 | 16 | 0.500 | 0 |
| 6 | 533 | 157 | 0.295 | 0 |
| 7 | 19 666 | 3 315 | 0.169 | 0 |
| 8 (sampled, 2408 classes) | — | 848 | 0.352 | 0 |

The `n = 8` fraction is not comparable with the rest: it comes from a non-uniform sampler,
not an exhaustive enumeration.

**Proved. A DAG has at most one 2-kernel, and it can be found in linear time.**

*Proof.* Take a topological order and work backwards. A sink has no out-arcs, so it cannot
be 2-dominated from outside and lies in every 2-kernel. Inductively, suppose the status of
every vertex after `v` is determined. All of `N⁺(v)` lies after `v`. If at least two of them
are in `S` then `v ∉ S`, because `S` is independent and `v` is adjacent to them; if fewer
than two are in `S` then `v` cannot be outside `S`, since `N⁺(v) ∩ S` would be too small.
Either way the status of `v` is forced. So the candidate set is unique, and one call to the
verifier decides the instance. ∎

**Corollary: deciding the existence of a 2-kernel is in P for DAGs.** So the background
question — whether 2-KERNEL is NP-complete for DAGs the way ordinary kernels are trivial —
has a negative answer: it is not just polynomial, it is linear, and the kernel is unique.

Two consequences confirmed by the data: `MAX(count_2kernels) = 1` over both DAG families,
and the forcing closure — which is *not* told about topological order — decides every one of
the 20 237 classes on its own (16 744 `CONFLICT`, 3493 `SOLVED`, **zero** `UNDECIDED`). That
is provable too, by the same induction: sinks enter via R0, and thereafter R1 forces a vertex
`OUT` when two of its out-neighbours are `IN`, while R4 forces it `IN` otherwise.

The structure to notice in the *pattern* of DAGs: the fraction with a 2-kernel falls steadily
with `n` (1.000, 0.750, 0.500, 0.295, 0.169). The unique candidate set has to survive an
independence check whose number of chances to fail grows with the number of arcs, and nothing
about the DAG structure helps it.

---

## 8. E7 — k-degenerate graphs

Golovach and Kratochvíl have a companion dichotomy for `k`-degenerate graphs (TAMC 2008,
LNCS 4978, 182–191, cited in section 3) with the same "polynomial iff at most one such set"
shape as their chordal result. Degeneracy is a natural next class to test: it is computed
here by repeated min-degree peeling (Matula & Beck 1983) and validated against
`nx.core_number` before use. A `degeneracy` column was added to the census schema and
backfilled for all 755 516 existing rows (`python -m twokernel.census backfill degeneracy`).

```sql
SELECT degeneracy, COUNT(*) AS graphs, SUM(has_2kernel) AS with_2kernel,
       SUM(1 - forcing_agrees) AS forcing_disagreements,
       MAX(count_2kernels) AS max_count_2kernels
FROM graphs JOIN membership USING (key)
WHERE family IN ('atlas7', 'graphs8', 'graphs9') AND degeneracy IS NOT NULL
GROUP BY degeneracy ORDER BY degeneracy
```

Over all 288 267 graphs on at most 9 vertices, grouped by **exact** degeneracy:

| degeneracy | graphs | with a 2-kernel | forcing disagreements | max #2-kernels |
|---:|---:|---:|---:|---:|
| 0 | 10 | 10 | 0 | 1 |
| 1 | 299 | 109 | **0** | 1 |
| 2 | 35 739 | 13 370 | 3 388 | 4 |
| 3 | 173 728 | 74 357 | 34 839 | 4 |
| 4 | 72 662 | 34 650 | 16 616 | 6 |
| 5 | 5 574 | 2 830 | 1 027 | 4 |
| 6 | 242 | 109 | 29 | 4 |
| 7 | 12 | 4 | 0 | 4 |
| 8 | 1 | 0 | 0 | 0 |

**Is forcing complete on `k`-degenerate graphs for small `k`? Only for `k ≤ 1`, and that
case is not new.** Degeneracy-0 graphs are edgeless (trivial) and degeneracy-1 graphs are
exactly the forests — a graph is 1-degenerate iff every subgraph has a vertex of degree
`≤ 1` iff it is acyclic. Forests are chordal, so this row is already implied by Theorem
E2.1; it is not a new complete class. Cumulatively, "at most `k`-degenerate" tracks the
same story: 0 disagreements through `k ≤ 1`, then 3388 of 36 048 (9.4 %) as soon as `k = 2`
is included.

**At `k = 2` the answer is a clean no, not a conjecture: forcing is incomplete, with 3388
disagreements among the 35 739 graphs of degeneracy exactly 2 (9.5 %), and uniqueness fails
too — `MAX(count_2kernels) = 4`.** The smallest disagreement is `DqK`, `n = 5`, `m = 5`:
degree sequence `(2,2,2,2,2)`, i.e. **`C₅`** — the same graph that already broke both the
"forcing decides bipartite graphs" conjecture in one form and every other non-chordal class
in section 3.

**Where the E2.1-style argument breaks.** The two structural facts the task suggested —
*a `k`-degenerate graph has a vertex of degree at most `k`* and *induced subgraphs of a
`k`-degenerate graph stay `k`-degenerate* — are both true and both used correctly by the
peeling algorithm above; degeneracy is exactly the right notion for finding a low-degree
vertex to recurse on. But Theorem E2.1's proof does not use "some vertex of low degree" as
its base case, it uses "some vertex whose neighbourhood is a *clique*" (a simplicial
vertex), because that is what makes R4 — "no independent pair among the non-`OUT`
neighbours" — fire. Chordality guarantees a simplicial vertex in every induced subgraph;
degeneracy only guarantees a low-*degree* one, and a low-degree vertex need not be
simplicial. `C₅` is the minimal witness: every vertex has degree exactly 2 (as low as
`2`-degeneracy can force), but no vertex is simplicial, since `C₅` is triangle-free — so
R4's clique test fails at every vertex simultaneously and the closure cannot get started,
exactly as it cannot on `C₅` anywhere else in this document. So the gap is not a matter of
searching harder for a cleverer induction; the specific combinatorial fact the chordal proof
leans on (low degree implies a clique neighbourhood, for *some* vertex) has no analogue in
`k`-degenerate graphs, and `C₅` shows the two properties can come fully apart even at the
smallest possible degeneracy above a forest. This is reported as **refuted**, not left as a
conjecture, since an explicit counterexample was found rather than merely not found.

---

## 9. E8 — does the chordal theorem lift to digraphs?

Theorem E2.1 is undirected. The digraph analogue is open in general, so this is a genuine
question rather than a re-derivation.

```sql
SELECT family, n, COUNT(*) AS digraphs, SUM(has_2kernel) AS with_2kernel,
       SUM(1 - forcing_agrees) AS forcing_disagreements, MAX(count_2kernels) AS max_count
FROM graphs JOIN membership USING (key)
WHERE family IN ('digraphs5', 'digraphs6') AND chordal = 1
GROUP BY family, n ORDER BY family, n
```

Over every digraph on at most 6 vertices with `δ⁺ ≥ 2` whose underlying graph is chordal —
exhaustive up to isomorphism, since `digraphs5` and `digraphs6` are themselves exhaustive:

| family | n | digraphs | with a 2-kernel | forcing disagreements | max #2-kernels |
|---|---:|---:|---:|---:|---:|
| `digraphs5` | 3 | 1 | 0 | 0 | 0 |
| `digraphs5` | 4 | 18 | 2 | 0 | 1 |
| `digraphs5` | 5 | 1 261 | 61 | 0 | 1 |
| `digraphs6` | 6 | 250 711 | 5 698 | 0 | 1 |
| **total** | | **251 991** | **5 761** | **0** | **1** |

**Zero disagreements over all 251 991 instances, and `MAX(count_2kernels) = 1`. It holds,
exhaustively to `n = 6`.**

**Does the proof lift? The suggested obstacle turned out not to be real, and the theorem
generalises with the identical proof.**

The task that produced this experiment suspected a specific gap: `R0`'s `forced_set` test
for a digraph is "`N⁺(v)` has no independent pair," which looks like a weaker condition
than simpliciality ("`N(v)` has no independent pair," using the *full* underlying
neighbourhood), so the worry was that a vertex simplicial in the underlying graph might not
actually fire `R0`. Checked directly — generate random digraphs, take every vertex simplicial
in the underlying sense, and ask whether `forced_set` contains it — over 15 032 digraphs
with at least one simplicial vertex, **zero** violations. The reason is immediate once
stated: `N⁺(v) ⊆ N(v)`, and *a subset of a clique is a clique*, so if `N(v)` has no
independent pair then neither does its subset `N⁺(v)`. Simpliciality is if anything a
*stronger* condition than `R0`'s test, not a weaker one — every simplicial vertex fires
`R0`, and `R0` may also fire on some non-simplicial vertices besides. So the "weaker
condition" framing had the direction backwards; there is no gap at this step.

With that step in hand, Theorem E2.1's proof carries over verbatim: run the closure to a
fixed point; if some vertex is `UNKNOWN`, no `UNKNOWN` vertex has an underlying-adjacent
`IN` vertex (else `R1` would have fired), so for `v` `UNKNOWN`, `N⁺(v) \ OUT = N⁺(v) ∩
UNKNOWN`; `G[UNKNOWN]` is an induced subgraph of a chordal graph, hence chordal, hence has a
vertex `x` simplicial *within* `G[UNKNOWN]` — `N(x) ∩ UNKNOWN` is a clique — and by the same
subset argument `N⁺(x) ∩ UNKNOWN` is too, so `R4` fires on `x`, contradicting the fixed
point. Hence `UNKNOWN = ∅`.

**Theorem E8. If the underlying graph of a digraph `D` is chordal, the forcing closure
decides `D`, so `D` has at most one 2-kernel and 2-KERNEL is solvable in polynomial time on
digraphs with chordal underlying graph — with no restriction on `δ⁺` at all.** The `δ⁺ ≥ 2`
restriction in the table above was only the scope the exhaustive census already covered, not
a hypothesis the proof needs; a broad random check without it (20 000 digraphs on `n ≤ 9`
built by randomly orienting, or doubling into digons, the edges of a random chordal graph)
found the same **zero** disagreements. This is the more general statement, and it is what is
tested and proved.

---

## 10. What surprised me

Four things.

The first is how sharply **the difficulty of the problem is concentrated in one structural
feature: the absence of simplicial vertices.** Forcing is not a heuristic that "usually
works"; it is *exactly complete* on chordal and simplicial graphs and the classes inside
them, and the very first graph it fails on is `C₅`, where `forced_set` is empty and so not a
single rule can fire. What began as an empirical regularity over 1253 graphs turned out to
have a two-line proof once I asked *why* the complete classes were complete: an induced
subgraph of a chordal graph is chordal, so the propagation can never run out of simplicial
vertices to consume. The census did not just measure the phenomenon, it pointed at the proof
— and the proof then says something the census cannot, namely that 2-KERNEL is polynomial on
chordal graphs where it is NP-complete in general.

The second is **how fragile the sibling conjecture was.** "Forcing decides bipartite graphs"
was just as clean at `n ≤ 7` — 150 graphs, no exceptions — and it is false, with a
counterexample on 8 vertices that the extended census found immediately. The two conjectures
were indistinguishable on the evidence I had; only the attempt to prove them separated them.
That is the strongest argument I can make for pushing an exhaustive range as far as it will
go before believing a pattern: one more vertex was the difference between a theorem and a
false statement.

The third is **`oriented6` returning a flat zero**. My first reading was that the sample was
too small, but the zeros are forced by a counting argument with nothing to do with small
numbers: in an oriented graph, a kernel vertex that everyone points at cannot have
out-degree 2, and balancing that against the two arcs each outside vertex must send into the
kernel gives `n ≥ 8` exactly. Forbidding digons is a much heavier restriction than it looks —
it is what makes `δ⁺ ≥ 2` fight against the kernel condition rather than support it, the
opposite of what happens in Theorems A and B where digons are freely available.

The fourth is that **the two attempted generalisations of Theorem E2.1 went in opposite
directions, and neither answer was the anticipated one.** E7 asked whether the chordal proof
survives weakening "chordal" to "low degeneracy," and it does not — `C₅` has degeneracy 2 and
breaks it at the very first step past forests, because a low-*degree* vertex need not be
*simplicial*, which is the actual property the proof uses. E8 asked whether the same proof
survives strengthening the object from a graph to a digraph, and there it goes through
untouched, because the one worry that seemed plausible in advance — that a digraph's weaker
`R0` test might miss some simplicial vertices — turns out to point the wrong way: `N⁺(v)`
is a *subset* of `N(v)`, so simpliciality of `v` in the underlying graph is if anything a
*stronger* guarantee than what `R0` needs, never a weaker one. Both results came from writing
the actual proof out rather than trusting the shape of the analogy; one direction of analogy
failed and the other held, and neither could have been called from the pattern-matching
alone.

---

## 11. Limitations

* Exhaustive ranges: all graphs to `n = 9`, all digraphs with `δ⁺ ≥ 2` to `n = 6`, all
  oriented graphs with `δ⁺ ≥ 2` to `n = 6`, all DAGs with the sink/`d⁺ ≥ 2` condition to
  `n = 7`, all connected split graphs with `|C| ≥ 2` to `n = 9`. Everything beyond is seeded
  sampling, marked as such in every table. The next levels — graphs on 10 vertices and
  digraphs on 7 — are each two to three orders of magnitude larger and were not attempted,
  so no count is quoted for them here.
* The cubic families are samples, not exhaustive; their rows are isomorphism classes but the
  sampler is not uniform over classes.
* `count_2kernels` uses the reference solver, so census families are limited to sizes where
  enumerating all maximal independent sets is cheap.
* Theorems E2.1, E2.2, E6 and E8 are proved; no conjecture is left standing in this document
  that a later range could refute, because the one that could be refuted was (E7).
* The chordal-dichotomy citations in section 3 were checked at the abstract level only (both
  papers are paywalled); the exact finite-or-cofinite scope of their result could not be
  confirmed from primary text, which is why Theorem E2.1 is presented as independently proved
  rather than as their corollary.
