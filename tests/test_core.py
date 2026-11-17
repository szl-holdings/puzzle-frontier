import json

from frontier_puzzles.banks import BANKS, TOTAL_ITEMS
from frontier_puzzles.eval import canonical_solution, score_answer, grade_run
from frontier_puzzles.loader import load_all, load_bank


def _fixture(tmp_path):
    rows = [
        {"id": "t-1", "family": "zebra", "source": "estate-frontier-zebra_f7",
         "level": 3, "prompt": "p1", "solution": {"A": 1, "B": 2}},
        {"id": "t-2", "family": "sudoku", "source": "estate-frontier-sudoku_f12",
         "level": 2, "prompt": "p2", "solution": [[1, 2], [3, 4]]},
    ]
    p = tmp_path / "puzzles.jsonl"
    p.write_text(chr(10).join(json.dumps(r) for r in rows), encoding="utf-8")
    return str(p)


def test_bank_catalog_consistency():
    assert TOTAL_ITEMS == 436
    assert sum(m["n"] for m in BANKS.values()) == TOTAL_ITEMS


def test_loader_local(tmp_path):
    path = _fixture(tmp_path)
    items = load_all(path)
    assert len(items) == 2
    assert load_bank("zebra_f7", path)[0]["id"] == "t-1"
    assert load_bank("sudoku_f12", path)[0]["id"] == "t-2"


def test_scoring():
    item = {"id": "t-1", "family": "zebra", "source": "estate-frontier-zebra_f7",
            "level": 3, "solution": {"A": 1, "B": 2}}
    assert score_answer(item, "A=1; B=2")["correct"] is True
    assert score_answer(item, "  a=1; b=2 ")["correct"] is True
    assert score_answer(item, "a=1 ; b=2")["correct"] is False  # non-canonical spacing
    assert score_answer(item, "A=2; B=1")["correct"] is False
    assert "A=1" in canonical_solution({"A": 1})


def test_grade_run():
    items = [
        {"id": "a", "source": "b1", "solution": {"A": 1}},
        {"id": "b", "source": "b1", "solution": {"A": 2}},
    ]
    res = grade_run(items, {"a": "A=1", "b": "A=3"})
    assert res["n"] == 2 and res["correct"] == 1
    assert abs(res["accuracy"] - 0.5) < 1e-9
