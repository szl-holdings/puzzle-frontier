# puzzle-frontier

Certified-unique logic puzzles at sizes **beyond the published frontier**, plus a
**contamination-free evaluation protocol** for LLM reasoning.

**436 solver-certified puzzles. Zero LLM calls.** Every item is re-certified unique by
MiniSat and OR-Tools CP-SAT through the upstream pipeline, is minimal (every clue
necessary), carries its difficulty ladder level (L1 unit propagation ... L5 search),
solver metrics, and minimal-unsatisfiable-core explanations per fact.

## Why it matters

- The upstream paper names larger instances as the open axis: minimal puzzles rarely sit
  at L1 and top ladder levels are rare at released sizes. This bank pushes Zebra to
  7 houses x 5 categories, Futoshiki to 7x7, Sudoku to 12x12 and Killer Sudoku to the
  classic 9x9 - shifting the difficulty distribution upward.
- Models trained on the released 242-puzzle benchmark (or curricula derived from it) can
  be evaluated on fresh-seed instances that were never in any training corpus.

## Assets

| Asset | Link |
|---|---|
| Certified dataset (Hugging Face, MIT) | https://huggingface.co/datasets/SZLHOLDINGS/certified-puzzles-frontier-bank-v1 |
| Upstream contribution PR | https://github.com/sarabehnamian/Puzzle-generation-with-guaranteed-uniqueness/pull/8 |
| Upstream pipeline (MIT, Sara Behnamian) | https://github.com/sarabehnamian/Puzzle-generation-with-guaranteed-uniqueness |
| PyPI package | https://pypi.org/project/puzzle-frontier/ |

## Quickstart (dev)

    pip install -e ".[service]"
    uvicorn frontier_puzzles.service:app --port 8000
    # open http://127.0.0.1:8000

## Python API

    from frontier_puzzles import load_bank, grade_run
    items = load_bank("zebra_f7")            # pulls the certified dataset from the Hub
    result = grade_run(items, answers_by_id) # deterministic certified scoring

## REST API

- GET /health, GET /banks, GET /puzzle/{id}, GET /random, POST /validate
- Premium (x402-gated) endpoints under /premium/

## Deploy (Cloudflare)

See docs/DEPLOY_CLOUDFLARE.md - the Worker serves the web app at the edge and proxies the
API with an x402 payment gate.

## For investors

See docs/INVESTOR.md (traction receipts) and docs/MONETIZATION.md (revenue model).

## License

MIT. The certified puzzle pipeline is (c) 2026 Sara Behnamian (MIT); this repository's
code and data are MIT with attribution. See LICENSE.
