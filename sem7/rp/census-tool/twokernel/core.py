"""Bitmask digraph engine for 2-kernels.

A set ``S ⊆ V`` of a loopless digraph ``D = (V, A)`` is a **2-kernel** iff

1. *independence*: no arc of ``A`` has both ends in ``S``, in either direction;
2. *2-domination*: every ``v ∉ S`` satisfies ``|N⁺(v) ∩ S| ≥ 2``.

An undirected graph is represented by its symmetric digraph (every edge becomes two
opposite arcs), so ``N⁺(v) = N(v)`` and a 2-kernel is exactly the ``(2-d)``-kernel of
I. Włoch, *On 2-dominating kernels in graphs*, Australas. J. Combin. **53** (2012)
273--284.  One engine serves both cases.

Vertices are ``0 .. n-1`` and every vertex set is an ``int`` used as a bitmask.

The reference solver rests on one observation (Włoch, op. cit.): every 2-kernel is a
*maximal* independent set of the underlying graph, because a vertex outside ``S`` has
out-arcs into ``S`` and is therefore adjacent to ``S``.  Hence enumerating maximal
independent sets and filtering by the 2-domination test is complete.  Deciding existence
is NP-complete (P. Bednarz, C. Hernández-Cruz, I. Włoch, *On the existence and the number
of (2-d)-kernels in graphs*, Ars Combin. **121** (2015) 341--351), so the aim is
exponential-but-fast on small instances.
"""

from __future__ import annotations

from enum import IntEnum
from typing import Iterable, Iterator, Sequence

__all__ = [
    "Digraph",
    "Status",
    "Verdict",
    "bits",
    "popcount",
    "is_2kernel",
    "all_maximal_independent_sets",
    "all_2kernels",
    "has_2kernel",
    "count_2kernels",
    "min_2kernel_size",
    "max_2kernel_size",
    "forced_set",
    "forcing_closure",
    "solve_dpll",
]


# --------------------------------------------------------------------------------------
# bitmask helpers
# --------------------------------------------------------------------------------------


def bits(mask: int) -> Iterator[int]:
    """Yield the indices of the set bits of ``mask``, in increasing order."""
    while mask:
        low = mask & -mask
        yield low.bit_length() - 1
        mask ^= low


def popcount(mask: int) -> int:
    """Number of set bits of ``mask``."""
    return mask.bit_count()


def mask_of(vertices: Iterable[int]) -> int:
    """Bitmask of an iterable of vertex indices."""
    m = 0
    for v in vertices:
        m |= 1 << v
    return m


# --------------------------------------------------------------------------------------
# the digraph
# --------------------------------------------------------------------------------------


class Digraph:
    """A loopless digraph on ``0 .. n-1`` stored as bitmasks.

    ``out[v]``  -- out-neighbourhood ``N⁺(v)``
    ``inn[v]``  -- in-neighbourhood ``N⁻(v)``
    ``adj[v]``  -- ``out[v] | inn[v]``, the neighbourhood in the *underlying* graph, which
                   is the relation that independence is taken with respect to.
    ``labels``  -- original names of the vertices, used by :meth:`sub` to remember where a
                   relabelled induced sub-digraph came from.
    """

    __slots__ = ("n", "out", "inn", "adj", "labels")

    def __init__(
        self,
        n: int,
        out: Sequence[int],
        inn: Sequence[int],
        labels: Sequence[object] | None = None,
    ) -> None:
        if len(out) != n or len(inn) != n:
            raise ValueError("out/inn must have length n")
        self.n: int = n
        self.out: tuple[int, ...] = tuple(out)
        self.inn: tuple[int, ...] = tuple(inn)
        self.adj: tuple[int, ...] = tuple(o | i for o, i in zip(self.out, self.inn))
        self.labels: tuple[object, ...] = (
            tuple(range(n)) if labels is None else tuple(labels)
        )
        for v in range(n):
            if self.out[v] >> n or self.inn[v] >> n:
                raise ValueError(f"arc of vertex {v} leaves the vertex set")
            if (self.out[v] | self.inn[v]) & (1 << v):
                raise ValueError(f"loop at vertex {v}; loops are not supported")

    # -- construction ------------------------------------------------------------------

    @classmethod
    def from_arcs(cls, n: int, arcs: Iterable[tuple[int, int]]) -> "Digraph":
        """Build from an iterable of ``(tail, head)`` pairs.  Duplicates are absorbed."""
        out = [0] * n
        inn = [0] * n
        for u, v in arcs:
            if not (0 <= u < n and 0 <= v < n):
                raise ValueError(f"arc ({u}, {v}) outside 0..{n - 1}")
            if u == v:
                raise ValueError(f"loop at vertex {u}; loops are not supported")
            out[u] |= 1 << v
            inn[v] |= 1 << u
        return cls(n, out, inn)

    @classmethod
    def from_edges(cls, n: int, edges: Iterable[tuple[int, int]]) -> "Digraph":
        """Build the symmetric digraph of an undirected edge list."""
        arcs: list[tuple[int, int]] = []
        for u, v in edges:
            arcs.append((u, v))
            arcs.append((v, u))
        return cls.from_arcs(n, arcs)

    @classmethod
    def from_networkx(cls, G) -> "Digraph":
        """``nx.Graph`` -> symmetric digraph, ``nx.DiGraph`` -> as is.

        Vertices are indexed by ``G.nodes()`` order and the original names are kept in
        :attr:`labels`.
        """
        nodes = list(G.nodes())
        index = {u: i for i, u in enumerate(nodes)}
        n = len(nodes)
        out = [0] * n
        inn = [0] * n
        directed = G.is_directed()
        for u, v in G.edges():
            iu, iv = index[u], index[v]
            if iu == iv:
                raise ValueError(f"loop at vertex {u!r}; loops are not supported")
            out[iu] |= 1 << iv
            inn[iv] |= 1 << iu
            if not directed:
                out[iv] |= 1 << iu
                inn[iu] |= 1 << iv
        return cls(n, out, inn, labels=nodes)

    # -- views -------------------------------------------------------------------------

    @property
    def full(self) -> int:
        """Bitmask of the whole vertex set."""
        return (1 << self.n) - 1

    def underlying(self) -> "Digraph":
        """The symmetric digraph of the underlying graph (each edge both ways)."""
        return Digraph(self.n, self.adj, self.adj, labels=self.labels)

    def is_symmetric(self) -> bool:
        """True iff every arc has its reverse, i.e. ``D`` *is* an undirected graph."""
        return self.out == self.inn

    def sub(self, mask: int) -> "Digraph":
        """The sub-digraph induced on ``mask``, relabelled to ``0 .. k-1``.

        :attr:`labels` of the result records the vertices of ``self`` that survived.
        """
        keep = list(bits(mask & self.full))
        pos = {v: i for i, v in enumerate(keep)}
        k = len(keep)
        out = [0] * k
        inn = [0] * k
        for i, v in enumerate(keep):
            for w in bits(self.out[v] & mask):
                out[i] |= 1 << pos[w]
            for w in bits(self.inn[v] & mask):
                inn[i] |= 1 << pos[w]
        return Digraph(k, out, inn, labels=[self.labels[v] for v in keep])

    # -- small queries -----------------------------------------------------------------

    def arcs(self) -> Iterator[tuple[int, int]]:
        """Yield every arc ``(tail, head)``."""
        for v in range(self.n):
            for w in bits(self.out[v]):
                yield (v, w)

    @property
    def num_arcs(self) -> int:
        """Number of arcs."""
        return sum(popcount(o) for o in self.out)

    @property
    def num_edges(self) -> int:
        """Number of edges of the *underlying* graph."""
        return sum(popcount(a) for a in self.adj) // 2

    def out_degree(self, v: int) -> int:
        """``d⁺(v)``."""
        return popcount(self.out[v])

    def degree(self, v: int) -> int:
        """Degree of ``v`` in the underlying graph."""
        return popcount(self.adj[v])

    @property
    def min_outdeg(self) -> int:
        """``δ⁺(D)``; ``0`` for the empty digraph."""
        return min((self.out_degree(v) for v in range(self.n)), default=0)

    def to_networkx(self):
        """``nx.DiGraph`` copy, or ``nx.Graph`` when the digraph is symmetric."""
        import networkx as nx

        G = nx.Graph() if self.is_symmetric() else nx.DiGraph()
        G.add_nodes_from(range(self.n))
        G.add_edges_from(self.arcs())
        return G

    def to_digraph(self):
        """``nx.DiGraph`` copy, always directed even when the digraph is symmetric."""
        import networkx as nx

        G = nx.DiGraph()
        G.add_nodes_from(range(self.n))
        G.add_edges_from(self.arcs())
        return G

    def underlying_networkx(self):
        """``nx.Graph`` of the underlying graph."""
        import networkx as nx

        G = nx.Graph()
        G.add_nodes_from(range(self.n))
        for v in range(self.n):
            for w in bits(self.adj[v] & ~((1 << (v + 1)) - 1)):
                G.add_edge(v, w)
        return G

    def has_independent_pair(self, mask: int) -> bool:
        """True iff ``mask`` contains two distinct vertices non-adjacent in ``adj``."""
        rest = mask
        while rest:
            low = rest & -rest
            v = low.bit_length() - 1
            rest ^= low
            if mask & ~self.adj[v] & ~low:
                return True
        return False

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"Digraph(n={self.n}, arcs={sorted(self.arcs())})"


# --------------------------------------------------------------------------------------
# the verifier -- every set leaving this module passes through here
# --------------------------------------------------------------------------------------


def is_2kernel(D: Digraph, S: int) -> bool:
    """Certificate verifier: is the vertex set ``S`` a 2-kernel of ``D``?

    Checks the definition directly: independence in the underlying graph, and
    ``|N⁺(v) ∩ S| ≥ 2`` for every ``v ∉ S``.
    """
    if S & ~D.full:
        return False
    for v in bits(S):
        if D.adj[v] & S:
            return False
    for v in bits(D.full & ~S):
        if popcount(D.out[v] & S) < 2:
            return False
    return True


def _verified(D: Digraph, S: int) -> int:
    """Gate every returned set through :func:`is_2kernel`."""
    if not is_2kernel(D, S):  # pragma: no cover - defensive
        raise AssertionError(f"internal error: {S:b} is not a 2-kernel")
    return S


# --------------------------------------------------------------------------------------
# reference solver
# --------------------------------------------------------------------------------------


def all_maximal_independent_sets(D: Digraph) -> Iterator[int]:
    """Yield every maximal independent set of the underlying graph, as a bitmask.

    Bron--Kerbosch with pivoting, run on the *complement* of the underlying graph, where
    maximal cliques are exactly maximal independent sets.  ``nonadj[v]`` is the
    complement-neighbourhood of ``v``.
    """
    n = D.n
    full = D.full
    nonadj = [full & ~D.adj[v] & ~(1 << v) for v in range(n)]

    def expand(R: int, P: int, X: int) -> Iterator[int]:
        if not P and not X:
            yield R
            return
        # pivot: a vertex of P ∪ X with the most complement-neighbours in P
        pivot = max(bits(P | X), key=lambda u: popcount(P & nonadj[u]))
        for v in bits(P & ~nonadj[pivot]):
            bit = 1 << v
            yield from expand(R | bit, P & nonadj[v], X & nonadj[v])
            P &= ~bit
            X |= bit

    yield from expand(0, full, 0)


def all_2kernels(D: Digraph) -> list[int]:
    """Every 2-kernel of ``D``, as a sorted list of bitmasks.

    The reference solver: filter the maximal independent sets of the underlying graph by
    2-domination.  Complete because every 2-kernel is such a set (Włoch 2012).
    """
    return sorted(
        _verified(D, S) for S in all_maximal_independent_sets(D) if is_2kernel(D, S)
    )


def has_2kernel(D: Digraph) -> bool:
    """Does ``D`` have a 2-kernel?  Short-circuits on the first one found."""
    for S in all_maximal_independent_sets(D):
        if is_2kernel(D, S):
            return True
    return False


def count_2kernels(D: Digraph) -> int:
    """Number of 2-kernels of ``D``."""
    return sum(1 for S in all_maximal_independent_sets(D) if is_2kernel(D, S))


def min_2kernel_size(D: Digraph) -> int | None:
    """Size of a smallest 2-kernel, or ``None`` if there is none."""
    sizes = [popcount(S) for S in all_2kernels(D)]
    return min(sizes) if sizes else None


def max_2kernel_size(D: Digraph) -> int | None:
    """Size of a largest 2-kernel, or ``None`` if there is none."""
    sizes = [popcount(S) for S in all_2kernels(D)]
    return max(sizes) if sizes else None


# --------------------------------------------------------------------------------------
# forcing
# --------------------------------------------------------------------------------------


class Status(IntEnum):
    """Per-vertex state of a sound partial assignment."""

    UNKNOWN = 0
    IN = 1
    OUT = 2


class Verdict(IntEnum):
    """Outcome of :func:`forcing_closure`."""

    CONFLICT = 0
    SOLVED = 1
    UNDECIDED = 2

    def __str__(self) -> str:
        return self.name


def forced_set(D: Digraph) -> int:
    """Vertices whose out-neighbourhood contains no two non-adjacent vertices.

    Sound: if ``v ∉ S`` then ``|N⁺(v) ∩ S| ≥ 2`` and ``S`` is independent, so ``N⁺(v)``
    contains two distinct non-adjacent vertices.  Contrapositive: a vertex without such a
    pair lies in *every* 2-kernel.  This includes every ``v`` with ``d⁺(v) ≤ 1`` and, in
    the undirected case, every simplicial vertex and every leaf.
    """
    forced = 0
    for v in range(D.n):
        if not D.has_independent_pair(D.out[v]):
            forced |= 1 << v
    return forced


def _closure(D: Digraph, in_mask: int, out_mask: int) -> tuple[int, int, Verdict]:
    """Propagate R0--R4 to a fixed point from a partial assignment.

    Invariant maintained by every rule: *every* 2-kernel that contains ``in_mask`` and
    avoids ``out_mask`` still does so afterwards.  Started from ``(0, 0)`` this means IN =
    "in every 2-kernel" and OUT = "in no 2-kernel".
    """
    full = D.full
    forced = forced_set(D)

    changed = True
    while changed:
        changed = False

        if in_mask & out_mask:
            return in_mask, out_mask, Verdict.CONFLICT

        # R0: every vertex of forced_set is IN.
        # Sound: proved in forced_set -- such a vertex lies in every 2-kernel.
        if forced & ~in_mask:
            in_mask |= forced
            changed = True

        # R1: v IN => every underlying neighbour of v is OUT.
        # Sound: S is independent, so no neighbour of a member of S is in S.
        for v in bits(in_mask):
            new_out = D.adj[v] & ~out_mask
            if new_out:
                out_mask |= new_out
                changed = True
        if in_mask & out_mask:
            return in_mask, out_mask, Verdict.CONFLICT

        for v in bits(out_mask):
            U = D.out[v] & ~out_mask

            # R2: v OUT whose out-neighbourhood has no independent pair among its non-OUT
            # members => CONFLICT.
            # Sound: v ∉ S forces two distinct non-adjacent members of N⁺(v) into S, and
            # every member of S is non-OUT; if no such pair exists no 2-kernel extends
            # this assignment.
            if not D.has_independent_pair(U):
                return in_mask, out_mask, Verdict.CONFLICT

            # R3: v OUT with |U(v)| <= 2 => all of U(v) is IN; |U(v)| < 2 is a CONFLICT.
            # Sound: N⁺(v) ∩ S ⊆ U(v) and |N⁺(v) ∩ S| ≥ 2, so with |U(v)| = 2 both members
            # are in S, and with |U(v)| < 2 the requirement cannot be met.
            if popcount(U) < 2:
                return in_mask, out_mask, Verdict.CONFLICT
            if popcount(U) == 2 and (U & ~in_mask):
                in_mask |= U
                changed = True

        # R4: an UNKNOWN vertex that cannot be OUT (the R2 test) is IN.
        # Sound: every vertex is either in S or not; if "not" is impossible then it is in.
        for v in bits(full & ~in_mask & ~out_mask):
            if not D.has_independent_pair(D.out[v] & ~out_mask):
                in_mask |= 1 << v
                changed = True

    if in_mask & out_mask:
        return in_mask, out_mask, Verdict.CONFLICT

    unknown = full & ~in_mask & ~out_mask
    if unknown:
        return in_mask, out_mask, Verdict.UNDECIDED
    # No UNKNOWN left: any 2-kernel extending the assignment equals in_mask exactly, so
    # the verifier decides the instance outright.
    if is_2kernel(D, in_mask):
        return in_mask, out_mask, Verdict.SOLVED
    return in_mask, out_mask, Verdict.CONFLICT


def forcing_closure(D: Digraph) -> tuple[list[Status], Verdict]:
    """Sound forcing propagation on ``D``.

    Returns the per-vertex :class:`Status` array and a :class:`Verdict`.  ``CONFLICT``
    proves no 2-kernel exists; ``SOLVED`` means the IN vertices form the unique 2-kernel
    (verified); ``UNDECIDED`` means propagation alone did not decide.
    """
    in_mask, out_mask, verdict = _closure(D, 0, 0)
    if verdict is Verdict.SOLVED:
        _verified(D, in_mask)
    status = [Status.UNKNOWN] * D.n
    for v in bits(in_mask):
        status[v] = Status.IN
    for v in bits(out_mask & ~in_mask):
        status[v] = Status.OUT
    return status, verdict


def solve_dpll(D: Digraph) -> int | None:
    """Find one 2-kernel by forcing + branching, or ``None`` if there is none.

    Closure first; if it leaves UNKNOWN vertices, branch on the one of largest underlying
    degree (it propagates hardest) and recurse on ``IN`` then ``OUT``.  Both branches
    together cover all cases, and the closure is sound, so exhausting them proves
    non-existence.
    """
    full = D.full

    def search(in_mask: int, out_mask: int) -> int | None:
        in_mask, out_mask, verdict = _closure(D, in_mask, out_mask)
        if verdict is Verdict.CONFLICT:
            return None
        if verdict is Verdict.SOLVED:
            return in_mask
        unknown = full & ~in_mask & ~out_mask
        v = max(bits(unknown), key=D.degree)
        bit = 1 << v
        return search(in_mask | bit, out_mask) or search(in_mask, out_mask | bit)

    S = search(0, 0)
    return None if S is None else _verified(D, S)
