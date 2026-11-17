# Cloudflare onboarding

1. Install: npm i -g wrangler; wrangler login
2. Point API_BASE at your FastAPI host (edit the [vars] section in wrangler.toml, or:
   wrangler secret put API_BASE)
3. Set the premium payee: wrangler secret put X402_PAY_TO
4. Deploy the edge app: wrangler deploy
5. Local dev: wrangler dev (proxies to http://127.0.0.1:8000 - start the API with
   uvicorn frontier_puzzles.service:app --port 8000)

Routes: static assets from ./web; /api/* proxied to the API; /api/premium/* x402-gated
(402 responses carry the payee address).
