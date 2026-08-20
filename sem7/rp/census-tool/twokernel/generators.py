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

import itertools
import random
from collections import deque
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
    "all_orientations",
    "random_gnp",
    "random_regular",
    "random_tree",
    "random_bipartite",
    "random_chordal",
    "random_split",
    "random_orientation",
    "orientation_out_of",
    "random_strong_even_digraph",
    "all_split_graphs",
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


# --------------------------------------------------------------------------------------
# random families -- every one of these takes an explicit seed
# --------------------------------------------------------------------------------------


def random_gnp(n: int, p: float, seed: int) -> Digraph:
    """Erdos--Renyi ``G(n, p)``."""
    return from_nx(nx.gnp_random_graph(n, p, seed=seed))


def random_regular(n: int, d: int, seed: int) -> Digraph:
    """A random ``d``-regular graph on ``n`` vertices (``n*d`` must be even)."""
    return from_nx(nx.random_regular_graph(d, n, seed=seed))


def random_tree(n: int, seed: int) -> Digraph:
    """A uniformly random labelled tree on ``n`` vertices."""
    return from_nx(nx.random_labeled_tree(n, seed=seed))


def random_bipartite(a: int, b: int, p: float, seed: int) -> tuple[Digraph, int, int]:
    """A random bipartite graph, plus the masks of the two parts ``A`` and ``B``.

    ``A`` is ``0 .. a-1`` and ``B`` is ``a .. a+b-1``.
    """
    rng = random.Random(seed)
    edges = [
        (u, a + v) for u in range(a) for v in range(b) if rng.random() < p
    ]
    A = (1 << a) - 1
    B = ((1 << (a + b)) - 1) & ~A
    return Digraph.from_edges(a + b, edges), A, B


def random_chordal(n: int, seed: int, p: float = 0.5) -> Digraph:
    """A random chordal graph.

    Vertices are added one at a time, each joined to a random subset of a randomly grown
    clique among the vertices already present.  Every new vertex is therefore simplicial
    when added, so the reverse insertion order is a perfect elimination ordering and the
    result is chordal.
    """
    rng = random.Random(seed)
    adj = [0] * n
    for v in range(1, n):
        u = rng.randrange(v)
        clique = [u]
        cand = [w for w in range(v) if w != u and adj[u] & (1 << w)]
        rng.shuffle(cand)
        for w in cand:
            if all(adj[w] & (1 << c) for c in clique):
                clique.append(w)
        for w in clique:
            if w == u or rng.random() < p:
                adj[v] |= 1 << w
                adj[w] |= 1 << v
    return Digraph(n, adj, adj)


def random_split(
    n: int, seed: int, clique_size: int | None = None, p: float = 0.5
) -> tuple[Digraph, int, int]:
    """A random split graph, plus the masks of the clique ``C`` and independent set ``I``.

    ``C`` is ``0 .. k-1`` and ``I`` is the rest; every ``C``--``I`` pair is joined with
    probability ``p``.
    """
    rng = random.Random(seed)
    k = clique_size if clique_size is not None else rng.randint(1, max(1, n - 1))
    edges = [(u, v) for u in range(k) for v in range(u + 1, k)]
    edges += [
        (u, v) for u in range(k) for v in range(k, n) if rng.random() < p
    ]
    C = (1 << k) - 1
    return Digraph.from_edges(n, edges), C, ((1 << n) - 1) & ~C


def _repair_out_degrees(
    n: int, orient: dict[tuple[int, int], tuple[int, int]], req: list[int]
) -> None:
    """Flip arcs in place until every vertex ``v`` has out-degree at least ``req[v]``.

    Augmenting paths: to give a deficient ``v`` one more out-arc, find a directed path
    ``y -> ... -> v`` whose first vertex has out-degree to spare and reverse every arc on
    it.  ``y`` loses one out-arc, ``v`` gains one, and every interior vertex trades an
    out-arc for an out-arc, so the total deficiency drops by one per augmentation.  Raises
    :class:`ValueError` when no such path exists, which means the constraint is infeasible
    for this graph.
    """
    outdeg = [0] * n
    for tail, _head in orient.values():
        outdeg[tail] += 1

    def augment(v: int) -> None:
        parent: dict[int, int] = {v: -1}
        queue = deque([v])
        while queue:
            x = queue.popleft()
            for edge, (tail, head) in orient.items():
                if head != x or tail in parent:
                    continue
                parent[tail] = x
                if outdeg[tail] > req[tail]:
                    y = tail
                    while y != v:
                        nxt = parent[y]
                        edge_key = (y, nxt) if (y, nxt) in orient else (nxt, y)
                        orient[edge_key] = (nxt, y)
                        y = nxt
                    outdeg[tail] -= 1
                    outdeg[v] += 1
                    return
                queue.append(tail)
        raise ValueError(f"out-degree {req[v]} at vertex {v} is not achievable")

    for v in range(n):
        while outdeg[v] < req[v]:
            augment(v)


def _edge_list(D: Digraph) -> list[tuple[int, int]]:
    return [
        (v, w) for v in range(D.n) for w in bits(D.adj[v] & ~((1 << (v + 1)) - 1))
    ]


def random_orientation(D: Digraph, seed: int, min_outdeg: int = 0) -> Digraph:
    """A random orientation of the underlying graph with ``delta+ >= min_outdeg``.

    The orientation is drawn uniformly and then repaired by
    :func:`_repair_out_degrees`; rejection sampling is useless here because the
    constraint is often tight (a ``2k``-regular graph with ``delta+ >= k`` forces an
    Eulerian orientation, which random draws essentially never hit).  Raises
    :class:`ValueError` when no orientation meets the constraint.
    """
    rng = random.Random(seed)
    edges = _edge_list(D)
    orient = {
        (v, w): ((w, v) if rng.random() < 0.5 else (v, w)) for v, w in edges
    }
    if min_outdeg:
        _repair_out_degrees(D.n, orient, [min_outdeg] * D.n)
    return Digraph.from_arcs(D.n, list(orient.values()))


def orientation_out_of(D: Digraph, part: int, k: int, seed: int) -> Digraph:
    """Random orientation in which every vertex of ``part`` has out-degree at least ``k``.

    Used for Theorem A: orient a bipartite graph so that every vertex of one part has
    out-degree at least 2.  Vertices outside ``part`` are unconstrained.
    """
    rng = random.Random(seed)
    edges = _edge_list(D)
    orient = {
        (v, w): ((w, v) if rng.random() < 0.5 else (v, w)) for v, w in edges
    }
    req = [k if part & (1 << v) else 0 for v in range(D.n)]
    _repair_out_degrees(D.n, orient, req)
    return Digraph.from_arcs(D.n, list(orient.values()))


def random_strong_even_digraph(
    a: int, b: int, seed: int, min_outdeg: int = 2, extra: float = 0.3
) -> tuple[Digraph, int, int]:
    """A random strong digraph in which every directed cycle is even.

    Built from a parity 2-colouring: the vertex set is split into ``A`` (``0..a-1``) and
    ``B`` (``a..a+b-1``) and *every* arc runs between the classes, so every directed cycle
    alternates and is even.  A closed alternating walk through all vertices is laid down
    first to make the digraph strong, then random cross arcs are added until
    ``delta+ >= min_outdeg``.  Returns the digraph and the two class masks.
    """
    if a < 1 or b < 1:
        raise ValueError("both classes must be non-empty")
    rng = random.Random(seed)
    n = a + b
    A = list(range(a))
    B = list(range(a, n))
    arcs: set[tuple[int, int]] = set()

    # closed alternating walk covering every vertex -> strongly connected
    steps = max(a, b)
    for i in range(steps):
        u, v, w = A[i % a], B[i % b], A[(i + 1) % a]
        arcs.add((u, v))
        arcs.add((v, w))

    for u in A:
        for v in B:
            if rng.random() < extra:
                arcs.add((u, v))
            if rng.random() < extra:
                arcs.add((v, u))

    D = Digraph.from_arcs(n, sorted(arcs))
    while D.min_outdeg < min_outdeg:
        for v in range(n):
            targets = B if v < a else A
            while D.out_degree(v) < min_outdeg:
                w = rng.choice(targets)
                if w != v:
                    arcs.add((v, w))
                    D = Digraph.from_arcs(n, sorted(arcs))
    Amask = (1 << a) - 1
    return D, Amask, ((1 << n) - 1) & ~Amask


def all_split_graphs(
    n: int, min_clique: int = 2, connected: bool = True
) -> Iterator[tuple[Digraph, int, int]]:
    """Every split graph on ``n`` vertices, with the split partition it was built from.

    A split graph is a clique ``C`` (vertices ``0 .. k-1``), an independent set ``I``, and
    an arbitrary bipartite adjacency between them, so it is fully described by the
    *multiset* of neighbourhoods ``N(u) ⊆ C`` for ``u ∈ I``.  Enumerating sorted multisets
    covers every split graph on ``n`` vertices up to isomorphism (isomorphic copies may
    appear more than once, which is harmless for exhaustive verification).

    With ``connected=True`` every ``N(u)`` is non-empty, which for a split graph with
    non-empty ``C`` is exactly connectedness.
    """
    for k in range(min_clique, n + 1):
        size = n - k
        pool = list(range(1 if connected else 0, 1 << k))
        for combo in itertools.combinations_with_replacement(pool, size):
            edges = [(u, v) for u in range(k) for v in range(u + 1, k)]
            for j, nbhd in enumerate(combo):
                edges.extend((c, k + j) for c in bits(nbhd))
            C = (1 << k) - 1
            yield Digraph.from_edges(n, edges), C, ((1 << n) - 1) & ~C
