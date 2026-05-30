import logging
import os
from io import BytesIO

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from ocr_local import detect_text_local
from pokemon import RatePokemon
from pokemon_db import db

load_dotenv()
logger = logging.getLogger(__name__)

def _detect_text(image_bytes):
    """Run local Tesseract OCR from in-memory image bytes."""
    return detect_text_local(image_bytes, source='bytes')


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

    photo_file = await photo.get_file()

    try:
        image_buffer = BytesIO()
        await photo_file.download_to_memory(out=image_buffer)
        ocr_results = _detect_text(image_buffer.getvalue())
        if not ocr_results:
            await message.reply_text(
                "Could not read the image. Please use a clear screenshot showing the Pokemon name, nature, and subskills."
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
        production_score = result.get('production_score')
        recommendation = result.get('recommendation')
        recommendation_reasons = result.get('recommendation_reasons', [])
        data_version = result.get('data_version')

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

        if production_score is not None:
            lines += ["", f"*Production Score*: {production_score}/100"]

        if recommendation:
            lines += ["", f"*Recommendation*: {recommendation}"]
            lines.extend(f"- {reason}" for reason in recommendation_reasons[:3])

        if data_version:
            lines += ["", f"_Data: {data_version}_"]

        await message.reply_text("\n".join(lines), parse_mode="Markdown")

    except Exception as e:
        logger.error("Error processing /rateps: %s", type(e).__name__, exc_info=True)
        await message.reply_text(
            "Pokémon not found. Please check the image upload (name, nature, and subskills) or try again."
        )

def build_application(token=None):
    token = token or os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN environment variable is not set.")

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("rateps", rateps))
    app.add_handler(MessageHandler(filters.PHOTO & filters.CaptionRegex(r"^/rateps"), rateps))
    app.add_handler(MessageHandler(filters.PHOTO & ~filters.CAPTION, rateps))
    return app


def main() -> None:
    app = build_application()

    logger.info("Telegram bot starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
