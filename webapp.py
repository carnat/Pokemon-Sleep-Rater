"""Flask web application for Pokémon Sleep Rater.

Provides a simple web interface for uploading screenshots and getting ratings.
Uses the same OCR + rating pipeline as the Discord/Telegram bots.
"""

import logging
import os
import asyncio
import time
import uuid

from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
from telegram import Update

from mcp_server import handle_json_rpc
from ocr_local import detect_text_local
from pokemon import RatePokemon
from pokemon_db import db
from telegram_bot import build_application

load_dotenv()
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload


@app.route('/')
def index():
    """Serve the upload form."""
    return render_template('index.html')


@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({'status': 'ok'})


def _metadata_log(request_id, platform, status, started_at, pokemon_name=None, error_category=None):
    logger.info(
        "request_id=%s platform=%s status=%s duration_ms=%s pokemon=%s error=%s",
        request_id,
        platform,
        status,
        int((time.monotonic() - started_at) * 1000),
        pokemon_name or "",
        error_category or "",
    )


def _optional_int(name):
    value = request.form.get(name, '').strip()
    if not value:
        return None
    return int(value)


def _optional_bool(name):
    value = request.form.get(name, '').strip().lower()
    if not value:
        return None
    return value in {'1', 'true', 'yes', 'on'}


@app.route('/rate', methods=['POST'])
def rate():
    """Accept an image upload and return the Pokémon rating as JSON.

    Expects a multipart form with:
      - image: the screenshot file
      - level (optional): integer Pokémon level
    """
    request_id = uuid.uuid4().hex
    started_at = time.monotonic()

    if 'image' not in request.files:
        _metadata_log(request_id, 'web', 'error', started_at, error_category='missing_image')
        return jsonify({'error': 'No image file provided'}), 400

    file = request.files['image']
    if file.filename == '':
        _metadata_log(request_id, 'web', 'error', started_at, error_category='empty_filename')
        return jsonify({'error': 'No file selected'}), 400

    # Read image bytes
    image_bytes = file.read()
    if not image_bytes:
        _metadata_log(request_id, 'web', 'error', started_at, error_category='empty_file')
        return jsonify({'error': 'Empty file'}), 400

    # Parse optional level
    try:
        level = _optional_int('level')
        main_skill_level = _optional_int('main_skill_level')
        energy = _optional_int('energy')
    except ValueError:
        _metadata_log(request_id, 'web', 'error', started_at, error_category='invalid_number')
        return jsonify({'error': 'Level, main skill level, and energy must be numbers'}), 400

    good_camp = bool(_optional_bool('good_camp'))
    favored_berry = _optional_bool('favored_berry')
    area = request.form.get('area', '').strip() or None
    ingredient_spread = [
        item.strip()
        for item in request.form.get('ingredient_spread', '').split(',')
        if item.strip()
    ] or None

    # Run OCR
    ocr_results = detect_text_local(image_bytes, source='bytes')
    if not ocr_results:
        _metadata_log(request_id, 'web', 'error', started_at, error_category='ocr_failed')
        return jsonify({'error': 'Could not read the image. Please use a clear screenshot showing the Pokemon name, nature, and subskills.'}), 422

    # Rate the Pokémon
    result = RatePokemon().rate_pokemon(
        ocr_results,
        pokemon_level=level,
        ingredient_spread=ingredient_spread,
        main_skill_level=main_skill_level,
        energy=energy,
        good_camp=good_camp,
        area=area,
        favored_berry=favored_berry,
    )
    if not result:
        _metadata_log(request_id, 'web', 'error', started_at, error_category='pokemon_not_found')
        return jsonify({
            'error': 'Pokémon not found. Please check the image (name, nature, and subskills must be visible).',
        }), 422

    # Format response
    response_data = {
        'name': result['name'],
        'specialty': result['specialty'],
        'nature': result['nature'],
        'nature_rating': result['nature_rating'],
        'grade': result['grade'],
        'final_grade_text': _strip_discord_emojis(result['final_grade']),
        'percentile': result['percentile'],
        'skills': result['skills_value'],
        'locked_skills': list(result['locked_skills']),
        'all_scores': result['all_scores'],
        'helps_per_day': result['helps_per_day'],
        'production_score': result['production_score'],
        'production_breakdown': result['production_breakdown'],
        'recommendation': result['recommendation'],
        'recommendation_score': result['recommendation_score'],
        'recommendation_reasons': result['recommendation_reasons'],
        'assumptions_used': result['assumptions_used'],
        'data_version': result['data_version'],
    }

    _metadata_log(request_id, 'web', 'ok', started_at, pokemon_name=result['name'])
    return jsonify(response_data)


@app.route('/mcp', methods=['POST'])
def mcp():
    """Expose the shared calculator as a JSON-RPC MCP-style endpoint."""
    token = os.getenv("MCP_TOKEN")
    if not token:
        return jsonify({'jsonrpc': '2.0', 'id': None, 'error': {'code': -32002, 'message': 'MCP token is not configured'}}), 503
    auth_header = request.headers.get("Authorization", "")
    if auth_header != f"Bearer {token}":
        return jsonify({'jsonrpc': '2.0', 'id': None, 'error': {'code': -32001, 'message': 'Unauthorized'}}), 401

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({'jsonrpc': '2.0', 'id': None, 'error': {'code': -32700, 'message': 'Parse error'}}), 400
    response = handle_json_rpc(payload)
    if response is None:
        return '', 202
    return jsonify(response)


async def _process_telegram_update(payload):
    tg_app = build_application()
    await tg_app.initialize()
    try:
        update = Update.de_json(payload, tg_app.bot)
        await tg_app.process_update(update)
    finally:
        await tg_app.shutdown()


@app.route('/telegram/webhook/<secret>', methods=['POST'])
def telegram_webhook(secret):
    """Receive Telegram webhook updates without storing screenshots."""
    expected = os.getenv("TELEGRAM_WEBHOOK_SECRET")
    if not expected or secret != expected:
        return jsonify({'error': 'not found'}), 404

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({'error': 'bad request'}), 400

    asyncio.run(_process_telegram_update(payload))
    return jsonify({'ok': True})


def _strip_discord_emojis(text):
    """Remove Discord custom emoji markup from grade text."""
    import re
    # Remove <:name:id> and <a:name:id> patterns
    text = re.sub(r'<a?:[^:]+:\d+>', '', text)
    # Remove ** bold markers
    text = text.replace('**', '')
    return text.strip()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=os.getenv('FLASK_DEBUG', 'false').lower() == 'true')
