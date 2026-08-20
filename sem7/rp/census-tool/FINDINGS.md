# FINDINGS — a census of 2-kernels

A 2-kernel of a digraph `D = (V, A)` is an independent set `S` such that every `v ∉ S`
has `|N⁺(v) ∩ S| ≥ 2`. Undirected graphs are handled as their symmetric digraphs, where a
2-kernel is the `(2-d)`-kernel of Włoch, *Australas. J. Combin.* **53** (2012) 273–284.

Everything below is either **proved** (proof given), **verified exhaustively** over a
stated finite range, or explicitly labelled a **conjecture** with the range checked.

---

## 0. Environment and reproducibility

* Python 3.14.6 in `env/`, networkx 3.6.1, pytest. The brief said 3.12; that was an
  oversight and the newest interpreter on the machine was used instead.
* **`pynauty` is not available here.** Its C extension fails to build for want of
  `Python.h` (`python3.14-devel` is not installed), and no `nauty` CLI (`geng`,
  `directg`) is on `PATH`. Nothing depends on it. The fallbacks are:
  * `nx.graph_atlas_g()` — exhaustive up to isomorphism for `n ≤ 7` (1253 graphs);
  * **structured exhaustive encodings** where one exists: all orientations of each atlas
    graph (exhaustive for oriented graphs up to isomorphism, since every oriented graph's
    underlying graph is isomorphic to exactly one atlas representative); split graphs by
    the multiset of clique-side neighbourhoods; DAGs by upper-triangular arc sets; all
    digraphs with `δ⁺ ≥ 2` by direct choice of out-neighbourhoods;
  * a home-grown canonical form (1-WL colour refinement, then minimise the adjacency bit
    vector over colour-preserving relabellings). Exact but super-polynomial in the colour
    class sizes, so it is capped at `n ≤ 7`; the `canonical` column records which rows
    got one. It reproduces exactly 1253 distinct keys on the atlas and agrees with VF2
    isomorphism on orientations of `C₅`;
  * seeded random sampling above those ranges, always with the seed in the code.

Reproduce everything with:

```
python3.14 -m venv env && ./env/bin/pip install networkx pytest
./env/bin/python -m pytest -q                                   # 101 tests
./env/bin/python -m twokernel.census run --family atlas7 --family named \
    --family oriented6 --family digraphs5 --family digraphs6sample \
    --family dags7 --family dags8sample --family cubic \
    --family cubic_trianglefree --family cubic_girth5
./env/bin/python -m twokernel.census query classes    # E1
./env/bin/python -m twokernel.census query forcing    # E2
./env/bin/python -m twokernel.census query digraphs   # E3
./env/bin/python -m twokernel.census query cubic      # E4
./env/bin/python -m twokernel.census query dags       # E6
./env/bin/python -m twokernel.experiments all         # E5, E6
```

Every canned query prints the exact SQL it runs before its output.

---

## 1. Ground truth

All 101 tests pass. No expected value was edited and no disagreement with a published
theorem was found, so there is nothing to report in this section beyond the values the
brief asked to have recorded.

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
with **zero** disagreements: Thm 2.11 over all **470** simplicial graphs in the atlas, Thm
2.12 over all **123 973** connected split graphs with `|C| ≥ 2` up to `n = 9`
(enumerated with multiplicity, so every isomorphism class is covered at least once). As a bonus,
the split criterion turned out to be **independent of which split partition is used**
(checked over every valid partition with `|C| ≥ 2` of every connected split graph up to
`n = 8`), which the theorem statement does not promise.

---

## 2. E1 — exhaustive census of the atlas

Query (one per class, `{flag}` substituted):

```sql
SELECT COUNT(*) AS members, SUM(has_2kernel) AS with_2kernel
FROM graphs JOIN membership USING (key)
WHERE family = 'atlas7' AND {flag} = 1
```

All **1253** graphs on at most 7 vertices; **537** (42.9 %) have a 2-kernel.

| class | members | with a 2-kernel | smallest members without |
|---|---:|---:|---|
| bipartite | 150 | 97 | `K₂`, `K₂ + K₁`, `K₂ + 2K₁` |
| connected | 996 | 441 | `K₂`, `K₃`, `P₄` |
| tree | 25 | 14 | `K₂`, `P₄`, the 5-vertex fork `DC[` |
| forest | 80 | 38 | `K₂`, `K₂ + K₁`, `K₂ + 2K₁` |
| unicyclic | 54 | 19 | `K₃`, the paw `CN`, `D@{` |
| cactus | 221 | 73 | `K₂`, `K₂ + K₁`, `K₃` |
| chordal | 532 | 155 | `K₂`, `K₂ + K₁`, `K₃` |
| split | 258 | 108 | `K₂`, `K₂ + K₁`, `K₃` |
| interval | 506 | 144 | `K₂`, `K₂ + K₁`, `K₃` |
| cograph | 288 | 145 | `K₂`, `K₂ + K₁`, `K₃` |
| claw-free | 431 | 121 | `K₂`, `K₂ + K₁`, `K₃` |
| planar | 1016 | 410 | `K₂`, `K₂ + K₁`, `K₃` |
| regular | 27 | 13 | `K₂`, `K₃`, `2K₂` |
| triangle-free | 173 | 100 | `K₂`, `K₂ + K₁`, `K₂ + 2K₁` |
| block graph | 215 | 49 | `K₂`, `K₂ + K₁`, `K₃` |
| simplicial graph | 471 | 116 | `K₂`, `K₂ + K₁`, `K₃` |
| strong (= connected here) | 996 | 441 | `K₂`, `K₃`, `P₄` |
| DAG (= edgeless here) | 8 | **8** | *none — every member has one* |
| symmetric (all of them) | 1253 | 537 | `K₂`, `K₂ + K₁`, `K₃` |
| underlying bipartite | 150 | 97 | `K₂`, `K₂ + K₁`, `K₂ + 2K₁` |
| all cycles even (= bipartite here) | 150 | 97 | `K₂`, `K₂ + K₁`, `K₂ + 2K₁` |

`K₂` is the universal smallest obstruction: it is in every class that contains an edge and
it never has a 2-kernel. The only class with no obstruction at all is the DAG class, which
for symmetric digraphs means the edgeless graphs, where `S = V` works vacuously.

---

## 3. E2 — is forcing complete?

Query (one per class):

```sql
SELECT COUNT(*) AS members, SUM(1 - forcing_agrees) AS disagreements
FROM graphs JOIN membership USING (key)
WHERE family = 'atlas7' AND {flag} = 1
```

`forcing_agrees` records whether `forcing_verdict != CONFLICT` matches `has_2kernel`.

**Classes where forcing is complete over the whole atlas — zero disagreements:**

| class | members, all decided correctly |
|---|---:|
| chordal | 532 |
| interval | 506 |
| simplicial graph | 471 |
| split | 258 |
| block graph | 215 |
| bipartite / underlying bipartite / all cycles even | 150 |
| forest | 80 |
| tree | 25 |
| DAG | 8 |

**Classes where it is incomplete**, with the smallest disagreement:

| class | members | disagreements | smallest |
|---|---:|---:|---|
| symmetric (all) | 1253 | 91 | `C₅` (`DLo`, n=5, m=5) |
| connected / strong | 996 | 82 | `C₅` |
| planar | 1016 | 52 | `C₅` |
| claw-free | 431 | 48 | `C₅` |
| triangle-free | 173 | 13 | `C₅` |
| cograph | 288 | 6 | `Ejmw` (n=6, m=11) |
| cactus | 221 | 4 | `C₅` |
| regular | 27 | 4 | `C₅` |
| unicyclic | 54 | 2 | `C₅` |

Every disagreement is of one kind: the verdict is `UNDECIDED` while no 2-kernel exists.
Checked across the whole database, not just this family: of 30 385 rows, all 597
disagreements are `(UNDECIDED, has_2kernel = 0)`, and there is not one row where `CONFLICT`
or `SOLVED` is wrong. That is as it should be — both verdicts carry proofs, `CONFLICT` of
non-existence and `SOLVED` of a verified kernel — so the only failure available to forcing
is under-deciding.

`C₅` is the smallest instance where forcing gives up, and the reason is visible: forcing
starts from `forced_set`, which is empty on `C₅` (no vertex has out-degree `≤ 1` and none
is simplicial), so no rule can fire at all. That also explains the pattern in the complete
classes: chordal, interval, split, block and simplicial graphs all guarantee simplicial
vertices, and forests and bipartite graphs give the rules a foothold too.

**Conjecture E2.1.** *For chordal graphs the forcing closure decides the existence of a
2-kernel.* Verified for all 532 chordal graphs on at most 7 vertices. The subclasses
interval (506), split (258), block (215), simplicial (471), forest (80) and tree (25) are
covered by the same check.

**Conjecture E2.2.** *For bipartite graphs the forcing closure decides the existence of a
2-kernel.* Verified for all 150 bipartite graphs on at most 7 vertices, and — see E3 — for
every digraph with underlying bipartite graph or with all cycles even in the digraph
families below.

These two are exactly the kind of "structural result worth writing up" the brief asked
for; they are stated as conjectures because the check is exhaustive only to `n = 7`.

---

## 4. E3 — digraphs with `δ⁺ ≥ 2`

Three families, two exhaustive and one sampled.

```sql
SELECT family, n, COUNT(*) AS digraphs, SUM(has_2kernel) AS with_2kernel,
       SUM(1 - forcing_agrees) AS forcing_disagreements
FROM graphs JOIN membership USING (key)
WHERE family IN ('oriented6', 'digraphs5', 'digraphs6sample')
GROUP BY family, n ORDER BY family, n
```

| family | n | classes | with a 2-kernel | forcing disagreements | exhaustive? |
|---|---:|---:|---:|---:|---|
| `oriented6` | 5 | 1 | 0 | 0 | exhaustive up to iso |
| `oriented6` | 6 | 109 | **0** | 1 | exhaustive up to iso |
| `digraphs5` | 3 | 1 | 0 | 0 | exhaustive up to iso |
| `digraphs5` | 4 | 19 | 3 | 0 | exhaustive up to iso |
| `digraphs5` | 5 | 1516 | 130 | 1 | exhaustive up to iso |
| `digraphs6sample` | 6 | 3713 | 115 | 19 | **sampled** (4000 seeds) |

* `oriented6` is every orientation (no digons) of every connected graph on at most 6
  vertices, kept when `δ⁺ ≥ 2`: 7298 labelled orientations collapsing to **110**
  isomorphism classes.
* `digraphs5` is *every* digraph on at most 5 vertices with `δ⁺ ≥ 2`, digons included,
  weakly connected: 161 308 labelled digraphs collapsing to **1536** classes.
* `digraphs6sample` is a seeded sample; all digraphs on 6 vertices with `δ⁺ ≥ 2` number
  about `3.1 × 10⁸` labelled, which is out of reach without nauty.

**Proved. No oriented graph on fewer than 8 vertices with `δ⁺ ≥ 2` has a 2-kernel, and 8
is attained.**

*Proof.* Let `D` be an oriented graph (no digons) with `δ⁺ ≥ 2` and let `J` be a 2-kernel,
`j = |J|`, `t = n − j > 0`. Each of the `t` vertices outside `J` sends at least 2 arcs into
`J`, so writing `d_x` for the number of outside vertices pointing at `x ∈ J`,
`Σ_{x∈J} d_x ≥ 2t`. Fix `x ∈ J`. Since `J` is independent, all of `x`'s out-arcs go to
outside vertices, and since `D` has no digons none of them may go to a vertex pointing at
`x`; as `d⁺(x) ≥ 2` this gives `t − d_x ≥ 2`, i.e. `d_x ≤ t − 2` for every `x`. Hence
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
`{4,5,6,7}`. Both the theorem and the example are covered by tests. This fully explains
the zeros in the `oriented6` rows: they are not a small-sample artefact, they are forced.

**Theorems B and C, seen in the census.** Restricting to `δ⁺ ≥ 2` (true by construction in
these families):

| | classes | with a 2-kernel |
|---|---:|---:|
| strong **and** all cycles even (`digraphs5` + `digraphs6sample`) | 11 | **11** |
| all cycles even but **not** strong | 14 | 5 |

The first row is Theorem B, which is proved, so it had better be 11/11. The second row is
Theorem C: dropping strongness costs the conclusion in 9 of 14 cases, so the counterexample
in test 14 is typical rather than exotic. Forcing is complete on every digraph in these
families whose underlying graph is bipartite or whose cycles are all even (0 disagreements
in every such row), which is the evidence for Conjecture E2.2 on the directed side.

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
rejection-sampled down to triangle-free and to girth `≥ 5`. Since `n > 7` here the
canonical form is out of range, so rows are *labelled* graphs and the same graph can be
sampled twice under different labellings. The isomorphism-class counts below were computed
separately with VF2 and are the honest denominators.

| family | rows | iso classes | classes with a 2-kernel | fraction |
|---|---:|---:|---:|---:|
| `cubic` (unrestricted) | 360 | 293 | 160 | **0.546** |
| `cubic_trianglefree` | 360 | 240 | 131 | **0.546** |
| `cubic_girth5` | 340 | 158 | 79 | **0.500** |

Per size (iso classes / with a 2-kernel): unrestricted `10: 14/7, 12: 41/20, 14: 58/35,
16: 60/35, 18: 60/31, 20: 60/32`; girth `≥ 5` `10: 1/1, 12: 2/1, 14: 8/4, 16: 30/19,
18: 57/27, 20: 60/27`.

**Answer: the fraction does not rise with girth.** It sits near one half everywhere. Two
caveats worth stating: girth-5 cubic graphs are rare under rejection sampling (about 1.2 %
of random cubic graphs at `n = 20`), and at `n = 10` the *only* cubic graph of girth 5 is
the Petersen graph, so that row's "48 samples, all with a 2-kernel" is one graph counted 48
times — which is why the table above reports isomorphism classes.

So at `d = 3` there is no support for the idea that *d*-regular triangle-free graphs with
`d` large have a 2-kernel: about half of them do, girth makes no visible difference, and
the failures do not thin out as `n` grows. The hypothesis is not refuted for large `d` —
nothing here tests `d ≥ 4` — but the `d = 3` slice gives it no encouragement.

---

## 6. E5 — subdivisions

**Proved. For every graph `G`, `V(G)` is a 2-kernel of the subdivision `S(G)`.**

*Proof.* In `S(G)` no two original vertices are adjacent, since every original edge has
been subdivided, so `V(G)` is independent. Every other vertex of `S(G)` is a subdivision
vertex, whose neighbourhood is exactly the two endpoints of its edge, both in `V(G)`; so it
has exactly 2 neighbours in `V(G)`. If `G` has no edges then `S(G) = G` and `V(G)` is
everything, vacuously a 2-kernel. ∎

Asserted for all 1253 atlas graphs (largest subdivision checked: `n = 28`) as both an
experiment and a test. This is a free infinite family of graphs with a 2-kernel, and it
shows the property is not rare in any interesting structural sense — every graph is one
subdivision away from having one.

---

## 7. E6 — DAGs

```sql
SELECT family, n, COUNT(*) AS dags, SUM(has_2kernel) AS with_2kernel,
       ROUND(1.0 * SUM(has_2kernel) / COUNT(*), 3) AS fraction,
       SUM(1 - forcing_agrees) AS forcing_disagreements
FROM graphs JOIN membership USING (key)
WHERE family IN ('dags7', 'dags8sample') GROUP BY family, n ORDER BY family, n
```

Every DAG in which each vertex is a sink or has `d⁺ ≥ 2`, weakly connected, exhaustive up
to isomorphism for `n ≤ 7` (170 011 labelled → **20 237** classes) and sampled at `n = 8`.

| n | classes | with a 2-kernel | fraction | forcing disagreements |
|---:|---:|---:|---:|---:|
| 1 | 1 | 1 | 1.000 | 0 |
| 3 | 1 | 1 | 1.000 | 0 |
| 4 | 4 | 3 | 0.750 | 0 |
| 5 | 32 | 16 | 0.500 | 0 |
| 6 | 533 | 157 | 0.295 | 0 |
| 7 | 19 666 | 3315 | 0.169 | 0 |
| 8 (sampled, 2486) | — | 897 | 0.361 | 0 |

The `n = 8` fraction is not comparable with the rest: it comes from a non-uniform sampler,
not from an exhaustive enumeration.

**Proved. A DAG has at most one 2-kernel, and it can be found in linear time.**

*Proof.* Take a topological order and work backwards. A sink has no out-arcs, so it cannot
be 2-dominated from outside and lies in every 2-kernel. Inductively, suppose the status of
every vertex after `v` is determined. All of `N⁺(v)` lies after `v`. If at least two of
them are in `S` then `v ∉ S`, because `S` is independent and `v` is adjacent to them; if
fewer than two are in `S` then `v` cannot be outside `S`, since `N⁺(v) ∩ S` would be too
small. Either way the status of `v` is forced. So the candidate set is unique, and one call
to the verifier decides the instance. ∎

**Corollary: deciding the existence of a 2-kernel is in P for DAGs.** So the background
question — whether 2-KERNEL is NP-complete for DAGs the way ordinary kernels are trivial —
has a negative answer: it is not just polynomial, it is linear, and the kernel is unique.

Two consequences confirmed by the data: `MAX(count_2kernels) = 1` over both DAG families,
and the forcing closure — which is *not* told about topological order — decides every one
of the 20 237 classes on its own (16 744 `CONFLICT`, 3493 `SOLVED`, **zero** `UNDECIDED`).
That is also provable: sinks enter via R0, and thereafter R1 forces a vertex OUT when two
of its out-neighbours are IN, while R4 forces it IN otherwise, which is exactly the
propagation above.

The structure to notice in the *pattern* of DAGs: the fraction with a 2-kernel falls
steadily with `n` (1.000, 0.750, 0.500, 0.295, 0.169). The unique candidate set has to
survive an independence check whose number of chances to fail grows with the number of
arcs, and nothing about the DAG structure helps it.

---

## 8. What surprised me

Three things.

The first is how sharply **the difficulty of the problem is concentrated in one structural
feature: the absence of simplicial vertices.** Forcing is not a heuristic that "usually
works"; over the atlas it is *exactly complete* on chordal, interval, split, block,
simplicial, forest and bipartite graphs, and the very first graph it fails on is `C₅`,
where `forced_set` is empty and so not a single rule can fire. The classes where forcing
is complete are precisely the ones that guarantee it somewhere to start. I expected a
gradual decay in accuracy across classes and instead got a clean split.

The second is **the DAG result**. I went in expecting E6 to be a counting exercise probing
an open NP-completeness question, and the answer turned out to be a three-line induction:
a DAG has at most one 2-kernel, findable in linear time. Ordinary kernels in a DAG are
unique for the same backwards-induction reason, so the two notions behave identically here
— and the intuition that "2-domination is much harder than domination" simply does not
survive contact with acyclicity. The reason it does not is worth stating: acyclicity means
every vertex's fate depends only on vertices strictly later in the order, which kills the
circular dependencies that make the general problem NP-complete.

The third is **`oriented6` returning a flat zero**. My first reading was that the sample
was too small, but the zeros are forced by a counting argument that has nothing to do with
small numbers: in an oriented graph, a kernel vertex that everyone points at cannot have
out-degree 2, and balancing that against the two arcs each outside vertex must send into
the kernel gives `n ≥ 8` exactly. Forbidding digons is a much heavier restriction than it
looks — it is what makes `δ⁺ ≥ 2` fight against the kernel condition rather than support it,
which is the opposite of what happens in Theorems A and B where digons are freely
available.

---

## 9. Limitations

* No `pynauty`, so exhaustive generation stops where a structured encoding stops: `n ≤ 7`
  for graphs, `n ≤ 5` for all digraphs with `δ⁺ ≥ 2`, `n ≤ 6` for oriented graphs, `n ≤ 7`
  for DAGs. Everything above those is seeded sampling, marked as such in every table.
* Canonical forms are capped at `n ≤ 7`, so rows for larger graphs (`cubic`, `named`) are
  keyed by their labelled string and an isomorphism class can appear more than once. Where
  that mattered (E4) the isomorphism-class counts were recomputed with VF2 and reported.
* Conjectures E2.1 and E2.2 are exhaustive only to `n = 7`.
* `count_2kernels` uses the reference solver, so census families are limited to sizes where
  enumerating all maximal independent sets is cheap.
