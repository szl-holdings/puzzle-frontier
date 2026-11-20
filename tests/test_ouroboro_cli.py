"""Fail-closed tests for the ouroboro pass-1 batch-verify CLI."""
import json
import subprocess
import sys

from frontier_puzzles.ouroboro_pass1 import CLI_VERSION, run_batch, main

VALID_ZEBRA = {
    "family": "zebra",
    "n_houses": 2,
    "categories": ["cat"],
    "clues": [{"type": "left", "a": "cat:a", "b": "cat:b"}],
}
VALID_PLAN = {"cat": {"a": 1, "b": 2}}
BAD_PLAN = {"cat": {"a": 2, "b": 1}}

def env(action_id, item, plan):
    return {"action_id": action_id, "item": item, "plan": plan}


def test_valid_batch_opens_gate_deterministic():
    batch = [env("act-1", VALID_ZEBRA, VALID_PLAN)]
    r1, r2 = run_batch(batch), run_batch(batch)
    assert r1["gate"] == "OPEN" and r1["n_verified"] == 1
    assert r1["batch_sha256"] == r2["batch_sha256"]
    assert json.dumps(r1, sort_keys=True) == json.dumps(r2, sort_keys=True)


def test_bad_plan_closes_gate():
    r = run_batch([env("act-1", VALID_ZEBRA, BAD_PLAN)])
    assert r["gate"] == "CLOSED" and r["n_verified"] == 0
    assert r["per_item"][0]["verified"] is False
    assert r["per_item"][0]["missing_fields"] == []


def test_missing_and_extra_keys_fail_closed_with_report():
    missing = {"action_id": "act-1", "item": VALID_ZEBRA}
    extra = env("act-2", VALID_ZEBRA, VALID_PLAN)
    extra["priority"] = 1
    r = run_batch([missing, extra])
    assert r["n_malformed"] == 2 and r["gate"] == "CLOSED"
    assert r["per_item"][0]["missing_fields"] == ["plan"]
    assert "<envelope:extra-key:priority>" in r["per_item"][1]["missing_fields"]


def test_non_dict_envelope_reports_malformed():
    r = run_batch(["not-an-envelope", 42, None])
    assert r["n_malformed"] == 3 and r["gate"] == "CLOSED"
    assert all(p["action_id"] == "<malformed>" for p in r["per_item"])


def test_empty_batch_fails_closed():
    r = run_batch([])
    assert r["gate"] == "CLOSED" and "empty batch" in r["reason"]


def test_non_list_batch_fails_closed():
    r = run_batch({"items": []})
    assert r["gate"] == "CLOSED" and "list" in r["error"]


def test_cli_exit_codes_and_receipt_file(tmp_path):
    batch = tmp_path / "batch.json"
    batch.write_text(json.dumps([env("act-1", VALID_ZEBRA, VALID_PLAN)]))
    out = tmp_path / "receipt.json"
    rc_ok = main([str(batch), "--out", str(out)])
    assert rc_ok == 0 and out.exists()
    saved = json.loads(out.read_text())
    assert saved["receipt"] == CLI_VERSION and saved["gate"] == "OPEN"
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps([env("act-1", VALID_ZEBRA, BAD_PLAN)]))
    assert main([str(bad)]) == 1


def test_cli_subprocess_fails_closed_on_garbage(tmp_path):
    garbage = tmp_path / "garbage.json"
    garbage.write_text("{not json")
    proc = subprocess.run(
        [sys.executable, "-m", "frontier_puzzles.ouroboro_pass1", str(garbage)],
        capture_output=True, text=True, cwd=".", timeout=60,
    )
    assert proc.returncode == 2
    receipt = json.loads(proc.stdout)
    assert receipt["gate"] == "CLOSED" and "unreadable" in receipt["error"]
