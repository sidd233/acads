"""The census layer: the graph6/digraph6 codec, canonical forms, idempotent inserts,
and the two experiment results that are theorems rather than tabulations (E5 and E6)."""

from __future__ import annotations

import itertools
import random

import networkx as nx
import pytest

from twokernel import canon
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


def test_both_canonical_backends_induce_the_same_isomorphism_classes() -> None:
    """The fallback backend must partition digraphs exactly as pynauty does.

    Skipped when pynauty is absent, in which case the fallback *is* the only backend and
    the tests around it already cover it.
    """
    if not canon.has_pynauty:
        pytest.skip("pynauty not installed; the fallback is the only backend")
    rng = random.Random(11)
    instances = []
    for _ in range(150):
        n = rng.randint(2, 7)
        arcs = [
            (u, v) for u in range(n) for v in range(n) if u != v and rng.random() < 0.35
        ]
        instances.append(Digraph.from_arcs(n, arcs))
    for A, B in itertools.combinations(instances, 2):
        if A.n != B.n:
            continue
        fallback_same = _fallback_key(A) == _fallback_key(B)
        pynauty_same = canon.canonical_key(A)[0] == canon.canonical_key(B)[0]
        assert fallback_same == pynauty_same


def _fallback_key(D: Digraph) -> str:
    """The key the fallback backend would produce, bypassing pynauty."""
    perm = canon._wl_canonical_labelling(D)
    assert perm is not None
    pos = {u: i for i, u in enumerate(perm)}
    return canon.encode(Digraph.from_arcs(D.n, [(pos[u], pos[w]) for u, w in D.arcs()]))


def test_canonical_key_agrees_with_networkx_isomorphism_on_digraphs() -> None:
    """Same canonical key iff isomorphic, checked against VF2 on orientations of C5."""
    orientations = list(gen.all_orientations(gen.cycle(5)))
    for A, B in itertools.combinations(orientations, 2):
        same_key = census.canonical_key(A)[0] == census.canonical_key(B)[0]
        assert same_key == nx.is_isomorphic(A.to_digraph(), B.to_digraph())


def test_all_graphs_reproduces_the_known_counts() -> None:
    """Canonical augmentation must reproduce the number of graphs on n vertices."""
    known = {0: 1, 1: 1, 2: 2, 3: 4, 4: 11, 5: 34, 6: 156, 7: 1044, 8: 12346}
    for n, expected in known.items():
        if n == 8 and not canon.has_pynauty:
            continue  # the fallback backend cannot canonicalise n = 8
        assert sum(1 for _ in gen.all_graphs(n)) == expected


def test_all_digraphs_reproduces_the_known_counts() -> None:
    """OEIS A000273: digraphs on n nodes up to isomorphism."""
    known = {0: 1, 1: 1, 2: 3, 3: 16, 4: 218, 5: 9608}
    for n, expected in known.items():
        if n >= 5 and not canon.has_pynauty:
            continue  # the fallback backend is too slow to enumerate this level
        assert sum(1 for _ in gen.all_digraphs(n)) == expected


def test_all_digraphs_are_pairwise_non_isomorphic() -> None:
    for n in range(1, 5):
        digraphs = list(gen.all_digraphs(n))
        for A, B in itertools.combinations(digraphs, 2):
            assert not nx.is_isomorphic(A.to_digraph(), B.to_digraph())


def test_all_graphs_are_pairwise_non_isomorphic() -> None:
    for n in range(1, 8):
        graphs = list(gen.all_graphs(n))
        for A, B in itertools.combinations(graphs, 2):
            assert not nx.is_isomorphic(A.underlying_networkx(), B.underlying_networkx())


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
        assert row["degeneracy"] == cls.degeneracy(D)


def test_migration_adds_missing_columns_and_backfill_fills_them(tmp_path) -> None:
    """A database built before `degeneracy` existed gets the column added on connect,
    and `backfill_column` fills it in without touching any other column."""
    db = str(tmp_path / "t.sqlite3")
    conn = census.connect(db)
    census.run_family(conn, "named", quiet=True)
    before = {
        r["key"]: dict(r) for r in conn.execute("SELECT * FROM graphs").fetchall()
    }

    conn.execute("ALTER TABLE graphs RENAME TO graphs_old")
    columns = [c for c in census.ALL_COLUMNS if c != "degeneracy"]
    conn.execute(
        f"CREATE TABLE graphs AS SELECT {', '.join(columns)} FROM graphs_old"
    )
    conn.execute("DROP TABLE graphs_old")
    conn.commit()
    assert "degeneracy" not in {
        r["name"] for r in conn.execute("PRAGMA table_info(graphs)")
    }

    conn = census.connect(db)  # re-running connect() must migrate the schema
    assert "degeneracy" in {r["name"] for r in conn.execute("PRAGMA table_info(graphs)")}
    assert conn.execute(
        "SELECT COUNT(*) c FROM graphs WHERE degeneracy IS NULL"
    ).fetchone()["c"] == len(before)

    n = census.backfill_column(conn, "degeneracy", cls.degeneracy)
    assert n == len(before)
    for row in conn.execute("SELECT * FROM graphs").fetchall():
        D = census.decode(row["key"])
        assert row["degeneracy"] == cls.degeneracy(D)
        for col in columns:
            assert row[col] == before[row["key"]][col], f"{col} changed during backfill"


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


def _extremal_j4t4_constructions():
    """Every labelled instance of the j=4, t=4 extremal shape: each of 4 outside
    vertices chooses 2 of 4 kernel vertices to point at, kept only when every kernel
    vertex ends up pointed at by exactly 2 outside vertices (the balance the proof's
    equalities force); the kernel-to-outside arcs are then forced -- each kernel vertex
    points at exactly the 2 outside vertices that do not point at it."""
    for choice in itertools.product(itertools.combinations(range(4), 2), repeat=4):
        pointers = [0, 0, 0, 0]
        for sub in choice:
            for j in sub:
                pointers[j] += 1
        if pointers != [2, 2, 2, 2]:
            continue
        points_at = [set() for _ in range(4)]
        for i, sub in enumerate(choice):
            for j in sub:
                points_at[j].add(i)
        arcs = [(4 + i, j) for i, sub in enumerate(choice) for j in sub]
        for j in range(4):
            arcs += [(j, 4 + i) for i in range(4) if i not in points_at[j]]
        yield choice, Digraph.from_arcs(8, arcs)


def test_e3_extremal_shape_has_exactly_two_isomorphism_classes() -> None:
    """The j=4, t=4 extremal shape from the tightness proof: exhaustively enumerating
    every way to balance the outside vertices' choices gives 90 labelled instances,
    every one a genuine (J, B) 2-kernel pair, splitting into exactly 2 isomorphism
    classes (sizes 72 and 18) -- so the example already covered by
    test_e3_extremal_oriented_graph_on_eight_vertices is not the only one."""
    Jmask, Bmask = 0b00001111, 0b11110000
    classes: dict[object, list] = {}
    for choice, D in _extremal_j4t4_constructions():
        assert D.min_outdeg == 2
        assert not any(D.out[v] & D.inn[v] for v in range(8)), "must have no digons"
        assert is_2kernel(D, Jmask) and is_2kernel(D, Bmask)
        assert len(all_2kernels(D)) == 2
        classes.setdefault(canon.certificate(D), []).append((choice, D))

    total = sum(len(v) for v in classes.values())
    assert total == 90
    assert len(classes) == 2
    assert sorted(len(v) for v in classes.values()) == [18, 72]

    # the digraph from the other test must appear among these 90, in the size-72 class
    arcs = []
    for i in range(4):
        arcs += [(4 + i, i), (4 + i, (i + 1) % 4)]
    for j in range(4):
        pointing_at_j = {(j - 1) % 4, j}
        arcs += [(j, 4 + b) for b in range(4) if b not in pointing_at_j]
    other_test_D = Digraph.from_arcs(8, arcs)
    other_cert = canon.certificate(other_test_D)
    assert other_cert in classes
    assert len(classes[other_cert]) == 72

    # every instance has underlying graph K_{4,4} on J vs B
    for _choice, D in itertools.chain.from_iterable(classes.values()):
        U = D.underlying_networkx()
        assert sorted(dict(U.degree()).values()) == [4] * 8
        assert all(not (U.has_edge(u, v)) for u, v in itertools.combinations(range(4), 2))
        assert all(
            not (U.has_edge(u, v)) for u, v in itertools.combinations(range(4, 8), 2)
        )
