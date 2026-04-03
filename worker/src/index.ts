/**
 * Cloudflare Worker entry point for Pokémon Sleep Rater.
 *
 * Routes:
 *   POST /discord            →  Discord Interactions webhook
 *   POST /telegram/webhook   →  Telegram Bot webhook
 *   POST /mcp                →  MCP JSON-RPC endpoint (Streamable HTTP)
 *   GET  / or /health        →  Health check
 *   OPTIONS *                →  CORS preflight
 *
 * Environment variables (set via `wrangler secret put`):
 *   DISCORD_PUBLIC_KEY       — Discord application public key
 *   DISCORD_APPLICATION_ID   — Discord application ID
 *   TELEGRAM_BOT_TOKEN       — Telegram bot token from @BotFather
 *   GOOGLE_CLOUD_API_KEY     — Google Cloud API key (Vision API enabled)
 */

import { handleDiscord } from "./discord.js";
import { handleTelegram } from "./telegram.js";
import { handleMcp } from "./mcp.js";

// ---------------------------------------------------------------------------
// Environment interface
// ---------------------------------------------------------------------------

interface Env {
  DISCORD_PUBLIC_KEY: string;
  DISCORD_APPLICATION_ID: string;
  TELEGRAM_BOT_TOKEN: string;
  GOOGLE_CLOUD_API_KEY: string;
}

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
  async fetch(
    request: Request,
    env: Env,
    ctx: ExecutionContext
  ): Promise<Response> {
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
        endpoints: ["/discord", "/telegram/webhook", "/mcp"],
      });
    }

    // ── Discord Interactions webhook ──────────────────────────────────────

    if (pathname === "/discord") {
      if (method !== "POST") {
        return new Response("Method Not Allowed", {
          status: 405,
          headers: CORS_HEADERS,
        });
      }

      const response = await handleDiscord(request, {
        DISCORD_PUBLIC_KEY: env.DISCORD_PUBLIC_KEY,
        DISCORD_APPLICATION_ID: env.DISCORD_APPLICATION_ID,
        GOOGLE_CLOUD_API_KEY: env.GOOGLE_CLOUD_API_KEY,
      });

      // If the handler attached background work (deferred slash command),
      // use waitUntil to let it finish after the response is sent.
      const bgWork = (response as Response & { _backgroundWork?: Promise<void> })
        ._backgroundWork;
      if (bgWork) {
        ctx.waitUntil(bgWork);
      }

      return response;
    }

    // ── Telegram webhook ─────────────────────────────────────────────────

    if (pathname === "/telegram/webhook") {
      if (method !== "POST") {
        return new Response("Method Not Allowed", {
          status: 405,
          headers: CORS_HEADERS,
        });
      }

      return handleTelegram(request, {
        TELEGRAM_BOT_TOKEN: env.TELEGRAM_BOT_TOKEN,
        GOOGLE_CLOUD_API_KEY: env.GOOGLE_CLOUD_API_KEY,
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
        const result = await handleMcp(body, {
          GOOGLE_CLOUD_API_KEY: env.GOOGLE_CLOUD_API_KEY,
        });

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

    return new Response("Not Found", { status: 404 });
  },
};
