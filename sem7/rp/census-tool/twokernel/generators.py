"""Graph and digraph generators.  All randomness takes an explicit seed.

Everything returns a :class:`~twokernel.core.Digraph`; undirected graphs are represented
by their symmetric digraph, as everywhere else in this package.

Exhaustive generation uses ``nx.graph_atlas_g()`` (all 1253 graphs on at most 7 vertices).
``pynauty`` is not available in this environment (its C extension needs ``Python.h``), so
larger exhaustive sweeps are done by direct structured encodings -- all orientations of a
graph, split graphs by clique-side neighbourhood multisets, DAGs by upper-triangular arc
sets -- and by seeded random sampling.  This is stated in FINDINGS.md.
"""

from __future__ import annotations

import random
from typing import Iterable, Iterator, Sequence

import networkx as nx

from twokernel.core import Digraph, bits, popcount

__all__ = [
    "from_nx",
    "atlas_graphs",
    "path",
    "cycle",
    "complete",
    "complete_bipartite",
    "star",
    "double_star",
    "spider",
    "petersen",
    "generalized_petersen",
    "hypercube",
    "grid",
    "subdivision",
    "corona_leaves",
]


def from_nx(G) -> Digraph:
    """Convert a networkx graph to a :class:`Digraph`, relabelling nodes to ``0..n-1``."""
    H = nx.convert_node_labels_to_integers(G, ordering="sorted")
    return Digraph.from_networkx(H)


# --------------------------------------------------------------------------------------
# exhaustive
# --------------------------------------------------------------------------------------


def atlas_graphs(min_n: int = 0, max_n: int = 7) -> Iterator[Digraph]:
    """All graphs of ``nx.graph_atlas_g()`` with ``min_n <= n <= max_n``.

    The atlas is exhaustive up to isomorphism for ``n <= 7``: 1253 graphs, ordered by
    number of vertices then number of edges.
    """
    for G in nx.graph_atlas_g():
        if min_n <= G.number_of_nodes() <= max_n:
            yield from_nx(G)


# --------------------------------------------------------------------------------------
# named families
# --------------------------------------------------------------------------------------


def path(n: int) -> Digraph:
    """The path ``P_n`` on ``n`` vertices (``n-1`` edges)."""
    return from_nx(nx.path_graph(n))


def cycle(n: int) -> Digraph:
    """The cycle ``C_n``, ``n >= 3``."""
    if n < 3:
        raise ValueError("cycles need at least 3 vertices")
    return from_nx(nx.cycle_graph(n))


def complete(n: int) -> Digraph:
    """The complete graph ``K_n``."""
    return from_nx(nx.complete_graph(n))


def complete_bipartite(a: int, b: int) -> Digraph:
    """The complete bipartite graph ``K_{a,b}``."""
    return from_nx(nx.complete_bipartite_graph(a, b))


def star(k: int) -> Digraph:
    """The star ``K_{1,k}``: one centre, ``k`` leaves."""
    return from_nx(nx.star_graph(k))


def double_star(a: int, b: int) -> Digraph:
    """Two adjacent centres carrying ``a`` and ``b`` leaves.

    Vertices ``0`` and ``1`` are the centres; ``2 .. a+1`` are the leaves of ``0`` and the
    rest are the leaves of ``1``.  With ``a, b >= 2`` both centres are strong support
    vertices, so the leaf set is a 2-kernel (Włoch, Thm 2.3); the leaves of the two centres
    are at odd distance from each other, hence lie in *different* bipartition classes.
    """
    if a < 1 or b < 1:
        raise ValueError("each centre needs at least one leaf")
    edges = [(0, 1)]
    nxt = 2
    for _ in range(a):
        edges.append((0, nxt))
        nxt += 1
    for _ in range(b):
        edges.append((1, nxt))
        nxt += 1
    return Digraph.from_edges(nxt, edges)


def spider(legs: Sequence[int]) -> Digraph:
    """A spider: a centre (vertex ``0``) with legs of the given lengths."""
    if any(length < 1 for length in legs):
        raise ValueError("legs must have length at least 1")
    edges: list[tuple[int, int]] = []
    nxt = 1
    for length in legs:
        prev = 0
        for _ in range(length):
            edges.append((prev, nxt))
            prev = nxt
            nxt += 1
    return Digraph.from_edges(nxt, edges)


def petersen() -> Digraph:
    """The Petersen graph under ``nx.petersen_graph()`` labelling."""
    return from_nx(nx.petersen_graph())


def generalized_petersen(n: int, k: int) -> Digraph:
    """The generalized Petersen graph ``GP(n, k)``."""
    return from_nx(nx.generalized_petersen_graph(n, k))


def hypercube(d: int) -> Digraph:
    """The ``d``-dimensional hypercube ``Q_d``."""
    return from_nx(nx.hypercube_graph(d))


def grid(rows: int, cols: int) -> Digraph:
    """The ``rows x cols`` grid graph."""
    return from_nx(nx.grid_2d_graph(rows, cols))


def subdivision(D: Digraph) -> tuple[Digraph, int]:
    """The subdivision ``S(G)`` of the underlying graph, plus the mask of ``V(G)``.

    Original vertices keep their indices ``0 .. n-1``; one new vertex is inserted in each
    edge.  ``V(G)`` is always a 2-kernel of ``S(G)``: it is independent (all original
    edges are gone) and every subdivision vertex has exactly its two original endpoints as
    neighbours.
    """
    n = D.n
    edges: list[tuple[int, int]] = []
    nxt = n
    for v in range(n):
        for w in bits(D.adj[v] & ~((1 << (v + 1)) - 1)):
            edges.append((v, nxt))
            edges.append((w, nxt))
            nxt += 1
    return Digraph.from_edges(nxt, edges), (1 << n) - 1


def corona_leaves(D: Digraph, k: int = 2) -> tuple[Digraph, int]:
    """Attach ``k`` pendant leaves to every vertex of the underlying graph of ``D``.

    Returns the new graph and the mask of the leaves.  Every original vertex becomes a
    strong support vertex when ``k >= 2``, so this builds instances for Włoch Thm 2.3.
    """
    if k < 1:
        raise ValueError("k must be at least 1")
    n = D.n
    edges = [
        (v, w) for v in range(n) for w in bits(D.adj[v] & ~((1 << (v + 1)) - 1))
    ]
    leaves = 0
    nxt = n
    for v in range(n):
        for _ in range(k):
            edges.append((v, nxt))
            leaves |= 1 << nxt
            nxt += 1
    return Digraph.from_edges(nxt, edges), leaves


# --------------------------------------------------------------------------------------
# orientations
# --------------------------------------------------------------------------------------


def all_orientations(D: Digraph) -> Iterator[Digraph]:
    """Every orientation of the underlying graph of ``D`` (``2^m`` of them).

    An *orientation* keeps one arc per edge, so the results are oriented graphs: no
    digons.  Applied to ``K_n`` this enumerates all labelled tournaments.
    """
    edges = [
        (v, w) for v in range(D.n) for w in bits(D.adj[v] & ~((1 << (v + 1)) - 1))
    ]
    m = len(edges)
    for choice in range(1 << m):
        arcs = [
            (w, v) if (choice >> i) & 1 else (v, w)
            for i, (v, w) in enumerate(edges)
        ]
        yield Digraph.from_arcs(D.n, arcs)
