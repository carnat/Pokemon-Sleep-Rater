"""Local OCR using Tesseract — free alternative to Google Cloud Vision.

This module provides the same interface as ocr.py (returns a list of text
strings) but uses pytesseract for text detection. It crops specific regions
from a standardized Pokémon Sleep screenshot to improve accuracy, then uses
fuzzy matching against known Pokémon names, natures, and subskills.

System requirement: tesseract-ocr must be installed (apt install tesseract-ocr).
"""

import re
import difflib
import logging
from io import BytesIO

import requests
from PIL import Image, ImageFilter, ImageOps

import pytesseract

from pokemon import RatePokemon

logger = logging.getLogger(__name__)

# Known valid values for fuzzy matching
_POKEMON_NAMES = list(RatePokemon.pokemon.keys())
_NATURES = list(RatePokemon.natures.keys())
_SUBSKILLS = list(RatePokemon.subskills.keys())

# Standard resolution the game screenshots are normalized to
_STANDARD_SIZE = (1080, 2400)

# Crop regions (left, upper, right, lower) on a 1080×2400 canvas
_CROP_NAME = (311, 226, 596, 297)
_CROP_NATURE = (135, 1559, 449, 1622)
_CROP_SKILLS = [
    (92, 820, 500, 888),    # Skill 1 (Lv.10)
    (585, 819, 989, 882),   # Skill 2 (Lv.50)
    (93, 990, 497, 1053),   # Skill 3 (Lv.100)
    (582, 989, 984, 1054),  # Skill 4 (Lv.25)
    (99, 1158, 501, 1223),  # Skill 5 (Lv.75)
]


def _preprocess(img, upscale=2):
    """Preprocess a cropped image region for better OCR accuracy.

    Steps: upscale, convert to grayscale, sharpen, binarize.
    """
    # Upscale small crops for better character recognition
    if upscale > 1:
        img = img.resize((img.width * upscale, img.height * upscale), Image.LANCZOS)

    # Convert to grayscale
    img = ImageOps.grayscale(img)

    # Sharpen to enhance edges
    img = img.filter(ImageFilter.SHARPEN)

    # Binarize with a threshold (works well for game UI text)
    img = img.point(lambda x: 255 if x > 140 else 0, '1')

    return img


def _ocr_single_line(img):
    """Run Tesseract in single-line mode on a preprocessed image."""
    processed = _preprocess(img)
    text = pytesseract.image_to_string(processed, config='--psm 7').strip()
    # Remove common OCR artifacts
    text = re.sub(r'[|_\[\]{}]', '', text)
    return text


def _ocr_block(img):
    """Run Tesseract in block mode on a preprocessed image."""
    processed = _preprocess(img)
    text = pytesseract.image_to_string(processed, config='--psm 6').strip()
    text = re.sub(r'[|_\[\]{}]', '', text)
    return text


def _fuzzy_match(text, candidates, cutoff=0.6):
    """Find the closest match from candidates using fuzzy matching.

    Returns the best match or the original text if no match found.
    """
    if not text:
        return text
    # Try exact match first (case-insensitive)
    for candidate in candidates:
        if candidate.lower() == text.lower():
            return candidate
    # Fuzzy match
    matches = difflib.get_close_matches(text, candidates, n=1, cutoff=cutoff)
    if matches:
        return matches[0]
    return text


def _load_image_from_url(url):
    """Download an image from a URL and return a PIL Image.

    Only allows HTTPS URLs to trusted hosts (Telegram API, Discord CDN)
    to prevent SSRF attacks.
    """
    from urllib.parse import urlparse
    parsed = urlparse(url)

    # Only allow HTTPS
    if parsed.scheme != 'https':
        raise ValueError("Only HTTPS URLs are allowed")

    # Allowlist of trusted hosts for image downloads
    allowed_hosts = (
        'api.telegram.org',
        'cdn.discordapp.com',
        'media.discordapp.net',
    )
    if not any(parsed.hostname == host or (parsed.hostname and parsed.hostname.endswith('.' + host))
               for host in allowed_hosts):
        raise ValueError(f"Host not allowed: {parsed.hostname}")

    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return Image.open(BytesIO(response.content))


def _load_image_from_bytes(image_bytes):
    """Load a PIL Image from raw bytes."""
    return Image.open(BytesIO(image_bytes))


def detect_text_local(image, source='url'):
    """Perform OCR on a Pokémon Sleep screenshot using Tesseract.

    Args:
        image: Either a URL string (source='url'), raw bytes (source='bytes'),
               or a PIL Image (source='pil').
        source: One of 'url', 'bytes', or 'pil'.

    Returns:
        A list of strings (same format as ocr.detect_text_uri) containing
        the Pokémon name, nature, and subskills detected from the image.
        Returns None if OCR fails completely.
    """
    try:
        if source == 'url':
            img = _load_image_from_url(image)
        elif source == 'bytes':
            img = _load_image_from_bytes(image)
        elif source == 'pil':
            img = image
        else:
            raise ValueError(f"Unknown source type: {source}")

        # Resize to standard resolution
        img_resized = img.resize(_STANDARD_SIZE, Image.LANCZOS)

        results = []

        # OCR the name region
        name_img = img_resized.crop(_CROP_NAME)
        raw_name = _ocr_single_line(name_img)
        # Strip "Lv. X" prefix if present (same as original ocr.py)
        raw_name = re.sub(r'.*?L[vV]\. ?\d+ ?', '', raw_name).strip()
        matched_name = _fuzzy_match(raw_name, _POKEMON_NAMES, cutoff=0.5)
        results.append(matched_name)

        # OCR the nature region
        nature_img = img_resized.crop(_CROP_NATURE)
        raw_nature = _ocr_single_line(nature_img)
        # Nature text often has extra words like "Nature: Bold" — extract the nature word
        nature_words = raw_nature.split()
        matched_nature = None
        for word in nature_words:
            clean_word = re.sub(r'[^a-zA-Z]', '', word)
            match = _fuzzy_match(clean_word, _NATURES, cutoff=0.6)
            if match in _NATURES:
                matched_nature = match
                break
        if matched_nature:
            results.append(matched_nature)

        # OCR each subskill region
        for crop_box in _CROP_SKILLS:
            skill_img = img_resized.crop(crop_box)
            raw_skill = _ocr_single_line(skill_img)
            # Strip "Lv. X" prefix
            raw_skill = re.sub(r'.*?L[vV]\. ?\d+ ?', '', raw_skill).strip()
            if raw_skill:
                matched_skill = _fuzzy_match(raw_skill, _SUBSKILLS, cutoff=0.5)
                results.append(matched_skill)

        if not results:
            return None

        return results

    except Exception as e:
        logger.error("Local OCR failed: %s", e, exc_info=True)
        return None


def detect_text_uri_local(uri):
    """Drop-in replacement for ocr.detect_text_uri using local Tesseract.

    Args:
        uri: Public URL of the image to analyse.

    Returns:
        List of text strings extracted from the image, or None on failure.
    """
    return detect_text_local(uri, source='url')
