"""Flask web application for Pokémon Sleep Rater.

Provides a simple web interface for uploading screenshots and getting ratings.
Uses the same OCR + rating pipeline as the Discord/Telegram bots.
"""

import logging
import os

from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv

from ocr_local import detect_text_local
from pokemon import RatePokemon
from pokemon_db import db

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


@app.route('/rate', methods=['POST'])
def rate():
    """Accept an image upload and return the Pokémon rating as JSON.

    Expects a multipart form with:
      - image: the screenshot file
      - level (optional): integer Pokémon level
    """
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    # Read image bytes
    image_bytes = file.read()
    if not image_bytes:
        return jsonify({'error': 'Empty file'}), 400

    # Parse optional level
    level = None
    level_str = request.form.get('level', '').strip()
    if level_str:
        try:
            level = int(level_str)
        except ValueError:
            return jsonify({'error': 'Level must be a number'}), 400

    # Run OCR
    ocr_results = detect_text_local(image_bytes, source='bytes')
    if not ocr_results:
        return jsonify({'error': 'Could not read the image. Please check the screenshot and try again.'}), 422

    # Rate the Pokémon
    result = RatePokemon().rate_pokemon(ocr_results, pokemon_level=level)
    if not result:
        return jsonify({
            'error': 'Pokémon not found. Please check the image (name, nature, and subskills must be visible).',
            'ocr_raw': ocr_results,
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
    }

    return jsonify(response_data)


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
