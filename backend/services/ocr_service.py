"""
ocr_service.py — Tesseract OCR with script-aware language selection.

Fixes garbled Latin output on Gujarati/Hindi document photos by:
  1. Not defaulting to English when frontend omits `lang`
  2. Trying each Indic Tesseract pack separately and picking the best result
  3. Scoring output by native-script character ratio (rejects gibberish)
  4. Dual preprocessing paths for phone photos vs clean scans
"""

from __future__ import annotations

import logging
import os
import re

import pytesseract
from PIL import Image, ImageEnhance, ImageFilter, ImageOps, UnidentifiedImageError

from config import Config
from services.ocr_lang_map import (
    ISO_TO_TESSERACT,
    resolve_tesseract_lang,
)
from services.tessdata_manager import ensure_for_ocr, invalidate_lang_cache

logger = logging.getLogger(__name__)

if Config.TESSERACT_CMD:
    pytesseract.pytesseract.tesseract_cmd = Config.TESSERACT_CMD

# Indian + common languages tried when auto-detecting script
_INDIC_CANDIDATES = [
    "guj", "hin", "mar", "ben", "pan", "tam", "tel", "kan", "mal", "urd", "ori", "eng",
]

# PSM: full page auto, OSD auto, uniform block, single column, sparse
_PSM_MODES = (3, 1, 6, 4, 11)
_PSM_FAST = (3, 6)

# Fast auto-detect pass — common Indian document langs before full sweep
_AUTO_FAST_LANGS = ("guj", "hin", "mar", "ben", "eng")
_EARLY_EXIT_SCORE = 72.0

# Tesseract lang → dominant Unicode script key for scoring
_LANG_SCRIPT = {
    "guj": "gujarati",
    "hin": "devanagari",
    "mar": "devanagari",
    "ben": "bengali",
    "pan": "gurmukhi",
    "tam": "tamil",
    "tel": "telugu",
    "kan": "kannada",
    "mal": "malayalam",
    "urd": "arabic",
    "ori": "oriya",
    "eng": "latin",
}

# Human-readable install hints
_LANG_INSTALL_HINTS = {
    "guj": "Gujarati (guj)",
    "hin": "Hindi (hin)",
    "mar": "Marathi (mar)",
    "ben": "Bengali (ben)",
    "pan": "Punjabi (pan)",
    "tam": "Tamil (tam)",
    "tel": "Telugu (tel)",
    "kan": "Kannada (kan)",
    "mal": "Malayalam (mal)",
    "urd": "Urdu (urd)",
}

_INSTALLED_LANGS: set[str] | None = None


def _installed_tesseract_langs() -> set[str]:
    """Cache list of Tesseract language packs on this machine."""
    global _INSTALLED_LANGS
    if _INSTALLED_LANGS is not None:
        return _INSTALLED_LANGS
    try:
        langs = set(pytesseract.get_languages(config=""))
        # Windows builds may return empty when PREFIX is misconfigured; fall back to scan
        if not langs:
            from pathlib import Path

            prefix = Path(os.environ.get("TESSDATA_PREFIX", ""))
            if prefix.is_dir():
                langs = {p.stem for p in prefix.glob("*.traineddata")}
        _INSTALLED_LANGS = langs or {"eng"}
    except Exception as exc:
        logger.warning("Could not list Tesseract languages: %s", exc)
        _INSTALLED_LANGS = {"eng"}
    return _INSTALLED_LANGS


def _lang_is_installed(tess_lang: str) -> bool:
    parts = tess_lang.split("+")
    installed = _installed_tesseract_langs()
    return all(p in installed for p in parts)


def _missing_pack_error(source_lang: str | None) -> RuntimeError | None:
    """Return a clear error when the required Tesseract pack is not installed."""
    if not source_lang or source_lang == "auto":
        return None
    tess = ISO_TO_TESSERACT.get(source_lang.strip())
    if not tess or _lang_is_installed(tess):
        return None
    hint = _LANG_INSTALL_HINTS.get(tess, tess)
    return RuntimeError(
        f"{hint} OCR is not installed in Tesseract. "
        f"Re-run the Tesseract installer (https://github.com/UB-Mannheim/tesseract/wiki) "
        f"and select '{hint}', then restart the backend. "
        f"Installed packs: {', '.join(sorted(_installed_tesseract_langs())[:12])}…"
    )


def _reset_stream(file_storage) -> None:
    stream = getattr(file_storage, "stream", file_storage)
    if hasattr(stream, "seek"):
        stream.seek(0)


def _to_rgb(image: Image.Image) -> Image.Image:
    if image.mode in ("RGBA", "P", "LA"):
        background = Image.new("RGB", image.size, (255, 255, 255))
        if image.mode == "P":
            image = image.convert("RGBA")
        background.paste(
            image,
            mask=image.split()[-1] if image.mode in ("RGBA", "LA") else None,
        )
        return background
    if image.mode != "RGB":
        return image.convert("RGB")
    return image


def _upscale(image: Image.Image, min_long_side: int = 2000) -> Image.Image:
    w, h = image.size
    long_side = max(w, h)
    if long_side >= min_long_side:
        return image
    scale = min(4.0, min_long_side / long_side)
    return image.resize(
        (int(w * scale), int(h * scale)), Image.Resampling.LANCZOS,
    )


def _preprocess_photo(image: Image.Image) -> Image.Image:
    """
    Gentle pipeline for phone photos of documents (Gujarati/Hindi forms).
    Avoids aggressive binarization that destroys Indic script strokes.
    """
    image = _to_rgb(image)
    gray = ImageOps.grayscale(image)
    gray = _upscale(gray, min_long_side=2200)
    gray = ImageEnhance.Contrast(gray).enhance(1.6)
    gray = ImageEnhance.Brightness(gray).enhance(1.05)
    gray = ImageEnhance.Sharpness(gray).enhance(1.8)
    return gray


def _preprocess_scan(image: Image.Image) -> Image.Image:
    """Aggressive binarization for clean scans / screenshots."""
    image = _to_rgb(image)
    gray = ImageOps.grayscale(image)
    gray = _upscale(gray, min_long_side=1800)
    gray = ImageEnhance.Contrast(gray).enhance(2.0)
    gray = ImageEnhance.Sharpness(gray).enhance(1.5)
    gray = gray.filter(ImageFilter.MedianFilter(size=3))

    try:
        import cv2
        import numpy as np

        arr = np.array(gray)
        arr = cv2.fastNlMeansDenoising(arr, h=8)
        arr = cv2.adaptiveThreshold(
            arr, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 8,
        )
        return Image.fromarray(arr)
    except ImportError:
        return gray
    except Exception as exc:
        logger.debug("OpenCV scan preprocess skipped: %s", exc)
        return gray


def _script_counts(text: str) -> dict[str, int]:
    counts = {
        "gujarati": 0, "devanagari": 0, "bengali": 0, "gurmukhi": 0,
        "tamil": 0, "telugu": 0, "kannada": 0, "malayalam": 0,
        "arabic": 0, "latin": 0, "other": 0,
    }
    for ch in text:
        if ch.isspace() or not ch.isprintable():
            continue
        cp = ord(ch)
        if 0x0A80 <= cp <= 0x0AFF:
            counts["gujarati"] += 1
        elif 0x0900 <= cp <= 0x097F:
            counts["devanagari"] += 1
        elif 0x0980 <= cp <= 0x09FF:
            counts["bengali"] += 1
        elif 0x0A00 <= cp <= 0x0A7F:
            counts["gurmukhi"] += 1
        elif 0x0B80 <= cp <= 0x0BFF:
            counts["tamil"] += 1
        elif 0x0C00 <= cp <= 0x0C7F:
            counts["telugu"] += 1
        elif 0x0C80 <= cp <= 0x0CFF:
            counts["kannada"] += 1
        elif 0x0D00 <= cp <= 0x0D7F:
            counts["malayalam"] += 1
        elif 0x0600 <= cp <= 0x06FF:
            counts["arabic"] += 1
        elif cp < 128 and ch.isalpha():
            counts["latin"] += 1
        elif cp > 127:
            counts["other"] += 1
    return counts


def _quality_score(text: str, confidences: list[int], tess_lang: str) -> float:
    """
    Score OCR output — prefer native-script text over Latin gibberish.
    """
    text = text.strip()
    if not text or len(text) < 3:
        return 0.0

    avg_conf = (sum(confidences) / len(confidences)) if confidences else 25.0
    score = avg_conf

    counts = _script_counts(text)
    total = sum(counts.values()) or 1
    expected_script = _LANG_SCRIPT.get(tess_lang.split("+")[0], "latin")
    native = counts.get(expected_script, 0)
    native_ratio = native / total

    # Strong bonus for correct native script (Gujarati doc → Gujarati chars)
    if native_ratio >= 0.25:
        score += 45
    elif native_ratio >= 0.10:
        score += 25
    elif tess_lang != "eng" and total > 20 and native_ratio < 0.03:
        score -= 35  # Indic lang but no Indic chars = gibberish

    # Penalize symbol soup typical of wrong-language OCR
    junk = len(re.findall(r"[\[\]{}~|`<>@#$%^&*\\]", text))
    if junk > max(3, len(text) * 0.04):
        score -= 25

    # Penalize very short random Latin tokens on Indic attempts
    if tess_lang in _LANG_SCRIPT and tess_lang != "eng":
        latin_ratio = counts["latin"] / total
        if latin_ratio > 0.85 and native_ratio < 0.05:
            score -= 30

    return score


def _run_ocr(image: Image.Image, tess_lang: str, psm: int) -> tuple[str, list[int]]:
    config = f"--oem 3 --psm {psm}"
    data = pytesseract.image_to_data(
        image, lang=tess_lang, output_type=pytesseract.Output.DICT, config=config,
    )
    text = pytesseract.image_to_string(image, lang=tess_lang, config=config)
    confidences = [
        int(c) for c in data.get("conf", [])
        if str(c).lstrip("-").isdigit() and int(c) > 0
    ]
    return text.strip(), confidences


def _candidate_langs(tess_lang: str, source_lang: str | None) -> list[str]:
    """Build ordered list of Tesseract langs to try (installed packs only)."""
    installed = _installed_tesseract_langs()

    if tess_lang and tess_lang not in ("auto", ""):
        candidates = [tess_lang]
        if "+" not in tess_lang and tess_lang != "eng":
            candidates.append(f"{tess_lang}+eng")
    else:
        candidates = list(_INDIC_CANDIDATES)
        if source_lang and source_lang not in ("auto", ""):
            mapped = ISO_TO_TESSERACT.get(source_lang.strip())
            if mapped and mapped in candidates:
                candidates.remove(mapped)
                candidates.insert(0, mapped)

    # Keep only installed packs
    filtered = [l for l in candidates if _lang_is_installed(l)]
    if not filtered and "eng" in installed:
        filtered = ["eng"]
    return filtered


def _is_gibberish(text: str, tess_lang: str) -> bool:
    """True when OCR output looks like wrong-language Latin noise."""
    counts = _script_counts(text)
    total = sum(counts.values()) or 1
    expected = _LANG_SCRIPT.get(tess_lang.split("+")[0], "")
    if expected and expected != "latin":
        native_ratio = counts.get(expected, 0) / total
        if native_ratio >= 0.08:
            return False
        latin_ratio = counts["latin"] / total
        junk = len(re.findall(r"[\[\]{}~|`<>@#$%^&*\\]", text))
        if latin_ratio > 0.7 and junk >= 3 and len(text) > 30:
            return True
    return False


def _has_strong_native_text(text: str, tess_lang: str) -> bool:
    """True when OCR output clearly matches the expected script."""
    counts = _script_counts(text)
    total = sum(counts.values()) or 1
    primary = tess_lang.split("+")[0]
    expected = _LANG_SCRIPT.get(primary, "latin")
    if expected == "latin":
        return total >= 8
    return counts.get(expected, 0) / total >= 0.12


def _ocr_best(
    images: list[Image.Image],
    tess_lang: str,
    source_lang: str | None,
) -> tuple[str, float, str]:
    """Try multiple langs × PSM × preprocess variants; return best result."""
    is_auto = tess_lang in ("auto", "")
    all_langs = _candidate_langs(tess_lang, source_lang)

    phases: list[tuple[list[Image.Image], list[str], tuple[int, ...]]] = []
    if is_auto:
        fast_langs = [l for l in _AUTO_FAST_LANGS if l in all_langs]
        if fast_langs:
            phases.append((images[:1], fast_langs, _PSM_FAST))
        remaining = [l for l in all_langs if l not in fast_langs]
        if remaining:
            phases.append((images, remaining, _PSM_MODES))
        if not phases:
            phases.append((images, all_langs, _PSM_MODES))
    else:
        phases.append((images, all_langs, _PSM_MODES))

    best_text = ""
    best_conf = 0.0
    best_lang = tess_lang
    best_score = -1.0

    for phase_images, langs, psms in phases:
        for img in phase_images:
            for lang in langs:
                for psm in psms:
                    try:
                        text, confidences = _run_ocr(img, lang, psm)
                        if not text:
                            continue
                        q = _quality_score(text, confidences, lang)
                        avg = (sum(confidences) / len(confidences) / 100.0) if confidences else 0.5
                        avg = min(0.99, max(0.1, avg))

                        if q > best_score:
                            best_score = q
                            best_text = text
                            best_conf = round(avg, 2)
                            best_lang = lang
                            logger.debug(
                                "OCR candidate lang=%s psm=%d score=%.1f conf=%.2f chars=%d",
                                lang, psm, q, avg, len(text),
                            )
                            if (
                                best_score >= _EARLY_EXIT_SCORE
                                and _has_strong_native_text(best_text, best_lang)
                            ):
                                return best_text, best_conf, best_lang
                    except pytesseract.TesseractError as exc:
                        err = str(exc).lower()
                        if "language" in err or "traineddata" in err:
                            logger.warning("Missing Tesseract pack: %s", lang)
                            break
                    except Exception as exc:
                        logger.debug("OCR skip lang=%s psm=%d: %s", lang, psm, exc)

        if (
            best_score >= _EARLY_EXIT_SCORE
            and _has_strong_native_text(best_text, best_lang)
        ):
            break

    return best_text, best_conf, best_lang


def extract_text_from_image(
    file_storage,
    lang: str | None = None,
    source_lang: str | None = None,
) -> dict:
    """
    Extract text from an uploaded image using Tesseract OCR.

    Returns:
        {"extracted_text", "confidence", "ocr_lang", "detected_script"?}
    """
    _reset_stream(file_storage)
    tess_lang = resolve_tesseract_lang(explicit_lang=lang, source_lang=source_lang)

    # Auto-download missing language packs (guj, hin, …) on first use
    try:
        ensure_for_ocr(source_lang)
        invalidate_lang_cache()
    except Exception as exc:
        logger.warning("Tessdata auto-download failed: %s", exc)

    try:
        raw = Image.open(file_storage.stream)
        photo = _preprocess_photo(raw)
        scan = _preprocess_scan(raw)
        images = [photo, scan]
    except UnidentifiedImageError as exc:
        raise RuntimeError(
            "Could not read image file. Supported: PNG, JPG, WEBP, GIF, BMP."
        ) from exc
    except Exception as exc:
        logger.error("Image processing error: %s", exc)
        raise RuntimeError(f"Failed to process image: {exc}") from exc
    finally:
        _reset_stream(file_storage)

    try:
        extracted, avg_confidence, used_lang = _ocr_best(images, tess_lang, source_lang)

        if not extracted:
            installed = sorted(_installed_tesseract_langs())
            raise RuntimeError(
                "No text found in image. For Gujarati/Hindi documents, install the matching "
                f"Tesseract language pack. Installed: {', '.join(installed[:15])}"
            )

        if _is_gibberish(extracted, used_lang):
            raise RuntimeError(
                "OCR could not read this document accurately. "
                "Select the correct image language (e.g. Gujarati) and ensure the "
                "matching Tesseract language pack is installed. "
                "Tip: re-run the Tesseract installer and check 'Gujarati' / 'Hindi'."
            )

        counts = _script_counts(extracted)
        indic_installed = any(
            l in _installed_tesseract_langs()
            for l in _INDIC_CANDIDATES if l != "eng"
        )
        if (
            source_lang in (None, "auto")
            and not indic_installed
            and counts["gujarati"] + counts["devanagari"] == 0
            and len(extracted) > 40
        ):
            raise RuntimeError(
                "This looks like an Indian-language document but Indic OCR packs "
                "could not be loaded. Restart the backend and ensure the server has "
                "internet access so language packs can download on first use."
            )

        counts = _script_counts(extracted)
        dominant = max(counts, key=counts.get) if any(counts.values()) else "latin"

        logger.info(
            "OCR extracted %d chars lang=%s script=%s confidence=%.2f",
            len(extracted), used_lang, dominant, avg_confidence,
        )
        return {
            "extracted_text": extracted,
            "confidence": avg_confidence,
            "ocr_lang": used_lang,
            "detected_script": dominant,
        }
    except pytesseract.TesseractNotFoundError as exc:
        raise RuntimeError(
            "Tesseract OCR is not installed. Install from "
            "https://github.com/UB-Mannheim/tesseract/wiki and set TESSERACT_CMD in .env"
        ) from exc
    except RuntimeError:
        raise
    except Exception as exc:
        logger.error("Tesseract OCR error: %s", exc)
        raise RuntimeError(f"OCR processing failed: {exc}") from exc


def ocr_lang_to_iso(tess_lang: str) -> str | None:
    """Map winning Tesseract code back to app ISO code for translation."""
    primary = tess_lang.split("+")[0]
    reverse = {v: k for k, v in ISO_TO_TESSERACT.items() if v}
    return reverse.get(primary)
