"""The census database: one row per graph, keyed by its graph6/digraph6 string.

Rows are keyed by a *canonical* graph6 (symmetric digraphs) or digraph6 (everything else)
string whenever the vertex count allows one to be computed, so inserts are idempotent and
a graph reached from two different families lands in one row.  ``pynauty`` is unavailable
here, so canonical forms are computed directly: 1-dimensional Weisfeiler--Leman refinement
gives isomorphism-invariant colour classes, and the canonical labelling is the one
minimising the adjacency bit vector over the colour-preserving relabellings.  That is
exact but super-polynomial in the size of the colour classes, hence the ``n <= 7`` cap;
above it the labelled string is used and the ``canonical`` column is 0.

Note on column names: SQLite identifiers are case-insensitive, so the brief's ``delta``
and ``Delta`` cannot both exist.  They are ``min_degree`` (delta) and ``max_degree``
(Delta) here.
"""

from __future__ import annotations

import argparse
import itertools
import sqlite3
import sys
from collections.abc import Callable, Iterable, Iterator

import networkx as nx

from twokernel import classes as cls
from twokernel import generators as gen
from twokernel.core import (
    Digraph,
    Verdict,
    all_2kernels,
    bits,
    forcing_closure,
    has_2kernel,
    popcount,
    solve_dpll,
)

DEFAULT_DB = "census.sqlite3"
CANON_MAX_N = 7

FLAG_COLUMNS: tuple[str, ...] = cls.UNDIRECTED_FLAGS + cls.DIGRAPH_FLAGS


# --------------------------------------------------------------------------------------
# graph6 / digraph6
# --------------------------------------------------------------------------------------


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


def canonical_labelling(D: Digraph, max_n: int = CANON_MAX_N) -> list[int] | None:
    """A canonical vertex order, or ``None`` when ``n`` exceeds ``max_n``.

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


def canonical_key(D: Digraph, max_n: int = CANON_MAX_N) -> tuple[str, bool]:
    """``(key, is_canonical)``: the canonical graph6/digraph6 string when it is
    computable, otherwise the string of the labelling as given."""
    perm = canonical_labelling(D, max_n)
    if perm is None:
        return encode(D), False
    pos = {u: i for i, u in enumerate(perm)}
    arcs = [(pos[u], pos[w]) for u, w in D.arcs()]
    return encode(Digraph.from_arcs(D.n, arcs)), True


# --------------------------------------------------------------------------------------
# rows
# --------------------------------------------------------------------------------------

BASE_COLUMNS: tuple[str, ...] = (
    "key",
    "canonical",
    "directed",
    "n",
    "m",
    "num_arcs",
    "min_degree",
    "max_degree",
    "min_outdeg",
    "alpha",
    "omega",
    "girth",
    "odd_girth",
    "num_simplicial",
)

RESULT_COLUMNS: tuple[str, ...] = (
    "has_2kernel",
    "count_2kernels",
    "min_size",
    "max_size",
    "forcing_verdict",
    "forcing_agrees",
)

ALL_COLUMNS: tuple[str, ...] = BASE_COLUMNS + FLAG_COLUMNS + RESULT_COLUMNS


def row_for(D: Digraph, canon_max_n: int = CANON_MAX_N) -> dict[str, object]:
    """Everything the census records about one digraph."""
    key, canonical = canonical_key(D, canon_max_n)
    inv = cls.invariants(D)
    flags = cls.flags(D)
    kernels = all_2kernels(D)
    sizes = [popcount(S) for S in kernels]
    _status, verdict = forcing_closure(D)
    exists = bool(kernels)
    row: dict[str, object] = {
        "key": key,
        "canonical": int(canonical),
        "directed": int(not D.is_symmetric()),
        "n": inv["n"],
        "m": inv["m"],
        "num_arcs": inv["num_arcs"],
        "min_degree": inv["delta"],
        "max_degree": inv["Delta"],
        "min_outdeg": inv["min_outdeg"],
        "alpha": inv["alpha"],
        "omega": inv["omega"],
        "girth": inv["girth"],
        "odd_girth": inv["odd_girth"],
        "num_simplicial": inv["num_simplicial"],
        "has_2kernel": int(exists),
        "count_2kernels": len(kernels),
        "min_size": min(sizes) if sizes else None,
        "max_size": max(sizes) if sizes else None,
        "forcing_verdict": str(verdict),
        "forcing_agrees": int((verdict is not Verdict.CONFLICT) == exists),
    }
    for name in FLAG_COLUMNS:
        row[name] = int(flags[name])
    return row


# --------------------------------------------------------------------------------------
# database
# --------------------------------------------------------------------------------------


def connect(path: str = DEFAULT_DB) -> sqlite3.Connection:
    """Open the census database and make sure the schema is present."""
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    columns = ", ".join(
        f"{name} {'TEXT' if name in ('key', 'forcing_verdict') else 'INTEGER'}"
        + (" PRIMARY KEY" if name == "key" else "")
        for name in ALL_COLUMNS
    )
    conn.execute(f"CREATE TABLE IF NOT EXISTS graphs ({columns})")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS membership "
        "(key TEXT, family TEXT, PRIMARY KEY (key, family))"
    )
    conn.execute("CREATE INDEX IF NOT EXISTS graphs_n ON graphs (n)")
    conn.commit()
    return conn


def insert(conn: sqlite3.Connection, rows: Iterable[dict[str, object]], family: str) -> int:
    """Idempotent insert: re-running a family rewrites the same rows, never duplicates."""
    placeholders = ", ".join("?" for _ in ALL_COLUMNS)
    sql = (
        f"INSERT INTO graphs ({', '.join(ALL_COLUMNS)}) VALUES ({placeholders}) "
        f"ON CONFLICT(key) DO UPDATE SET "
        + ", ".join(f"{c}=excluded.{c}" for c in ALL_COLUMNS if c != "key")
    )
    count = 0
    for row in rows:
        conn.execute(sql, [row[c] for c in ALL_COLUMNS])
        conn.execute(
            "INSERT OR IGNORE INTO membership (key, family) VALUES (?, ?)",
            (row["key"], family),
        )
        count += 1
        if count % 500 == 0:
            conn.commit()
    conn.commit()
    return count


# --------------------------------------------------------------------------------------
# families
# --------------------------------------------------------------------------------------


def _connected(D: Digraph) -> bool:
    """Weakly connected, i.e. the underlying graph is connected."""
    return D.n > 0 and nx.is_connected(D.underlying_networkx())


def _atlas7() -> Iterator[Digraph]:
    """All 1253 graphs on at most 7 vertices.  Exhaustive up to isomorphism."""
    yield from gen.atlas_graphs()


def _named() -> Iterator[Digraph]:
    """The named families, as a sanity strip through the database."""
    for n in range(1, 15):
        yield gen.path(n)
    for n in range(3, 15):
        yield gen.cycle(n)
    for n in range(1, 8):
        yield gen.complete(n)
    for a in range(1, 5):
        for b in range(1, 6):
            yield gen.complete_bipartite(a, b)
    for k in range(1, 7):
        yield gen.star(k)
    for a in range(1, 4):
        for b in range(1, 4):
            yield gen.double_star(a, b)
    yield gen.spider([1, 2, 3])
    yield gen.spider([2, 2, 2])
    yield gen.petersen()
    for k in (2, 3):
        for n in range(5, 10):
            if 2 * k < n:
                yield gen.generalized_petersen(n, k)
    for d in range(1, 5):
        yield gen.hypercube(d)
    for r in range(2, 5):
        for c in range(2, 5):
            yield gen.grid(r, c)


def _oriented6() -> Iterator[Digraph]:
    """Every orientation (no digons) of every connected graph on at most 6 vertices, kept
    when it is weakly connected with delta+ >= 2.  Exhaustive up to isomorphism."""
    for G in gen.atlas_graphs(min_n=1, max_n=6):
        if not _connected(G):
            continue
        for D in gen.all_orientations(G):
            if D.min_outdeg >= 2:
                yield D


def _digraphs5() -> Iterator[Digraph]:
    """Every digraph on at most 5 vertices with delta+ >= 2, digons included, kept when
    weakly connected.  Exhaustive up to isomorphism."""
    for n in range(1, 6):
        for D in gen.all_digraphs_min_outdeg(n, 2):
            if _connected(D):
                yield D


def _digraphs6sample() -> Iterator[Digraph]:
    """A seeded sample of digraphs on 6 vertices with delta+ >= 2.  NOT exhaustive:
    there are ~3.1e8 of them, which is out of reach without nauty."""
    for seed in range(4000):
        D = gen.random_digraph_min_outdeg(6, 2, seed=seed, p=0.2 + 0.05 * (seed % 8))
        if _connected(D):
            yield D


def _dags7() -> Iterator[Digraph]:
    """Every DAG on at most 7 vertices in which each vertex is a sink or has d+ >= 2,
    kept when weakly connected.  Exhaustive up to isomorphism."""
    for n in range(1, 8):
        for D in gen.all_dags_min_outdeg(n, 2):
            if _connected(D):
                yield D


def _dags8sample() -> Iterator[Digraph]:
    """A seeded sample of the same on 8 vertices (2.3e7 labelled ones, so sampled)."""
    for seed in range(4000):
        D = gen.random_dag_min_outdeg(8, 2, seed=seed)
        if _connected(D):
            yield D


def _cubic() -> Iterator[Digraph]:
    """Seeded random 3-regular graphs on 10..20 vertices, 60 per size."""
    for n in range(10, 21, 2):
        for seed in range(60):
            yield gen.random_regular(n, 3, seed=seed + 1000 * n)


def _cubic_filtered(predicate, tag: str) -> Iterator[Digraph]:
    """Rejection-sampled 3-regular graphs, 60 per size, satisfying ``predicate``."""
    for n in range(10, 21, 2):
        kept = 0
        for seed in range(20000):
            if kept >= 60:
                break
            D = gen.random_regular(n, 3, seed=seed + 7919 * n)
            if predicate(D):
                kept += 1
                yield D


def _cubic_trianglefree() -> Iterator[Digraph]:
    """Seeded random 3-regular graphs restricted to the triangle-free ones."""
    yield from _cubic_filtered(
        lambda D: cls.undirected_flags(D)["triangle_free"], "tf"
    )


def _cubic_girth5() -> Iterator[Digraph]:
    """Seeded random 3-regular graphs restricted to girth >= 5."""
    yield from _cubic_filtered(
        lambda D: (cls.girth(D) or 99) >= 5, "g5"
    )


FAMILIES: dict[str, Callable[[], Iterator[Digraph]]] = {
    "cubic_trianglefree": _cubic_trianglefree,
    "cubic_girth5": _cubic_girth5,
    "atlas7": _atlas7,
    "named": _named,
    "oriented6": _oriented6,
    "digraphs5": _digraphs5,
    "digraphs6sample": _digraphs6sample,
    "dags7": _dags7,
    "dags8sample": _dags8sample,
    "cubic": _cubic,
}

EXHAUSTIVE: frozenset[str] = frozenset(
    {"atlas7", "oriented6", "digraphs5", "dags7"}
)


def run_family(
    conn: sqlite3.Connection, family: str, limit: int | None = None, quiet: bool = False
) -> tuple[int, int]:
    """Populate one family.  Returns ``(seen, inserted)``.

    Duplicates are dropped by canonical key *before* the expensive per-row work, so an
    isomorphism class is analysed once however many labellings reach it.
    """
    if family not in FAMILIES:
        raise SystemExit(f"unknown family {family!r}; known: {', '.join(FAMILIES)}")
    seen: set[str] = set()
    rows: list[dict[str, object]] = []
    total = 0
    for D in FAMILIES[family]():
        total += 1
        key, canonical = canonical_key(D)
        if key in seen:
            continue
        seen.add(key)
        row = row_for(D)
        row["key"] = key
        row["canonical"] = int(canonical)
        rows.append(row)
        if not quiet and len(rows) % 250 == 0:
            print(f"  {family}: {len(rows)} distinct of {total} seen", file=sys.stderr)
        if limit is not None and len(rows) >= limit:
            break
    inserted = insert(conn, rows, family)
    if not quiet:
        kind = "exhaustive" if family in EXHAUSTIVE else "sampled"
        print(
            f"{family}: {total} generated, {inserted} distinct rows ({kind})",
            file=sys.stderr,
        )
    return total, inserted


# --------------------------------------------------------------------------------------
# canned queries
# --------------------------------------------------------------------------------------


def _show(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> list[sqlite3.Row]:
    """Print the exact SQL, run it, print the result as a table."""
    print(f"-- SQL: {' '.join(sql.split())}")
    if params:
        print(f"-- params: {params}")
    rows = conn.execute(sql, params).fetchall()
    if not rows:
        print("   (no rows)")
        return rows
    headers = rows[0].keys()
    widths = [
        max(len(h), max(len(str(r[h])) for r in rows)) for h in headers
    ]
    print("   " + "  ".join(h.ljust(w) for h, w in zip(headers, widths)))
    print("   " + "  ".join("-" * w for w in widths))
    for r in rows:
        print("   " + "  ".join(str(r[h]).ljust(w) for h, w in zip(headers, widths)))
    return rows


def q_summary(conn: sqlite3.Connection, family: str | None = None) -> None:
    """Row counts per family and per vertex count."""
    _show(
        conn,
        """SELECT family, COUNT(*) AS graphs, SUM(has_2kernel) AS with_2kernel,
                  MIN(n) AS min_n, MAX(n) AS max_n
           FROM membership JOIN graphs USING (key)
           GROUP BY family ORDER BY family""",
    )


def q_classes(conn: sqlite3.Connection, family: str = "atlas7") -> None:
    """E1: per class, how many members and how many have a 2-kernel."""
    sql = """SELECT ? AS class, COUNT(*) AS members, SUM(has_2kernel) AS with_2kernel,
                    COUNT(*) - SUM(has_2kernel) AS without
             FROM graphs JOIN membership USING (key)
             WHERE family = ? AND {flag} = 1"""
    print(f"-- E1 over family {family}")
    print(f"-- SQL (one per class): {' '.join(sql.split())}")
    print(f"   {'class':<20} {'members':>8} {'with':>8} {'without':>8}")
    print(f"   {'-' * 20} {'-' * 8} {'-' * 8} {'-' * 8}")
    for flag in FLAG_COLUMNS:
        row = conn.execute(sql.format(flag=flag), (flag, family)).fetchone()
        if row["members"]:
            print(
                f"   {flag:<20} {row['members']:>8} {row['with_2kernel']:>8} "
                f"{row['without']:>8}"
            )
    print()
    print("-- smallest members of each class with NO 2-kernel")
    small = """SELECT key, n, m FROM graphs JOIN membership USING (key)
               WHERE family = ? AND {flag} = 1 AND has_2kernel = 0
               ORDER BY n, m, key LIMIT 3"""
    print(f"-- SQL (one per class): {' '.join(small.split())}")
    for flag in FLAG_COLUMNS:
        rows = conn.execute(small.format(flag=flag), (family,)).fetchall()
        if rows:
            shown = ", ".join(f"{r['key']} (n={r['n']}, m={r['m']})" for r in rows)
            print(f"   {flag:<20} {shown}")
        else:
            total = conn.execute(
                f"SELECT COUNT(*) AS c FROM graphs JOIN membership USING (key) "
                f"WHERE family = ? AND {flag} = 1",
                (family,),
            ).fetchone()["c"]
            if total:
                print(f"   {flag:<20} none -- all {total} members have a 2-kernel")


def q_forcing(conn: sqlite3.Connection, family: str = "atlas7") -> None:
    """E2: does 'forcing did not report CONFLICT' coincide with has_2kernel?"""
    print(f"-- E2 over family {family}")
    sql = """SELECT COUNT(*) AS members, SUM(1 - forcing_agrees) AS disagreements
             FROM graphs JOIN membership USING (key)
             WHERE family = ? AND {flag} = 1"""
    print(f"-- SQL (one per class): {' '.join(sql.split())}")
    small = """SELECT key, n, m, forcing_verdict, has_2kernel
               FROM graphs JOIN membership USING (key)
               WHERE family = ? AND {flag} = 1 AND forcing_agrees = 0
               ORDER BY n, m, key LIMIT 1"""
    print(f"   {'class':<20} {'members':>8} {'disagree':>9}  smallest disagreement")
    print(f"   {'-' * 20} {'-' * 8} {'-' * 9}  {'-' * 40}")
    for flag in FLAG_COLUMNS:
        row = conn.execute(sql.format(flag=flag), (family,)).fetchone()
        if not row["members"]:
            continue
        worst = conn.execute(small.format(flag=flag), (family,)).fetchone()
        detail = (
            f"{worst['key']} (n={worst['n']}, m={worst['m']}, "
            f"{worst['forcing_verdict']}, has_2kernel={worst['has_2kernel']})"
            if worst
            else "none -- forcing is complete on this class"
        )
        print(
            f"   {flag:<20} {row['members']:>8} {row['disagreements']:>9}  {detail}"
        )


def q_digraphs(conn: sqlite3.Connection, family: str | None = None) -> None:
    """E3: the digraph families, split by exhaustive and sampled."""
    _show(
        conn,
        """SELECT family, n, COUNT(*) AS digraphs, SUM(has_2kernel) AS with_2kernel,
                  SUM(1 - forcing_agrees) AS forcing_disagreements
           FROM graphs JOIN membership USING (key)
           WHERE family IN ('oriented6', 'digraphs5', 'digraphs6sample')
           GROUP BY family, n ORDER BY family, n""",
    )
    print()
    _show(
        conn,
        """SELECT family, strong, all_cycles_even, COUNT(*) AS digraphs,
                  SUM(has_2kernel) AS with_2kernel
           FROM graphs JOIN membership USING (key)
           WHERE family IN ('oriented6', 'digraphs5', 'digraphs6sample')
           GROUP BY family, strong, all_cycles_even
           ORDER BY family, strong, all_cycles_even""",
    )


def q_cubic(conn: sqlite3.Connection, family: str | None = None) -> None:
    """E4: 3-regular samples by size and by girth."""
    _show(
        conn,
        """SELECT n, COUNT(*) AS graphs, SUM(has_2kernel) AS with_2kernel,
                  ROUND(1.0 * SUM(has_2kernel) / COUNT(*), 3) AS fraction
           FROM graphs JOIN membership USING (key)
           WHERE family = 'cubic' GROUP BY n ORDER BY n""",
    )
    print()
    _show(
        conn,
        """SELECT girth, COUNT(*) AS graphs, SUM(has_2kernel) AS with_2kernel,
                  ROUND(1.0 * SUM(has_2kernel) / COUNT(*), 3) AS fraction
           FROM graphs JOIN membership USING (key)
           WHERE family = 'cubic' GROUP BY girth ORDER BY girth""",
    )
    print()
    _show(
        conn,
        """SELECT triangle_free, COUNT(*) AS graphs, SUM(has_2kernel) AS with_2kernel,
                  ROUND(1.0 * SUM(has_2kernel) / COUNT(*), 3) AS fraction
           FROM graphs JOIN membership USING (key)
           WHERE family = 'cubic' GROUP BY triangle_free ORDER BY triangle_free""",
    )
    print()
    _show(
        conn,
        """SELECT family, n, COUNT(*) AS graphs, SUM(has_2kernel) AS with_2kernel,
                  ROUND(1.0 * SUM(has_2kernel) / COUNT(*), 3) AS fraction
           FROM graphs JOIN membership USING (key)
           WHERE family IN ('cubic', 'cubic_trianglefree', 'cubic_girth5')
           GROUP BY family, n ORDER BY family, n""",
    )


def q_dags(conn: sqlite3.Connection, family: str | None = None) -> None:
    """E6: DAGs with delta+ >= 2 away from sinks."""
    _show(
        conn,
        """SELECT family, n, COUNT(*) AS dags, SUM(has_2kernel) AS with_2kernel,
                  ROUND(1.0 * SUM(has_2kernel) / COUNT(*), 3) AS fraction,
                  SUM(1 - forcing_agrees) AS forcing_disagreements
           FROM graphs JOIN membership USING (key)
           WHERE family IN ('dags7', 'dags8sample')
           GROUP BY family, n ORDER BY family, n""",
    )
    print()
    _show(
        conn,
        """SELECT n, num_simplicial, COUNT(*) AS dags, SUM(has_2kernel) AS with_2kernel
           FROM graphs JOIN membership USING (key)
           WHERE family = 'dags7' GROUP BY n, num_simplicial ORDER BY n, num_simplicial""",
    )


QUERIES: dict[str, Callable[..., None]] = {
    "summary": q_summary,
    "classes": q_classes,
    "forcing": q_forcing,
    "digraphs": q_digraphs,
    "cubic": q_cubic,
    "dags": q_dags,
}


# --------------------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m twokernel.census")
    parser.add_argument("--db", default=DEFAULT_DB, help="sqlite file (default census.sqlite3)")
    sub = parser.add_subparsers(dest="command", required=True)

    run_cmd = sub.add_parser("run", help="populate one or more families")
    run_cmd.add_argument("--family", action="append", required=True, choices=sorted(FAMILIES))
    run_cmd.add_argument("--limit", type=int, default=None)
    run_cmd.add_argument("--quiet", action="store_true")
    run_cmd.add_argument("--db", dest="db_override", default=None)

    query_cmd = sub.add_parser("query", help="run a canned query")
    query_cmd.add_argument("name", choices=sorted(QUERIES))
    query_cmd.add_argument("--family", default=None)
    query_cmd.add_argument("--db", dest="db_override", default=None)

    sub.add_parser("families", help="list the known families")

    args = parser.parse_args(argv)
    if args.command == "families":
        for name, fn in sorted(FAMILIES.items()):
            kind = "exhaustive" if name in EXHAUSTIVE else "sampled"
            doc = (fn.__doc__ or "").strip().splitlines()[0]
            print(f"{name:<18} {kind:<11} {doc}")
        return 0

    conn = connect(getattr(args, "db_override", None) or args.db)
    if args.command == "run":
        for family in args.family:
            run_family(conn, family, limit=args.limit, quiet=args.quiet)
        return 0
    query = QUERIES[args.name]
    if args.family is not None:
        query(conn, args.family)
    else:
        query(conn)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
