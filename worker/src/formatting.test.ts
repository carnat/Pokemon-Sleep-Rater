/**
 * Tests for the subskill formatting module (formatting.ts).
 */

import { describe, it, expect } from "vitest";
import { subskillsToString } from "./formatting.js";

// ---------------------------------------------------------------------------
// Basic formatting
// ---------------------------------------------------------------------------

describe("subskillsToString", () => {
  it("formats 5 skills in ascending level order", () => {
    const results: Record<string, number> = {
      "Skill A": 5, // detection idx 0 → Lv.10
      "Skill B": 4, // detection idx 1 → Lv.50
      "Skill C": 3, // detection idx 2 → Lv.100
      "Skill D": 2, // detection idx 3 → Lv.25
      "Skill E": 1, // detection idx 4 → Lv.75
    };
    const output = subskillsToString(results);
    const lines = output.split("\n");
    expect(lines).toHaveLength(5);

    // Display order: Lv.10 (idx 0), Lv.25 (idx 3), Lv.50 (idx 1), Lv.75 (idx 4), Lv.100 (idx 2)
    expect(lines[0]).toContain("[Lv. 10] Skill A: 5");
    expect(lines[1]).toContain("[Lv. 25] Skill D: 2");
    expect(lines[2]).toContain("[Lv. 50] Skill B: 4");
    expect(lines[3]).toContain("[Lv. 75] Skill E: 1");
    expect(lines[4]).toContain("[Lv. 100] Skill C: 3");
  });

  it("handles 3 skills (missing indices are skipped)", () => {
    const results: Record<string, number> = {
      "Skill A": 5, // idx 0
      "Skill B": 4, // idx 1
      "Skill C": 3, // idx 2
    };
    const output = subskillsToString(results);
    const lines = output.split("\n");
    // Order [0, 3, 1, 4, 2]: idx 0 present, idx 3 missing, idx 1 present, idx 4 missing, idx 2 present
    expect(lines).toHaveLength(3);
    expect(lines[0]).toContain("[Lv. 10]");
    expect(lines[1]).toContain("[Lv. 50]");
    expect(lines[2]).toContain("[Lv. 100]");
  });

  it("returns empty string for empty results", () => {
    expect(subskillsToString({})).toBe("");
  });

  it("handles single skill", () => {
    const output = subskillsToString({ "Berry Finding S": 5 });
    const lines = output.split("\n");
    expect(lines).toHaveLength(1);
    expect(lines[0]).toContain("[Lv. 10]");
    expect(lines[0]).toContain("Berry Finding S: 5");
  });
});

// ---------------------------------------------------------------------------
// Locked skills
// ---------------------------------------------------------------------------

describe("subskillsToString — locked skills", () => {
  it("shows 🔒 for locked skills", () => {
    const results: Record<string, number> = {
      "Skill A": 5,
      "Skill B": 0,
    };
    const locked = new Set(["Skill B"]);
    const output = subskillsToString(results, locked);
    expect(output).toContain("🔒 not yet unlocked");
    expect(output).toContain("Skill B: 🔒");
  });

  it("shows values for unlocked skills", () => {
    const results: Record<string, number> = {
      "Skill A": 5,
      "Skill B": 4,
    };
    const output = subskillsToString(results, new Set());
    expect(output).not.toContain("🔒");
  });

  it("handles mixed locked and unlocked", () => {
    const results: Record<string, number> = {
      "Skill A": 5,
      "Skill B": 0,
      "Skill C": 0,
      "Skill D": 0,
      "Skill E": 0,
    };
    const locked = new Set(["Skill B", "Skill C", "Skill D", "Skill E"]);
    const output = subskillsToString(results, locked);
    const lines = output.split("\n");
    // First line (Skill A) should show value
    expect(lines[0]).not.toContain("🔒");
    // All other lines should show locked
    for (let i = 1; i < lines.length; i++) {
      expect(lines[i]).toContain("🔒 not yet unlocked");
    }
  });

  it("defaults to empty set when lockedSkills is omitted", () => {
    const output = subskillsToString({ "Skill A": 5 });
    expect(output).not.toContain("🔒");
    expect(output).toContain("Skill A: 5");
  });
});
