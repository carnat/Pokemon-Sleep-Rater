/**
 * Format subskill results for display.
 *
 * Ported from pokemon_db/db.py — subskills_to_string().
 */

/**
 * Format subskill results into a human-readable string.
 *
 * Subskills are detected in column-reading order (Lv.10, Lv.50, Lv.100, Lv.25, Lv.75).
 * The order array remaps detection indices to ascending display order.
 */
export function subskillsToString(
  results: Record<string, number>,
  lockedSkills: Set<string> = new Set()
): string {
  const order = [0, 3, 1, 4, 2];
  const prefixes = ["[Lv. 10]", "[Lv. 25]", "[Lv. 50]", "[Lv. 75]", "[Lv. 100]"];

  const keys = Object.keys(results);
  const lines: string[] = [];

  for (let i = 0; i < order.length; i++) {
    const idx = order[i];
    if (idx >= keys.length) continue;
    const key = keys[idx];
    const scoreStr = lockedSkills.has(key)
      ? "🔒 not yet unlocked"
      : String(results[key]);
    lines.push(`${prefixes[i]} ${key}: ${scoreStr}`);
  }

  return lines.join("\n");
}
