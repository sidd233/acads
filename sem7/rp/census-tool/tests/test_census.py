"""The census layer: the graph6/digraph6 codec, canonical forms, idempotent inserts,
and the two experiment results that are theorems rather than tabulations (E5 and E6)."""

from __future__ import annotations

import itertools
import random

import networkx as nx
import pytest

from twokernel import census
from twokernel import classes as cls
from twokernel import experiments
from twokernel import generators as gen
from twokernel.core import Digraph, all_2kernels, has_2kernel, is_2kernel


# --------------------------------------------------------------------------------------
# codec
# --------------------------------------------------------------------------------------


def test_graph6_matches_networkx_over_the_whole_atlas() -> None:
    for D in gen.atlas_graphs():
        expected = (
            nx.to_graph6_bytes(D.underlying_networkx(), header=False).decode().strip()
        )
        assert census.graph6(D) == expected


def test_digraph6_round_trips() -> None:
    rng = random.Random(0)
    for _ in range(400):
        n = rng.randint(1, 8)
        arcs = [
            (u, v) for u in range(n) for v in range(n) if u != v and rng.random() < 0.4
        ]
        D = Digraph.from_arcs(n, arcs)
        back = census.decode(census.encode(D))
        assert (back.out, back.inn) == (D.out, D.inn)


# --------------------------------------------------------------------------------------
# canonical form
# --------------------------------------------------------------------------------------


def test_canonical_key_separates_exactly_the_isomorphism_classes() -> None:
    """The atlas is one graph per isomorphism class, so all 1253 keys must differ."""
    keys = [census.canonical_key(D)[0] for D in gen.atlas_graphs()]
    assert len(set(keys)) == len(keys) == 1253


def test_canonical_key_is_invariant_under_relabelling() -> None:
    rng = random.Random(7)
    for i, D in enumerate(gen.atlas_graphs(min_n=1)):
        if i % 5:
            continue
        perm = list(range(D.n))
        rng.shuffle(perm)
        relabelled = Digraph.from_arcs(D.n, [(perm[u], perm[v]) for u, v in D.arcs()])
        assert census.canonical_key(relabelled)[0] == census.canonical_key(D)[0]


def test_canonical_key_agrees_with_networkx_isomorphism_on_digraphs() -> None:
    """Same canonical key iff isomorphic, checked against VF2 on orientations of C5."""
    orientations = list(gen.all_orientations(gen.cycle(5)))
    for A, B in itertools.combinations(orientations, 2):
        same_key = census.canonical_key(A)[0] == census.canonical_key(B)[0]
        assert same_key == nx.is_isomorphic(A.to_digraph(), B.to_digraph())


# --------------------------------------------------------------------------------------
# database
# --------------------------------------------------------------------------------------


def test_inserts_are_idempotent(tmp_path) -> None:
    db = str(tmp_path / "t.sqlite3")
    conn = census.connect(db)
    for _ in range(2):
        census.run_family(conn, "atlas7", limit=40, quiet=True)
    assert conn.execute("SELECT COUNT(*) FROM graphs").fetchone()[0] == 40
    assert conn.execute("SELECT COUNT(*) FROM membership").fetchone()[0] == 40


def test_row_contents_match_the_library(tmp_path) -> None:
    db = str(tmp_path / "t.sqlite3")
    conn = census.connect(db)
    census.run_family(conn, "named", quiet=True)
    for row in conn.execute("SELECT * FROM graphs").fetchall():
        D = census.decode(row["key"])
        kernels = all_2kernels(D)
        assert row["count_2kernels"] == len(kernels)
        assert row["has_2kernel"] == int(bool(kernels))
        assert row["n"] == D.n and row["m"] == D.num_edges
        if kernels:
            assert row["min_size"] == min(bin(S).count("1") for S in kernels)


# --------------------------------------------------------------------------------------
# E5 and E6, which are proved statements and so belong under test
# --------------------------------------------------------------------------------------


def test_e5_subdivision_always_has_the_original_vertices_as_a_2kernel() -> None:
    """E5: V(G) is a 2-kernel of S(G) for every atlas graph.  A free infinite family."""
    for G in gen.atlas_graphs():
        S, original = gen.subdivision(G)
        assert is_2kernel(S, original)


def test_e6_dags_have_at_most_one_2kernel_and_it_is_computable_in_linear_time() -> None:
    """E6: reverse-topological propagation is exact on DAGs, so a DAG has at most one
    2-kernel and existence is decidable in polynomial time."""
    for n in range(1, 7):
        for D in gen.all_dags_min_outdeg(n, 2):
            kernels = all_2kernels(D)
            assert len(kernels) <= 1
            mine = experiments.dag_2kernel(D)
            assert (mine is not None) == bool(kernels)
            if mine is not None:
                assert mine == kernels[0]


def test_e6_holds_for_dags_without_the_degree_condition() -> None:
    rng = random.Random(0)
    for _ in range(3000):
        n = rng.randint(1, 8)
        arcs = [
            (i, j) for i in range(n) for j in range(i + 1, n) if rng.random() < 0.35
        ]
        D = Digraph.from_arcs(n, arcs)
        kernels = all_2kernels(D)
        assert len(kernels) <= 1
        mine = experiments.dag_2kernel(D)
        assert (mine is not None) == bool(kernels)


def test_e3_no_oriented_graph_below_eight_vertices_has_a_2kernel() -> None:
    """E3: exhaustive over every orientation of every connected graph on <= 6 vertices
    with delta+ >= 2, and the counting bound in FINDINGS.md pushes it to n <= 7."""
    seen = 0
    for G in gen.atlas_graphs(min_n=1, max_n=6):
        if G.n == 0 or not nx.is_connected(G.underlying_networkx()):
            continue
        for D in gen.all_orientations(G):
            if D.min_outdeg >= 2:
                seen += 1
                assert not has_2kernel(D)
    assert seen > 100


def test_e3_extremal_oriented_graph_on_eight_vertices() -> None:
    """The counting bound n >= 8 is tight: this oriented graph attains it."""
    arcs = []
    for i in range(4):
        arcs += [(4 + i, i), (4 + i, (i + 1) % 4)]
    for j in range(4):
        pointing_at_j = {(j - 1) % 4, j}
        arcs += [(j, 4 + b) for b in range(4) if b not in pointing_at_j]
    D = Digraph.from_arcs(8, arcs)
    assert D.min_outdeg == 2
    assert not any(D.out[v] & D.inn[v] for v in range(8)), "must have no digons"
    assert is_2kernel(D, 0b00001111)
    assert len(all_2kernels(D)) == 2
