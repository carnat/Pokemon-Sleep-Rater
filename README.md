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

Both share the same scoring data, grading logic, and Google Cloud Vision OCR integration.

## How to Use

### Discord
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
The Cloudflare Worker exposes an MCP endpoint at `POST /mcp` that speaks JSON-RPC 2.0. AI assistants and other MCP-compatible clients can call the following tools:

| Tool | Description |
|------|-------------|
| `rate_pokemon` | Rate a Pokémon by providing `name`, `nature`, and `subskills` directly. If the user provides a screenshot, the LLM reads it and passes the extracted data. Accepts an optional `level`. |
| `list_pokemon` | List all supported Pokémon, optionally filtered by `specialty` (Berries, Ingredients, or Skills). |
| `get_pokemon_info` | Get a Pokémon's specialty, base helping frequency, and estimated helps per day. |

## Self-Hosting Setup

### Option A — Cloudflare Worker (recommended)

The worker handles Discord, Telegram, and MCP from a single deployment.

#### Prerequisites

- Node.js 22+
- A [Cloudflare](https://dash.cloudflare.com/) account
- A [Google Cloud Vision API](https://cloud.google.com/vision/docs/setup) key (used for OCR)
- A Discord application and/or a Telegram bot token

#### 1. Install Dependencies

```bash
cd worker
npm ci
```

#### 2. Configure Secrets

Add the following secrets to your Cloudflare Worker (via the dashboard or `wrangler secret put`):

| Secret | Required for |
|--------|-------------|
| `DISCORD_PUBLIC_KEY` | Discord — Ed25519 signature verification |
| `DISCORD_APPLICATION_ID` | Discord — follow-up messages |
| `TELEGRAM_BOT_TOKEN` | Telegram |
| `GOOGLE_CLOUD_API_KEY` | OCR (all platforms) |

> `DISCORD_BOT_TOKEN` is used only for slash command registration (step 5) and should be added as a **GitHub repository secret**, not a Cloudflare secret.

#### 3. Deploy

```bash
npx wrangler deploy
```

The worker auto-deploys on push to `master` (when files in `worker/` change) via the GitHub Actions workflow.

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
- A [Google Cloud Vision API](https://cloud.google.com/vision/docs/setup) service account with credentials (used for OCR)
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

# Links
- SaintPebble's spreadsheet: [Link](https://docs.google.com/spreadsheets/d/1HSEzTWlboKHFOV7piqsk82E1Wapa9J-dQmOOdY8RNJY/edit?usp=sharing)
- /u/drake8thecake's spreadsheet: [Link](https://www.reddit.com/r/PokemonSleep/comments/167tiuz/updated_pokemon_sleep_data_and_tier_list_incl/?rdt=39154)
- /u/PigsInTrees's infographic: [Link](https://www.reddit.com/r/PokemonSleep/comments/15wkab7/pigs_made_a_nature_infograph/)
- Discord Bot Invite: [Link](https://discord.com/oauth2/authorize?client_id=1148461688690069628&permissions=412317240384&scope=bot)

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
