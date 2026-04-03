/**
 * MCP tool definitions and dispatcher for Pokémon Sleep Rater.
 *
 * Exposes four tools:
 *   1. rate_pokemon_from_url  — Rate a Pokémon from a screenshot URL (OCR)
 *   2. rate_pokemon_manual    — Rate a Pokémon by providing data directly
 *   3. list_pokemon           — List supported Pokémon
 *   4. get_pokemon_info       — Get info about a specific Pokémon
 */

import { detectTextUri } from "./ocr.js";
import {
  ratePokemon,
  ratePokemonFromOcr,
  listPokemon,
  getPokemonInfo,
} from "./rating-engine.js";
import type { RatingResult } from "./rating-engine.js";
import { subskillsToString } from "./formatting.js";

// ---------------------------------------------------------------------------
// Env
// ---------------------------------------------------------------------------

export interface ToolEnv {
  GOOGLE_CLOUD_API_KEY: string;
}

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
    name: "rate_pokemon_from_url",
    description:
      "Rate a Pokémon Sleep screenshot by providing its image URL. " +
      "Uses Google Cloud Vision OCR to extract the Pokémon's name, nature, and subskills, " +
      "then computes a rating grade (F through S), percentile, and production estimate.",
    inputSchema: {
      type: "object",
      properties: {
        image_url: {
          type: "string",
          description: "Public URL of the Pokémon Sleep screenshot image",
        },
        level: {
          type: "number",
          description:
            "Optional: Pokémon's current level (enables level-aware scoring — " +
            "subskills not yet unlocked are excluded)",
        },
      },
      required: ["image_url"],
    },
  },
  {
    name: "rate_pokemon_manual",
    description:
      "Rate a Pokémon by providing its name, nature, and subskills directly " +
      "(no screenshot needed). Returns grade, percentile, all-specialty scores, " +
      "and production estimate.",
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
            "Array of subskill names in OCR detection order " +
            "(Lv.10, Lv.50, Lv.100, Lv.25, Lv.75), e.g. " +
            "['Energy Recovery Bonus', 'Inventory Up S', 'Helping Speed M']",
        },
        level: {
          type: "number",
          description: "Optional: Pokémon's current level for level-aware scoring",
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

export async function callTool(
  name: string,
  args: Record<string, unknown>,
  env: ToolEnv
): Promise<string> {
  switch (name) {
    case "rate_pokemon_from_url": {
      const imageUrl = str(args.image_url);
      if (!imageUrl) return "Error: image_url is required";

      const level =
        typeof args.level === "number" ? args.level : null;

      const ocrResults = await detectTextUri(imageUrl, env.GOOGLE_CLOUD_API_KEY);
      if (!ocrResults) return "Error: Could not read the image via OCR.";

      const result = ratePokemonFromOcr(ocrResults, level);
      if (!result) {
        return (
          "Error: Pokémon not found. The screenshot must show the " +
          "Pokémon's name, nature, and subskills."
        );
      }

      return serialiseRating(result);
    }

    case "rate_pokemon_manual": {
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
