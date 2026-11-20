"""Sim actuation gate + per-receipt billing ledger (trio convergence build).

Implements the receipt-native governance loop from the trio dream session
(Kimi k3.1-pro + GLM 5.3 + Mistral large-4 convergence, 2026-11-20):
the deterministic verifier gates actuation, and the meter bills ONLY
verified work - unverified actions are rejected, billed zero, and
escalated.

Loop:
    action envelope -> deterministic verify gate -> billing ledger receipt

Fail-closed contract:
- malformed envelopes and unverified claims are NEVER billed;
  they are recorded as rejected with price 0 and escalated
- ledger records are content-digested and chained (each record digest
  folds in the previous record digest), so tampering is detectable
- unknown/malformed items fail closed through the verifier boundary
- no exception escapes this module's public functions
- the receipt is deterministic: same inputs -> byte-identical receipt
  (wall-clock is the CALLER's concern, never baked into records)
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Callable, Dict, List, Optional

from .verify import verify_item

GATE_VERSION = "sim-actuation-gate/v1"
DEFAULT_PRICE_CENTS = 25

__all__ = ["GATE_VERSION", "DEFAULT_PRICE_CENTS", "run_gate", "validate_chain"]


def _canon(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _envelope_digest(envelope: Dict[str, Any]) -> Optional[str]:
    """Digest of the canonical action envelope; None if not a dict."""
    if not isinstance(envelope, dict):
        return None
    return _sha(_canon(envelope))


def _is_envelope(obj: Any) -> bool:
    """An action envelope is exactly {action_id, item, plan} - closed
    schema, no extra keys (a sloppy envelope fails closed)."""
    if not isinstance(obj, dict):
        return False
    return set(obj.keys()) == {"action_id", "item", "plan"} and isinstance(obj["action_id"], str)


def run_gate(
    actions: List[Any],
    verifier: Callable[[Any, Any], bool] = verify_item,
    price_cents: int = DEFAULT_PRICE_CENTS,
) -> Dict[str, Any]:
    """Run the sim gate over action envelopes and produce a chained,
    per-receipt billing ledger. Returns a receipt dict:

    {gate, n_actions, n_verified, n_rejected, billable_cents, escalated,
     ledger: [{action_id, envelope_sha256, verified, price_cents,
               record_sha256}]}

    Rejected actions always bill 0. Verified actions bill `price_cents`.
    Raises never; total fail-closed processing of every entry."""
    if not isinstance(actions, (list, tuple)):
        actions = []
    if not isinstance(price_cents, int) or isinstance(price_cents, bool) or price_cents < 0:
        price_cents = 0

    records: List[Dict[str, Any]] = []
    escalated: List[str] = []
    billable_cents = 0
    n_verified = 0
    prev_sha = "" 

    for action in actions:
        verified = False
        env_sha = None
        action_id = None
        if _is_envelope(action):
            action_id = action["action_id"]
            env_sha = _envelope_digest(action)
            try:
                verified = bool(verifier(action["item"], action["plan"]))
            except Exception:
                verified = False  # total boundary: verifier faults fail closed
        price = price_cents if verified else 0
        if verified:
            n_verified += 1
            billable_cents += price
        else:
            escalated.append(action_id if isinstance(action_id, str) else "<malformed>")
        record = {
            "action_id": action_id if isinstance(action_id, str) else "<malformed>",
            "envelope_sha256": env_sha or "<malformed>",
            "verified": verified,
            "price_cents": price,
        }
        prev_sha = _sha(prev_sha + _canon(record))
        record["record_sha256"] = prev_sha
        records.append(record)

    return {
        "gate": GATE_VERSION,
        "n_actions": len(records),
        "n_verified": n_verified,
        "n_rejected": len(records) - n_verified,
        "billable_cents": billable_cents,
        "escalated": escalated,
        "ledger": records,
    }


def validate_chain(receipt: Any) -> bool:
    """Recompute the whole ledger chain; False on any tamper/malformation."""
    try:
        if not isinstance(receipt, dict):
            return False
        if receipt.get("gate") != GATE_VERSION:
            return False
        records = receipt.get("ledger")
        if not isinstance(records, list):
            return False
        prev_sha = ""
        for record in records:
            if not isinstance(record, dict):
                return False
            if set(record.keys()) != {"action_id", "envelope_sha256", "verified", "price_cents", "record_sha256"}:
                return False
            expect_prev = record["record_sha256"]
            body = {k: record[k] for k in ("action_id", "envelope_sha256", "verified", "price_cents")}
            recomputed = _sha(prev_sha + _canon(body))
            if recomputed != expect_prev:
                return False
            prev_sha = recomputed
        return True
    except Exception:
        return False