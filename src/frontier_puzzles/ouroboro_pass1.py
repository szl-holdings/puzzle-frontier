"""Ouroboro pass-1: fail-closed batch-verify CLI over the puzzle verifier.

Trio spec (Mistral large-4, adapted): one CLI entrypoint that runs the
existing deterministic verifier over a closed batch of envelopes and
emits a mesh-style receipt: per-item pass/fail, missing_fields for
malformed envelopes, and content digests. No scoring logic changes.

Fail-closed contract:
- envelopes must be dicts with EXACTLY {action_id, item, plan}
- a malformed batch file (not a JSON list, unreadable, bad JSON) fails
  closed with exit 2 and emits a receipt naming the error
- verification failures fail closed with exit 1
- an empty batch fails closed: zero items is not a pass
- receipts are deterministic: same batch -> byte-identical receipt
  (wall-clock is the caller's concern, never baked in)
- no exception escapes main()
"""
from __future__ import annotations

import hashlib
import json
import sys
from typing import Any, Dict, List, Optional

from .verify import verify_item

CLI_VERSION = "ouroboro-pass1/vr-cli-r1"
ENVELOPE_KEYS = {"action_id", "item", "plan"}

__all__ = ["CLI_VERSION", "run_batch", "main"]


def _canon(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _envelope_report(env: Any, index: int) -> Dict[str, Any]:
    """Closed-envelope check + verify, total: never raises."""
    missing: List[str] = []
    extra: List[str] = []
    if not isinstance(env, dict):
        return {
            "index": index,
            "action_id": "<malformed>",
            "verified": False,
            "missing_fields": ["<envelope:not-a-dict>"],
            "envelope_sha256": None,
        }
    missing = sorted(ENVELOPE_KEYS - set(env.keys()))
    extra = sorted(set(env.keys()) - ENVELOPE_KEYS)
    problems = missing + ["<envelope:extra-key:%s>" % k for k in extra]
    action_id = env.get("action_id")
    if not isinstance(action_id, str) or not action_id:
        problems.append("action_id:not-a-nonempty-string")
        action_id = repr(action_id)[:40]
    digest = _sha(_canon(env))
    verified = False
    if not problems:
        verified = bool(verify_item(env["item"], env["plan"]))
    return {
        "index": index,
        "action_id": action_id,
        "verified": verified,
        "missing_fields": problems,
        "envelope_sha256": digest,
    }


def run_batch(envelopes: Any) -> Dict[str, Any]:
    """Deterministic fail-closed receipt for a batch of envelopes."""
    if not isinstance(envelopes, list):
        return {
            "receipt": CLI_VERSION,
            "gate": "CLOSED",
            "error": "batch must be a JSON list of envelopes",
            "n_items": 0,
            "n_verified": 0,
            "per_item": [],
            "batch_sha256": None,
        }
    per_item = [_envelope_report(env, i) for i, env in enumerate(envelopes)]
    n_bad = len([r for r in per_item if r["missing_fields"]])
    n_fail = len([r for r in per_item if not r["verified"]])
    batch_digest = _sha(_canon(per_item))
    return {
        "receipt": CLI_VERSION,
        "gate": "OPEN" if (envelopes and n_fail == 0) else "CLOSED",
        "reason": None if (envelopes and n_fail == 0) else (
            "empty batch fails closed" if not envelopes else
            ("malformed or unverifiable envelopes present" if n_bad else "verification failures")
        ),
        "n_items": len(envelopes),
        "n_verified": len([r for r in per_item if r["verified"]]),
        "n_malformed": n_bad,
        "per_item": per_item,
        "batch_sha256": batch_digest,
    }


def _write_receipt(path: str, receipt: Dict[str, Any]) -> bool:
    """Best-effort receipt write; returns success. Never raises."""
    try:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(receipt, fh, indent=1, sort_keys=True)
            fh.write("\n")
        return True
    except Exception as exc:  # noqa: BLE001 - fail-closed, no escape
        sys.stderr.write("receipt write failed: %s\n" % exc)
        return False


def main(argv: Optional[List[str]] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    out_path = None
    args = list(argv)
    if "--out" in args:
        i = args.index("--out")
        try:
            out_path = args[i + 1]
        except IndexError:
            out_path = None
        args = [a for j, a in enumerate(args) if j not in (i, i + 1)]
    if len(args) != 1:
        sys.stderr.write("usage: python -m frontier_puzzles.ouroboro_pass1 BATCH.json [--out RECEIPT.json]\n")
        return 2
    try:
        with open(args[0], "r", encoding="utf-8") as fh:
            batch = json.load(fh)
        receipt = run_batch(batch)
        exit_code = 0 if receipt["gate"] == "OPEN" else 1
    except Exception as exc:  # noqa: BLE001 - fail-closed, no escape
        receipt = {
            "receipt": CLI_VERSION,
            "gate": "CLOSED",
            "error": "batch unreadable or invalid JSON: %s" % exc,
            "n_items": 0,
            "n_verified": 0,
            "per_item": [],
            "batch_sha256": None,
        }
        exit_code = 2
    print(json.dumps(receipt, indent=1, sort_keys=True))
    if out_path:
        if not _write_receipt(out_path, receipt):
            exit_code = 2
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
