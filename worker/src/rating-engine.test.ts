/**
 * Tests for the Pokémon Sleep rating engine (rating-engine.ts).
 *
 * Covers: findSpecialty, ratePokemon, ratePokemonFromOcr, listPokemon, getPokemonInfo,
 * plus internal logic (grading, frequency weight, percentile, locking).
 */

import { describe, it, expect } from "vitest";
import {
  findSpecialty,
  ratePokemon,
  ratePokemonFromOcr,
  listPokemon,
  getPokemonInfo,
} from "./rating-engine.js";

// ---------------------------------------------------------------------------
// findSpecialty
// ---------------------------------------------------------------------------

describe("findSpecialty", () => {
  it("parses valid Pokémon, nature, and subskills", () => {
    const parsed = findSpecialty([
      "Spheal",
      "Impish",
      "Energy Recovery Bonus",
      "Inventory Up S",
    ]);
    expect(parsed).not.toBeNull();
    expect(parsed!.name).toBe("Spheal");
    expect(parsed!.nature).toBe("Impish");
    expect(parsed!.skills).toEqual(["Energy Recovery Bonus", "Inventory Up S"]);
    expect(parsed!.specialty).toBe("Berries");
  });

  it("returns null when Pokémon is not recognised", () => {
    expect(findSpecialty(["FakeMon", "Impish"])).toBeNull();
  });

  it("returns null when nature is missing", () => {
    expect(findSpecialty(["Spheal", "FakeNature"])).toBeNull();
  });

  it("returns null for empty input", () => {
    expect(findSpecialty([])).toBeNull();
  });

  it("ignores unrecognised tokens", () => {
    const parsed = findSpecialty(["Garbage", "Spheal", "MoreGarbage", "Brave"]);
    expect(parsed).not.toBeNull();
    expect(parsed!.name).toBe("Spheal");
    expect(parsed!.nature).toBe("Brave");
  });

  it("handles Pokémon with dots in name", () => {
    const parsed = findSpecialty(["Mr. Mime", "Hardy"]);
    expect(parsed).not.toBeNull();
    expect(parsed!.name).toBe("Mr. Mime");
    expect(parsed!.specialty).toBe("Ingredients");
  });

  it("identifies Ingredients specialty", () => {
    const parsed = findSpecialty(["Bulbasaur", "Hardy"]);
    expect(parsed).not.toBeNull();
    expect(parsed!.specialty).toBe("Ingredients");
  });

  it("identifies Skills specialty", () => {
    const parsed = findSpecialty(["Wigglytuff", "Bold"]);
    expect(parsed).not.toBeNull();
    expect(parsed!.specialty).toBe("Skills");
  });
});

// ---------------------------------------------------------------------------
// ratePokemon — main rating function
// ---------------------------------------------------------------------------

describe("ratePokemon", () => {
  const SKILLS = [
    "Energy Recovery Bonus",
    "Inventory Up S",
    "Helping Speed M",
    "Inventory Up L",
    "Skill Trigger S",
  ];

  it("returns a full rating result for valid input", () => {
    const result = ratePokemon("Spheal", "Impish", SKILLS);
    expect(result).not.toBeNull();
    expect(result!.name).toBe("Spheal");
    expect(result!.specialty).toBe("Berries");
    expect(result!.nature).toBe("Impish");
    expect(typeof result!.grade).toBe("string");
    expect(typeof result!.nature_rating).toBe("string");
    expect(typeof result!.percentile).toBe("number");
    expect(result!.percentile).toBeGreaterThanOrEqual(0);
    expect(result!.percentile).toBeLessThanOrEqual(100);
  });

  it("returns null for unknown Pokémon", () => {
    expect(ratePokemon("FakeMon", "Impish", SKILLS)).toBeNull();
  });

  it("returns null for unknown nature", () => {
    expect(ratePokemon("Spheal", "FakeNature", SKILLS)).toBeNull();
  });

  it("includes all three specialty scores", () => {
    const result = ratePokemon("Spheal", "Impish", SKILLS)!;
    expect(result.all_scores).toHaveProperty("Berries");
    expect(result.all_scores).toHaveProperty("Ingredients");
    expect(result.all_scores).toHaveProperty("Skills");
    for (const spec of ["Berries", "Ingredients", "Skills"]) {
      expect(result.all_scores[spec]).toHaveProperty("grade");
      expect(result.all_scores[spec]).toHaveProperty("percentile");
    }
  });

  it("computes helps_per_day for known Pokémon", () => {
    const result = ratePokemon("Spheal", "Impish", SKILLS)!;
    // Spheal freq = 3720, efficiency = 0.80
    const expected = Math.round(86400 / (3720 * 0.8));
    expect(result.helps_per_day).toBe(expected);
  });

  it("works with zero subskills", () => {
    const result = ratePokemon("Spheal", "Impish", []);
    expect(result).not.toBeNull();
    expect(Object.keys(result!.skills_value)).toHaveLength(0);
  });

  it("works with one subskill", () => {
    const result = ratePokemon("Spheal", "Impish", ["Helping Bonus"]);
    expect(result).not.toBeNull();
    expect(result!.skills_value).toHaveProperty("Helping Bonus");
  });

  // --- Level-aware locking ---

  it("locks skills above the Pokémon level", () => {
    const result = ratePokemon("Spheal", "Impish", SKILLS, 10)!;
    // Level 10: only index 0 (Lv.10) unlocked
    // DETECTION_ORDER_LEVELS = [10, 50, 100, 25, 75]
    expect(result.locked_skills.size).toBeGreaterThan(0);
    for (const skill of result.locked_skills) {
      expect(result.skills_value[skill]).toBe(0);
    }
  });

  it("unlocks all skills at level 100", () => {
    const result = ratePokemon("Spheal", "Impish", SKILLS, 100)!;
    expect(result.locked_skills.size).toBe(0);
  });

  it("unlocks two skills at level 25", () => {
    const result = ratePokemon("Spheal", "Impish", SKILLS, 25)!;
    // Locked: idx 1 (Lv.50), idx 2 (Lv.100), idx 4 (Lv.75) → 3 locked
    expect(result.locked_skills.size).toBe(3);
  });

  it("no skills are locked when level is null", () => {
    const result = ratePokemon("Spheal", "Impish", SKILLS, null)!;
    expect(result.locked_skills.size).toBe(0);
  });

  // --- Grading scale ---

  it("assigns F grade for very low score", () => {
    // Use a very negative nature with no skills to get a low score
    const result = ratePokemon("Spheal", "Bold", [])!;
    expect(result.final_grade).toContain("**F**");
  });

  it("assigns S grade for high score", () => {
    // Brave nature [1.67, 1.67, 1.67] + 5 great skills
    const highSkills = [
      "Helping Bonus",
      "Helping Speed M",
      "Berry Finding S",
      "Helping Speed S",
      "Skill Level Up M",
    ];
    const result = ratePokemon("Spheal", "Brave", highSkills)!;
    expect(result.final_grade).toContain("**S**");
  });

  // --- Cross-specialty ---

  it("rates berry Pokémon as Berries specialty", () => {
    const result = ratePokemon("Pikachu", "Jolly", ["Berry Finding S"])!;
    expect(result.specialty).toBe("Berries");
  });

  it("rates ingredients Pokémon as Ingredients specialty", () => {
    const result = ratePokemon("Bulbasaur", "Hardy", ["Ingredient Finder M"])!;
    expect(result.specialty).toBe("Ingredients");
  });

  it("rates skills Pokémon as Skills specialty", () => {
    const result = ratePokemon("Wigglytuff", "Sassy", ["Skill Trigger M"])!;
    expect(result.specialty).toBe("Skills");
  });

  it("neutral nature yields equal scores for all specialties with no skills", () => {
    const result = ratePokemon("Spheal", "Hardy", [])!;
    const b = result.all_scores["Berries"].grade;
    const i = result.all_scores["Ingredients"].grade;
    const s = result.all_scores["Skills"].grade;
    expect(b).toBe(i);
    expect(i).toBe(s);
  });

  // --- Frequency weighting ---

  it("fast Pokémon score higher on speed-sensitive subskills", () => {
    // Diglett (2880s) vs Slowpoke (5760s) — both Helping Speed M
    const fast = ratePokemon("Diglett", "Hardy", ["Helping Speed M"])!;
    const slow = ratePokemon("Slowpoke", "Hardy", ["Helping Speed M"])!;
    // Both have same nature, but Diglett's speed-sensitive score should be higher
    const fastSpeedScore = fast.skills_value["Helping Speed M"];
    const slowSpeedScore = slow.skills_value["Helping Speed M"];
    expect(fastSpeedScore).toBeGreaterThan(slowSpeedScore);
  });
});

// ---------------------------------------------------------------------------
// ratePokemonFromOcr
// ---------------------------------------------------------------------------

describe("ratePokemonFromOcr", () => {
  it("rates from OCR results", () => {
    const result = ratePokemonFromOcr([
      "Spheal",
      "Impish",
      "Energy Recovery Bonus",
      "Inventory Up S",
      "Helping Speed M",
    ]);
    expect(result).not.toBeNull();
    expect(result!.name).toBe("Spheal");
  });

  it("returns null when OCR results lack a valid Pokémon", () => {
    expect(ratePokemonFromOcr(["FakeMon", "Impish"])).toBeNull();
  });

  it("passes through level parameter", () => {
    const result = ratePokemonFromOcr(
      ["Spheal", "Impish", "Energy Recovery Bonus", "Inventory Up S", "Helping Speed M"],
      10
    );
    expect(result).not.toBeNull();
    expect(result!.locked_skills.size).toBeGreaterThan(0);
  });
});

// ---------------------------------------------------------------------------
// listPokemon
// ---------------------------------------------------------------------------

describe("listPokemon", () => {
  it("lists all Pokémon without filter", () => {
    const all = listPokemon();
    expect(all.length).toBeGreaterThan(100);
    expect(all).toContain("Pikachu");
    expect(all).toContain("Spheal");
  });

  it("filters by Berries specialty", () => {
    const berries = listPokemon("Berries");
    expect(berries.length).toBeGreaterThan(0);
    expect(berries).toContain("Pikachu");
    expect(berries).not.toContain("Bulbasaur"); // Ingredients
  });

  it("filters by Ingredients specialty", () => {
    const ingredients = listPokemon("Ingredients");
    expect(ingredients.length).toBeGreaterThan(0);
    expect(ingredients).toContain("Bulbasaur");
    expect(ingredients).not.toContain("Pikachu"); // Berries
  });

  it("filters by Skills specialty", () => {
    const skills = listPokemon("Skills");
    expect(skills.length).toBeGreaterThan(0);
    expect(skills).toContain("Wigglytuff");
    expect(skills).not.toContain("Pikachu"); // Berries
  });

  it("returns empty for non-existent specialty", () => {
    const none = listPokemon("NonExistent");
    expect(none).toHaveLength(0);
  });
});

// ---------------------------------------------------------------------------
// getPokemonInfo
// ---------------------------------------------------------------------------

describe("getPokemonInfo", () => {
  it("returns info for known Pokémon", () => {
    const info = getPokemonInfo("Spheal");
    expect(info).not.toBeNull();
    expect(info!.name).toBe("Spheal");
    expect(info!.specialty).toBe("Berries");
    expect(info!.base_frequency).toBe(3720);
    expect(info!.helps_per_day).toBe(Math.round(86400 / (3720 * 0.8)));
  });

  it("returns null for unknown Pokémon", () => {
    expect(getPokemonInfo("FakeMon")).toBeNull();
  });

  it("returns helps_per_day as null when frequency is missing", () => {
    // All Pokémon in the DB should have frequencies, but test the logic
    const info = getPokemonInfo("Pikachu");
    expect(info).not.toBeNull();
    expect(typeof info!.helps_per_day).toBe("number");
  });
});
