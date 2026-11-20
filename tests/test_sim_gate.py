"""Fail-closed tests for sim_gate (verifier-gated billing ledger).

Doctrine under test: unverified work bills ZERO and is escalated;
the ledger chain detects tampering; receipts are deterministic;"""
import copy
import json

from frontier_puzzles.sim_gate import (
    GATE_VERSION,
    DEFAULT_PRICE_CENTS,
    run_gate,
    validate_chain,
)


VALID_ZEBRA = {
    "family": "zebra",
    "n_houses": 2,
    "categories": ["cat"],
    "clues": [{"type": "left", "a": "cat:a", "b": "cat:b"}],
}
VALID_PLAN = {"cat": {"a": 1, "b": 2}}
BAD_CLUE_PLAN = {"cat": {"a": 2, "b": 1}}  # violates the 'next' clue


def env(action_id, item, plan):
    return {"action_id": action_id, "item": item, "plan": plan}


def test_verified_bills_rejected_bills_zero():
    receipt = run_gate([
        env("act-1", VALID_ZEBRA, VALID_PLAN),
        env("act-2", VALID_ZEBRA, BAD_CLUE_PLAN),
    ])
    assert receipt["n_verified"] == 1
    assert receipt["n_rejected"] == 1
    assert receipt["billable_cents"] == DEFAULT_PRICE_CENTS
    assert receipt["escalated"] == ["act-2"]
    r1, r2 = receipt["ledger"]
    assert r1["verified"] is True and r1["price_cents"] == DEFAULT_PRICE_CENTS
    assert r2["verified"] is False and r2["price_cents"] == 0


def test_all_rejected_run_bills_zero():
    receipt = run_gate([
        env("act-1", VALID_ZEBRA, BAD_CLUE_PLAN),
        env("act-2", {"family": "unknown"}, {}),
        "not-a-dict",
        {"action_id": "act-x", "item": VALID_ZEBRA},  # open schema: missing key
    ])
    assert receipt["billable_cents"] == 0
    assert receipt["n_verified"] == 0
    assert receipt["n_actions"] == 4
    assert receipt["escalated"] == ["act-1", "act-2", "<malformed>", "<malformed>"]


def test_open_schema_and_extra_keys_fail_closed():
    extra = env("act-1", VALID_ZEBRA, VALID_PLAN)
    extra["priority"] = 1  # extra key: envelope no longer closed
    receipt = run_gate([extra])
    assert receipt["n_verified"] == 0 and receipt["billable_cents"] == 0


def test_verifier_exception_fails_closed():
    def exploding(item, plan):
        raise RuntimeError("boom")
    receipt = run_gate([env("act-1", VALID_ZEBRA, VALID_PLAN)], verifier=exploding)
    assert receipt["n_verified"] == 0
    assert receipt["billable_cents"] == 0
    assert receipt["escalated"] == ["act-1"]


def test_receipt_is_deterministic():
    actions = [env("act-1", VALID_ZEBRA, VALID_PLAN), env("act-2", VALID_ZEBRA, BAD_CLUE_PLAN)]
    a = json.dumps(run_gate(actions), sort_keys=True)
    b = json.dumps(run_gate(copy.deepcopy(actions)), sort_keys=True)
    assert a == b


def test_chain_validates_and_detects_tamper():
    receipt = run_gate([
        env("act-1", VALID_ZEBRA, VALID_PLAN),
        env("act-2", VALID_ZEBRA, VALID_PLAN),
        env("act-3", VALID_ZEBRA, BAD_CLUE_PLAN),
    ])
    assert validate_chain(receipt) is True
    tampered = copy.deepcopy(receipt)
    tampered["ledger"][0]["price_cents"] = 10_000  # price forge: must break chain
    assert validate_chain(tampered) is False
    tampered2 = copy.deepcopy(receipt)
    tampered2["ledger"].pop(1)  # record removal must break chain
    assert validate_chain(tampered2) is False
    assert validate_chain({}) is False
    assert validate_chain({"gate": "wrong", "ledger": []}) is False


def test_bad_price_args_fail_closed():
    receipt = run_gate([env("act-1", VALID_ZEBRA, VALID_PLAN)], price_cents=True)
    assert receipt["billable_cents"] == 0  # bool is not an int price: rejected
    receipt2 = run_gate([env("act-1", VALID_ZEBRA, VALID_PLAN)], price_cents=-5)
    assert receipt2["billable_cents"] == 0


def test_empty_run_is_a_valid_empty_receipt():
    receipt = run_gate([])
    assert receipt["n_actions"] == 0
    assert receipt["billable_cents"] == 0
    assert validate_chain(receipt) is True
    assert receipt["gate"] == GATE_VERSION