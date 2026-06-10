"""
routes/ocr.py — OCR extraction and image translation endpoints.
"""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from services.ocr_service import extract_text_from_image, ocr_lang_to_iso
from services.translator import translate_text

ocr_bp = Blueprint("ocr", __name__)

MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_MIME_PREFIXES = ("image/",)
ALLOWED_IMAGE_EXTENSIONS = frozenset({
    "png", "jpg", "jpeg", "webp", "gif", "bmp", "tif", "tiff", "heic", "heif",
})


def _file_extension(filename: str) -> str:
    if not filename or "." not in filename:
        return ""
    return filename.rsplit(".", 1)[-1].lower()


def _validate_image(file):
    """Return error string or None if valid."""
    if not file or not file.filename:
        return "No file selected"

    content_type = (file.content_type or "").lower()
    ext = _file_extension(file.filename)

    mime_ok = any(content_type.startswith(p) for p in ALLOWED_MIME_PREFIXES)
    ext_ok = ext in ALLOWED_IMAGE_EXTENSIONS

    if not mime_ok and not ext_ok:
        return (
            f"Unsupported file type: {content_type or ext}. "
            "Please upload PNG, JPG, WEBP, GIF, or BMP."
        )

    file.stream.seek(0, 2)
    size = file.stream.tell()
    file.stream.seek(0)
    if size > MAX_IMAGE_SIZE:
        return f"Image too large ({size // 1024} KB). Maximum is 10 MB."
    if size == 0:
        return "Uploaded file is empty."
    return None


def _ocr_kwargs() -> dict:
    """OCR language kwargs — only use explicit `lang` if the client sent it."""
    lang = request.form.get("lang")
    return {
        "lang": lang if lang else None,
        "source_lang": request.form.get("source_lang", "auto"),
    }


@ocr_bp.route("/extract", methods=["POST"])
def extract():
    if "image" not in request.files:
        return jsonify({"error": "Image file is required"}), 400

    file = request.files["image"]
    err = _validate_image(file)
    if err:
        return jsonify({"error": err}), 400

    try:
        result = extract_text_from_image(file, **_ocr_kwargs())
        if not result.get("extracted_text"):
            return jsonify({
                "error": "No text found in image. Try a clearer photo or set the image language.",
                "extracted_text": "",
                "confidence": result.get("confidence", 0.0),
                "ocr_lang": result.get("ocr_lang"),
            }), 400
        return jsonify(result)
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 503
    except Exception as exc:
        return jsonify({"error": f"OCR failed: {exc}"}), 500


@ocr_bp.route("/translate-image", methods=["POST"])
def translate_image():
    if "image" not in request.files:
        return jsonify({"error": "Image file is required"}), 400

    file = request.files["image"]
    err = _validate_image(file)
    if err:
        return jsonify({"error": err}), 400

    target_lang = request.form.get("target_lang", "en")
    source_lang = request.form.get("source_lang", "auto")

    if not target_lang or target_lang == "auto":
        return jsonify({"error": "A valid target language is required"}), 400

    try:
        ocr_result = extract_text_from_image(file, **_ocr_kwargs())
        text = ocr_result.get("extracted_text", "").strip()

        if not text:
            return jsonify({
                "error": (
                    "No text found in image. Try a clearer image, better lighting, "
                    "or select the correct image language."
                ),
                "extracted_text": "",
                "ocr_lang": ocr_result.get("ocr_lang"),
            }), 400

        # Use OCR-detected script when translation source is auto
        effective_source = source_lang
        if source_lang == "auto":
            iso_from_ocr = ocr_lang_to_iso(ocr_result.get("ocr_lang", ""))
            if iso_from_ocr:
                effective_source = iso_from_ocr

        translation = translate_text(text, effective_source, target_lang)

        return jsonify({
            "extracted_text": text,
            "translated_text": translation["translated_text"],
            "detected_lang": translation["detected_lang"],
            "detected_lang_info": translation.get("detected_lang_info", {}),
            "ocr_confidence": ocr_result["confidence"],
            "translation_confidence": translation["confidence"],
            "provider": translation.get("provider", "unknown"),
            "ocr_lang": ocr_result.get("ocr_lang"),
        })

    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 503
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        return jsonify({"error": f"Image translation failed: {exc}"}), 500
