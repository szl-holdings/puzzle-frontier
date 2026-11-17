# Monetization model (v1)

| Tier | What | Price |
|---|---|---|
| OSS core | Python package, dataset, self-hosted API (MIT) | free, forever |
| Hosted API | /random, /validate, eval runs at the edge | per-call credits via x402 micropayments |
| Premium banks | larger sizes, guaranteed-fresh evals for model labs | subscription / per-bank |
| Enterprise | certified training and eval data at custom sizes, SLA | license |

## Implementation state (honest)

- x402 gate scaffolded in worker/worker.js (402 with pay_to when X-PAYMENT missing);
  on-chain receipt verification is TODO.
- FastAPI backend exposes the endpoints; Cloudflare deploy steps in DEPLOY_CLOUDFLARE.md.
- Pricing decisions are the owner's; no numbers are committed here.
