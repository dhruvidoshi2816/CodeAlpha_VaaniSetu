"""
routes/ai.py — AI-powered grammar and summarisation endpoints.
"""

from flask import Blueprint, request, jsonify
from services.ai_service import correct_grammar, summarize_text
from services.translator import translate_text

ai_bp = Blueprint("ai", __name__)

MAX_TEXT_LENGTH = 10_000


@ai_bp.route("/grammar", methods=["POST"])
def grammar():
    data = request.get_json() or {}
    text = data.get("text", "").strip()
    if not text:
        return jsonify({"error": "Text is required"}), 400
    if len(text) > MAX_TEXT_LENGTH:
        return jsonify({"error": "Text too long"}), 400
    try:
        result = correct_grammar(text)
        return jsonify(result)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@ai_bp.route("/summarize-translate", methods=["POST"])
def summarize_translate():
    data = request.get_json() or {}
    text = data.get("text", "").strip()
    target_lang = data.get("target_lang", "en")
    source_lang = data.get("source_lang", "auto")

    if not text:
        return jsonify({"error": "Text is required"}), 400
    if len(text) > MAX_TEXT_LENGTH:
        return jsonify({"error": "Text too long"}), 400

    try:
        summary_result = summarize_text(text)
        summary = summary_result["summary"]
        translation = translate_text(summary, source_lang, target_lang)
        return jsonify({
            "summary": summary,
            "translated_text": translation["translated_text"],
            "detected_lang": translation["detected_lang"],
            "detected_lang_info": translation.get("detected_lang_info", {}),
            "confidence": translation["confidence"],
            "used_ai": summary_result.get("used_ai", False),
        })
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500
