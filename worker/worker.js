// puzzle-frontier edge worker: serves the web app, proxies the API, gates premium routes with x402.
const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type,X-PAYMENT",
};

function json(body, status) {
  return new Response(JSON.stringify(body), {
    status: status || 200,
    headers: Object.assign({ "Content-Type": "application/json" }, CORS),
  });
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (request.method === "OPTIONS") return new Response(null, { status: 204, headers: CORS });
    if (url.pathname.startsWith("/api/")) {
      if (url.pathname.startsWith("/api/premium")) {
        const pay = request.headers.get("X-PAYMENT");
        if (!pay) {
          return json({
            error: "payment required",
            scheme: "x402",
            pay_to: env.X402_PAY_TO || "set X402_PAY_TO secret",
            resource: url.pathname,
          }, 402);
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
