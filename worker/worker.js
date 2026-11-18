// puzzle-frontier edge worker: serves the web app, proxies the API, gates premium routes with x402 v2.
// Payment requirement mirrors the estate gateway (inference.a-11-oy.com): exact USDC on Base.
const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type,X-PAYMENT,PAYMENT-SIGNATURE,Payment-Context",
  "Access-Control-Expose-Headers": "PAYMENT-REQUIRED,PAYMENT-RESPONSE",
};

function json(body, status, headers) {
  return new Response(JSON.stringify(body), {
    status: status || 200,
    headers: Object.assign({ "Content-Type": "application/json" }, CORS, headers || {}),
  });
}

function x402Challenge(url, env) {
  const accept = {
    scheme: "exact",
    network: "eip155:8453",
    amount: env.X402_PRICE || "20000",
    asset: "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
    payTo: env.X402_PAY_TO || "set X402_PAY_TO secret",
    maxTimeoutSeconds: 3600,
    extra: { name: "USD Coin", version: "2" },
  };
  return {
    x402Version: 2,
    error: "payment required",
    resource: { url: url },
    accepts: [accept],
    help: {
      docs: "https://developers.cloudflare.com/monetization-gateway/",
      spec: "https://github.com/x402-foundation/x402",
      instructions: "Pay by re-sending this request with an X-PAYMENT header carrying a PAYMENT-SIGNATURE authorization for the advertised payment requirement. Scheme exact: the advertised amount is the full price, in atomic units of the asset contract.",
    },
  };
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (request.method === "OPTIONS") return new Response(null, { status: 204, headers: CORS });
    if (url.pathname.startsWith("/api/")) {
      if (url.pathname.startsWith("/api/premium")) {
        const pay = request.headers.get("X-PAYMENT");
        if (!pay) {
          const ch = x402Challenge(url.toString(), env);
          return json(ch, 402, { "PAYMENT-REQUIRED": btoa(JSON.stringify(ch)) });
        }
      }
      let base = env.API_BASE || "http://127.0.0.1:8000";
      if (base.endsWith("/")) base = base.slice(0, -1);
      const upstream = base + url.pathname.slice(4) + url.search;
      const init = { method: request.method, headers: { "Content-Type": "application/json" } };
      if (request.method === "POST") init.body = await request.text();
      try {
        const resp = await fetch(upstream, init);
        const text = await resp.text();
        return new Response(text, { status: resp.status, headers: Object.assign({ "Content-Type": "application/json" }, CORS) });
      } catch (e) {
        return json({ error: "upstream unavailable", detail: String(e) }, 502);
      }
    }
    return env.ASSETS.fetch(request);
  },
};
