"""Deterministic, independent constraint checkers for estate puzzle families.

These checkers verify a claimed plan against the *structural and clue*
constraints of a puzzle item WITHOUT consulting the known solution.
They are the deterministic gate referenced by the VGL rec-4 frontier study:
verifier-guided decoding must be checked against exact constraint logic,
never against model self-verification alone.

Fail-closed contract (hardened after Kimi peer review round 2):
- every public checker is total: malformed input returns False, never raises
- zebra clue DSL is closed: exactly keys {type, a, b}, type in {same, next,
  left, adjacent}; adjacent means spatial adjacency (|ha - hb| == 1)
- killer cages are REQUIRED and must partition the whole grid
- bools are rejected wherever int metadata/cell/sum values are expected
- a clue-less killer item fails closed; clue-less zebra/futoshiki verify
  structurally only (documented weaker signal)
"""
from __future__ import annotations

from typing import Any, Dict, Sequence, Tuple

__all__ = [
    "is_latin_square",
    "verify_grid",
    "verify_zebra",
    "check_zebra_clues",
    "check_killer_cages",
    "check_futoshiki_clues",
    "verify_item",
]

# family -> (side, box_rows, box_cols)
GRID_SHAPES: Dict[str, Tuple[int, int, int]] = {
    "sudoku_9": (9, 3, 3),
    "sudoku_12": (12, 3, 4),
    "killer_6": (6, 2, 3),
    "killer_9": (9, 3, 3),
    "futoshiki_6": (6, 0, 0),   # 0,0 = no boxes (latin only)
    "futoshiki_7": (7, 0, 0),
}

_SIZES = {
    ("sudoku", None): "sudoku_9",
    ("sudoku", "9x9"): "sudoku_9",
    ("sudoku", "12x12 (box 3x4)"): "sudoku_12",
    ("killer", None): "killer_9",
    ("killer", "6x6"): "killer_6",
    ("killer", "9x9 (box 3x3)"): "killer_9",
    ("futoshiki", None): "futoshiki_7",
    ("futoshiki", "6x6"): "futoshiki_6",
    ("futoshiki", "7x7"): "futoshiki_7",
}


def _plain_int(v: Any) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def _shape_for(item: Any) -> Tuple[int, int, int] | None:
    """Strict dispatch: a DECLARED size string must be a known (family, size)
    combo or the item fails closed; only an absent size falls back to the
    family default. Never silently substitutes a shape."""
    if not isinstance(item, dict):
        return None
    family = item.get("family")
    size = item.get("size")
    if size is not None and not isinstance(size, str):
        return None
    key = (family, size) if size is not None else (family, None)
    return GRID_SHAPES.get(_SIZES.get(key, "__none__"))


def is_latin_square(grid: Any, side: int,
                    box_rows: int = 0, box_cols: int = 0) -> bool:
    """Total, fail-closed latin/box check. Returns False on any malformed
    grid, non-plain-int value, or (when boxes are declared and the side is
    not divisible into them) instead of silently skipping the box check."""
    try:
        if not isinstance(grid, (list, tuple)) or len(grid) != side:
            return False
        want = set(range(1, side + 1))
        for row in grid:
            if not isinstance(row, (list, tuple)) or len(row) != side:
                return False
            if any(not _plain_int(v) for v in row):
                return False
            if set(row) != want:  # unhashable members raise -> caught below
                return False
        for c in range(side):
            if {grid[r][c] for r in range(side)} != want:
                return False
        if box_rows and box_cols:
            if side % box_rows != 0 or side % box_cols != 0:
                return False
            for br in range(0, side, box_rows):
                for bc in range(0, side, box_cols):
                    box = {grid[r][c]
                           for r in range(br, br + box_rows)
                           for c in range(bc, bc + box_cols)}
                    if box != want:
                        return False
        return True
    except (TypeError, ValueError, IndexError):
        return False


def verify_grid(grid: Any, item: Any) -> bool:
    shape = _shape_for(item)
    if shape is None:
        return False
    side, br, bc = shape
    return is_latin_square(grid, side, br, bc)


def verify_zebra(solution: Any, n_houses: int = 5,
                 categories: Sequence[str] | None = None) -> bool:
    """Total structural zebra check: every category maps item labels to a
    permutation of houses 1..n_houses. Categories carry their own label
    sets (colors, pets, ...); cross-category label identity is not checked."""
    try:
        if not _plain_int(n_houses) or n_houses < 1 or not isinstance(solution, dict):
            return False
        cats = list(solution.keys())
        if not cats or not all(isinstance(c, str) for c in cats):
            return False
        if categories is not None:
            if (not isinstance(categories, (list, tuple))
                    or sorted(cats) != sorted(categories)):
                return False
        for values in solution.values():
            if not isinstance(values, dict) or not values:
                return False
            if any(not isinstance(k, str) or not _plain_int(v) or v < 1 or v > n_houses
                   for k, v in values.items()):
                return False
            if sorted(values.values()) != list(range(1, n_houses + 1)):
                return False
        return True
    except (TypeError, ValueError, AttributeError):
        return False


_ZEBRA_TYPES = {"same": lambda a, b: a == b,
                "next": lambda a, b: abs(a - b) == 1,
                "left": lambda a, b: a < b,
                "adjacent": lambda a, b: abs(a - b) == 1}


def check_zebra_clues(solution: Any, clues: Any) -> bool:
    """Closed-schema, total clue check. Clue = exactly {"type","a","b"} with
    str refs "category:label"; every clue must hold. Anything else: False."""

    def house(ref: Any) -> int:
        if not isinstance(ref, str) or ":" not in ref:
            raise ValueError("bad ref")
        cat, label = ref.split(":", 1)
        return solution[cat][label]

    if not isinstance(clues, (list, tuple)) or not clues:
        return False
    try:
        for clue in clues:
            if not isinstance(clue, dict) or set(clue.keys()) != {"type", "a", "b"}:
                return False
            fn = _ZEBRA_TYPES.get(clue["type"])
            if fn is None:
                raise ValueError("bad type")
            if not fn(house(clue["a"]), house(clue["b"])):
                return False
        return True
    except (TypeError, ValueError, KeyError, IndexError, AttributeError):
        return False


def check_killer_cages(grid: Any, cages: Any) -> bool:
    """Total killer-cage check. Cages must be a non-empty partition of the
    grid: each cage {"cells": [[r,c],...], "sum": int} with plain-int
    0-based in-bounds coordinates, no repeats within a cage, sums exact,
    and every cell covered exactly once."""
    if not isinstance(grid, (list, tuple)) or not grid:
        return False
    if not isinstance(cages, (list, tuple)) or not cages:
        return False
    side = len(grid)
    seen = set()
    try:
        for cage in cages:
            if not isinstance(cage, dict) or set(cage.keys()) != {"cells", "sum"}:
                return False
            cells, s = cage["cells"], cage["sum"]
            if not isinstance(cells, (list, tuple)) or not cells or not _plain_int(s):
                return False
            vals = []
            for cell in cells:
                if (not isinstance(cell, (list, tuple)) or len(cell) != 2
                        or not all(_plain_int(x) for x in cell)):
                    return False
                r, c = cell
                if not (0 <= r < side and 0 <= c < side):
                    return False
                if isinstance(grid[r], (list, tuple)) is False:
                    return False
                if (r, c) in seen:
                    return False
                seen.add((r, c))
                vals.append(grid[r][c])
            if sum(vals) != s or len(set(vals)) != len(vals):
                return False
        return len(seen) == side * side  # full partition required
    except (TypeError, ValueError, IndexError):
        return False


def check_futoshiki_clues(clues: Any, solution_grid: Any) -> bool:
    """Total inequality check. Clue = {"lt"|"gt": [[r1,c1],[r2,c2]]} with
    plain-int in-bounds coordinates; both orders enforced strictly."""
    if not isinstance(solution_grid, (list, tuple)) or not solution_grid:
        return False
    if not isinstance(clues, (list, tuple)) or not clues:
        return False
    side = len(solution_grid)
    try:
        for clue in clues:
            if not isinstance(clue, dict) or len(clue) != 1:
                return False
            op, pair = next(iter(clue.items()))
            if op not in ("lt", "gt"):
                return False
            if not isinstance(pair, (list, tuple)) or len(pair) != 2:
                return False
            coords = []
            for cell in pair:
                if (not isinstance(cell, (list, tuple)) or len(cell) != 2
                        or not all(_plain_int(x) for x in cell)):
                    return False
                r, c = cell
                if not (0 <= r < side and 0 <= c < len(solution_grid[r])):
                    return False
                coords.append(solution_grid[r][c])
            if not ((coords[0] < coords[1]) if op == "lt" else (coords[0] > coords[1])):
                return False
        return True
    except (TypeError, ValueError, IndexError):
        return False


def verify_item(item: Any, plan: Any) -> bool:
    """Fail-closed independent verification of a claimed plan against the
    structural rules and clue constraints of an item (never the answer key).

    Zebra/futoshiki: structure always checked; clue set checked when present
    (an item with no clues verifies structurally only - callers should treat
    that as a weaker signal, per the rec-4 doctrine).
    Killer: cages are definitional; a killer item without cages fails closed.
    Totality: no malformed item or plan raises from this boundary."""
    try:
        if not isinstance(item, dict):
            return False
        family = item.get("family")
        if family == "zebra":
            n = item.get("n_houses", 5)
            if not _plain_int(n) or n < 1:
                return False
            if not verify_zebra(plan, n, item.get("categories")):
                return False
            clues = item.get("clues") or []
            return check_zebra_clues(plan, clues) if clues else True
        if family == "futoshiki":
            if not verify_grid(plan, item):
                return False
            clues = item.get("clues") or []
            return check_futoshiki_clues(clues, plan) if clues else True
        if family == "sudoku":
            return verify_grid(plan, item)
        if family == "killer":
            cages = item.get("cages")
            if not cages:
                return False  # cages are definitional for killer
            return verify_grid(plan, item) and check_killer_cages(plan, cages)
        return False
    except (TypeError, ValueError, KeyError, IndexError, AttributeError, RecursionError):
        return False
