# puzzle-frontier - investor brief

**One line:** a bank of solver-certified logic puzzles at sizes beyond the published
frontier, with a contamination-free evaluation protocol - the substrate for measuring
and training LLM reasoning at the hard end.

## Why now

- The published benchmark tops out at small sizes; top difficulty levels are rare there.
  We generated and certified items at genuinely new sizes (Zebra 7x5, Futoshiki 7x7,
  Sudoku 12x12, Killer 9x9) - the difficulty distribution shifts upward.
- Training data is saturating; contamination-free eval is the scarce good. Our fresh-seed
  banks never appeared in any training corpus and regenerate deterministically.

## Traction receipts (verifiable)

- 436 certified items published: https://huggingface.co/datasets/SZLHOLDINGS/certified-puzzles-frontier-bank-v1
- Upstream contribution under review by the pipeline author:
  https://github.com/sarabehnamian/Puzzle-generation-with-guaranteed-uniqueness/pull/8
- Every item carries machine-checkable certificates (MiniSat + CP-SAT uniqueness, MUS
  explanations) - an honesty bar no synthetic-data vendor currently meets.

## Moat

1. Certification pipeline (pure solver code; MIT upstream plus our new-size extensions).
2. Regenerability: seeded, resumable configs - unlimited fresh contamination-free evals.
3. Estate AI models (SZLHOLDINGS on Hugging Face) already training on this curriculum.

## Roadmap

- PyPI package: puzzle-frontier (loader + certified scoring + service)
- Hosted API on Cloudflare with x402 per-call payments
- Premium banks: larger sizes, enterprise licensing of certified data

## Honest risks

- Heavy-size certification is compute-bound (per-item MUS cost grows fast); mitigated by
  resumable banks and solver swappability.
- Revenue model is early (see MONETIZATION.md); pricing not yet set.
