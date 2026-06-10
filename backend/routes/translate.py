"""
routes/translate.py — Translation API endpoints for VaaniSetu.

Improvements:
- /detect now returns full language info (name, native script, confidence)
- /translate validates input length
- /languages returns native script display names
- Proper error classification (ValueError → 400, RuntimeError → 502, else → 500)
"""

from flask import Blueprint, request, jsonify
from services.translator import translate_text, get_languages, detect_language
from models.history import save_translation

translate_bp = Blueprint("translate", __name__)

MAX_TEXT_LENGTH = 10_000


@translate_bp.route("/languages", methods=["GET"])
def languages():
    return jsonify({"languages": get_languages()})


@translate_bp.route("/detect", methods=["POST"])
def detect():
    data = request.get_json() or {}
    text = data.get("text", "").strip()
    if not text:
        return jsonify({"error": "Text is required"}), 400
    try:
        info = detect_language(text)
        return jsonify(info)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@translate_bp.route("/translate", methods=["POST"])
def translate():
    data = request.get_json() or {}
    text = data.get("text", "").strip()
    source_lang = data.get("source_lang", "auto")
    target_lang = data.get("target_lang", "en")
    tone = data.get("tone", "professional")
    save_history = data.get("save_history", False)

    if not text:
        return jsonify({"error": "Text is required"}), 400

    if len(text) > MAX_TEXT_LENGTH:
        return jsonify({"error": f"Text exceeds maximum length of {MAX_TEXT_LENGTH} characters"}), 400

    if not target_lang or target_lang == "auto":
        return jsonify({"error": "A valid target language is required"}), 400

    try:
        result = translate_text(text, source_lang, target_lang, tone)

        if save_history:
            save_translation({
                "original_text": text,
                "translated_text": result["translated_text"],
                "source_lang": result["detected_lang"],
                "target_lang": target_lang,
                "tone": tone,
                "confidence": result["confidence"],
            })

        return jsonify(result)

    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 502
    except Exception as exc:
        return jsonify({"error": "Translation service error", "detail": str(exc)}), 500
