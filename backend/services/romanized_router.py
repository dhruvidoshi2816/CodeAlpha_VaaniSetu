"""
romanized_router.py — Unified entry point for all romanized Latin-script detection
and normalization (Indian, Japanese, Korean, Chinese, Arabic, etc.).
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

# All language codes that may use Latin input requiring normalization
ROMANIZED_LATIN_CODES = frozenset({
    "gu", "hi", "mr", "bn", "pa", "ta", "te", "kn", "ml", "ur", "or", "ne", "sa",
    "ja", "ko", "zh-CN", "zh-TW", "ar", "th", "vi", "tr",
    "fr", "de", "es", "it", "ru", "pt",
})


def detect_any_romanized(text: str) -> dict | None:
    """
    Run all romanized detectors and return the highest-scoring match.
    Order does not matter — best score wins.
    """
    candidates: list[dict] = []

    for module, func_name in (
        ("services.romanized_detector", "detect_romanized_language"),
        ("services.romanized_romaji", "detect_romanized_japanese"),
        ("services.romanized_global", "detect_romanized_global"),
    ):
        try:
            import importlib
            mod = importlib.import_module(module)
            fn = getattr(mod, func_name)
            result = fn(text)
            if result:
                candidates.append(result)
        except Exception as exc:
            logger.warning("%s failed: %s", func_name, exc)

    if not candidates:
        return None

    def sort_key(r: dict) -> float:
        return float(r.get("score", r.get("confidence", 0) * 12))

    best = max(candidates, key=sort_key)
    logger.debug(
        "Best romanized match for %r: %s (candidates=%d)",
        text[:40], best["code"], len(candidates),
    )
    return best


def normalize_romanized_text(text: str, lang_code: str) -> str:
    """Route normalization to the correct language module."""
    if not text or not lang_code:
        return text

    if lang_code == "ja":
        from services.romanized_romaji import normalize_romaji_text
        return normalize_romaji_text(text)

    if lang_code in ("gu", "hi", "mr", "bn", "pa", "ta", "te", "kn", "ml", "ur", "or", "ne", "sa"):
        from services.romanized_detector import normalize_romanized_text
        return normalize_romanized_text(text, lang_code)

    from services.romanized_global import normalize_global_text
    return normalize_global_text(text, lang_code)
