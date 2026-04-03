/**
 * Telegram Bot webhook handler for Cloudflare Workers.
 *
 * Handles incoming Telegram webhook updates for the /rateps command.
 * No long-polling needed — Telegram pushes updates to the webhook URL.
 *
 * Setup:
 *   1. Create a bot via @BotFather
 *   2. Set the webhook URL:
 *      curl https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://<worker>/telegram/webhook
 *   3. Store TELEGRAM_BOT_TOKEN and GOOGLE_CLOUD_API_KEY as Cloudflare secrets
 */

import { detectTextUri } from "./ocr.js";
import { ratePokemonFromOcr } from "./rating-engine.js";
import { subskillsToString } from "./formatting.js";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface TelegramUpdate {
  update_id: number;
  message?: TelegramMessage;
}

interface TelegramMessage {
  message_id: number;
  chat: { id: number };
  text?: string;
  caption?: string;
  photo?: Array<{ file_id: string; file_size?: number }>;
  reply_to_message?: TelegramMessage;
}

// ---------------------------------------------------------------------------
// Telegram API helpers
// ---------------------------------------------------------------------------

async function sendMessage(
  token: string,
  chatId: number,
  text: string,
  parseMode: string = "Markdown"
): Promise<void> {
  const url = `https://api.telegram.org/bot${token}/sendMessage`;
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      chat_id: chatId,
      text,
      parse_mode: parseMode,
    }),
  });
  if (!res.ok) {
    console.error(`Telegram sendMessage failed: ${res.status} ${await res.text()}`);
  }
}

async function getFileUrl(token: string, fileId: string): Promise<string | null> {
  const url = `https://api.telegram.org/bot${token}/getFile?file_id=${encodeURIComponent(fileId)}`;
  const res = await fetch(url);
  if (!res.ok) return null;
  const data = (await res.json()) as { ok: boolean; result?: { file_path?: string } };
  if (!data.ok || !data.result?.file_path) return null;
  return `https://api.telegram.org/file/bot${token}/${data.result.file_path}`;
}

// ---------------------------------------------------------------------------
// Format rating result for Telegram
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

function formatTelegramResponse(result: RatingResult, level: number | null): string {
  const levelNote = level ? ` (Lv. ${level})` : "";
  const topPct = 100 - result.percentile;

  const lines: string[] = [
    `*Pokémon Evaluation*`,
    `Your ${result.name}${levelNote} is rated ${result.final_grade}`,
    "",
    "*Subskills*",
    subskillsToString(result.skills_value, result.locked_skills),
    "",
    `*Nature*: ${result.nature}: ${result.nature_rating}`,
    "",
    `*Total Score (${result.specialty})*: ${result.grade}  •  Top ${topPct}% for ${result.specialty}`,
    "",
    "*All Specialty Scores*",
  ];

  for (const [spec, data] of Object.entries(result.all_scores)) {
    const marker = spec === result.specialty ? "★" : "  ";
    lines.push(
      `${marker} ${spec}: *${data.grade}* (top ${100 - data.percentile}%)`
    );
  }

  if (result.helps_per_day) {
    lines.push("", `*Est. Production*: ~${result.helps_per_day} helps/day`);
  }

  return lines.join("\n");
}

// ---------------------------------------------------------------------------
// Main handler
// ---------------------------------------------------------------------------

export interface TelegramEnv {
  TELEGRAM_BOT_TOKEN: string;
  GOOGLE_CLOUD_API_KEY: string;
}

export async function handleTelegram(
  request: Request,
  env: TelegramEnv
): Promise<Response> {
  let update: TelegramUpdate;
  try {
    update = (await request.json()) as TelegramUpdate;
  } catch {
    return new Response("Bad request", { status: 400 });
  }

  const message = update.message;
  if (!message) {
    return new Response("OK", { status: 200 });
  }

  const chatId = message.chat.id;
  const text = message.text ?? message.caption ?? "";

  // Handle /start command
  if (text.startsWith("/start")) {
    await sendMessage(
      env.TELEGRAM_BOT_TOKEN,
      chatId,
      "Welcome to Pokémon Sleep Rater! 🌙\n\n" +
        "Send a photo of your Pokémon with the caption /rateps to get a rating.\n" +
        "You can also include your Pokémon's level after the command:\n" +
        "  /rateps 35\n\n" +
        "The screenshot must show the Pokémon's name, nature, and subskills."
    );
    return new Response("OK", { status: 200 });
  }

  // Handle /rateps command
  if (text.startsWith("/rateps")) {
    // Parse optional level argument
    let level: number | null = null;
    const parts = text.split(/\s+/);
    if (parts.length > 1) {
      const parsed = parseInt(parts[1], 10);
      if (isNaN(parsed)) {
        await sendMessage(
          env.TELEGRAM_BOT_TOKEN,
          chatId,
          "Level must be a number, e.g. /rateps 35"
        );
        return new Response("OK", { status: 200 });
      }
      level = parsed;
    }

    // Find photo — attached to this message or in the replied-to message
    let photoFileId: string | null = null;
    if (message.photo && message.photo.length > 0) {
      photoFileId = message.photo[message.photo.length - 1].file_id;
    } else if (
      message.reply_to_message?.photo &&
      message.reply_to_message.photo.length > 0
    ) {
      const replyPhotos = message.reply_to_message.photo;
      photoFileId = replyPhotos[replyPhotos.length - 1].file_id;
    }

    if (!photoFileId) {
      await sendMessage(
        env.TELEGRAM_BOT_TOKEN,
        chatId,
        "Please send a Pokémon screenshot as a photo with the caption /rateps."
      );
      return new Response("OK", { status: 200 });
    }

    try {
      // Get public URL for the photo
      const imageUrl = await getFileUrl(env.TELEGRAM_BOT_TOKEN, photoFileId);
      if (!imageUrl) {
        await sendMessage(
          env.TELEGRAM_BOT_TOKEN,
          chatId,
          "Could not retrieve the photo. Please try again."
        );
        return new Response("OK", { status: 200 });
      }

      // OCR
      const ocrResults = await detectTextUri(imageUrl, env.GOOGLE_CLOUD_API_KEY);
      if (!ocrResults) {
        await sendMessage(
          env.TELEGRAM_BOT_TOKEN,
          chatId,
          "Could not read the image. Please check the screenshot and try again."
        );
        return new Response("OK", { status: 200 });
      }

      // Rate
      const result = ratePokemonFromOcr(ocrResults, level);
      if (!result) {
        await sendMessage(
          env.TELEGRAM_BOT_TOKEN,
          chatId,
          "Pokémon not found. Please check the image (name, nature, and subskills must be visible)."
        );
        return new Response("OK", { status: 200 });
      }

      // Send result
      const responseText = formatTelegramResponse(result, level);
      await sendMessage(env.TELEGRAM_BOT_TOKEN, chatId, responseText);
    } catch (e) {
      console.error("Error processing Telegram /rateps:", e);
      await sendMessage(
        env.TELEGRAM_BOT_TOKEN,
        chatId,
        "Pokémon not found. Please check the image upload (name, nature, and subskills) or try again."
      );
    }

    return new Response("OK", { status: 200 });
  }

  // Unknown command — ignore
  return new Response("OK", { status: 200 });
}
