/**
 * Tests for the MCP protocol handler (mcp.ts).
 *
 * Covers: handleMcp — initialize, ping, tools/list, tools/call,
 * notifications, batches, unknown methods, and error handling.
 */

import { describe, it, expect } from "vitest";
import { handleMcp } from "./mcp.js";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function req(method: string, params?: unknown, id: number | string = 1) {
  return { jsonrpc: "2.0" as const, id, method, params };
}

function notification(method: string, params?: unknown) {
  return { jsonrpc: "2.0" as const, method, params };
}

// ---------------------------------------------------------------------------
// initialize
// ---------------------------------------------------------------------------

describe("handleMcp — initialize", () => {
  it("returns server info and capabilities", async () => {
    const resp = (await handleMcp(req("initialize"))) as {
      jsonrpc: string;
      id: number;
      result: { protocolVersion: string; serverInfo: { name: string }; capabilities: unknown };
    };
    expect(resp.jsonrpc).toBe("2.0");
    expect(resp.id).toBe(1);
    expect(resp.result.protocolVersion).toBe("2024-11-05");
    expect(resp.result.serverInfo.name).toBe("pokemon-sleep-rater");
    expect(resp.result.capabilities).toHaveProperty("tools");
  });
});

// ---------------------------------------------------------------------------
// ping
// ---------------------------------------------------------------------------

describe("handleMcp — ping", () => {
  it("returns empty result", async () => {
    const resp = (await handleMcp(req("ping"))) as {
      jsonrpc: string;
      id: number;
      result: Record<string, never>;
    };
    expect(resp.jsonrpc).toBe("2.0");
    expect(resp.id).toBe(1);
    expect(resp.result).toEqual({});
  });
});

// ---------------------------------------------------------------------------
// tools/list
// ---------------------------------------------------------------------------

describe("handleMcp — tools/list", () => {
  it("returns list of tools", async () => {
    const resp = (await handleMcp(req("tools/list"))) as {
      result: { tools: Array<{ name: string }> };
    };
    const names = resp.result.tools.map((t: { name: string }) => t.name);
    expect(names).toContain("rate_pokemon");
    expect(names).toContain("list_pokemon");
    expect(names).toContain("get_pokemon_info");
  });
});

// ---------------------------------------------------------------------------
// tools/call
// ---------------------------------------------------------------------------

describe("handleMcp — tools/call", () => {
  it("calls rate_pokemon successfully", async () => {
    const resp = (await handleMcp(
      req("tools/call", {
        name: "rate_pokemon",
        arguments: {
          name: "Spheal",
          nature: "Impish",
          subskills: ["Energy Recovery Bonus"],
        },
      })
    )) as {
      result: { content: Array<{ type: string; text: string }> };
    };
    expect(resp.result.content).toHaveLength(1);
    expect(resp.result.content[0].type).toBe("text");
    const parsed = JSON.parse(resp.result.content[0].text);
    expect(parsed.name).toBe("Spheal");
  });

  it("calls list_pokemon successfully", async () => {
    const resp = (await handleMcp(
      req("tools/call", { name: "list_pokemon", arguments: {} })
    )) as {
      result: { content: Array<{ type: string; text: string }> };
    };
    const parsed = JSON.parse(resp.result.content[0].text);
    expect(parsed.count).toBeGreaterThan(0);
  });

  it("calls get_pokemon_info successfully", async () => {
    const resp = (await handleMcp(
      req("tools/call", { name: "get_pokemon_info", arguments: { name: "Pikachu" } })
    )) as {
      result: { content: Array<{ type: string; text: string }> };
    };
    const parsed = JSON.parse(resp.result.content[0].text);
    expect(parsed.name).toBe("Pikachu");
    expect(parsed.specialty).toBe("Berries");
  });

  it("returns error for missing tool name", async () => {
    const resp = (await handleMcp(req("tools/call", {}))) as {
      error: { code: number; message: string };
    };
    expect(resp.error).toBeDefined();
    expect(resp.error.code).toBe(-32602);
  });

  it("throws for unknown tool", async () => {
    const resp = (await handleMcp(
      req("tools/call", { name: "nonexistent_tool", arguments: {} })
    )) as {
      error: { code: number; message: string };
    };
    expect(resp.error).toBeDefined();
  });
});

// ---------------------------------------------------------------------------
// Unknown method
// ---------------------------------------------------------------------------

describe("handleMcp — unknown method", () => {
  it("returns method not found error", async () => {
    const resp = (await handleMcp(req("nonexistent/method"))) as {
      error: { code: number; message: string };
    };
    expect(resp.error).toBeDefined();
    expect(resp.error.code).toBe(-32601);
    expect(resp.error.message).toContain("not found");
  });
});

// ---------------------------------------------------------------------------
// Notifications
// ---------------------------------------------------------------------------

describe("handleMcp — notifications", () => {
  it("returns null for a notification", async () => {
    const resp = await handleMcp(notification("notifications/initialized"));
    expect(resp).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// Batch handling
// ---------------------------------------------------------------------------

describe("handleMcp — batch", () => {
  it("handles a batch of requests", async () => {
    const batch = [req("ping", undefined, 1), req("ping", undefined, 2)];
    const resp = (await handleMcp(batch)) as Array<{ id: number }>;
    expect(resp).toHaveLength(2);
    expect(resp[0].id).toBe(1);
    expect(resp[1].id).toBe(2);
  });

  it("returns null for a batch of only notifications", async () => {
    const batch = [
      notification("notifications/initialized"),
      notification("notifications/cancelled"),
    ];
    const resp = await handleMcp(batch);
    expect(resp).toBeNull();
  });

  it("filters notifications from mixed batch", async () => {
    const batch = [
      notification("notifications/initialized"),
      req("ping", undefined, 1),
    ];
    const resp = (await handleMcp(batch)) as Array<{ id: number }>;
    expect(resp).toHaveLength(1);
    expect(resp[0].id).toBe(1);
  });

  it("preserves request IDs in batch responses", async () => {
    const batch = [
      req("initialize", undefined, "alpha"),
      req("ping", undefined, "beta"),
    ];
    const resp = (await handleMcp(batch)) as Array<{ id: string }>;
    expect(resp[0].id).toBe("alpha");
    expect(resp[1].id).toBe("beta");
  });
});
