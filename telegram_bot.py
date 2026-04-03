import logging
import os

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from ocr import detect_text_uri
from pokemon import RatePokemon
from pokemon_db import db

load_dotenv()
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Welcome to Pokémon Sleep Rater! 🌙\n\n"
        "Send a photo of your Pokémon with the caption /rateps to get a rating.\n"
        "You can also include your Pokémon's level after the command:\n"
        "  /rateps 35\n\n"
        "The screenshot must show the Pokémon's name, nature, and subskills."
    )


async def rateps(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /rateps command sent as a photo caption or as a reply to a photo."""
    message = update.message

    # Determine the photo and optional level argument.
    photo = None
    level = None

    if message.photo:
        photo = message.photo[-1]  # highest resolution
    elif message.reply_to_message and message.reply_to_message.photo:
        photo = message.reply_to_message.photo[-1]

    # context.args is populated by CommandHandler; when arriving via a
    # MessageHandler (photo caption), parse the level from the caption instead.
    raw_args = context.args
    if not raw_args and message.caption:
        parts = message.caption.split()
        raw_args = parts[1:] if len(parts) > 1 else []

    if raw_args:
        try:
            level = int(raw_args[0])
        except ValueError:
            await message.reply_text("Level must be a number, e.g. /rateps 35")
            return

    if not photo:
        await message.reply_text(
            "Please send a Pokémon screenshot as a photo with the caption /rateps."
        )
        return

    # Resolve a public URL for the photo so Google Vision can fetch it.
    photo_file = await photo.get_file()
    image_url = photo_file.file_path

    try:
        ocr_results = detect_text_uri(image_url)
        if not ocr_results:
            await message.reply_text(
                "Could not read the image. Please check the screenshot and try again."
            )
            return

        result = RatePokemon().rate_pokemon(ocr_results, pokemon_level=level)
        if not result:
            await message.reply_text(
                "Pokémon not found. Please check the image (name, nature, and subskills must be visible)."
            )
            return

        name = result['name']
        final_grade = result['final_grade']
        skills_value = result['skills_value']
        locked_skills = result['locked_skills']
        nature = result['nature']
        nature_rating = result['nature_rating']
        grade = result['grade']
        percentile = result['percentile']
        all_scores = result['all_scores']
        helps_per_day = result['helps_per_day']
        specialty = result['specialty']

        level_note = f" (Lv. {level})" if level else ""
        top_pct = 100 - percentile

        lines = [
            f"*Pokémon Evaluation*",
            f"Your {name}{level_note} is rated {final_grade}",
            "",
            "*Subskills*",
            db.subskills_to_string(skills_value, locked_skills),
            "",
            f"*Nature*: {nature}: {nature_rating}",
            "",
            f"*Total Score ({specialty})*: {grade}  •  Top {top_pct}% for {specialty}",
            "",
            "*All Specialty Scores*",
        ]

        for spec, data in all_scores.items():
            marker = "★" if spec == specialty else "  "
            lines.append(f"{marker} {spec}: *{data['grade']}* (top {100 - data['percentile']}%)")

        if helps_per_day:
            lines += ["", f"*Est. Production*: ~{helps_per_day} helps/day"]

        await message.reply_text("\n".join(lines), parse_mode="Markdown")

    except Exception as e:
        logger.error("Error processing /rateps: %s", e, exc_info=True)
        await message.reply_text(
            "Pokémon not found. Please check the image upload (name, nature, and subskills) or try again."
        )


def main() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN environment variable is not set.")

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("rateps", rateps))
    # Also handle photos sent with the caption /rateps (with optional level arg)
    app.add_handler(MessageHandler(filters.PHOTO & filters.CaptionRegex(r"^/rateps"), rateps))

    logger.info("Telegram bot starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
