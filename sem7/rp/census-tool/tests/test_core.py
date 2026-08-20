"""Engine sanity: the bitmask machinery, the reference solver, and the forcing rules.

The reference solver is validated against a *naive* solver that tests every one of the
``2^n`` subsets, which assumes nothing about maximal independent sets.  That is what makes
"every 2-kernel is a maximal independent set" a checked claim rather than an assumption.
"""

from __future__ import annotations

import itertools

import pytest

from twokernel import generators as gen
from twokernel.core import (
    Digraph,
    Status,
    Verdict,
    all_2kernels,
    all_maximal_independent_sets,
    bits,
    count_2kernels,
    forced_set,
    forcing_closure,
    has_2kernel,
    is_2kernel,
    max_2kernel_size,
    min_2kernel_size,
    popcount,
    solve_dpll,
)


def brute_force_2kernels(D: Digraph) -> list[int]:
    """Every 2-kernel, by testing all ``2^n`` subsets.  Ground truth for small ``n``."""
    return [S for S in range(1 << D.n) if is_2kernel(D, S)]


def small_atlas() -> list[Digraph]:
    return list(gen.atlas_graphs(max_n=6))


def small_digraphs() -> list[Digraph]:
    """All orientations of every atlas graph on at most 4 vertices, plus C5 and K5."""
    out: list[Digraph] = []
    for G in gen.atlas_graphs(max_n=4):
        out.extend(gen.all_orientations(G))
    out.extend(gen.all_orientations(gen.cycle(5)))
    out.extend(gen.all_orientations(gen.complete(5)))
    return out


# --------------------------------------------------------------------------------------
# representation
# --------------------------------------------------------------------------------------


def test_loops_are_rejected() -> None:
    with pytest.raises(ValueError):
        Digraph.from_arcs(2, [(0, 0)])


def test_symmetric_round_trip() -> None:
    G = gen.petersen()
    assert G.is_symmetric()
    assert G.underlying().out == G.out
    assert G.num_edges == 15
    assert G.num_arcs == 30


def test_orientation_is_not_symmetric_but_has_the_same_underlying_graph() -> None:
    C = gen.cycle(5)
    for D in gen.all_orientations(C):
        assert not D.is_symmetric()
        assert D.adj == C.adj
        assert D.num_arcs == 5


def test_sub_induces_and_relabels() -> None:
    P = gen.path(5)
    H = P.sub(0b11100)  # vertices 2, 3, 4 of the path 0-1-2-3-4
    assert H.n == 3
    assert H.labels == (2, 3, 4)
    assert sorted(H.arcs()) == [(0, 1), (1, 0), (1, 2), (2, 1)]


# --------------------------------------------------------------------------------------
# the reference solver
# --------------------------------------------------------------------------------------


def test_maximal_independent_sets_are_maximal_and_independent() -> None:
    for D in small_atlas():
        seen = set()
        for S in all_maximal_independent_sets(D):
            assert S not in seen, "Bron-Kerbosch must not repeat a set"
            seen.add(S)
            for v in bits(S):
                assert D.adj[v] & S == 0
            for v in bits(D.full & ~S):
                assert D.adj[v] & S, "a maximal set dominates everything outside it"


def test_reference_solver_matches_brute_force_on_graphs() -> None:
    for D in small_atlas():
        assert all_2kernels(D) == sorted(brute_force_2kernels(D))


def test_reference_solver_matches_brute_force_on_digraphs() -> None:
    for D in small_digraphs():
        assert all_2kernels(D) == sorted(brute_force_2kernels(D))


def test_counts_and_sizes_agree_with_the_list() -> None:
    for D in small_atlas():
        kernels = all_2kernels(D)
        assert count_2kernels(D) == len(kernels)
        assert has_2kernel(D) == bool(kernels)
        if kernels:
            assert min_2kernel_size(D) == min(popcount(S) for S in kernels)
            assert max_2kernel_size(D) == max(popcount(S) for S in kernels)
        else:
            assert min_2kernel_size(D) is None
            assert max_2kernel_size(D) is None


def test_verifier_rejects_near_misses() -> None:
    P5 = gen.path(5)
    assert is_2kernel(P5, 0b10101)
    assert not is_2kernel(P5, 0b10111)  # not independent
    assert not is_2kernel(P5, 0b00101)  # vertex 4 sees only one kernel vertex
    assert not is_2kernel(P5, 0)


# --------------------------------------------------------------------------------------
# forcing
# --------------------------------------------------------------------------------------


def test_forced_set_is_contained_in_every_2kernel() -> None:
    for D in small_atlas() + small_digraphs():
        forced = forced_set(D)
        for S in all_2kernels(D):
            assert forced & ~S == 0, "a forced vertex is missing from a 2-kernel"


def test_forced_set_contains_low_outdegree_and_simplicial_vertices() -> None:
    for D in small_atlas():
        forced = forced_set(D)
        for v in range(D.n):
            if D.out_degree(v) <= 1:
                assert forced & (1 << v)
            if not D.has_independent_pair(D.adj[v]):  # simplicial in the undirected case
                assert forced & (1 << v)


def test_forcing_closure_is_sound() -> None:
    """IN must hold in every 2-kernel, OUT in none, and CONFLICT must mean there is none."""
    for D in small_atlas() + small_digraphs():
        status, verdict = forcing_closure(D)
        kernels = all_2kernels(D)
        if verdict is Verdict.CONFLICT:
            assert kernels == [], "CONFLICT claimed but a 2-kernel exists"
            continue
        for S in kernels:
            for v in range(D.n):
                if status[v] is Status.IN:
                    assert S & (1 << v), "IN vertex missing from a 2-kernel"
                elif status[v] is Status.OUT:
                    assert not S & (1 << v), "OUT vertex present in a 2-kernel"
        if verdict is Verdict.SOLVED:
            solution = sum(1 << v for v in range(D.n) if status[v] is Status.IN)
            assert kernels == [solution], "SOLVED must mean a unique, verified 2-kernel"
        else:
            assert Status.UNKNOWN in status


def test_dpll_agrees_with_the_reference_solver() -> None:
    for D in small_atlas() + small_digraphs():
        S = solve_dpll(D)
        assert (S is not None) == has_2kernel(D)
        if S is not None:
            assert is_2kernel(D, S)
            assert S in all_2kernels(D)


# --------------------------------------------------------------------------------------
# completeness of the forcing closure on the classes where it is provably complete
# --------------------------------------------------------------------------------------


def test_forcing_decides_every_chordal_graph() -> None:
    """Theorem E2.1: on a chordal graph the closure never stalls.

    ``G[UNKNOWN]`` is an induced subgraph of a chordal graph, hence chordal, so while it is
    non-empty it has a simplicial vertex, whose non-OUT neighbourhood is a clique -- and
    R4 fires on it.  So no vertex is left UNKNOWN, and the 2-kernel is unique when it
    exists.  Checked here over the atlas; the census checks all 17175 chordal graphs on at
    most 9 vertices.
    """
    import networkx as nx

    checked = 0
    for D in gen.atlas_graphs(min_n=1):
        if not nx.is_chordal(D.underlying_networkx()):
            continue
        checked += 1
        _status, verdict = forcing_closure(D)
        assert verdict is not Verdict.UNDECIDED, "the closure stalled on a chordal graph"
        assert len(all_2kernels(D)) <= 1, "a chordal graph has at most one 2-kernel"
    assert checked > 500, f"only {checked} chordal graphs exercised the theorem"


def test_forcing_decides_every_simplicial_graph_with_r0_and_r1_alone() -> None:
    """Theorem E2.2: every simplicial vertex is forced IN by R0, and every other vertex
    lies in some ``N[x]`` and so is put OUT by R1.  Nothing is left UNKNOWN."""
    from twokernel import classes as cls

    checked = 0
    for D in gen.atlas_graphs(min_n=1):
        if not cls.is_simplicial_graph(D):
            continue
        checked += 1
        _status, verdict = forcing_closure(D)
        assert verdict is not Verdict.UNDECIDED
        assert len(all_2kernels(D)) <= 1
    assert checked > 400, f"only {checked} simplicial graphs exercised the theorem"


def test_bipartite_forcing_completeness_is_false() -> None:
    """The conjecture that forcing decides bipartite graphs held for every bipartite graph
    on at most 7 vertices and is false at 8.  This is the smallest counterexample."""
    import networkx as nx

    from twokernel.canon import decode

    D = decode("G?KsZ_")
    G = D.underlying_networkx()
    assert D.n == 8 and D.num_edges == 10
    assert nx.is_bipartite(G) and nx.is_connected(G)
    assert not has_2kernel(D), "the counterexample must have no 2-kernel"
    _status, verdict = forcing_closure(D)
    assert verdict is Verdict.UNDECIDED, "forcing must fail to decide it"
    # and it does not contradict Wloch Thm 2.4: the two pendants are in different classes
    left, right = nx.bipartite.sets(G)
    pendants = {v for v in range(D.n) if D.degree(v) == 1}
    assert pendants & left and pendants & right
