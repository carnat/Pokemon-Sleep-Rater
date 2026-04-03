# Pokémon Sleep Rater
A multi-platform bot (Discord + Telegram) that rates Pokémon from Pokémon Sleep! Upload a screenshot containing the Pokémon's name (no nicknames), nature, and subskills. The bot may fail if a screenshot is unclear or if too many requests are made at once.

<p align="center">Example Output:</p>

<p align="center">
  <img src="https://i.imgur.com/dSDM6rh.png">
</p>

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

## Self-Hosting Setup

### Prerequisites

- Python 3.11+
- A [Google Cloud Vision API](https://cloud.google.com/vision/docs/setup) service account with credentials (used for OCR)
- A Discord bot token and/or a Telegram bot token

### 1. Clone and Install Dependencies

```bash
git clone https://github.com/carnat/Pokemon-Sleep-Rater.git
cd Pokemon-Sleep-Rater
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the project root with the following variables:

```env
# Discord bot token (required to run the Discord bot)
BOT_TOKEN=your_discord_bot_token

# Telegram bot token (required to run the Telegram bot)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
```

### 3. Discord Bot Setup

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications) and click **New Application**.
2. Under the **Bot** tab, copy the bot token (click **Reset Token** if the token is no longer visible). Paste it as `BOT_TOKEN` in your `.env` file.
3. Under **OAuth2 → URL Generator**, select the **bot** scope and the permissions your bot needs (Send Messages, Attach Files, Use Slash Commands). Copy the generated URL and open it in your browser to invite the bot to your server.
4. Start the Discord bot:

```bash
python bot.py
```

### 4. Telegram Bot Setup

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
