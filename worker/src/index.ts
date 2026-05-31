/**
 * Cloudflare Worker entry point for Pokémon Sleep Rater.
 *
 * Routes:
 *   POST /mcp                →  MCP JSON-RPC endpoint (Streamable HTTP, no secrets)
 *   GET  / or /health        →  Health check
 *   OPTIONS *                →  CORS preflight
 *   /rate, /telegram*, /discord → 501 deferred to Render Flask
 *
 * The /mcp endpoint requires NO secrets — it is a pure-computation engine.
 * OCR, Telegram, Discord, and Google Vision are NOT served here.
 */

import { handleMcp } from "./mcp.js";

// ---------------------------------------------------------------------------
// CORS
// ---------------------------------------------------------------------------

const CORS_HEADERS: Record<string, string> = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type, Mcp-Session-Id",
  "Access-Control-Max-Age": "86400",
};

function json(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json", ...CORS_HEADERS },
  });
}

// ---------------------------------------------------------------------------
// Worker
// ---------------------------------------------------------------------------

export default {
  async fetch(request: Request): Promise<Response> {
    const { method } = request;
    const { pathname } = new URL(request.url);

    // CORS preflight
    if (method === "OPTIONS") {
      return new Response(null, { status: 204, headers: CORS_HEADERS });
    }

    // Health check
    if (pathname === "/" || pathname === "/health") {
      return json({
        name: "pokemon-sleep-rater",
        status: "ok",
        runtime: "cloudflare-worker-mcp",
        transport: "streamable-http",
        active_runtime: "render-flask-tesseract",
        endpoints: ["/mcp"],
      });
    }

    // ── MCP endpoint ─────────────────────────────────────────────────────

    if (pathname === "/mcp") {
      if (method !== "POST") {
        return new Response("Method Not Allowed", {
          status: 405,
          headers: CORS_HEADERS,
        });
      }

      let body: unknown;
      try {
        body = await request.json();
      } catch {
        return json(
          {
            jsonrpc: "2.0",
            id: null,
            error: { code: -32700, message: "Parse error" },
          },
          400
        );
      }

      try {
        const result = await handleMcp(body);

        if (result === null) {
          return new Response(null, { status: 202, headers: CORS_HEADERS });
        }

        return json(result);
      } catch (e) {
        const message =
          e instanceof Error ? e.message : "Internal server error";
        return json(
          { jsonrpc: "2.0", id: null, error: { code: -32603, message } },
          500
        );
      }
    }

    // ── Deferred endpoints (served by Render Flask) ──────────────────────

    if (
      pathname === "/rate" ||
      pathname === "/discord" ||
      pathname.startsWith("/telegram")
    ) {
      return json(
        {
          error: "not_implemented",
          runtime: "cloudflare-worker-mcp",
          active_runtime: "render-flask-tesseract",
          message:
            "This endpoint is deferred. Use the Render Flask service instead.",
        },
        501
      );
    }

    return new Response("Not Found", { status: 404 });
  },
};
