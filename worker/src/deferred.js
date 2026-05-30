/**
 * Cloudflare Worker – deferred placeholder.
 *
 * The active runtime for pokemon-sleep-rater v1 is Render (Flask + Tesseract).
 * This Worker exists only so the Cloudflare Git integration deploys successfully
 * without compiling the legacy TypeScript Worker code.
 */

const JSON_HEADERS = { "Content-Type": "application/json" };
const CORS_HEADERS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type",
};

function json(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...JSON_HEADERS, ...CORS_HEADERS },
  });
}

export default {
  async fetch(request) {
    const url = new URL(request.url);
    const path = url.pathname;

    // CORS preflight
    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: CORS_HEADERS });
    }

    // Health / root
    if (path === "/" || path === "/health") {
      return json({
        name: "pokemon-sleep-rater",
        status: "ok",
        runtime: "cloudflare-worker-deferred",
        active_runtime: "render-flask-tesseract",
        message:
          "Cloudflare Worker is deferred. The Render Flask service handles OCR, Telegram, web, and MCP.",
      });
    }

    // Deferred endpoints
    if (
      path === "/rate" ||
      path === "/mcp" ||
      path === "/discord" ||
      path.startsWith("/telegram")
    ) {
      return json(
        {
          error: "not_implemented",
          runtime: "cloudflare-worker-deferred",
          active_runtime: "render-flask-tesseract",
          message:
            "This endpoint is deferred. Use the Render Flask service instead.",
        },
        501
      );
    }

    // Unknown paths
    return json(
      {
        error: "not_found",
        runtime: "cloudflare-worker-deferred",
        message: "Unknown path. The active runtime is Render Flask.",
      },
      404
    );
  },
};
