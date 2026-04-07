/**
 * Tests for the MCP tool dispatcher (tools.ts).
 */

import { describe, it, expect } from "vitest";
import { callTool, TOOLS } from "./tools.js";

// ---------------------------------------------------------------------------
// TOOLS definitions
// ---------------------------------------------------------------------------

describe("TOOLS", () => {
  it("defines three tools", () => {
    expect(TOOLS).toHaveLength(3);
  });

  it("contains rate_pokemon, list_pokemon, get_pokemon_info", () => {
    const names = TOOLS.map((t) => t.name);
    expect(names).toContain("rate_pokemon");
    expect(names).toContain("list_pokemon");
    expect(names).toContain("get_pokemon_info");
  });

  it("each tool has name, description, and inputSchema", () => {
    for (const tool of TOOLS) {
      expect(typeof tool.name).toBe("string");
      expect(typeof tool.description).toBe("string");
      expect(tool.inputSchema.type).toBe("object");
    }
  });
});

// ---------------------------------------------------------------------------
// callTool — rate_pokemon
// ---------------------------------------------------------------------------

describe("callTool — rate_pokemon", () => {
  it("rates a valid Pokémon", () => {
    const result = callTool("rate_pokemon", {
      name: "Spheal",
      nature: "Impish",
      subskills: ["Energy Recovery Bonus", "Inventory Up S", "Helping Speed M"],
    });
    const parsed = JSON.parse(result);
    expect(parsed.name).toBe("Spheal");
    expect(parsed.specialty).toBe("Berries");
    expect(parsed.nature).toBe("Impish");
    expect(parsed).toHaveProperty("grade");
    expect(parsed).toHaveProperty("formatted_subskills");
  });

  it("includes formatted_subskills in output", () => {
    const result = callTool("rate_pokemon", {
      name: "Spheal",
      nature: "Impish",
      subskills: ["Energy Recovery Bonus"],
    });
    const parsed = JSON.parse(result);
    expect(parsed.formatted_subskills).toContain("[Lv. 10]");
  });

  it("converts locked_skills Set to array", () => {
    const result = callTool("rate_pokemon", {
      name: "Spheal",
      nature: "Impish",
      subskills: ["Energy Recovery Bonus", "Inventory Up S", "Helping Speed M"],
      level: 10,
    });
    const parsed = JSON.parse(result);
    expect(Array.isArray(parsed.locked_skills)).toBe(true);
  });

  it("returns error for missing name", () => {
    const result = callTool("rate_pokemon", {
      nature: "Impish",
      subskills: [],
    });
    expect(result).toContain("Error");
  });

  it("returns error for missing nature", () => {
    const result = callTool("rate_pokemon", {
      name: "Spheal",
      subskills: [],
    });
    expect(result).toContain("Error");
  });

  it("returns error for unknown Pokémon", () => {
    const result = callTool("rate_pokemon", {
      name: "FakeMon",
      nature: "Impish",
      subskills: [],
    });
    expect(result).toContain("Error");
    expect(result).toContain("FakeMon");
  });

  it("returns error for unknown nature", () => {
    const result = callTool("rate_pokemon", {
      name: "Spheal",
      nature: "FakeNature",
      subskills: [],
    });
    expect(result).toContain("Error");
  });

  it("handles missing subskills gracefully", () => {
    const result = callTool("rate_pokemon", {
      name: "Spheal",
      nature: "Impish",
    });
    // subskills defaults to [] when not provided
    const parsed = JSON.parse(result);
    expect(parsed.name).toBe("Spheal");
  });

  it("accepts level parameter", () => {
    const result = callTool("rate_pokemon", {
      name: "Spheal",
      nature: "Impish",
      subskills: ["Energy Recovery Bonus", "Inventory Up S"],
      level: 25,
    });
    const parsed = JSON.parse(result);
    expect(parsed.locked_skills.length).toBeGreaterThan(0);
  });
});

// ---------------------------------------------------------------------------
// callTool — list_pokemon
// ---------------------------------------------------------------------------

describe("callTool — list_pokemon", () => {
  it("lists all Pokémon without filter", () => {
    const result = callTool("list_pokemon", {});
    const parsed = JSON.parse(result);
    expect(parsed.count).toBeGreaterThan(100);
    expect(parsed.pokemon).toContain("Pikachu");
  });

  it("filters by specialty", () => {
    const result = callTool("list_pokemon", { specialty: "Berries" });
    const parsed = JSON.parse(result);
    expect(parsed.count).toBeGreaterThan(0);
    expect(parsed.pokemon).toContain("Pikachu");
    expect(parsed.pokemon).not.toContain("Bulbasaur"); // Ingredients
  });

  it("handles empty specialty (lists all)", () => {
    const result = callTool("list_pokemon", { specialty: "" });
    const parsed = JSON.parse(result);
    expect(parsed.count).toBeGreaterThan(100);
  });
});

// ---------------------------------------------------------------------------
// callTool — get_pokemon_info
// ---------------------------------------------------------------------------

describe("callTool — get_pokemon_info", () => {
  it("returns info for known Pokémon", () => {
    const result = callTool("get_pokemon_info", { name: "Spheal" });
    const parsed = JSON.parse(result);
    expect(parsed.name).toBe("Spheal");
    expect(parsed.specialty).toBe("Berries");
    expect(typeof parsed.base_frequency).toBe("number");
    expect(typeof parsed.helps_per_day).toBe("number");
  });

  it("returns error for unknown Pokémon", () => {
    const result = callTool("get_pokemon_info", { name: "FakeMon" });
    expect(result).toContain("Error");
  });

  it("returns error for missing name", () => {
    const result = callTool("get_pokemon_info", {});
    expect(result).toContain("Error");
  });
});

// ---------------------------------------------------------------------------
// callTool — unknown tool
// ---------------------------------------------------------------------------

describe("callTool — unknown tool", () => {
  it("throws for unknown tool name", () => {
    expect(() => callTool("nonexistent_tool", {})).toThrow("Unknown tool");
  });
});
