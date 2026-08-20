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

import networkx as nx
import pytest

from twokernel import generators as gen
from twokernel.core import (
    Digraph,
    all_2kernels,
    bits,
    count_2kernels,
    has_2kernel,
    is_2kernel,
    min_2kernel_size,
    popcount,
)

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
    G = D.to_networkx()
    assert not D.is_symmetric()

    cycles = list(nx.simple_cycles(G))
    assert cycles, "the digraph does have directed cycles"
    assert all(len(c) % 2 == 0 for c in cycles), (
        f"odd cycle found: {[c for c in cycles if len(c) % 2]}"
    )
    assert D.min_outdeg == 2
    assert not has_2kernel(D), "Theorem C: this digraph must have no 2-kernel"


def test_theorem_c_is_not_strong() -> None:
    """The one hypothesis of Theorem B that fails here is strong connectedness."""
    assert not nx.is_strongly_connected(theorem_c_digraph().to_networkx())
