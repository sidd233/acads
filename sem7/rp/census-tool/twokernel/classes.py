"""Boolean recognizers and numeric invariants for graphs and digraphs.

Every *undirected* flag is a property of the **underlying graph** of the digraph handed
in, so the same function serves a graph (given as its symmetric digraph) and a digraph.
Digraph flags read the arcs.

The empty digraph (``n = 0``) satisfies every flag vacuously except ``connected``.
"""

from __future__ import annotations

import itertools
from collections import deque
from typing import Iterator

import networkx as nx

from twokernel.core import Digraph, bits, popcount

__all__ = [
    "UNDIRECTED_FLAGS",
    "DIGRAPH_FLAGS",
    "simplicial_vertices",
    "simplices",
    "is_cactus",
    "is_block_graph",
    "is_split",
    "is_interval",
    "is_cograph",
    "is_claw_free",
    "is_simplicial_graph",
    "all_cycles_even",
    "parity_classes",
    "undirected_flags",
    "digraph_flags",
    "flags",
    "girth",
    "odd_girth",
    "independence_number",
    "clique_number",
    "invariants",
]

UNDIRECTED_FLAGS = (
    "bipartite",
    "connected",
    "tree",
    "forest",
    "unicyclic",
    "cactus",
    "chordal",
    "split",
    "interval",
    "cograph",
    "claw_free",
    "planar",
    "regular",
    "triangle_free",
    "block_graph",
    "simplicial_graph",
)

DIGRAPH_FLAGS = (
    "strong",
    "dag",
    "tournament",
    "symmetric",
    "underlying_bipartite",
    "all_cycles_even",
)


# --------------------------------------------------------------------------------------
# simplicial structure
# --------------------------------------------------------------------------------------


def simplicial_vertices(D: Digraph) -> int:
    """Mask of the vertices whose neighbourhood in the underlying graph is a clique."""
    return sum(
        1 << v for v in range(D.n) if not D.has_independent_pair(D.adj[v])
    )


def simplices(D: Digraph) -> list[int]:
    """The distinct closed neighbourhoods ``N[x]`` of simplicial vertices ``x``.

    Distinct *as sets*: two simplicial vertices with the same closed neighbourhood (two
    twins, or all of ``K_n``) contribute one simplex containing both of them.  This is the
    reading of "simplex" used for Włoch Thm 2.11 in :mod:`tests.test_literature`.
    """
    seen: dict[int, None] = {}
    for x in bits(simplicial_vertices(D)):
        seen.setdefault(D.adj[x] | (1 << x), None)
    return sorted(seen)


def is_simplicial_graph(D: Digraph) -> bool:
    """Every vertex lies in ``N[x]`` for some simplicial ``x``."""
    covered = 0
    for simplex in simplices(D):
        covered |= simplex
    return covered == D.full


# --------------------------------------------------------------------------------------
# undirected recognizers
# --------------------------------------------------------------------------------------


def _biconnected_sizes(G) -> Iterator[tuple[int, int]]:
    """``(vertices, edges)`` of each biconnected component of ``G``."""
    for edges in nx.biconnected_component_edges(G):
        edges = list(edges)
        nodes = {u for e in edges for u in e}
        yield len(nodes), len(edges)


def is_cactus(D: Digraph) -> bool:
    """No edge lies on two cycles, i.e. every biconnected component is an edge or cycle.

    A biconnected component on ``k >= 3`` vertices has at least ``k`` edges, with equality
    exactly for a cycle, so the test is ``e <= k`` throughout.
    """
    G = D.underlying_networkx()
    return all(e <= k for k, e in _biconnected_sizes(G))


def is_block_graph(D: Digraph) -> bool:
    """Every biconnected component (block) is a complete graph."""
    G = D.underlying_networkx()
    return all(e == k * (k - 1) // 2 for k, e in _biconnected_sizes(G))


def is_split(D: Digraph) -> bool:
    """Hammer--Simeone degree-sequence criterion.

    With ``d_1 >= ... >= d_n`` and ``k = max{i : d_i >= i-1}``, ``G`` is split iff
    ``sum_{i<=k} d_i = k(k-1) + sum_{i>k} d_i``.
    """
    if D.n == 0:
        return True
    degrees = sorted((D.degree(v) for v in range(D.n)), reverse=True)
    k = max(i for i in range(1, D.n + 1) if degrees[i - 1] >= i - 1)
    return sum(degrees[:k]) == k * (k - 1) + sum(degrees[k:])


def split_partitions(D: Digraph) -> Iterator[tuple[int, int]]:
    """Every partition ``(C, I)`` of the underlying graph into a clique and an
    independent set, as masks.  Split partitions are not unique, which matters for the
    split-graph criterion of Włoch Thm 2.12, so the tests quantify over all of them."""
    if not is_split(D):
        return
    for size in range(D.n + 1):
        for combo in itertools.combinations(range(D.n), size):
            C = sum(1 << v for v in combo)
            I = D.full & ~C
            if all(D.adj[v] & C == C & ~(1 << v) for v in bits(C)) and all(
                D.adj[v] & I == 0 for v in bits(I)
            ):
                yield C, I


def is_claw_free(D: Digraph) -> bool:
    """No induced ``K_{1,3}``: no neighbourhood contains an independent triple."""
    for v in range(D.n):
        nb = list(bits(D.adj[v]))
        for a, b, c in itertools.combinations(nb, 3):
            if not (D.adj[a] & (1 << b) or D.adj[a] & (1 << c) or D.adj[b] & (1 << c)):
                return False
    return True


def is_cograph(D: Digraph) -> bool:
    """``P_4``-free.  Checked directly on all 4-subsets, which is fine at census sizes."""
    for quad in itertools.combinations(range(D.n), 4):
        mask = sum(1 << v for v in quad)
        degrees = sorted(popcount(D.adj[v] & mask) for v in quad)
        # an induced P4 is the only 4-vertex graph with degree sequence (1,1,2,2)
        if degrees == [1, 1, 2, 2]:
            edges = sum(popcount(D.adj[v] & mask) for v in quad) // 2
            if edges == 3:
                return False
    return True


def _components_avoiding(D: Digraph, x: int) -> dict[int, int]:
    """Component id of each vertex of ``G - N[x]``."""
    closed = D.adj[x] | (1 << x)
    comp: dict[int, int] = {}
    cid = 0
    for s in bits(D.full & ~closed):
        if s in comp:
            continue
        queue = deque([s])
        comp[s] = cid
        while queue:
            u = queue.popleft()
            for w in bits(D.adj[u] & ~closed):
                if w not in comp:
                    comp[w] = cid
                    queue.append(w)
        cid += 1
    return comp


def is_interval(D: Digraph) -> bool:
    """Chordal and asteroidal-triple-free (Lekkerkerker--Boland, 1962).

    An asteroidal triple is three pairwise non-adjacent vertices such that between any two
    there is a path avoiding the closed neighbourhood of the third.
    """
    if D.n == 0:
        return True
    if not nx.is_chordal(D.underlying_networkx()):
        return False
    comps = {x: _components_avoiding(D, x) for x in range(D.n)}

    def linked(u: int, v: int, avoid: int) -> bool:
        c = comps[avoid]
        return u in c and v in c and c[u] == c[v]

    for x, y, z in itertools.combinations(range(D.n), 3):
        if D.adj[x] & (1 << y) or D.adj[x] & (1 << z) or D.adj[y] & (1 << z):
            continue
        if linked(y, z, x) and linked(x, z, y) and linked(x, y, z):
            return False
    return True


def undirected_flags(D: Digraph) -> dict[str, bool]:
    """All :data:`UNDIRECTED_FLAGS` of the underlying graph of ``D``."""
    n = D.n
    G = D.underlying_networkx()
    m = D.num_edges
    if n == 0:
        # The null graph satisfies each flag vacuously, except the two that require a
        # vertex to be connected to: it is neither connected nor a tree.
        return {
            name: name not in ("connected", "tree", "unicyclic")
            for name in UNDIRECTED_FLAGS
        }
    ncomp = nx.number_connected_components(G)
    connected = ncomp == 1
    forest = m == n - ncomp
    degrees = [D.degree(v) for v in range(n)]
    return {
        "bipartite": nx.is_bipartite(G),
        "connected": connected,
        "tree": connected and forest,
        "forest": forest,
        "unicyclic": connected and m == n,
        "cactus": is_cactus(D),
        "chordal": nx.is_chordal(G),
        "split": is_split(D),
        "interval": is_interval(D),
        "cograph": is_cograph(D),
        "claw_free": is_claw_free(D),
        "planar": nx.check_planarity(G, counterexample=False)[0],
        "regular": len(set(degrees)) <= 1,
        "triangle_free": all(
            D.adj[u] & D.adj[v] == 0 for u, v in G.edges()
        ),
        "block_graph": is_block_graph(D),
        "simplicial_graph": is_simplicial_graph(D),
    }


# --------------------------------------------------------------------------------------
# digraph recognizers
# --------------------------------------------------------------------------------------


def all_cycles_even(D: Digraph) -> bool:
    """Is every directed cycle of ``D`` of even length?

    Every directed cycle lies inside one strong component, so each component is handled
    separately: 2-colour it by BFS parity in its underlying graph (connected, because the
    component is strong) from any root and check that every arc flips colour.  For a
    strong digraph that test is exact: if all cycles are even, colouring ``v`` by the
    parity of any directed path from the root is well defined -- two paths of different
    parity would close, through a return path, into an odd closed walk and hence an odd
    cycle -- and every arc flips it.
    """
    G = D.to_digraph()
    for comp in nx.strongly_connected_components(G):
        mask = sum(1 << v for v in comp)
        H = D.sub(mask)
        if H.n <= 1:
            continue
        colour = {0: 0}
        queue = deque([0])
        while queue:
            u = queue.popleft()
            for w in bits(H.adj[u]):
                if w not in colour:
                    colour[w] = colour[u] ^ 1
                    queue.append(w)
        if any(colour[u] == colour[w] for u, w in H.arcs()):
            return False
    return True


def parity_classes(D: Digraph) -> tuple[int, int] | None:
    """The BFS 2-colouring of the underlying graph as a pair of masks, or ``None``.

    ``None`` when the underlying graph is not bipartite.  For a weakly connected digraph
    in which every directed cycle is even this is *the* parity 2-colouring of
    :func:`all_cycles_even`, and Theorem B says both classes are then 2-kernels when the
    digraph is strong with ``delta+ >= 2``.
    """
    colour: dict[int, int] = {}
    for s in range(D.n):
        if s in colour:
            continue
        colour[s] = 0
        queue = deque([s])
        while queue:
            u = queue.popleft()
            for w in bits(D.adj[u]):
                if w not in colour:
                    colour[w] = colour[u] ^ 1
                    queue.append(w)
                elif colour[w] == colour[u]:
                    return None
    left = sum(1 << v for v, c in colour.items() if c == 0)
    return left, D.full & ~left


def is_tournament(D: Digraph) -> bool:
    """Exactly one arc between every pair of distinct vertices."""
    if D.n < 2:
        return False
    for v in range(D.n):
        for w in range(v + 1, D.n):
            if popcount(D.out[v] & (1 << w)) + popcount(D.out[w] & (1 << v)) != 1:
                return False
    return True


def digraph_flags(D: Digraph) -> dict[str, bool]:
    """All :data:`DIGRAPH_FLAGS` of ``D``."""
    if D.n == 0:
        # Vacuous, except that the null digraph is not strongly connected and a
        # tournament needs at least two vertices.
        return {
            name: name not in ("strong", "tournament") for name in DIGRAPH_FLAGS
        }
    DG = D.to_digraph()
    return {
        "strong": nx.is_strongly_connected(DG),
        "dag": nx.is_directed_acyclic_graph(DG),
        "tournament": is_tournament(D),
        "symmetric": D.is_symmetric(),
        "underlying_bipartite": nx.is_bipartite(D.underlying_networkx()),
        "all_cycles_even": all_cycles_even(D),
    }


def flags(D: Digraph) -> dict[str, bool]:
    """Undirected flags of the underlying graph plus digraph flags of ``D``."""
    return {**undirected_flags(D), **digraph_flags(D)}


# --------------------------------------------------------------------------------------
# numeric invariants
# --------------------------------------------------------------------------------------


def independence_number(D: Digraph) -> int:
    """``alpha`` of the underlying graph."""
    from twokernel.core import all_maximal_independent_sets

    return max((popcount(S) for S in all_maximal_independent_sets(D)), default=0)


def clique_number(D: Digraph) -> int:
    """``omega`` of the underlying graph."""
    if D.n == 0:
        return 0
    return max(len(c) for c in nx.find_cliques(D.underlying_networkx()))


def girth(D: Digraph) -> int | None:
    """Length of a shortest cycle of the underlying graph; ``None`` for a forest."""
    if D.n == 0:
        return None
    g = nx.girth(D.underlying_networkx())
    return None if g == float("inf") else int(g)


def odd_girth(D: Digraph) -> int | None:
    """Length of a shortest odd cycle of the underlying graph; ``None`` if bipartite.

    Computed as the shortest odd closed walk: the distance from ``(s, 0)`` to ``(s, 1)``
    in the bipartite double cover, minimised over ``s``.  An odd closed walk contains an
    odd cycle of no greater length, so the two minima coincide.
    """
    best: int | None = None
    for s in range(D.n):
        dist = {(s, 0): 0}
        queue = deque([(s, 0)])
        while queue:
            u, par = queue.popleft()
            d = dist[(u, par)]
            if best is not None and d >= best:
                break
            for w in bits(D.adj[u]):
                nxt = (w, par ^ 1)
                if nxt not in dist:
                    dist[nxt] = d + 1
                    if nxt == (s, 1):
                        queue.clear()
                        break
                    queue.append(nxt)
        if (s, 1) in dist and (best is None or dist[(s, 1)] < best):
            best = dist[(s, 1)]
    return best


def invariants(D: Digraph) -> dict[str, int | None]:
    """Basic parameters recorded for every census row."""
    degrees = [D.degree(v) for v in range(D.n)]
    return {
        "n": D.n,
        "m": D.num_edges,
        "num_arcs": D.num_arcs,
        "delta": min(degrees, default=0),
        "Delta": max(degrees, default=0),
        "min_outdeg": D.min_outdeg,
        "alpha": independence_number(D),
        "omega": clique_number(D),
        "girth": girth(D),
        "odd_girth": odd_girth(D),
        "num_simplicial": popcount(simplicial_vertices(D)),
    }
