# Pokémon Sleep Rater
A multi-platform bot (Discord, Telegram, and MCP) that rates Pokémon from Pokémon Sleep! Upload a screenshot containing the Pokémon's name (no nicknames), nature, and subskills. The bot may fail if a screenshot is unclear or if too many requests are made at once.

<p align="center">Example Output:</p>

<p align="center">
  <img src="https://i.imgur.com/dSDM6rh.png">
</p>

## Architecture

The project provides two implementations of the same rating engine:

- **Python** — standalone Discord and Telegram bots, run locally or on a cloud VM.
- **Cloudflare Worker (TypeScript)** — a single serverless deployment that serves Discord (Interactions endpoint), Telegram (webhook), and an MCP server over HTTP.

The free-hosted v1 runtime uses local Tesseract OCR only. Screenshots are processed transiently and are not stored.

## How to Use

### Discord
Discord is deferred for the free-hosted v1 path. The existing Python Discord bot can still be run manually, but the Render deployment focuses on web upload, Telegram webhook, and protected MCP.

Use the slash command `/rateps` and attach a screenshot. An optional `level` argument lets you specify your Pokémon's current level so that subskills not yet unlocked are excluded from the score.

```
/rateps image:<screenshot>
/rateps image:<screenshot> level:35
```

### Telegram
Send a photo to the bot with the caption `/rateps`. You can also include an optional level number after the command:

```
/rateps
/rateps 35
```

You can also send a photo first and then reply to it with `/rateps`.

### MCP (Model Context Protocol)
The Flask app exposes a protected MCP endpoint at `POST /mcp` that speaks JSON-RPC 2.0. It is a **pure-computation engine**: clients provide structured fields such as name, nature, subskills, and optional level. Screenshots should be submitted through web/Telegram OCR or parsed by the client before calling MCP.

AI assistants and other MCP-compatible clients can call the following tools:

| Tool | Description |
|------|-------------|

| `rate_pokemon` | Rate a Pokémon by providing `name`, `nature`, and `subskills` directly. If the user provides a screenshot, the LLM reads it and passes the extracted data. Accepts an optional `level`. |
| `list_pokemon` | List all supported Pokémon, optionally filtered by `specialty` (Berries, Ingredients, or Skills). |
| `get_pokemon_info` | Get a Pokémon's specialty, base helping frequency, and estimated helps per day. |

## Self-Hosting Setup

For the free-hosted v1 path, deploy the Dockerized Flask service. Discord and the TypeScript Cloudflare Worker remain legacy/deferred paths and are not required for OCR hosting.

### Option A - Render Free Docker (recommended)

The Docker service handles web upload, Telegram webhook, and protected MCP from one free web service.

#### Prerequisites

- A Render account
- A Telegram bot token from @BotFather
- Local Tesseract OCR, installed by the Dockerfile

#### 1. Install Dependencies

```bash
docker build -t pokemon-sleep-rater .
```

#### 2. Configure Secrets

Set the following Render environment variables:

| Secret | Required for |
|--------|-------------|
| `TELEGRAM_BOT_TOKEN` | Telegram |
| `TELEGRAM_WEBHOOK_SECRET` | Secret path segment for Telegram webhook |
| `MCP_TOKEN` | Bearer token required by `/mcp` |

Render can generate `TELEGRAM_WEBHOOK_SECRET` and `MCP_TOKEN` from `render.yaml`.

#### 3. Deploy

```bash
gunicorn webapp:app --bind 0.0.0.0:$PORT
```

Render can deploy the Dockerfile directly from the repository.

#### 4. Create a Discord Application

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications) and click **New Application**.
2. Under the **General Information** tab, copy the **Application ID** and **Public Key**.
   - Set `DISCORD_APPLICATION_ID` and `DISCORD_PUBLIC_KEY` as Cloudflare secrets (see step 2 above).
3. Under **OAuth2 → URL Generator**, select the **bot** and **applications.commands** scopes, add the **Send Messages** and **Attach Files** bot permissions, then open the generated URL to invite the bot to your server.

#### 5. Register the `/rateps` Slash Command

The Cloudflare Worker uses Discord's Interactions endpoint (no gateway), so the slash command must be registered with Discord. This is handled **automatically** by the GitHub Actions workflow at `.github/workflows/register-discord-commands.yml`, which runs whenever `worker/src/discord.ts` or `worker/scripts/register-commands.mjs` changes on `master`, or can be triggered manually via **workflow_dispatch**.

The workflow requires two GitHub repository secrets in addition to those listed in step 2:

| Secret | Description |
|--------|-------------|
| `DISCORD_APPLICATION_ID` | Your Discord application / client ID |
| `DISCORD_BOT_TOKEN` | Bot token from the Discord Developer Portal |

To register commands **manually** from your local machine:

```bash
cd worker
DISCORD_APPLICATION_ID=<YOUR_APPLICATION_ID> DISCORD_BOT_TOKEN=<YOUR_BOT_TOKEN> npm run register-commands
```

> The script uses a bulk `PUT` (idempotent) against the Discord HTTP API. Global commands appear within an hour; re-running the script at any time is safe.

#### 6. Set Up Webhooks

- **Discord:** In the [Discord Developer Portal](https://discord.com/developers/applications), go to your application → **General Information** → set the **Interactions Endpoint URL** to `https://<worker-url>/discord`. Discord will send a verification ping; the worker must respond correctly for the URL to be saved.
- **Telegram:** Register the webhook with `https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://<worker-url>/telegram/webhook`.

#### Worker Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/` or `/health` | Health check |
| `POST` | `/discord` | Discord Interactions webhook |
| `POST` | `/telegram/webhook` | Telegram Bot webhook |
| `POST` | `/mcp` | MCP JSON-RPC 2.0 server |

### Option B — Python Bots (standalone)

Run the Discord and/or Telegram bots as long-running processes.

#### Prerequisites

- Python 3.11+
- A Discord bot token and/or a Telegram bot token

#### 1. Clone and Install Dependencies

```bash
git clone https://github.com/carnat/Pokemon-Sleep-Rater.git
cd Pokemon-Sleep-Rater
pip install -r requirements.txt
```

#### 2. Configure Environment Variables

Create a `.env` file in the project root with the following variables:

```env
# Discord bot token (required to run the Discord bot)
BOT_TOKEN=your_discord_bot_token

# Telegram bot token (required to run the Telegram bot)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
```

#### 3. Discord Bot Setup

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications) and click **New Application**.
2. Under the **Bot** tab, click **Reset Token** to generate a token and copy it. Paste it as `BOT_TOKEN` in your `.env` file.
3. Under **OAuth2 → URL Generator**, select the **bot** and **applications.commands** scopes and the **Send Messages** and **Attach Files** bot permissions. Copy the generated URL and open it in your browser to invite the bot to your server.
4. Start the Discord bot:

```bash
python bot.py
```

> The bot uses [py-cord](https://docs.pycord.dev/) which automatically registers the `/rateps` slash command with Discord when it connects. No manual command registration is needed—just invite the bot and start it.

#### 4. Telegram Bot Setup

1. Open Telegram and search for [@BotFather](https://t.me/BotFather).
2. Send `/newbot` and follow the prompts to choose a name and username for your bot.
3. BotFather will provide a bot token. Paste it as `TELEGRAM_BOT_TOKEN` in your `.env` file.
4. Start the Telegram bot:

```bash
python telegram_bot.py
```

## Scoring

Scores for the subskills are credited to u/drake8thecake's spreadsheet. Each Pokémon is graded differently according to their specialty.

<p align="center">
  <img src="https://i.imgur.com/ZLEUsjJ.png">
</p>

Scores for the nature are an aggregation calculated by SaintPebble from three different sources including u/PigsInTrees, u/drake8thecake, and the Discord [Sleep Mathcord](https://discord.gg/mphzREMkwe).

### Frequency-Weighted Scoring
Speed-sensitive subskills (**Helping Speed S/M** and **Berry Finding S**) are weighted by the Pokémon's base helping frequency. Faster Pokémon (lower base frequency) benefit more from these subskills, making the rating more accurate across different Pokémon speeds.

### Level-Aware Subskills
If you provide your Pokémon's current level, subskills that have not yet been unlocked at that level are excluded from the score and shown as 🔒 in the output. Subskill unlock levels follow the in-game layout: Lv. 10, 25, 50, 75, 100.

### All-Specialty Display
Scores for all three specialties (Berries, Ingredients, Skills) are shown side by side, with the Pokémon's primary specialty highlighted. This lets you quickly see how the Pokémon compares across all roles.

### Production Estimate
An approximate **helps per day** figure is shown based on the Pokémon's base helping frequency at ~80% efficiency (approximating a Lv. 30–50 Pokémon with typical camp bonuses).

### Production-Based Recommendation
The Python runtime also calculates a production score and cautious recommendation:

- **Keep** - strong role fit or high expected production.
- **Consider** - usable, but compare against your current team and goals.
- **Release** - weak investment unless it is shiny, a favorite, or fills a niche.

The first implementation uses reviewed JSON snapshots in `data/sleep/` as the source of truth. Species-specific production rates are seeded with conservative role defaults where reviewed rates are not yet available; update them through reviewed snapshot diffs rather than live scraping.

### Data Updates
Run the non-mutating validator before merging curated data updates:

```bash
python scripts/validate_sleep_data.py
```

To review a proposed snapshot without editing checked-in files:

```bash
python scripts/validate_sleep_data.py --species path/to/species.json --scoring path/to/scoring.json
```

The validator checks schema integrity, reports added/removed/changed Pokemon, and keeps data updates reviewable.

### Python MCP Endpoint
The Flask app exposes `POST /mcp` for calculator-only MCP clients. It accepts structured fields such as name, nature, subskills, level, energy, main skill level, and favored berry. Screenshots should be parsed by the client/assistant before calling MCP.

### Grading Scale
The bot combines all raw scores and rates the Pokémon using the following scale:

S: 24+

A: 21 — 23

B: 18 — 20

C: 15 — 17

D: > 11 — 14

F: 11 and under

The scale accounts for the varying min/max values of the three specialties: Berries: ~4 — 28, Ingredients 11 — 24, and Skills 10.5 — 26. A Pokémon's specialty is the first value to be considered then rated in the proper category. All emojis used in the bot's final evaluation belong to their respective creators.

### Supported Pokémon
The bot covers Pokémon from **Generation 1 through 6** as they appear in Pokémon Sleep.

The grading scale as well as the values of each subskill and nature are subjective. Opinions, suggestions, or changes are welcome—whether regarding the bot or the code @ alfendi on Discord.

# Change Log
- v1.0 Released (9/9/23)
- v1.1 Update (9/14/23)
- v1.2 Update
  - Added frequency-weighted scoring for speed-sensitive subskills
  - Added optional `level` parameter for level-aware subskill scoring
  - Expanded Pokémon database to Generation 6
  - Added all-specialty score display
  - Added production estimate (helps per day)
  - Added Telegram bot support
- v1.3 Update
  - Migrated to Cloudflare Worker (TypeScript) for serverless deployment
  - Added MCP (Model Context Protocol) server with four tools
  - Unified Discord and Telegram behind a single HTTP worker
  - Added GitHub Actions CI/CD for automatic worker deployment
