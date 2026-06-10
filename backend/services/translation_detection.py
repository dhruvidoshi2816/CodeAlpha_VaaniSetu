"""
translation_detection.py — Multi-signal language detection for VaaniSetu.

Signals (merged with confidence scoring):
  1. Romanized Indian phrase dictionaries (Latin script)
  2. Unicode script ranges (native Indic / CJK / etc.)
  3. langdetect probability distribution
  4. Google auto-detect (optional tie-breaker for ambiguous Latin text)

Public entry: detect_language_full(text, get_language_info) → dict
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable

logger = logging.getLogger(__name__)

LANGDETECT_MAP = {
    "zh-cn": "zh-CN", "zh-tw": "zh-TW", "zh": "zh-CN",
    "iw": "he", "he": "he", "nb": "no", "nn": "no",
    "mr": "mr", "hi": "hi", "gu": "gu",
}

# Devanagari used by Hindi, Marathi, Nepali — disambiguate with langdetect when possible
_DEVANAGARI_LANGS = ("hi", "mr", "ne", "sa", "bho", "mai")


@dataclass
class DetectionCandidate:
    code: str
    confidence: float
    source: str


def is_latin_text(text: str) -> bool:
    if not text:
        return False
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return False
    latin = sum(1 for c in letters if ord(c) < 128)
    return latin / len(letters) > 0.8


def detect_by_script(text: str) -> str:
    """Map dominant Unicode script to ISO language code."""
    counts: dict[str, int] = {}
    for ch in text:
        cp = ord(ch)
        if 0x0900 <= cp <= 0x097F:
            counts["hi"] = counts.get("hi", 0) + 1
        elif 0x0A80 <= cp <= 0x0AFF:
            counts["gu"] = counts.get("gu", 0) + 1
        elif 0x0A00 <= cp <= 0x0A7F:
            counts["pa"] = counts.get("pa", 0) + 1
        elif 0x0B80 <= cp <= 0x0BFF:
            counts["ta"] = counts.get("ta", 0) + 1
        elif 0x0C00 <= cp <= 0x0C7F:
            counts["te"] = counts.get("te", 0) + 1
        elif 0x0C80 <= cp <= 0x0CFF:
            counts["kn"] = counts.get("kn", 0) + 1
        elif 0x0D00 <= cp <= 0x0D7F:
            counts["ml"] = counts.get("ml", 0) + 1
        elif 0x0980 <= cp <= 0x09FF:
            counts["bn"] = counts.get("bn", 0) + 1
        elif 0x0B00 <= cp <= 0x0B7F:
            counts["or"] = counts.get("or", 0) + 1
        elif 0x0600 <= cp <= 0x06FF or 0xFB50 <= cp <= 0xFDFF or 0xFE70 <= cp <= 0xFEFF:
            counts["ur"] = counts.get("ur", 0) + 1
        elif 0x4E00 <= cp <= 0x9FFF:
            counts["zh-CN"] = counts.get("zh-CN", 0) + 1
        elif 0x3040 <= cp <= 0x30FF:
            counts["ja"] = counts.get("ja", 0) + 1
        elif 0xAC00 <= cp <= 0xD7AF:
            counts["ko"] = counts.get("ko", 0) + 1
        elif 0x0400 <= cp <= 0x04FF:
            counts["ru"] = counts.get("ru", 0) + 1
        elif 0x0370 <= cp <= 0x03FF:
            counts["el"] = counts.get("el", 0) + 1
        elif 0x0E00 <= cp <= 0x0E7F:
            counts["th"] = counts.get("th", 0) + 1
        elif 0x1780 <= cp <= 0x17FF:
            counts["km"] = counts.get("km", 0) + 1

    if not counts:
        return "en"
    return max(counts, key=counts.get)


def detect_with_langdetect(text: str, registry: dict) -> list[DetectionCandidate]:
    """Return ranked candidates from langdetect probabilities."""
    try:
        from langdetect import DetectorFactory, detect_langs
        DetectorFactory.seed = 0
        probs = detect_langs(text)
    except Exception as exc:
        logger.debug("langdetect failed: %s", exc)
        return []

    candidates: list[DetectionCandidate] = []
    for item in probs[:3]:
        raw = item.lang.lower()
        code = LANGDETECT_MAP.get(raw, raw)
        if code not in registry and code.replace("-", "") not in registry:
            continue
        candidates.append(
            DetectionCandidate(
                code=code,
                confidence=min(0.92, float(item.prob) * 0.95),
                source="langdetect",
            )
        )
    return candidates


def refine_devanagari(text: str, script_guess: str, registry: dict) -> str:
    """Disambiguate Hindi vs Marathi when script is Devanagari."""
    if script_guess not in _DEVANAGARI_LANGS:
        return script_guess
    langs = detect_with_langdetect(text, registry)
    for c in langs:
        if c.code in _DEVANAGARI_LANGS:
            return c.code
    return script_guess


def merge_candidates(candidates: list[DetectionCandidate]) -> DetectionCandidate | None:
    """Pick best detection using weighted votes."""
    if not candidates:
        return None

    scores: dict[str, float] = {}
    sources: dict[str, str] = {}
    for c in candidates:
        weight = {
            "romanized": 1.25,
            "script": 1.0,
            "langdetect": 0.75,
            "google": 0.95,
            "default": 0.5,
        }.get(c.source, 0.8)
        scores[c.code] = scores.get(c.code, 0.0) + c.confidence * weight
        if c.code not in sources or c.confidence > 0.7:
            sources[c.code] = c.source

    if not scores:
        return None

    best_code = max(scores, key=scores.get)
    raw_score = scores[best_code]
    # Normalize to 0–0.99
    confidence = min(0.99, max(0.45, raw_score / max(len(candidates), 1)))
    return DetectionCandidate(best_code, round(confidence, 2), sources.get(best_code, "merged"))


def detect_language_full(
    text: str,
    get_language_info: Callable[[str], dict],
    language_registry: dict,
) -> dict:
    """
    Full detection pipeline. Returns same shape as translator.detect_language().
    """
    if not text or not text.strip():
        return {**get_language_info("en"), "confidence": 0.0}

    text = text.strip()
    candidates: list[DetectionCandidate] = []

    # --- Romanized Latin-script (Indian, Japanese, Korean, Chinese, etc.) ---
    if is_latin_text(text):
        try:
            from services.romanized_router import detect_any_romanized
            romanized = detect_any_romanized(text)
            if romanized:
                candidates.append(
                    DetectionCandidate(
                        romanized["code"],
                        float(romanized.get("confidence", 0.75)),
                        "romanized",
                    )
                )
        except Exception as exc:
            logger.warning("Romanized router error: %s", exc)

        # --- Google detect early for short Latin text ---
        if len(text.split()) <= 8:
            try:
                from services.translation_providers import detect_language_google
                g_code, g_conf = detect_language_google(text)
                if g_code:
                    mapped = LANGDETECT_MAP.get(g_code.lower(), g_code.lower())
                    if mapped in language_registry:
                        candidates.append(
                            DetectionCandidate(mapped, g_conf, "google")
                        )
            except Exception as exc:
                logger.debug("Google detection skip: %s", exc)

    # --- Native script ---
    if any(ord(c) > 127 for c in text):
        script_code = detect_by_script(text)
        if script_code in ("hi", "mr", "ne"):
            script_code = refine_devanagari(text, script_code, language_registry)
        word_count = len(text.split())
        script_conf = min(0.94, 0.72 + word_count * 0.012)
        candidates.append(
            DetectionCandidate(script_code, script_conf, "script")
        )

    # --- langdetect for Latin / mixed ---
    if is_latin_text(text) or not candidates:
        for ld in detect_with_langdetect(text, language_registry):
            candidates.append(ld)

    # --- Google tie-break when still ambiguous Latin ---
    if is_latin_text(text) and len(candidates) < 2:
        try:
            from services.translation_providers import detect_language_google
            g_code, g_conf = detect_language_google(text)
            if g_code and g_code in language_registry:
                mapped = LANGDETECT_MAP.get(g_code.lower(), g_code.lower())
                if mapped in language_registry:
                    candidates.append(
                        DetectionCandidate(mapped, g_conf, "google")
                    )
        except Exception as exc:
            logger.debug("Google detection skip: %s", exc)

    merged = merge_candidates(candidates)
    if merged:
        # Preserve strong romanized confidence when it wins (avoid dilution by langdetect)
        romanized_best = next(
            (
                c for c in candidates
                if c.source == "romanized" and c.code == merged.code
            ),
            None,
        )
        final_confidence = merged.confidence
        if romanized_best and romanized_best.confidence > final_confidence:
            final_confidence = romanized_best.confidence

        info = get_language_info(merged.code)
        result = {**info, "confidence": final_confidence}
        if merged.source == "romanized" or romanized_best:
            result["romanized"] = True
        return result

    # Short ASCII → English default
    word_count = len(text.split())
    confidence = min(0.75, 0.50 + word_count * 0.02)
    return {**get_language_info("en"), "confidence": round(confidence, 2)}
