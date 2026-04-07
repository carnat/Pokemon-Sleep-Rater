/**
 * Discord Interactions webhook handler for Cloudflare Workers.
 *
 * Handles Discord slash commands via the Interactions endpoint (no gateway
 * connection needed). Uses the Web Crypto API for Ed25519 signature
 * verification.
 *
 * Slash command: /rateps image:<attachment> [level:<number>]
 *
 * Setup:
 *   1. Create a Discord application at https://discord.com/developers
 *   2. Set the Interactions Endpoint URL to https://<worker>/discord
 *   3. Add DISCORD_APPLICATION_ID and DISCORD_BOT_TOKEN as GitHub secrets, then
 *      push to master (or trigger the "Register Discord Slash Commands" workflow
 *      manually) — registration runs automatically via GitHub Actions.
 *   4. Store DISCORD_PUBLIC_KEY and GOOGLE_CLOUD_API_KEY as Cloudflare secrets
 */

import { detectTextUri } from "./ocr.js";
import { ratePokemonFromOcr } from "./rating-engine.js";
import { subskillsToString } from "./formatting.js";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface DiscordInteraction {
  type: number;
  id: string;
  token: string;
  data?: {
    name: string;
    options?: Array<{
      name: string;
      type: number;
      value: unknown;
    }>;
    resolved?: {
      attachments?: Record<
        string,
        { id: string; url: string; filename: string }
      >;
    };
  };
}

// Discord interaction types
const PING = 1;
const APPLICATION_COMMAND = 2;

// Discord response types
const PONG = 1;
const CHANNEL_MESSAGE = 4;
const DEFERRED_CHANNEL_MESSAGE = 5;

// ---------------------------------------------------------------------------
// Ed25519 signature verification (Web Crypto API)
// ---------------------------------------------------------------------------

async function verifyDiscordSignature(
  publicKey: string,
  signature: string,
  timestamp: string,
  body: string
): Promise<boolean> {
  const encoder = new TextEncoder();

  const keyData = hexToBytes(publicKey);
  const key = await crypto.subtle.importKey(
    "raw",
    keyData,
    { name: "Ed25519", namedCurve: "Ed25519" },
    false,
    ["verify"]
  );

  const sigData = hexToBytes(signature);
  const message = encoder.encode(timestamp + body);

  return crypto.subtle.verify("Ed25519", key, sigData, message);
}

function hexToBytes(hex: string): Uint8Array {
  const bytes = new Uint8Array(hex.length / 2);
  for (let i = 0; i < hex.length; i += 2) {
    bytes[i / 2] = parseInt(hex.substring(i, i + 2), 16);
  }
  return bytes;
}

// ---------------------------------------------------------------------------
// Format rating result as Discord embed
// ---------------------------------------------------------------------------

interface RatingResult {
  name: string;
  final_grade: string;
  skills_value: Record<string, number>;
  locked_skills: Set<string>;
  nature: string;
  nature_rating: string;
  grade: string;
  percentile: number;
  all_scores: Record<string, { grade: number; percentile: number }>;
  helps_per_day: number | null;
  specialty: string;
}

function formatDiscordEmbed(
  result: RatingResult,
  imageUrl: string,
  level: number | null
): Record<string, unknown> {
  const levelNote = level ? ` (Lv. ${level})` : "";
  const topPct = 100 - result.percentile;

  const specLines: string[] = [];
  for (const [spec, data] of Object.entries(result.all_scores)) {
    const marker = spec === result.specialty ? "★" : "  ";
    specLines.push(
      `${marker} ${spec}: **${data.grade}** (top ${100 - data.percentile}%)`
    );
  }

  const fields = [
    {
      name: "Subskills",
      value: subskillsToString(result.skills_value, result.locked_skills),
      inline: false,
    },
    {
      name: "Nature",
      value: `${result.nature}: ${result.nature_rating}`,
      inline: false,
    },
    {
      name: `Total Score (${result.specialty})`,
      value: `${result.grade}  •  Top ${topPct}% for ${result.specialty}`,
      inline: false,
    },
    {
      name: "All Specialty Scores",
      value: specLines.join("\n"),
      inline: false,
    },
  ];

  if (result.helps_per_day) {
    fields.push({
      name: "Est. Production",
      value: `~${result.helps_per_day} helps/day`,
      inline: true,
    });
  }

  return {
    title: "Pokémon Evaluation",
    description: `[*Your ${result.name}${levelNote} is rated ${result.final_grade}*](${imageUrl})`,
    color: 0x57f287, // discord green
    fields,
    author: {
      name: "Pokémon Sleep Rater",
      icon_url: "https://i.imgur.com/xQ8V3OI.png",
    },
    thumbnail: { url: "https://i.imgur.com/Ox0DTqY.png" },
  };
}

// ---------------------------------------------------------------------------
// Send deferred follow-up via Discord webhook
// ---------------------------------------------------------------------------

async function sendFollowup(
  applicationId: string,
  interactionToken: string,
  payload: Record<string, unknown>
): Promise<void> {
  const url = `https://discord.com/api/v10/webhooks/${applicationId}/${interactionToken}`;
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    console.error(
      `Discord follow-up failed: ${res.status} ${await res.text()}`
    );
  }
}

// ---------------------------------------------------------------------------
// Main handler
// ---------------------------------------------------------------------------

export interface DiscordEnv {
  DISCORD_PUBLIC_KEY: string;
  DISCORD_APPLICATION_ID: string;
  GOOGLE_CLOUD_API_KEY: string;
}

export async function handleDiscord(
  request: Request,
  env: DiscordEnv
): Promise<Response> {
  const signature = request.headers.get("X-Signature-Ed25519") ?? "";
  const timestamp = request.headers.get("X-Signature-Timestamp") ?? "";
  const body = await request.text();

  // Verify signature
  const isValid = await verifyDiscordSignature(
    env.DISCORD_PUBLIC_KEY,
    signature,
    timestamp,
    body
  );
  if (!isValid) {
    return new Response("Invalid signature", { status: 401 });
  }

  const interaction: DiscordInteraction = JSON.parse(body);

  // Handle PING (Discord verification)
  if (interaction.type === PING) {
    return Response.json({ type: PONG });
  }

  // Handle slash commands
  if (interaction.type === APPLICATION_COMMAND) {
    if (interaction.data?.name === "rateps") {
      // Respond with deferred message immediately (we need to do OCR)
      const deferredResponse = Response.json({
        type: DEFERRED_CHANNEL_MESSAGE,
      });

      // Process the rating in the background using waitUntil-style pattern
      // Since we can't use waitUntil without ExecutionContext, we process
      // before returning for now. The 3-second Discord deadline means we
      // must defer and follow up.
      // We return the deferred response and use a separate fetch for follow-up.

      // Extract options
      const options = interaction.data.options ?? [];
      let imageUrl = "";
      let level: number | null = null;

      for (const opt of options) {
        if (opt.name === "image" && typeof opt.value === "string") {
          // Resolved attachment
          const attachment =
            interaction.data.resolved?.attachments?.[opt.value];
          if (attachment) imageUrl = attachment.url;
        }
        if (opt.name === "level" && typeof opt.value === "number") {
          level = opt.value;
        }
      }

      // Process in background — return deferred response immediately
      // We need ExecutionContext.waitUntil for this; handle via the caller
      const processPromise = processRating(
        env,
        interaction.id,
        interaction.token,
        imageUrl,
        level
      );

      // Return deferred, but also kick off the background work
      // The caller (index.ts) should pass ctx.waitUntil
      return Object.assign(deferredResponse, {
        _backgroundWork: processPromise,
      });
    }
  }

  return Response.json(
    { type: CHANNEL_MESSAGE, data: { content: "Unknown command." } }
  );
}

async function processRating(
  env: DiscordEnv,
  _interactionId: string,
  interactionToken: string,
  imageUrl: string,
  level: number | null
): Promise<void> {
  try {
    if (!imageUrl) {
      await sendFollowup(env.DISCORD_APPLICATION_ID, interactionToken, {
        content:
          "Pokémon not found. Please check image upload (name, nature, and subskills) or try again.",
      });
      return;
    }

    const ocrResults = await detectTextUri(imageUrl, env.GOOGLE_CLOUD_API_KEY);
    if (!ocrResults) {
      await sendFollowup(env.DISCORD_APPLICATION_ID, interactionToken, {
        content:
          "Could not read the image. Please check the screenshot and try again.",
      });
      return;
    }

    const result = ratePokemonFromOcr(ocrResults, level);
    if (!result) {
      await sendFollowup(env.DISCORD_APPLICATION_ID, interactionToken, {
        content:
          "Pokémon not found. Please check image upload (name, nature, and subskills) or try again.",
      });
      return;
    }

    const embed = formatDiscordEmbed(result, imageUrl, level);
    await sendFollowup(env.DISCORD_APPLICATION_ID, interactionToken, {
      embeds: [embed],
    });
  } catch (e) {
    console.error("Error processing Discord /rateps:", e);
    await sendFollowup(env.DISCORD_APPLICATION_ID, interactionToken, {
      content:
        "Pokémon not found. Please check image upload (name, nature, and subskills) or try again.",
    });
  }
}
