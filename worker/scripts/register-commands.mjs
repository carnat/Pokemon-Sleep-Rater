#!/usr/bin/env node
/**
 * register-commands.mjs
 *
 * Bulk-registers (PUT, idempotent) all Discord slash commands for the
 * Pokémon Sleep Rater application.
 *
 * Required environment variables:
 *   DISCORD_APPLICATION_ID  — Discord application / client ID
 *   DISCORD_BOT_TOKEN       — Bot token from the Discord Developer Portal
 *                             (the full string including the "Bot " prefix is
 *                             NOT required here; just the raw token)
 *
 * Usage:
 *   node scripts/register-commands.mjs
 *   npm run register-commands
 */

const { DISCORD_APPLICATION_ID, DISCORD_BOT_TOKEN } = process.env;

if (!DISCORD_APPLICATION_ID || !DISCORD_BOT_TOKEN) {
  console.error(
    "Error: DISCORD_APPLICATION_ID and DISCORD_BOT_TOKEN must be set."
  );
  process.exit(1);
}

// ---------------------------------------------------------------------------
// Command definitions
// ---------------------------------------------------------------------------

const commands = [
  {
    name: "rateps",
    description: "Rate a Pokémon Sleep screenshot and show its grade.",
    options: [
      {
        name: "image",
        description: "Screenshot showing the Pokémon's name, nature, and subskills.",
        type: 11, // ATTACHMENT
        required: true,
      },
      {
        name: "level",
        description: "Current Pokémon level (1–100). Enables level-aware subskill scoring.",
        type: 4, // INTEGER
        required: false,
        min_value: 1,
        max_value: 100,
      },
    ],
  },
];

// ---------------------------------------------------------------------------
// Register via Discord REST API
// ---------------------------------------------------------------------------

const url = `https://discord.com/api/v10/applications/${DISCORD_APPLICATION_ID}/commands`;

console.log(`Registering ${commands.length} command(s) for application ${DISCORD_APPLICATION_ID}…`);

const response = await fetch(url, {
  method: "PUT",
  headers: {
    "Content-Type": "application/json",
    Authorization: `Bot ${DISCORD_BOT_TOKEN}`,
  },
  body: JSON.stringify(commands),
});

const text = await response.text();

if (!response.ok) {
  console.error(`Discord API error ${response.status}: ${text}`);
  process.exit(1);
}

const registered = JSON.parse(text);
console.log(`Successfully registered ${registered.length} command(s):`);
for (const cmd of registered) {
  console.log(`  /${cmd.name} (id: ${cmd.id})`);
}
