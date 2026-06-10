"""
routes/slang.py — Gen-Z slang translation endpoints.

Improvements:
- Input length validation
- Proper error classification
- save_history uses historyApi pattern (POST to /history/)
"""

from flask import Blueprint, request, jsonify
from services.slang_service import translate_slang, get_slang_modes, get_glossary
from models.history import save_translation

slang_bp = Blueprint("slang", __name__)

MAX_SLANG_LENGTH = 2_000


@slang_bp.route("/modes", methods=["GET"])
def modes():
    return jsonify({"modes": get_slang_modes()})


@slang_bp.route("/glossary", methods=["GET"])
def glossary():
    limit = request.args.get("limit", 60, type=int)
    limit = min(limit, 300)  # cap to prevent abuse
    return jsonify({"glossary": get_glossary(limit)})


@slang_bp.route("/translate", methods=["POST"])
def translate():
    data = request.get_json() or {}
    text = data.get("text", "").strip()
    mode = data.get("mode", "genz_to_plain")
    use_ai = data.get("use_ai", True)
    save_history = data.get("save_history", False)

    if not text:
        return jsonify({"error": "Text is required"}), 400

    if len(text) > MAX_SLANG_LENGTH:
        return jsonify({"error": f"Text exceeds maximum length of {MAX_SLANG_LENGTH} characters"}), 400

    try:
        result = translate_slang(text, mode, use_ai)

        if save_history and result.get("translated_text"):
            save_translation({
                "original_text": text,
                "translated_text": result["translated_text"],
                "source_lang": "genz" if mode == "genz_to_plain" else "plain",
                "target_lang": "plain" if mode == "genz_to_plain" else "genz",
                "tone": mode,
                "confidence": result["confidence"],
            })

        return jsonify(result)

    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        return jsonify({"error": f"Slang translation failed: {exc}"}), 500
