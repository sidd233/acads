"""graph6/digraph6 encoding and canonical forms.

The census keys every graph by a canonical string, so that two labellings of the same graph
land in one row.  Two backends produce those canonical labellings:

* **pynauty**, when it is installed.  Exact at any size, and the one to prefer.
* a **built-in fallback** otherwise: 1-dimensional Weisfeiler--Leman refinement gives
  isomorphism-invariant colour classes, and the canonical labelling is the one minimising
  the adjacency bit vector over colour-preserving relabellings.  Exact, but
  super-polynomial in the size of the colour classes, so it is capped at
  :data:`CANON_MAX_N` vertices; above the cap the labelled string is returned and the
  caller is told the key is not canonical.

The two backends agree on which graphs are isomorphic -- checked against each other and
against VF2 in the tests -- but not on which labelling represents a class, so one database
should be built with one backend throughout.
"""

from __future__ import annotations

import itertools
from typing import Iterable

from twokernel.core import Digraph, bits

try:  # pragma: no cover - depends on the environment
    import pynauty

    has_pynauty = True
except ImportError:  # pragma: no cover
    pynauty = None
    has_pynauty = False

__all__ = [
    "CANON_MAX_N",
    "has_pynauty",
    "graph6",
    "digraph6",
    "encode",
    "decode",
    "wl_colours",
    "canonical_labelling",
    "canonical_key",
    "certificate",
]

#: Vertex cap for the fallback backend.  Ignored when pynauty is available.
CANON_MAX_N = 7


def _R(bitvector: list[int]) -> str:
    """nauty's ``R(x)``: pad to a multiple of 6, then one printable byte per 6 bits."""
    padded = bitvector + [0] * (-len(bitvector) % 6)
    return "".join(
        chr(63 + int("".join(map(str, padded[i : i + 6])), 2))
        for i in range(0, len(padded), 6)
    )


def _N(n: int) -> str:
    """nauty's ``N(n)`` for ``n <= 62``, which covers every census instance."""
    if n <= 62:
        return chr(63 + n)
    raise ValueError("n > 62 is outside the census range")


def graph6(D: Digraph) -> str:
    """graph6 of the underlying graph, without the ``>>graph6<<`` header."""
    bitvector = [
        1 if D.adj[i] & (1 << j) else 0 for j in range(D.n) for i in range(j)
    ]
    return _N(D.n) + _R(bitvector)


def digraph6(D: Digraph) -> str:
    """digraph6: ``&``, ``N(n)``, then the adjacency matrix read row by row."""
    bitvector = [
        1 if D.out[i] & (1 << j) else 0 for i in range(D.n) for j in range(D.n)
    ]
    return "&" + _N(D.n) + _R(bitvector)


def encode(D: Digraph) -> str:
    """graph6 when the digraph is symmetric (it *is* a graph), digraph6 otherwise."""
    return graph6(D) if D.is_symmetric() else digraph6(D)


def decode(key: str) -> Digraph:
    """Inverse of :func:`encode`, used to check the codec and to re-read the database."""
    if key.startswith("&"):
        n = ord(key[1]) - 63
        data = key[2:]
        bitvector = "".join(f"{ord(ch) - 63:06b}" for ch in data)
        arcs = [
            (i, j)
            for i in range(n)
            for j in range(n)
            if bitvector[i * n + j] == "1"
        ]
        return Digraph.from_arcs(n, arcs)
    n = ord(key[0]) - 63
    bitvector = "".join(f"{ord(ch) - 63:06b}" for ch in key[1:])
    edges = []
    pos = 0
    for j in range(n):
        for i in range(j):
            if bitvector[pos] == "1":
                edges.append((i, j))
            pos += 1
    return Digraph.from_edges(n, edges)


# --------------------------------------------------------------------------------------
# canonical form
# --------------------------------------------------------------------------------------


def wl_colours(D: Digraph) -> list[int]:
    """1-WL colour of each vertex, as ids assigned in a canonical (sorted) order.

    Colours are isomorphism-invariant, so an isomorphism can only map a vertex onto one of
    the same colour -- which is what makes the restricted search below exact.
    """
    colour = [0] * D.n
    for _ in range(D.n):
        signature = [
            (
                colour[v],
                tuple(sorted(colour[w] for w in bits(D.out[v]))),
                tuple(sorted(colour[w] for w in bits(D.inn[v]))),
            )
            for v in range(D.n)
        ]
        order = {sig: i for i, sig in enumerate(sorted(set(signature)))}
        new = [order[sig] for sig in signature]
        if new == colour:
            break
        colour = new
    return colour


def _signature(D: Digraph, perm: Iterable[int]) -> int:
    """Adjacency bit vector of ``D`` relabelled by ``perm`` (new index -> old vertex)."""
    perm = list(perm)
    n = D.n
    sig = 0
    for i, u in enumerate(perm):
        row = 0
        out = D.out[u]
        for j, w in enumerate(perm):
            if out & (1 << w):
                row |= 1 << (n - 1 - j)
        sig |= row << (n * (n - 1 - i))
    return sig


def _wl_canonical_labelling(D: Digraph, max_n: int = CANON_MAX_N) -> list[int] | None:
    """Fallback canonical vertex order, or ``None`` when ``n`` exceeds ``max_n``.

    The order minimises the adjacency bit vector over all relabellings that respect the
    1-WL colour classes.  Isomorphic digraphs have corresponding colour classes, so they
    reach the same minimum.
    """
    if D.n > max_n:
        return None
    colour = wl_colours(D)
    classes: dict[int, list[int]] = {}
    for v in range(D.n):
        classes.setdefault(colour[v], []).append(v)
    ordered = [classes[c] for c in sorted(classes)]
    best: tuple[int, list[int]] | None = None
    for combo in itertools.product(*(itertools.permutations(c) for c in ordered)):
        perm = [v for block in combo for v in block]
        sig = _signature(D, perm)
        if best is None or sig < best[0]:
            best = (sig, perm)
    assert best is not None
    return best[1]


def _pynauty_graph(D: Digraph):
    """``D`` as a pynauty graph.  Always directed: for a symmetric digraph the directed
    isomorphism classes coincide with the undirected ones, so nothing is lost."""
    return pynauty.Graph(
        max(D.n, 1),
        directed=True,
        adjacency_dict={v: list(bits(D.out[v])) for v in range(D.n)},
    )


def certificate(D: Digraph) -> bytes | str:
    """A value equal for two digraphs exactly when they are isomorphic.

    nauty's certificate when available, otherwise the canonical key of the fallback
    backend -- so that backend's size cap also caps exhaustive generation.
    """
    if has_pynauty and D.n:
        return pynauty.certificate(_pynauty_graph(D))
    return canonical_key(D)[0]


def canonical_labelling(D: Digraph, max_n: int = CANON_MAX_N) -> list[int] | None:
    """A canonical vertex order (new position ``i`` holds old vertex ``result[i]``), or
    ``None`` when the fallback backend is in use and ``n`` exceeds ``max_n``."""
    if has_pynauty:
        return [] if D.n == 0 else list(pynauty.canon_label(_pynauty_graph(D)))
    return _wl_canonical_labelling(D, max_n)


def canonical_key(D: Digraph, max_n: int = CANON_MAX_N) -> tuple[str, bool]:
    """``(key, is_canonical)``: the canonical graph6/digraph6 string when it is
    computable, otherwise the string of the labelling as given."""
    perm = canonical_labelling(D, max_n)
    if perm is None:
        return encode(D), False
    pos = {u: i for i, u in enumerate(perm)}
    return encode(Digraph.from_arcs(D.n, [(pos[u], pos[w]) for u, w in D.arcs()])), True
