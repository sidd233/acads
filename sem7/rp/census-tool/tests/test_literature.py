"""Ground truth: published theorems and hand proofs.

If one of these fails, the bug is in the library, not in the expected value.  An expected
value believed to be wrong is *not* edited: the disagreement and a minimal counterexample
go into FINDINGS.md and the test is left failing.

References
----------
* I. Włoch, *On 2-dominating kernels in graphs*, Australas. J. Combin. **53** (2012)
  273--284.  (Theorem numbers below are from this paper.)
* P. Bednarz, C. Hernández-Cruz, I. Włoch, *On the existence and the number of
  (2-d)-kernels in graphs*, Ars Combin. **121** (2015) 341--351.
"""

from __future__ import annotations

import itertools

import networkx as nx
import pytest

from twokernel import classes as cls
from twokernel import generators as gen
from twokernel.core import (
    Digraph,
    Verdict,
    all_2kernels,
    bits,
    count_2kernels,
    forcing_closure,
    has_2kernel,
    is_2kernel,
    min_2kernel_size,
    popcount,
    solve_dpll,
)

# --------------------------------------------------------------------------------------
# a shared pool of instances, used by the property-style tests 7, 15 and 16
# --------------------------------------------------------------------------------------


def census_instances() -> list[tuple[str, Digraph]]:
    """A broad, fully seeded pool: the atlas, small orientations, split graphs, named
    families and one of each random family."""
    pool: list[tuple[str, Digraph]] = []
    pool += [(f"atlas{i}", D) for i, D in enumerate(gen.atlas_graphs())]
    for i, G in enumerate(gen.atlas_graphs(max_n=4)):
        pool += [(f"orient{i}.{j}", D) for j, D in enumerate(gen.all_orientations(G))]
    for n in range(2, 8):
        pool += [
            (f"split{n}.{i}", D)
            for i, (D, _C, _I) in enumerate(gen.all_split_graphs(n))
        ]
    pool += [(f"P{n}", gen.path(n)) for n in range(1, 13)]
    pool += [(f"C{n}", gen.cycle(n)) for n in range(3, 13)]
    pool += [(f"K{n}", gen.complete(n)) for n in range(1, 7)]
    pool += [(f"K{a},{b}", gen.complete_bipartite(a, b)) for a in (1, 2, 3) for b in (2, 3, 4)]
    pool += [(f"star{k}", gen.star(k)) for k in range(1, 6)]
    pool += [(f"dstar{a},{b}", gen.double_star(a, b)) for a in (1, 2, 3) for b in (2, 3)]
    pool += [("spider", gen.spider([1, 2, 3])), ("spider2", gen.spider([2, 2, 2]))]
    pool += [("petersen", gen.petersen()), ("gp72", gen.generalized_petersen(7, 2))]
    pool += [("Q3", gen.hypercube(3)), ("grid34", gen.grid(3, 4))]
    for seed in range(5):
        pool.append((f"gnp{seed}", gen.random_gnp(8, 0.4, seed=seed)))
        pool.append((f"tree{seed}", gen.random_tree(9, seed=seed)))
        pool.append((f"chordal{seed}", gen.random_chordal(8, seed=seed)))
        pool.append((f"reg{seed}", gen.random_regular(10, 3, seed=seed)))
        pool.append((f"bip{seed}", gen.random_bipartite(4, 4, 0.5, seed=seed)[0]))
        pool.append((f"rsplit{seed}", gen.random_split(8, seed=seed)[0]))
        pool.append(
            (f"orient{seed}", gen.random_orientation(gen.random_regular(8, 4, seed=seed), seed=seed, min_outdeg=2))
        )
        pool.append((f"even{seed}", gen.random_strong_even_digraph(3, 4, seed=seed)[0]))
    return pool


POOL = census_instances()


# --------------------------------------------------------------------------------------
# 1.  Paths
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize("n", range(3, 16))
def test_path_2kernel_iff_odd(n: int) -> None:
    """P_n (n >= 3) has a 2-kernel iff n is odd; it is then unique, of size (n+1)/2."""
    P = gen.path(n)
    kernels = all_2kernels(P)
    if n % 2 == 1:
        assert len(kernels) == 1, f"P_{n} should have exactly one 2-kernel"
        assert popcount(kernels[0]) == (n + 1) // 2
        assert is_2kernel(P, kernels[0])
    else:
        assert kernels == [], f"P_{n} should have no 2-kernel"


# --------------------------------------------------------------------------------------
# 2.  Cycles
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize("n", range(4, 17))
def test_cycle_2kernel_iff_even(n: int) -> None:
    """C_n (n >= 4) has a 2-kernel iff n is even: exactly two, disjoint, of size n/2."""
    C = gen.cycle(n)
    kernels = all_2kernels(C)
    if n % 2 == 0:
        assert len(kernels) == 2, f"C_{n} should have exactly two 2-kernels"
        assert all(popcount(S) == n // 2 for S in kernels)
        assert kernels[0] & kernels[1] == 0, "the two 2-kernels must be disjoint"
        assert kernels[0] | kernels[1] == C.full
    else:
        assert kernels == [], f"C_{n} should have no 2-kernel"


# --------------------------------------------------------------------------------------
# 3.  P_4 and complete graphs
# --------------------------------------------------------------------------------------


def test_p4_has_no_2kernel() -> None:
    """P_4 has no 2-kernel."""
    assert not has_2kernel(gen.path(4))


@pytest.mark.parametrize("n", range(2, 9))
def test_complete_graph_has_no_2kernel(n: int) -> None:
    """K_n has no 2-kernel for every n >= 2: an independent set has at most one vertex."""
    assert not has_2kernel(gen.complete(n))


# --------------------------------------------------------------------------------------
# 4.  Double stars
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize("a,b", [(2, 2), (2, 3), (3, 3), (2, 5), (4, 4), (3, 6)])
def test_double_star_leaves_form_a_2kernel(a: int, b: int) -> None:
    """The leaf set of a double star is a 2-kernel, and it meets *both* colour classes.

    So the conjecture "the leaves of a graph with a 2-kernel lie in one bipartition class"
    is false: the leaves of the two centres are at distance 3.
    """
    D = gen.double_star(a, b)
    leaves = 0
    for v in range(D.n):
        if D.degree(v) == 1:
            leaves |= 1 << v
    assert popcount(leaves) == a + b
    assert is_2kernel(D, leaves)
    assert has_2kernel(D)

    G = D.underlying_networkx()
    left, right = nx.bipartite.sets(G)
    leaf_set = set(bits(leaves))
    assert leaf_set & left and leaf_set & right, (
        "the leaves of a double star must straddle both bipartition classes"
    )


# --------------------------------------------------------------------------------------
# 5.  Leaves and strong support vertices (Włoch Thm 2.3)
# --------------------------------------------------------------------------------------


def leaves_of(D: Digraph) -> int:
    """Mask of the vertices of degree 1."""
    return sum(1 << v for v in range(D.n) if D.degree(v) == 1)


def every_vertex_is_leaf_or_strong_support(D: Digraph) -> bool:
    """A strong support vertex is a vertex with at least two leaf neighbours."""
    leaves = leaves_of(D)
    return all(
        (leaves & (1 << v)) or popcount(D.adj[v] & leaves) >= 2 for v in range(D.n)
    )


def strong_support_instances() -> list[tuple[str, Digraph]]:
    out: list[tuple[str, Digraph]] = [
        (f"star{k}", gen.star(k)) for k in range(2, 7)
    ]
    out += [(f"dstar{a},{b}", gen.double_star(a, b)) for a, b in [(2, 2), (2, 4), (3, 3)]]
    bases = [
        ("P1", gen.path(1)), ("P2", gen.path(2)), ("P4", gen.path(4)),
        ("C3", gen.cycle(3)), ("C5", gen.cycle(5)), ("K4", gen.complete(4)),
        ("tree", gen.random_tree(6, seed=0)),
    ]
    for k in (2, 3):
        for name, base in bases:
            out.append((f"corona({name},{k})", gen.corona_leaves(base, k)[0]))
    return out


def test_leaves_are_a_2kernel_when_every_vertex_is_a_leaf_or_strong_support() -> None:
    """Włoch Thm 2.3: then the set of leaves is a 2-kernel."""
    instances = strong_support_instances()
    assert instances
    for name, D in instances:
        assert every_vertex_is_leaf_or_strong_support(D), f"{name} fails the hypothesis"
        leaves = leaves_of(D)
        assert is_2kernel(D, leaves), f"the leaf set of {name} is not a 2-kernel"


# --------------------------------------------------------------------------------------
# 6.  Bipartite graphs whose pendant vertices are pairwise at even distance
#     (Włoch Thm 2.4)
# --------------------------------------------------------------------------------------


def pendants_pairwise_even(D: Digraph) -> bool:
    """Is every pendant vertex at even distance from every other pendant vertex?"""
    G = D.underlying_networkx()
    pend = list(bits(leaves_of(D)))
    dist = dict(nx.all_pairs_shortest_path_length(G))
    return all(
        dist[u][v] % 2 == 0 for u, v in itertools.combinations(pend, 2)
    )


def pendant_part(D: Digraph) -> int:
    """The bipartition class holding the pendant vertices (either class if there are none).

    In a connected bipartite graph two vertices are at even distance exactly when they lie
    in the same class, so the hypothesis of Thm 2.4 says precisely that all pendants share
    a class; that class is the one the theorem calls V1.
    """
    left, right = cls.parity_classes(D)
    pend = leaves_of(D)
    return right if pend & right else left


def test_bipartite_even_pendant_distance_gives_a_2kernel_atlas() -> None:
    """Włoch Thm 2.4 over every connected bipartite atlas graph on >= 2 vertices."""
    checked = 0
    for D in gen.atlas_graphs(min_n=2):
        f = cls.undirected_flags(D)
        if not (f["connected"] and f["bipartite"]):
            continue
        if not pendants_pairwise_even(D):
            continue
        checked += 1
        V1 = pendant_part(D)
        assert is_2kernel(D, V1), "V1 must be a 2-kernel"
        # cross-check the reformulation used by pendant_part
        left, right = cls.parity_classes(D)
        pend = leaves_of(D)
        assert not (pend & left and pend & right), "pendants must share one class"
    assert checked > 50, f"only {checked} instances exercised the theorem"


def test_bipartite_min_degree_two_gives_two_2kernels() -> None:
    """The special case: no pendants at all, so *both* classes are 2-kernels."""
    seen = 0
    for D in gen.atlas_graphs(min_n=2):
        f = cls.undirected_flags(D)
        if not (f["connected"] and f["bipartite"]):
            continue
        if min(D.degree(v) for v in range(D.n)) < 2:
            continue
        seen += 1
        left, right = cls.parity_classes(D)
        assert is_2kernel(D, left) and is_2kernel(D, right)
    for seed in range(50):
        D, A, B = gen.random_bipartite(4, 5, 0.7, seed=seed)
        if D.n == 0 or min(D.degree(v) for v in range(D.n)) < 2:
            continue
        if not cls.undirected_flags(D)["connected"]:
            continue
        seen += 1
        assert is_2kernel(D, A) and is_2kernel(D, B)
    assert seen > 20


# --------------------------------------------------------------------------------------
# 7.  The size bound |J| >= n - m/2 (Włoch Thm 2.5)
# --------------------------------------------------------------------------------------


def test_size_bound_on_every_kernel_in_the_pool() -> None:
    """|J| >= n - m/2 for every 2-kernel, and |J| >= (n+1)/2 additionally for trees.

    Both are tight: the bound counts the >= 2 edges each outside vertex sends into J
    against the m edges available.
    """
    checked = 0
    for name, D in POOL:
        tree = cls.undirected_flags(D)["tree"]
        for S in all_2kernels(D):
            checked += 1
            size = popcount(S)
            assert 2 * size >= 2 * D.n - D.num_edges, (
                f"{name}: |J|={size} violates |J| >= n - m/2 (n={D.n}, m={D.num_edges})"
            )
            if tree:
                assert 2 * size >= D.n + 1, (
                    f"{name}: tree kernel |J|={size} violates |J| >= (n+1)/2"
                )
    assert checked > 1000, f"only {checked} kernels checked"


# --------------------------------------------------------------------------------------
# 8.  The Petersen graph
# --------------------------------------------------------------------------------------


def test_petersen_graph() -> None:
    """Petersen has 2-kernels; the count, the sizes, and {0,2,8,9} are all recorded here.

    Counting argument for the size: Petersen is cubic with n = 10, m = 15, so
    |J| >= n - m/2 = 2.5, and a set of size 4 leaves 6 vertices each needing two of the
    12 edges out of J -- so the 5 maximum independent sets are the only candidates.
    """
    P = gen.petersen()
    kernels = all_2kernels(P)
    assert kernels, "the Petersen graph must have a 2-kernel"
    assert len(kernels) == 5
    assert min_2kernel_size(P) == 4
    assert all(popcount(S) == 4 for S in kernels)
    assert is_2kernel(P, 0b1100000101)  # {0, 2, 8, 9}
    assert 0b1100000101 in kernels


# --------------------------------------------------------------------------------------
# 9.  Simplicial graphs (Włoch Thm 2.11)
# --------------------------------------------------------------------------------------


def simplicial_criterion(D: Digraph) -> bool:
    """Every simplex has exactly one simplicial vertex and every non-simplicial vertex
    lies in at least two simplices."""
    simp = cls.simplicial_vertices(D)
    sims = cls.simplices(D)
    if any(popcount(s & simp) != 1 for s in sims):
        return False
    return all(
        sum(1 for s in sims if s & (1 << v)) >= 2 for v in bits(D.full & ~simp)
    )


def test_simplicial_graph_criterion_over_the_atlas() -> None:
    """Włoch Thm 2.11, brute-forced over every simplicial graph on at most 7 vertices."""
    checked = 0
    for D in gen.atlas_graphs(min_n=1):
        if not cls.is_simplicial_graph(D):
            continue
        checked += 1
        assert simplicial_criterion(D) == has_2kernel(D), (
            f"criterion disagrees on the simplicial graph with edges "
            f"{sorted(D.underlying_networkx().edges())}"
        )
    assert checked > 400, f"only {checked} simplicial atlas graphs found"


# --------------------------------------------------------------------------------------
# 10.  Split graphs (Włoch Thm 2.12)
# --------------------------------------------------------------------------------------


def split_criterion(D: Digraph, C: int, I: int) -> bool:
    """(a) every vertex of C has >= 2 neighbours in I, or (b) exactly one has none."""
    degrees = [popcount(D.adj[c] & I) for c in bits(C)]
    return all(d >= 2 for d in degrees) or degrees.count(0) == 1


@pytest.mark.parametrize("n", range(2, 10))
def test_split_graph_criterion_exhaustive(n: int) -> None:
    """Brute force over every connected split graph on n <= 9 vertices, |C| >= 2."""
    checked = 0
    for D, C, I in gen.all_split_graphs(n):
        checked += 1
        assert split_criterion(D, C, I) == has_2kernel(D), (
            f"criterion disagrees on split graph with edges "
            f"{sorted(D.underlying_networkx().edges())}, C={C:b}"
        )
    assert checked > 0


@pytest.mark.parametrize("n", range(2, 8))
def test_split_criterion_does_not_depend_on_the_split_partition(n: int) -> None:
    """Split partitions are not unique; the criterion must not notice."""
    for D, _C, _I in gen.all_split_graphs(n):
        values = {
            split_criterion(D, C, I)
            for C, I in cls.split_partitions(D)
            if popcount(C) >= 2
        }
        assert len(values) <= 1, (
            f"criterion depends on the partition for edges "
            f"{sorted(D.underlying_networkx().edges())}"
        )


# --------------------------------------------------------------------------------------
# 11.  Tournaments
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize("n", range(2, 6))
def test_no_tournament_has_a_2kernel_exhaustive(n: int) -> None:
    """No tournament on n >= 2 vertices has a 2-kernel (all 2^C(n,2) of them)."""
    for T in gen.all_orientations(gen.complete(n)):
        assert not has_2kernel(T)


@pytest.mark.parametrize("n", range(6, 11))
def test_no_tournament_has_a_2kernel_sampled(n: int) -> None:
    """Same, on seeded random tournaments for the sizes that are too big to exhaust."""
    for seed in range(20):
        T = Digraph.from_networkx(nx.tournament.random_tournament(n, seed=seed))
        assert not has_2kernel(T)


# --------------------------------------------------------------------------------------
# 12.  Theorem A: bipartite underlying graph, out-degree >= 2 on one side
# --------------------------------------------------------------------------------------


def test_theorem_a_on_500_random_bipartite_orientations() -> None:
    """If the underlying graph is bipartite with parts A, B and every vertex of B has
    out-degree >= 2, then A is a 2-kernel.

    Proof in one line: every arc out of B lands in A because the underlying graph is
    bipartite, and A is independent for the same reason.
    """
    tested = 0
    seed = 0
    while tested < 500:
        a = 2 + seed % 4
        b = 2 + (seed // 4) % 4
        G, A, B = gen.random_bipartite(a, b, 0.45 + 0.1 * (seed % 3), seed=seed)
        seed += 1
        if any(G.degree(v) < 2 for v in bits(B)):
            continue
        D = gen.orientation_out_of(G, B, 2, seed=seed)
        assert D.adj == G.adj
        assert all(D.out_degree(v) >= 2 for v in bits(B))
        assert cls.digraph_flags(D)["underlying_bipartite"]
        assert is_2kernel(D, A), f"Theorem A fails at seed {seed}"
        tested += 1
    assert tested == 500


# --------------------------------------------------------------------------------------
# 13.  Theorem B: strong, all cycles even, delta+ >= 2
# --------------------------------------------------------------------------------------


def test_theorem_b_on_500_random_strong_even_digraphs() -> None:
    """Both parity classes of the BFS 2-colouring are 2-kernels.

    The first 50 instances also have their cycle parity confirmed by ``nx.simple_cycles``
    rather than by this package's own recognizer.
    """
    for seed in range(500):
        a = 2 + seed % 4
        b = 2 + (seed // 4) % 4
        D, A, B = gen.random_strong_even_digraph(a, b, seed=seed, min_outdeg=2)
        assert nx.is_strongly_connected(D.to_digraph())
        assert D.min_outdeg >= 2
        assert cls.all_cycles_even(D)
        if seed < 50:
            assert all(
                len(c) % 2 == 0 for c in nx.simple_cycles(D.to_digraph())
            ), f"odd directed cycle at seed {seed}"
        classes_ = cls.parity_classes(D)
        assert classes_ is not None
        assert set(classes_) == {A, B}
        assert is_2kernel(D, A), f"Theorem B fails for class A at seed {seed}"
        assert is_2kernel(D, B), f"Theorem B fails for class B at seed {seed}"


# --------------------------------------------------------------------------------------
# 14.  Theorem C: strongness cannot be dropped from Theorem B
# --------------------------------------------------------------------------------------


def theorem_c_digraph() -> Digraph:
    """Vertices 1,2,3,4,a,b -> 0,1,2,3,4,5.

    A symmetric C4 on 1-2-3-4-1 (all eight arcs), plus a->1, a->2, a->b, b->2, b->3.
    """
    c4 = [(0, 1), (1, 2), (2, 3), (3, 0)]
    arcs = [(u, v) for u, v in c4] + [(v, u) for u, v in c4]
    arcs += [(4, 0), (4, 1), (4, 5), (5, 1), (5, 2)]
    return Digraph.from_arcs(6, arcs)


def test_theorem_c_counterexample() -> None:
    """All directed cycles even and delta+ = 2, yet no 2-kernel.

    Verified independently of this package's own cycle test: the cycles come from
    ``nx.simple_cycles``.
    """
    D = theorem_c_digraph()
    assert not D.is_symmetric()

    cycles = list(nx.simple_cycles(D.to_digraph()))
    assert cycles, "the digraph does have directed cycles"
    assert all(len(c) % 2 == 0 for c in cycles), (
        f"odd cycle found: {[c for c in cycles if len(c) % 2]}"
    )
    assert D.min_outdeg == 2
    assert not has_2kernel(D), "Theorem C: this digraph must have no 2-kernel"


def test_theorem_c_is_not_strong() -> None:
    """The one hypothesis of Theorem B that fails here is strong connectedness."""
    assert not nx.is_strongly_connected(theorem_c_digraph().to_digraph())


# --------------------------------------------------------------------------------------
# 15.  Round trip: a symmetric digraph must behave exactly like the graph
# --------------------------------------------------------------------------------------


def test_symmetric_digraph_matches_the_undirected_graph() -> None:
    """For every graph in the pool, reading it as an nx.Graph and as the equivalent
    nx.DiGraph must give identical 2-kernel results."""
    for name, D in POOL:
        if not D.is_symmetric():
            continue
        G = D.underlying_networkx()
        as_graph = Digraph.from_networkx(G)
        as_digraph = Digraph.from_networkx(nx.DiGraph(G))
        assert as_digraph.is_symmetric()
        assert as_graph.out == as_digraph.out == D.out
        assert all_2kernels(as_graph) == all_2kernels(as_digraph) == all_2kernels(D), name
        assert cls.digraph_flags(as_digraph)["symmetric"]


# --------------------------------------------------------------------------------------
# 16.  Agreement between solve_dpll and the reference solver
# --------------------------------------------------------------------------------------


def test_dpll_agrees_with_the_reference_solver_on_the_pool() -> None:
    """Property test over the whole pool: existence must agree, and any set that
    solve_dpll returns must be a genuine 2-kernel."""
    for name, D in POOL:
        reference = all_2kernels(D)
        S = solve_dpll(D)
        assert (S is not None) == bool(reference), f"disagreement on {name}"
        if S is not None:
            assert is_2kernel(D, S) and S in reference, f"bad certificate on {name}"


def test_forcing_closure_never_contradicts_the_reference_solver() -> None:
    """A CONFLICT verdict is a proof of non-existence, so it must never be wrong."""
    for name, D in POOL:
        status, verdict = forcing_closure(D)
        exists = has_2kernel(D)
        if verdict is Verdict.CONFLICT:
            assert not exists, f"CONFLICT but a 2-kernel exists: {name}"
        if verdict is Verdict.SOLVED:
            assert exists, f"SOLVED but no 2-kernel exists: {name}"
