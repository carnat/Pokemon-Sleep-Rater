/**
 * MCP tool definitions and dispatcher for Pokémon Sleep Rater.
 *
 * Pure-computation tools — no external API calls, no secrets required.
 * The LLM reads screenshots natively and calls rate_pokemon with extracted data.
 *
 * Exposes three tools:
 *   1. rate_pokemon    — Rate a Pokémon by providing data directly
 *   2. list_pokemon    — List supported Pokémon
 *   3. get_pokemon_info — Get info about a specific Pokémon
 */

import {
  ratePokemon,
  listPokemon,
  getPokemonInfo,
} from "./rating-engine.js";
import type { RatingResult } from "./rating-engine.js";
import { subskillsToString } from "./formatting.js";

// ---------------------------------------------------------------------------
// Tool definitions (MCP spec format)
// ---------------------------------------------------------------------------

export interface Tool {
  name: string;
  description: string;
  inputSchema: {
    type: "object";
    properties: Record<string, unknown>;
    required?: string[];
  };
}

export const TOOLS: Tool[] = [
  {
    name: "rate_pokemon",
    description:
      "Rate a Pokémon from Pokémon Sleep. If the user provides a screenshot, " +
      "read the Pokémon's name, nature, and subskills from the image yourself, " +
      "then call this tool with the extracted data.\n\n" +
      "Subskills appear in a two-column grid on the Pokémon's detail screen:\n" +
      "  Column 1: Lv.10 (top), Lv.50 (middle), Lv.100 (bottom)\n" +
      "  Column 2: Lv.25 (top), Lv.75 (bottom)\n" +
      "Provide them in reading order: Lv.10, Lv.50, Lv.100, Lv.25, Lv.75.\n\n" +
      "Valid subskill names: Berry Finding S, Dream Shard Bonus, " +
      "Energy Recovery Bonus, Energy Recovery S, Energy Recovery M, " +
      "Helping Bonus, Helping Speed S, Helping Speed M, " +
      "Ingredient Finder S, Ingredient Finder M, " +
      "Inventory Up S, Inventory Up M, Inventory Up L, " +
      "Research EXP Bonus, Skill Level Up S, Skill Level Up M, " +
      "Skill Trigger S, Skill Trigger M, Sleep EXP Bonus.\n\n" +
      "Valid natures: Hardy, Lonely, Brave, Adamant, Naughty, Bold, Docile, " +
      "Relaxed, Impish, Lax, Timid, Hasty, Serious, Jolly, Naive, Modest, " +
      "Mild, Quiet, Bashful, Rash, Calm, Gentle, Sassy, Careful, Quirky.\n\n" +
      "Rating scale: F (≤11) → D (≤14) → C (≤17) → B (≤20) → A (≤23) → S (>23). " +
      "Each Pokémon has a primary specialty (Berries, Ingredients, or Skills) " +
      "and is scored across all three with a percentile ranking.",
    inputSchema: {
      type: "object",
      properties: {
        name: {
          type: "string",
          description: "Pokémon name, e.g. 'Spheal'",
        },
        nature: {
          type: "string",
          description: "Nature name, e.g. 'Impish'",
        },
        subskills: {
          type: "array",
          items: { type: "string" },
          description:
            "Array of subskill names in column-reading order " +
            "(Lv.10, Lv.50, Lv.100, Lv.25, Lv.75), e.g. " +
            "['Energy Recovery Bonus', 'Inventory Up S', 'Helping Speed M']",
        },
        level: {
          type: "number",
          description:
            "Optional: Pokémon's current level (enables level-aware scoring — " +
            "subskills not yet unlocked at the given level are excluded)",
        },
      },
      required: ["name", "nature", "subskills"],
    },
  },
  {
    name: "list_pokemon",
    description:
      "List all supported Pokémon (Gen 1-6). Optionally filter by specialty " +
      "(Berries, Ingredients, or Skills).",
    inputSchema: {
      type: "object",
      properties: {
        specialty: {
          type: "string",
          description: "Optional filter: 'Berries', 'Ingredients', or 'Skills'",
          enum: ["Berries", "Ingredients", "Skills"],
        },
      },
    },
  },
  {
    name: "get_pokemon_info",
    description:
      "Get detailed info about a specific Pokémon: specialty, base helping " +
      "frequency, and estimated helps per day.",
    inputSchema: {
      type: "object",
      properties: {
        name: {
          type: "string",
          description: "Pokémon name, e.g. 'Spheal'",
        },
      },
      required: ["name"],
    },
  },
];

// ---------------------------------------------------------------------------
// Serialise a rating result to a readable JSON string
// ---------------------------------------------------------------------------

function serialiseRating(result: RatingResult): string {
  // Convert Set to array for JSON serialisation
  return JSON.stringify(
    {
      ...result,
      locked_skills: [...result.locked_skills],
      formatted_subskills: subskillsToString(
        result.skills_value,
        result.locked_skills
      ),
    },
    null,
    2
  );
}

// ---------------------------------------------------------------------------
// Tool dispatcher
// ---------------------------------------------------------------------------

const str = (v: unknown, fallback = ""): string =>
  typeof v === "string" ? v : fallback;

export function callTool(
  name: string,
  args: Record<string, unknown>,
): string {
  switch (name) {
    case "rate_pokemon": {
      const pokemonName = str(args.name);
      const nature = str(args.nature);
      const subskills = Array.isArray(args.subskills)
        ? (args.subskills as string[])
        : [];
      const level =
        typeof args.level === "number" ? args.level : null;

      if (!pokemonName || !nature) {
        return "Error: name and nature are required";
      }

      const result = ratePokemon(pokemonName, nature, subskills, level);
      if (!result) {
        return `Error: Pokémon '${pokemonName}' or nature '${nature}' not recognised.`;
      }

      return serialiseRating(result);
    }

    case "list_pokemon": {
      const specialty = str(args.specialty) || undefined;
      const pokemon = listPokemon(specialty);
      return JSON.stringify({ count: pokemon.length, pokemon }, null, 2);
    }

    case "get_pokemon_info": {
      const pokemonName = str(args.name);
      if (!pokemonName) return "Error: name is required";

      const info = getPokemonInfo(pokemonName);
      if (!info) return `Error: Pokémon '${pokemonName}' not found.`;

      return JSON.stringify(info, null, 2);
    }

    default:
      throw new Error(`Unknown tool: ${name}`);
  }
}
