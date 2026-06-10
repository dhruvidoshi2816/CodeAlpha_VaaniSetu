"""
routes/document.py — Document translation endpoint.
"""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from services.document_parser import extract_text_from_document
from services.document_service import translate_document_text
from models.history import save_translation

document_bp = Blueprint("document", __name__)

MAX_DOC_SIZE = 20 * 1024 * 1024  # 20 MB
ALLOWED_EXTENSIONS = {"txt", "pdf", "docx"}


def _validate_document(file):
    if not file or not file.filename:
        return "No file selected"
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        return f"Unsupported file type '.{ext}'. Supported: TXT, PDF, DOCX"
    file.stream.seek(0, 2)
    size = file.stream.tell()
    file.stream.seek(0)
    if size > MAX_DOC_SIZE:
        return f"File too large ({size // 1024} KB). Maximum is 20 MB."
    if size == 0:
        return "Uploaded file is empty."
    return None


@document_bp.route("/translate", methods=["POST"])
def translate_document():
    if "document" not in request.files:
        return jsonify({"error": "Document file is required"}), 400

    file = request.files["document"]
    err = _validate_document(file)
    if err:
        return jsonify({"error": err}), 400

    target_lang = request.form.get("target_lang", "en")
    source_lang = request.form.get("source_lang", "auto")
    save_history = request.form.get("save_history", "false").lower() == "true"

    if not target_lang or target_lang == "auto":
        return jsonify({"error": "A valid target language is required"}), 400

    try:
        text = extract_text_from_document(file, file.filename)
        if not text.strip():
            return jsonify({"error": "No text found in document"}), 400

        result = translate_document_text(text, source_lang, target_lang)

        if save_history:
            snippet = lambda s: s[:500] + ("…" if len(s) > 500 else "")
            save_translation({
                "original_text": snippet(text),
                "translated_text": snippet(result["translated_text"]),
                "source_lang": result["detected_lang"],
                "target_lang": target_lang,
                "confidence": result["confidence"],
            })

        response = {
            "original_text": text,
            "translated_text": result["translated_text"],
            "detected_lang": result["detected_lang"],
            "detected_lang_info": result.get("detected_lang_info", {}),
            "confidence": result["confidence"],
            "provider": result.get("provider", "unknown"),
            "filename": file.filename,
            "char_count": len(text),
        }
        if result.get("chunks", 1) > 1:
            response["chunks"] = result["chunks"]

        return jsonify(response)

    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        return jsonify({"error": f"Document translation failed: {exc}"}), 500
