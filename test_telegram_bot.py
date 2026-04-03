"""Tests for the Telegram bot integration (telegram_bot.py).

All external dependencies (Telegram API, OCR, RatePokemon) are mocked so
the tests run without network access or real credentials.
"""

import sys
from unittest.mock import MagicMock

# Stub out Google Cloud and database modules that are not available in the
# test environment, before any production code is imported.
for _mod in (
    "google",
    "google.cloud",
    "google.cloud.vision",
    "google.cloud.sql",
    "google.cloud.sql.connector",
    "google.auth",
    "google.api_core",
    "pg8000",
    "sqlalchemy",
):
    sys.modules.setdefault(_mod, MagicMock())

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_message(text="", photo=None, reply_to_message=None):
    """Build a minimal mock telegram.Message."""
    msg = MagicMock()
    msg.text = text
    msg.photo = photo or []
    msg.reply_to_message = reply_to_message
    msg.reply_text = AsyncMock()
    return msg


def _make_update(message):
    update = MagicMock()
    update.message = message
    return update


def _make_context(args=None):
    ctx = MagicMock()
    ctx.args = args or []
    return ctx


def _make_photo_file(url="https://api.telegram.org/file/bot-token/photo.jpg"):
    pf = AsyncMock()
    pf.file_path = url
    return pf


def _make_photo(url="https://api.telegram.org/file/bot-token/photo.jpg"):
    photo = MagicMock()
    photo.get_file = AsyncMock(return_value=_make_photo_file(url))
    return photo


def _good_result(name="Spheal", specialty="Berries", level=None):
    """Return a plausible rate_pokemon result dict."""
    return {
        'name': name,
        'final_grade': '**B**! <a:squirtlevibe:1150206216451137586>',
        'skills_value': {
            'Energy Recovery Bonus': 3,
            'Inventory Up S': 2,
            'Helping Speed M': 4,
            'Inventory Up L': 4,
            'Skill Trigger S': 3,
        },
        'locked_skills': set(),
        'nature': 'Impish',
        'nature_rating': '1.5',
        'grade': '17.5',
        'percentile': 45,
        'all_scores': {
            'Berries': {'grade': 17.5, 'percentile': 45},
            'Ingredients': {'grade': 13.0, 'percentile': 20},
            'Skills': {'grade': 14.0, 'percentile': 25},
        },
        'helps_per_day': 24,
        'specialty': specialty,
    }


# ---------------------------------------------------------------------------
# Tests for /start
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_start_replies_with_welcome():
    from telegram_bot import start

    msg = _make_message()
    update = _make_update(msg)
    ctx = _make_context()

    await start(update, ctx)

    msg.reply_text.assert_awaited_once()
    reply_text = msg.reply_text.call_args[0][0]
    assert "Welcome" in reply_text
    assert "/rateps" in reply_text


# ---------------------------------------------------------------------------
# Tests for /rateps — no photo supplied
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_rateps_no_photo_returns_error():
    from telegram_bot import rateps

    msg = _make_message(photo=[], reply_to_message=None)
    update = _make_update(msg)
    ctx = _make_context()

    await rateps(update, ctx)

    msg.reply_text.assert_awaited_once()
    text = msg.reply_text.call_args[0][0]
    assert "screenshot" in text.lower() or "photo" in text.lower()


# ---------------------------------------------------------------------------
# Tests for /rateps — invalid level argument
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_rateps_invalid_level_returns_error():
    from telegram_bot import rateps

    photo = _make_photo()
    msg = _make_message(photo=[photo])
    update = _make_update(msg)
    ctx = _make_context(args=["notanumber"])

    await rateps(update, ctx)

    msg.reply_text.assert_awaited_once()
    text = msg.reply_text.call_args[0][0]
    assert "number" in text.lower()


# ---------------------------------------------------------------------------
# Tests for /rateps — OCR returns nothing
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@patch("telegram_bot.detect_text_uri", return_value=None)
async def test_rateps_ocr_failure(mock_ocr):
    from telegram_bot import rateps

    photo = _make_photo()
    msg = _make_message(photo=[photo])
    update = _make_update(msg)
    ctx = _make_context()

    await rateps(update, ctx)

    mock_ocr.assert_called_once()
    msg.reply_text.assert_awaited_once()
    text = msg.reply_text.call_args[0][0]
    assert "read" in text.lower() or "image" in text.lower()


# ---------------------------------------------------------------------------
# Tests for /rateps — Pokémon not recognised
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@patch("telegram_bot.RatePokemon")
@patch("telegram_bot.detect_text_uri", return_value=["Pikachu", "Impish", "Helping Bonus"])
async def test_rateps_pokemon_not_found(mock_ocr, MockRatePokemon):
    mock_instance = MockRatePokemon.return_value
    mock_instance.rate_pokemon.return_value = False

    from telegram_bot import rateps

    photo = _make_photo()
    msg = _make_message(photo=[photo])
    update = _make_update(msg)
    ctx = _make_context()

    await rateps(update, ctx)

    msg.reply_text.assert_awaited_once()
    text = msg.reply_text.call_args[0][0]
    assert "not found" in text.lower()


# ---------------------------------------------------------------------------
# Tests for /rateps — successful rating without level
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@patch("telegram_bot.RatePokemon")
@patch("telegram_bot.detect_text_uri")
async def test_rateps_success_no_level(mock_ocr, MockRatePokemon):
    mock_ocr.return_value = ["Spheal", "Impish", "Energy Recovery Bonus",
                             "Inventory Up S", "Helping Speed M", "Inventory Up L", "Skill Trigger S"]
    mock_instance = MockRatePokemon.return_value
    mock_instance.rate_pokemon.return_value = _good_result()

    from telegram_bot import rateps

    photo = _make_photo()
    msg = _make_message(photo=[photo])
    update = _make_update(msg)
    ctx = _make_context()

    await rateps(update, ctx)

    mock_instance.rate_pokemon.assert_called_once_with(mock_ocr.return_value, pokemon_level=None)
    msg.reply_text.assert_awaited_once()
    text = msg.reply_text.call_args[0][0]
    assert "Spheal" in text
    assert "Impish" in text
    assert "Berries" in text


# ---------------------------------------------------------------------------
# Tests for /rateps — successful rating with level
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@patch("telegram_bot.RatePokemon")
@patch("telegram_bot.detect_text_uri")
async def test_rateps_success_with_level(mock_ocr, MockRatePokemon):
    mock_ocr.return_value = ["Spheal", "Impish", "Energy Recovery Bonus",
                             "Inventory Up S", "Helping Speed M", "Inventory Up L", "Skill Trigger S"]
    result = _good_result()
    result['locked_skills'] = {'Skill Trigger S'}
    result['skills_value']['Skill Trigger S'] = 0
    mock_instance = MockRatePokemon.return_value
    mock_instance.rate_pokemon.return_value = result

    from telegram_bot import rateps

    photo = _make_photo()
    msg = _make_message(photo=[photo])
    update = _make_update(msg)
    ctx = _make_context(args=["35"])

    await rateps(update, ctx)

    mock_instance.rate_pokemon.assert_called_once_with(mock_ocr.return_value, pokemon_level=35)
    msg.reply_text.assert_awaited_once()
    text = msg.reply_text.call_args[0][0]
    assert "Lv. 35" in text
    assert "not yet unlocked" in text
    assert "🔒" in text


# ---------------------------------------------------------------------------
# Tests for /rateps — photo sent with caption (MessageHandler path)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@patch("telegram_bot.RatePokemon")
@patch("telegram_bot.detect_text_uri")
async def test_rateps_photo_with_caption(mock_ocr, MockRatePokemon):
    """Bot should also work when the photo is sent with a /rateps caption."""
    mock_ocr.return_value = ["Pikachu", "Jolly", "Berry Finding S",
                             "Helping Speed M", "Helping Bonus"]
    mock_instance = MockRatePokemon.return_value
    mock_instance.rate_pokemon.return_value = _good_result(name="Pikachu")

    from telegram_bot import rateps

    photo = _make_photo()
    msg = _make_message(photo=[photo])
    update = _make_update(msg)
    ctx = _make_context()

    await rateps(update, ctx)

    msg.reply_text.assert_awaited_once()
    text = msg.reply_text.call_args[0][0]
    assert "Pikachu" in text


# ---------------------------------------------------------------------------
# Tests for /rateps — photo in reply-to message
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@patch("telegram_bot.RatePokemon")
@patch("telegram_bot.detect_text_uri")
async def test_rateps_uses_reply_photo(mock_ocr, MockRatePokemon):
    """When no photo attached, bot should fall back to the replied-to message's photo."""
    mock_ocr.return_value = ["Gengar", "Modest", "Ingredient Finder M"]
    mock_instance = MockRatePokemon.return_value
    mock_instance.rate_pokemon.return_value = _good_result(name="Gengar", specialty="Ingredients")

    from telegram_bot import rateps

    reply_photo = _make_photo()
    reply_msg = MagicMock()
    reply_msg.photo = [reply_photo]

    msg = _make_message(photo=[], reply_to_message=reply_msg)
    update = _make_update(msg)
    ctx = _make_context()

    await rateps(update, ctx)

    msg.reply_text.assert_awaited_once()
    text = msg.reply_text.call_args[0][0]
    assert "Gengar" in text


# ---------------------------------------------------------------------------
# Tests for /rateps — unexpected exception
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@patch("telegram_bot.detect_text_uri", side_effect=RuntimeError("network error"))
async def test_rateps_unexpected_exception(mock_ocr):
    from telegram_bot import rateps

    photo = _make_photo()
    msg = _make_message(photo=[photo])
    update = _make_update(msg)
    ctx = _make_context()

    await rateps(update, ctx)

    msg.reply_text.assert_awaited_once()
    text = msg.reply_text.call_args[0][0]
    assert "not found" in text.lower() or "try again" in text.lower()


# ---------------------------------------------------------------------------
# Tests for /rateps — all-specialty display in response
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@patch("telegram_bot.RatePokemon")
@patch("telegram_bot.detect_text_uri")
async def test_rateps_all_specialty_scores_displayed(mock_ocr, MockRatePokemon):
    mock_ocr.return_value = ["Chansey", "Calm", "Skill Trigger M"]
    mock_instance = MockRatePokemon.return_value
    mock_instance.rate_pokemon.return_value = _good_result(name="Chansey", specialty="Skills")

    from telegram_bot import rateps

    photo = _make_photo()
    msg = _make_message(photo=[photo])
    update = _make_update(msg)
    ctx = _make_context()

    await rateps(update, ctx)

    text = msg.reply_text.call_args[0][0]
    assert "Berries" in text
    assert "Ingredients" in text
    assert "Skills" in text
    assert "★" in text  # primary specialty marker


# ---------------------------------------------------------------------------
# Tests for /rateps — production estimate displayed
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@patch("telegram_bot.RatePokemon")
@patch("telegram_bot.detect_text_uri")
async def test_rateps_helps_per_day_displayed(mock_ocr, MockRatePokemon):
    mock_ocr.return_value = ["Spheal", "Impish"]
    mock_instance = MockRatePokemon.return_value
    mock_instance.rate_pokemon.return_value = _good_result()

    from telegram_bot import rateps

    photo = _make_photo()
    msg = _make_message(photo=[photo])
    update = _make_update(msg)
    ctx = _make_context()

    await rateps(update, ctx)

    text = msg.reply_text.call_args[0][0]
    assert "helps/day" in text


# ---------------------------------------------------------------------------
# Tests for /rateps — no production estimate when helps_per_day is None
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@patch("telegram_bot.RatePokemon")
@patch("telegram_bot.detect_text_uri")
async def test_rateps_no_helps_per_day_not_shown(mock_ocr, MockRatePokemon):
    mock_ocr.return_value = ["UnknownMon", "Hardy"]
    result = _good_result()
    result['helps_per_day'] = None
    mock_instance = MockRatePokemon.return_value
    mock_instance.rate_pokemon.return_value = result

    from telegram_bot import rateps

    photo = _make_photo()
    msg = _make_message(photo=[photo])
    update = _make_update(msg)
    ctx = _make_context()

    await rateps(update, ctx)

    text = msg.reply_text.call_args[0][0]
    assert "helps/day" not in text
