# Contributing

- Python >= 3.10. pip install -e ".[dev,service]"; pytest -q
- Keep everything deterministic and certified: no LLM calls in the pipeline, and no
  puzzle ships without its MiniSat + CP-SAT certificate.
- Attribution matters: the pipeline is (c) Sara Behnamian (MIT). Keep notices intact.
