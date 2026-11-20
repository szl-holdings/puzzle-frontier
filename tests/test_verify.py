"""Adversarial tests for frontier_puzzles.verify.

Near-miss doctrine (rec-4): every checker must fail on subtly wrong plans,
not just on garbage. Peer-coded: Vibe wrote the module and round-1 tests;
Kimi adversarially reviewed (round 2) and contributed the hardened cases;
Vibe applied the hardening (round 3). Runnable with pytest OR directly.
"""

from frontier_puzzles.verify import (
    check_killer_cages,
    check_zebra_clues,
    is_latin_square,
    verify_grid,
    verify_item,
    verify_zebra,
)

SUDOKU_9 = [
    [5, 3, 4, 6, 7, 8, 9, 1, 2],
    [6, 7, 2, 1, 9, 5, 3, 4, 8],
    [1, 9, 8, 3, 4, 2, 5, 6, 7],
    [8, 5, 9, 7, 6, 1, 4, 2, 3],
    [4, 2, 6, 8, 5, 3, 7, 9, 1],
    [7, 1, 3, 9, 2, 4, 8, 5, 6],
    [9, 6, 1, 5, 3, 7, 2, 8, 4],
    [2, 8, 7, 4, 1, 9, 6, 3, 5],
    [3, 4, 5, 2, 8, 6, 1, 7, 9],
]

# cyclic latin square: rows/cols fine, every 3x3 box broken
CYCLIC_9 = [[((c - r) % 9) + 1 for c in range(9)] for r in range(9)]

KILLER_6 = [
    [1, 2, 3, 4, 5, 6],
    [4, 5, 6, 1, 2, 3],
    [2, 3, 4, 5, 6, 1],
    [5, 6, 1, 2, 3, 4],
    [3, 4, 5, 6, 1, 2],
    [6, 1, 2, 3, 4, 5],
]

ZEBRA = {
    "color": {"red": 1, "green": 2, "blue": 3, "yellow": 4, "white": 5},
    "pet": {"cat": 1, "dog": 2, "fish": 3, "bird": 4, "snake": 5},
}


def _killer_item(cages):
    return {"family": "killer", "size": "6x6", "cages": cages}


def _killer_partition(grid):
    cages = []
    for r in range(len(grid)):
        for c in (0, 2, 4):
            cages.append({"cells": [[r, c], [r, c + 1]],
                          "sum": grid[r][c] + grid[r][c + 1]})
    return cages


def test_valid_sudoku_9():
    item = {"family": "sudoku"}
    assert verify_grid(SUDOKU_9, item) is True
    assert verify_item(item, SUDOKU_9) is True


def test_nearmiss_row_dup():
    bad = [row[:] for row in SUDOKU_9]
    bad[0][0] = 6  # row 0 now has two 6s
    assert verify_item({"family": "sudoku"}, bad) is False


def test_nearmiss_latin_but_box_broken():
    # passes rows+columns, fails only the box constraint
    assert is_latin_square(CYCLIC_9, 9, 3, 3) is False
    assert is_latin_square(CYCLIC_9, 9, 0, 0) is True


def test_bool_poison():
    bad = [row[:] for row in SUDOKU_9]
    bad[4][4] = True  # True == 1 would sneak past sets alone
    assert verify_item({"family": "sudoku"}, bad) is False


def test_wrong_shape_rejected():
    assert verify_item({"family": "sudoku"}, KILLER_6) is False
    assert verify_item({"family": "sudoku", "size": "maybe"}, SUDOKU_9) is False


def test_killer_valid_partition_and_nearmisses():
    cages = _killer_partition(KILLER_6)
    assert verify_item(_killer_item(cages), KILLER_6) is True
    bad_sum = [dict(c) for c in cages]
    bad_sum[0]["sum"] += 1  # one cage sum off by one
    assert verify_item(_killer_item(bad_sum), KILLER_6) is False
    assert check_killer_cages(KILLER_6, [{"cells": [[0, 0], [1, 3]], "sum": 2}]) is False  # 1+1 duplicate in cage
    assert check_killer_cages(KILLER_6, [{"cells": [[0, 0]], "sum": 1},
                                         {"cells": [[0, 0]], "sum": 1}]) is False  # overlap
    assert check_killer_cages(KILLER_6, [{"cells": [[9, 9]], "sum": 1}]) is False  # out of range
    partial = cages[:10]  # partial coverage must fail closed
    assert verify_item(_killer_item(partial), KILLER_6) is False
    assert verify_item({"family": "killer", "size": "6x6"}, KILLER_6) is False  # cages are definitional


def test_zebra_structure_and_clues():
    assert verify_zebra(ZEBRA, 5) is True
    assert verify_zebra(ZEBRA, 5, ["color", "pet"]) is True
    broken = {"color": {"red": 1, "green": 1, "blue": 3, "yellow": 4, "white": 5},
              "pet": dict(ZEBRA["pet"])}
    assert verify_zebra(broken, 5) is False  # house 1 twice in color
    assert check_zebra_clues(ZEBRA, [{"type": "same", "a": "color:red", "b": "pet:cat"}]) is True
    assert check_zebra_clues(ZEBRA, [{"type": "same", "a": "color:red", "b": "pet:dog"}]) is False
    assert check_zebra_clues(ZEBRA, [{"type": "next", "a": "color:red", "b": "pet:dog"}]) is True
    assert check_zebra_clues(ZEBRA, [{"type": "left", "a": "color:white", "b": "pet:cat"}]) is False
    assert check_zebra_clues(ZEBRA, [{"type": "wat", "a": "color:red", "b": "pet:cat"}]) is False
    assert check_zebra_clues(ZEBRA, [{"type": "adjacent", "a": "color:red", "b": "color:white"}]) is False  # |1-5| != 1
    assert verify_item({"family": "zebra", "n_houses": 5,
                        "clues": [{"type": "same", "a": "color:red", "b": "pet:dog"}]}, ZEBRA) is False


def test_futoshiki_clues():
    item = {"family": "futoshiki", "size": "6x6",
            "clues": [{"lt": [[0, 0], [0, 1]]}]}  # 1 < 2 holds
    assert verify_item(item, KILLER_6) is True
    bad = {"family": "futoshiki", "size": "6x6",
           "clues": [{"gt": [[0, 0], [0, 1]]}]}  # 1 > 2 violated
    assert verify_item(bad, KILLER_6) is False


def test_fail_closed_unknown_family_and_malformed():
    assert verify_item({"family": "nonogram"}, SUDOKU_9) is False
    assert verify_item({}, SUDOKU_9) is False
    assert verify_item({"family": "zebra"}, "not-a-dict") is False
    assert verify_item({"family": "sudoku"}, [[1, 2], [3, 4]]) is False


# --- adversarial cases contributed by Kimi (peer review round 2) ---
def test_killer_incomplete_cage_coverage_false_accept():
    # A single valid cage must not make the other 33 cells unconstrained.
    item = {"family": "killer", "size": "6x6",
            "cages": [{"cells": [[0, 0]], "sum": 1}]}
    assert verify_item(item, KILLER_6) is False
    assert check_killer_cages(KILLER_6, []) is False

def test_zebra_adjacent_is_not_merely_different():
    clue = {"type": "adjacent", "a": "color:red", "b": "pet:snake"}
    # Houses 1 and 5 are different but not adjacent.
    assert check_zebra_clues(ZEBRA, [clue]) is False

def test_futoshiki_negative_indices_do_not_alias():
    item = {"family": "futoshiki", "size": "6x6",
            "clues": [{"lt": [[-1, -1], [0, 0]]}]}
    # Python currently aliases [-1][-1] to grid[5][5] == 5.
    assert verify_item(item, KILLER_6) is False

def test_malformed_public_inputs_return_false_not_raise():
    cases = [
        ({"family": "zebra", "n_houses": "five"}, ZEBRA),
        ({"family": "zebra", "n_houses": 5,
          "clues": [{"type": "same", "a": None, "b": "pet:cat"}]}, ZEBRA),
        ({"family": "futoshiki", "size": "6x6",
          "clues": [{"lt": [[99, 0], [0, 0]]}]}, KILLER_6),
        ({"family": "killer", "size": "6x6",
          "cages": [{"cells": [[0]], "sum": 1}]}, KILLER_6),
        ({"family": "sudoku"}, None),
    ]
    for item, plan in cases:
        try:
            result = verify_item(item, plan)
        except Exception as exc:
            raise AssertionError(f"raised {type(exc).__name__} for {item!r}") from exc
        assert result is False

def test_unhashable_grid_values_fail_closed():
    bad = [row[:] for row in SUDOKU_9]
    bad[0][0] = [5]
    try:
        result = verify_item({"family": "sudoku"}, bad)
    except Exception as exc:
        raise AssertionError(f"unhashable value raised {type(exc).__name__}") from exc
    assert result is False

def test_sudoku_12_valid_and_box_only_nearmiss():
    # Each band is a cyclic shift by 4 columns; stacks shift by one row.
    # This gives valid rows, columns, and 3x4 boxes.
    grid = []
    for r in range(12):
        shift = 4 * (r % 3) + (r // 3)
        grid.append([((c + shift) % 12) + 1 for c in range(12)])
    item = {"family": "sudoku", "size": "12x12 (box 3x4)"}
    assert verify_grid(grid, item) is True
    assert verify_item(item, grid) is True
    cyclic = [[((c - r) % 12) + 1 for c in range(12)] for r in range(12)]
    assert is_latin_square(cyclic, 12, 0, 0) is True
    assert verify_item(item, cyclic) is False

def test_futoshiki_7_default_and_explicit_clue_nearmiss():
    grid = [[((c - r) % 7) + 1 for c in range(7)] for r in range(7)]
    # grid[0][0] == 1 and grid[0][1] == 2.
    good_default = {"family": "futoshiki",
                    "clues": [{"lt": [[0, 0], [0, 1]]}]}
    good_explicit = {"family": "futoshiki", "size": "7x7",
                     "clues": [{"lt": [[0, 0], [0, 1]]}]}
    assert verify_item(good_default, grid) is True
    assert verify_item(good_explicit, grid) is True
    bad = dict(good_explicit)
    bad["clues"] = [{"gt": [[0, 0], [0, 1]]}]
    assert verify_item(bad, grid) is False

def test_zebra_boolean_n_houses_rejected():
    one_house = {"color": {"red": 1}}
    # bool is an int subclass; metadata True must not become n_houses=1.
    assert verify_item({"family": "zebra", "n_houses": True}, one_house) is False

def test_killer_bool_sum_and_coordinates_rejected():
    cages = [{"cells": [[False, False]], "sum": True}]
    # Current arithmetic can treat these as cell (0,0), value 1, sum 1.
    assert check_killer_cages(KILLER_6, cages) is False

def test_zebra_unknown_reference_and_missing_fields_fail_closed():
    malformed = [
        {"type": "same", "a": "color:red"},
        {"type": "same", "a": "color:red", "b": "color:missing"},
        {"type": "same", "a": "not-a-ref", "b": "pet:cat"},
        {"type": "same", "a": "color:red", "b": "pet:cat", "extra": 1},
    ]
    for clue in malformed[:3]:
        assert check_zebra_clues(ZEBRA, [clue]) is False
    # Extra fields are currently ignored; this assertion documents that
    # strict-schema behavior is required if the DSL is meant to be closed.
    assert check_zebra_clues(ZEBRA, [malformed[3]]) is False



def test_public_dimension_boundaries_fail_closed():
    # Previously an empty grid with side zero silently returned True.
    assert is_latin_square([], 0) is False
    assert is_latin_square([[1]], False) is False
    assert is_latin_square([[1]], True) is False
    assert is_latin_square([[1]], 1) is True
    # A supplied box constraint must not vanish when only one dimension is zero.
    assert is_latin_square(SUDOKU_9, 9, 3, 0) is False
    assert is_latin_square(SUDOKU_9, 9, 0, 3) is False
    assert is_latin_square(SUDOKU_9, 9, True, 3) is False
    assert is_latin_square(SUDOKU_9, 9, -3, 3) is False
    assert is_latin_square(SUDOKU_9, 9, 3, 3) is True


def test_public_zebra_dimension_is_bounded_before_allocation():
    # This pathological metadata must be rejected *before* any large range/list.
    assert verify_zebra(ZEBRA, 10**9) is False
    assert verify_item({"family": "zebra", "n_houses": 10**9}, ZEBRA) is False
    assert verify_zebra(ZEBRA, 5) is True
    assert verify_item({"family": "zebra", "n_houses": 5}, ZEBRA) is True


if __name__ == "__main__":
    import sys
    failures = []
    total = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            total += 1
            try:
                fn()
                print(f"PASS {name}")
            except AssertionError as exc:
                failures.append(name)
                print(f"FAIL {name} ({exc})")
            except Exception as exc:  # a raising checker is a bug, not a skip
                failures.append(name)
                print(f"RAISED {name}: {type(exc).__name__} {exc}")
    print(f"\n{total - len(failures)}/{total} passed")
    sys.exit(1 if failures else 0)
