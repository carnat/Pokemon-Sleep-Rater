/**
 * Pokémon Sleep rating engine.
 *
 * Ported from pokemon.py — the RatePokemon class logic.
 * Pure computation; no platform-specific APIs required.
 */

import {
  POKEMON_SPECIALTIES,
  NATURES,
  SUBSKILLS,
  BASE_FREQUENCIES,
  SPEED_SENSITIVE_SUBSKILLS,
  DETECTION_ORDER_LEVELS,
  SCORE_RANGES,
  BASELINE_FREQ,
  PRODUCTION_EFFICIENCY,
  SPECIALTIES,
  SPECIALTY_INDEX,
} from "./pokemon-data.js";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface SpecialtyScore {
  grade: number;
  percentile: number;
}

export interface RatingResult {
  name: string;
  final_grade: string;
  skills_value: Record<string, number>;
  locked_skills: Set<string>;
  nature: string;
  nature_rating: string;
  grade: string;
  percentile: number;
  all_scores: Record<string, SpecialtyScore>;
  helps_per_day: number | null;
  specialty: string;
}

// ---------------------------------------------------------------------------
// Grading scale
// ---------------------------------------------------------------------------

function gradingScale(grade: number): string {
  if (grade <= 11.0) return "**F**";
  if (grade <= 14.0) return "**D**";
  if (grade <= 17.0) return "**C**";
  if (grade <= 20.0) return "**B**";
  if (grade <= 23.0) return "**A**";
  return "**S**";
}

// ---------------------------------------------------------------------------
// Frequency weight
// ---------------------------------------------------------------------------

function frequencyWeight(name: string): number {
  const freq = BASE_FREQUENCIES[name];
  if (!freq) return 1.0;
  return BASELINE_FREQ / freq;
}

// ---------------------------------------------------------------------------
// Score a single subskill
// ---------------------------------------------------------------------------

function scoreSubskill(
  subskill: string,
  specialtyIdx: number,
  freqWeight: number
): number {
  const values = SUBSKILLS[subskill];
  if (!values) return 0;
  const base = values[specialtyIdx];
  if (SPEED_SENSITIVE_SUBSKILLS.has(subskill)) {
    return Math.round(base * freqWeight * 100) / 100;
  }
  return base;
}

// ---------------------------------------------------------------------------
// Rate for a single specialty
// ---------------------------------------------------------------------------

interface SpecialtyRating {
  grade: number;
  natureRating: number;
  skillsValue: Record<string, number>;
  lockedSkills: Set<string>;
  percentile: number;
}

function computePercentile(grade: number, specialty: string): number {
  const range = SCORE_RANGES[specialty];
  if (!range) return 50;
  const [minVal, maxVal] = range;
  const pct = ((grade - minVal) / (maxVal - minVal)) * 100;
  return Math.max(0, Math.min(100, Math.round(pct)));
}

function rateForSpecialty(
  name: string,
  nature: string,
  skills: string[],
  specialty: string,
  pokemonLevel: number | null
): SpecialtyRating {
  const idx = SPECIALTY_INDEX[specialty];
  const natureRating = NATURES[nature][idx];
  const freqW = frequencyWeight(name);

  let skillsRating = 0;
  const skillsValue: Record<string, number> = {};
  const lockedSkills = new Set<string>();

  for (let i = 0; i < skills.length; i++) {
    const skill = skills[i];
    const unlockLevel =
      i < DETECTION_ORDER_LEVELS.length ? DETECTION_ORDER_LEVELS[i] : 10;
    const isLocked = pokemonLevel !== null && pokemonLevel < unlockLevel;

    if (isLocked) {
      skillsValue[skill] = 0;
      lockedSkills.add(skill);
      continue;
    }

    const score = scoreSubskill(skill, idx, freqW);
    skillsValue[skill] = score;
    skillsRating += score;
  }

  const grade = Math.round((skillsRating + natureRating) * 100) / 100;
  const percentile = computePercentile(grade, specialty);

  return { grade, natureRating, skillsValue, lockedSkills, percentile };
}

// ---------------------------------------------------------------------------
// Parse OCR results
// ---------------------------------------------------------------------------

export interface ParsedPokemon {
  name: string;
  nature: string;
  skills: string[];
  specialty: string;
}

/**
 * Extract Pokémon name, nature, and subskills from OCR text results.
 * Returns null if the Pokémon or nature cannot be identified.
 */
export function findSpecialty(results: string[]): ParsedPokemon | null {
  let name = "";
  let nature = "";
  const skills: string[] = [];

  for (const item of results) {
    if (item in POKEMON_SPECIALTIES) name = item;
    if (item in NATURES) nature = item;
    if (item in SUBSKILLS) skills.push(item);
  }

  const specialty = POKEMON_SPECIALTIES[name];
  if (!specialty || !nature) return null;

  return { name, nature, skills, specialty };
}

// ---------------------------------------------------------------------------
// Main rating function
// ---------------------------------------------------------------------------

/**
 * Rate a Pokémon based on its name, nature, subskills, and optional level.
 *
 * Can be called with parsed data (no OCR needed) or with OCR results via
 * findSpecialty().
 */
export function ratePokemon(
  name: string,
  nature: string,
  skills: string[],
  pokemonLevel: number | null = null
): RatingResult | null {
  const specialty = POKEMON_SPECIALTIES[name];
  if (!specialty || !(nature in NATURES)) return null;

  // Primary specialty rating
  const primary = rateForSpecialty(name, nature, skills, specialty, pokemonLevel);

  // All-specialty scores
  const allScores: Record<string, SpecialtyScore> = {};
  for (const spec of SPECIALTIES) {
    const r = rateForSpecialty(name, nature, skills, spec, pokemonLevel);
    allScores[spec] = { grade: r.grade, percentile: r.percentile };
  }

  // Production estimate
  const freq = BASE_FREQUENCIES[name];
  const helpsPerDay = freq
    ? Math.round(86400 / (freq * PRODUCTION_EFFICIENCY))
    : null;

  return {
    name,
    final_grade: gradingScale(primary.grade),
    skills_value: primary.skillsValue,
    locked_skills: primary.lockedSkills,
    nature,
    nature_rating: String(primary.natureRating),
    grade: String(primary.grade),
    percentile: primary.percentile,
    all_scores: allScores,
    helps_per_day: helpsPerDay,
    specialty,
  };
}

/**
 * Rate a Pokémon from OCR results (convenience wrapper).
 */
export function ratePokemonFromOcr(
  ocrResults: string[],
  pokemonLevel: number | null = null
): RatingResult | null {
  const parsed = findSpecialty(ocrResults);
  if (!parsed) return null;
  return ratePokemon(parsed.name, parsed.nature, parsed.skills, pokemonLevel);
}

/**
 * List all supported Pokémon, optionally filtered by specialty.
 */
export function listPokemon(specialty?: string): string[] {
  if (specialty) {
    return Object.entries(POKEMON_SPECIALTIES)
      .filter(([, s]) => s === specialty)
      .map(([name]) => name);
  }
  return Object.keys(POKEMON_SPECIALTIES);
}

/**
 * Get info about a specific Pokémon.
 */
export function getPokemonInfo(name: string): Record<string, unknown> | null {
  const specialty = POKEMON_SPECIALTIES[name];
  if (!specialty) return null;

  return {
    name,
    specialty,
    base_frequency: BASE_FREQUENCIES[name] ?? null,
    helps_per_day: BASE_FREQUENCIES[name]
      ? Math.round(86400 / (BASE_FREQUENCIES[name] * PRODUCTION_EFFICIENCY))
      : null,
  };
}
