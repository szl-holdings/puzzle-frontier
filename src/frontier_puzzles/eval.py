def canonical_solution(solution):
    if isinstance(solution, dict):
        return "; ".join(str(k) + "=" + str(solution[k]) for k in sorted(solution, key=str))
    if isinstance(solution, list):
        return " | ".join(" ".join(str(x) for x in row) for row in solution)
    return str(solution)

def _norm(text):
    return " ".join(str(text).split()).strip().lower()

def score_answer(item, answer):
    """Deterministic exact-match scoring of a free-text answer against the certified
    solution (the solution is never exposed by the service; scoring runs server-side)."""
    expected = canonical_solution(item.get("solution"))
    got = _norm(answer)
    want = _norm(expected)
    return {
        "id": item.get("id"),
        "correct": got == want,
        "family": item.get("family"),
        "bank": item.get("source"),
        "level": item.get("level"),
    }

def grade_run(items, answers_by_id):
    """Grade a full run. answers_by_id: mapping of item id to free-text answer."""
    rows = [score_answer(i, answers_by_id[i["id"]]) for i in items if i["id"] in answers_by_id]
    n = len(rows)
    c = sum(1 for r in rows if r["correct"])
    per_bank = {}
    for r in rows:
        b = r["bank"]
        hit, tot = per_bank.get(b, (0, 0))
        per_bank[b] = (hit + int(r["correct"]), tot + 1)
    return {
        "n": n,
        "correct": c,
        "accuracy": (c / n) if n else 0.0,
        "per_bank": {b: {"correct": v[0], "n": v[1], "accuracy": (v[0] / v[1]) if v[1] else 0.0} for b, v in per_bank.items()},
    }
