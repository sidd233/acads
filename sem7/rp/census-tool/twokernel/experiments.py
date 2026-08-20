"""The experiments E1--E6 that are not plain SQL over the census.

E1, E2, E3, E4 and the counting half of E6 are canned queries in :mod:`twokernel.census`.
This module holds the parts that are assertions or structural analyses:

* **E5** every atlas graph ``G`` must have ``V(G)`` as a 2-kernel of its subdivision;
* **E6** the structure of 2-kernels in DAGs, where the propagation below is exact.

Run with ``python -m twokernel.experiments <name>``.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Iterator

import networkx as nx

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
    popcount,
    solve_dpll,
)

__all__ = ["dag_2kernel", "e5_subdivisions", "e6_dag_structure", "main"]


def dag_2kernel(D: Digraph) -> int | None:
    """The unique 2-kernel of a DAG, or ``None`` if it has none.  Linear time.

    In a DAG every sink lies in every 2-kernel (a sink has no out-arcs, so it cannot be
    2-dominated from outside).  Going backwards along a topological order, the status of
    ``v`` is forced by the vertices after it: ``v`` can be outside the kernel only if at
    least two of its out-neighbours are inside, and if two of them are inside then ``v``
    cannot be inside, because the kernel is independent.  So the candidate set is unique
    and one call to :func:`is_2kernel` decides the instance.

    Consequence: deciding the existence of a 2-kernel is in P for DAGs, and a DAG has at
    most one 2-kernel.  Verified exhaustively against the reference solver for every DAG
    on at most 7 vertices in which each vertex is a sink or has out-degree >= 2, and on
    20000 seeded random DAGs on up to 8 vertices with no degree condition.
    """
    order = list(nx.topological_sort(D.to_digraph()))
    S = 0
    for v in reversed(order):
        if popcount(D.out[v] & S) < 2:
            S |= 1 << v
    return S if is_2kernel(D, S) else None


def e5_subdivisions(max_n: int = 7) -> tuple[int, int]:
    """E5: for every atlas graph ``G``, ``V(G)`` is a 2-kernel of the subdivision ``S(G)``.

    True for every graph with at least one edge: the original vertices are pairwise
    non-adjacent in ``S(G)``, and every subdivision vertex has exactly the two endpoints
    of its edge as out-neighbours.  A graph with no edges is its own subdivision, where
    ``V(G)`` is still a 2-kernel because nothing lies outside it.  So this is a free
    infinite family of graphs with a 2-kernel.
    """
    checked = 0
    largest = 0
    for G in gen.atlas_graphs(max_n=max_n):
        S, original = gen.subdivision(G)
        assert is_2kernel(S, original), f"V(G) is not a 2-kernel of S(G) for {G!r}"
        checked += 1
        largest = max(largest, S.n)
    print(f"E5: V(G) is a 2-kernel of S(G) for all {checked} atlas graphs")
    print(f"    largest subdivision checked: n = {largest}")
    return checked, largest


def e6_dag_structure(max_n: int = 7, random_trials: int = 20000) -> None:
    """E6: check that DAG 2-kernels are unique and that :func:`dag_2kernel` is exact."""
    total = 0
    with_kernel = 0
    multiple = 0
    undecided = 0
    disagreements: list[str] = []
    for n in range(1, max_n + 1):
        for D in gen.all_dags_min_outdeg(n, 2):
            total += 1
            kernels = all_2kernels(D)
            with_kernel += bool(kernels)
            multiple += len(kernels) > 1
            _status, verdict = forcing_closure(D)
            undecided += verdict is Verdict.UNDECIDED
            mine = dag_2kernel(D)
            if (mine is not None) != bool(kernels) or (
                mine is not None and mine != kernels[0]
            ):
                disagreements.append(str(sorted(D.arcs())))
    print(
        f"E6: {total} labelled DAGs on n <= {max_n} where every vertex is a sink or has "
        f"d+ >= 2"
    )
    print(f"    with a 2-kernel:                     {with_kernel}")
    print(f"    with more than one 2-kernel:         {multiple}")
    print(f"    forcing closure left UNDECIDED:      {undecided}")
    print(f"    dag_2kernel vs reference solver:     {len(disagreements)} disagreements")

    import random

    rng = random.Random(0)
    multiple_r = 0
    bad_r = 0
    for _ in range(random_trials):
        n = rng.randint(1, 8)
        arcs = [
            (i, j) for i in range(n) for j in range(i + 1, n) if rng.random() < 0.35
        ]
        D = Digraph.from_arcs(n, arcs)
        kernels = all_2kernels(D)
        multiple_r += len(kernels) > 1
        mine = dag_2kernel(D)
        if (mine is not None) != bool(kernels) or (
            mine is not None and mine != kernels[0]
        ):
            bad_r += 1
    print(
        f"    {random_trials} seeded random DAGs with no degree condition: "
        f"{multiple_r} with >1 kernel, {bad_r} disagreements"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m twokernel.experiments")
    parser.add_argument("name", choices=["e5", "e6", "all"])
    args = parser.parse_args(argv)
    if args.name in ("e5", "all"):
        e5_subdivisions()
    if args.name in ("e6", "all"):
        e6_dag_structure()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
