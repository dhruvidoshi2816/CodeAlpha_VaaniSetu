"""
translator.py — Production translation service for VaaniSetu.

Architecture
------------
Public API (unchanged for routes / frontend):
  - get_languages()
  - get_language_info(code)
  - detect_language(text)
  - translate_text(text, source_lang, target_lang, tone)

Internal modules:
  - translation_detection  — script + langdetect + romanized fusion
  - translation_providers  — Google → LibreTranslate → MyMemory
  - romanized_detector     — Romanized Indian language handling

Pipeline
--------
Detection:  romanized → script → langdetect → Google (tie-break)
Translation: normalize Romanized Indic → Google → LibreTranslate → MyMemory → original
Resilience:  LRU cache, retries, timeouts, rate limits, structured logging
"""

from __future__ import annotations

import hashlib
import logging
import re
import unicodedata
from collections import OrderedDict

from config import Config
from services.translation_detection import detect_language_full, is_latin_text
from services.translation_providers import (
    is_valid_translation,
    translate_google_json,
    translate_google_scrape,
    translate_libre,
    translate_mymemory,
)
from services.romanized_router import ROMANIZED_LATIN_CODES, detect_any_romanized, normalize_romanized_text

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 100+ Language registry  {code: (english_name, native_script)}
# ---------------------------------------------------------------------------
LANGUAGE_REGISTRY = {
    "auto":  ("Auto Detect",            "Auto Detect"),
    # Indian
    "hi":    ("Hindi",                  "हिन्दी"),
    "gu":    ("Gujarati",               "ગુજરાતી"),
    "mr":    ("Marathi",                "मराठी"),
    "bn":    ("Bengali",                "বাংলা"),
    "pa":    ("Punjabi",                "ਪੰਜਾਬੀ"),
    "ta":    ("Tamil",                  "தமிழ்"),
    "te":    ("Telugu",                 "తెలుగు"),
    "kn":    ("Kannada",                "ಕನ್ನಡ"),
    "ml":    ("Malayalam",              "മലയാളം"),
    "ur":    ("Urdu",                   "اردو"),
    "or":    ("Odia",                   "ଓଡ଼ିଆ"),
    "as":    ("Assamese",               "অসমীয়া"),
    "ne":    ("Nepali",                 "नेपाली"),
    "si":    ("Sinhala",                "සිංහල"),
    "sd":    ("Sindhi",                 "سنڌي"),
    "ks":    ("Kashmiri",               "کٲشُر"),
    "sa":    ("Sanskrit",               "संस्कृतम्"),
    "mai":   ("Maithili",               "मैथिली"),
    "bho":   ("Bhojpuri",               "भोजपुरी"),
    "doi":   ("Dogri",                  "डोगरी"),
    "kok":   ("Konkani",                "कोंकणी"),
    "mni":   ("Manipuri",               "মৈতৈলোন্"),
    "sat":   ("Santali",                "ᱥᱟᱱᱛᱟᱲᱤ"),
    # European
    "en":    ("English",                "English"),
    "es":    ("Spanish",                "Español"),
    "fr":    ("French",                 "Français"),
    "de":    ("German",                 "Deutsch"),
    "it":    ("Italian",                "Italiano"),
    "pt":    ("Portuguese",             "Português"),
    "ru":    ("Russian",                "Русский"),
    "nl":    ("Dutch",                  "Nederlands"),
    "pl":    ("Polish",                 "Polski"),
    "sv":    ("Swedish",                "Svenska"),
    "da":    ("Danish",                 "Dansk"),
    "fi":    ("Finnish",                "Suomi"),
    "no":    ("Norwegian",              "Norsk"),
    "cs":    ("Czech",                  "Čeština"),
    "sk":    ("Slovak",                 "Slovenčina"),
    "sl":    ("Slovenian",              "Slovenščina"),
    "hr":    ("Croatian",               "Hrvatski"),
    "sr":    ("Serbian",                "Српски"),
    "bs":    ("Bosnian",                "Bosanski"),
    "bg":    ("Bulgarian",              "Български"),
    "ro":    ("Romanian",               "Română"),
    "hu":    ("Hungarian",              "Magyar"),
    "el":    ("Greek",                  "Ελληνικά"),
    "uk":    ("Ukrainian",              "Українська"),
    "lt":    ("Lithuanian",             "Lietuvių"),
    "lv":    ("Latvian",                "Latviešu"),
    "et":    ("Estonian",               "Eesti"),
    "is":    ("Icelandic",              "Íslenska"),
    "ga":    ("Irish",                  "Gaeilge"),
    "cy":    ("Welsh",                  "Cymraeg"),
    "eu":    ("Basque",                 "Euskara"),
    "ca":    ("Catalan",                "Català"),
    "gl":    ("Galician",               "Galego"),
    "sq":    ("Albanian",               "Shqip"),
    "mk":    ("Macedonian",             "Македонски"),
    "hy":    ("Armenian",               "Հայերեն"),
    "ka":    ("Georgian",               "ქართული"),
    "az":    ("Azerbaijani",            "Azərbaycan"),
    "kk":    ("Kazakh",                 "Қазақша"),
    "uz":    ("Uzbek",                  "O'zbek"),
    "tk":    ("Turkmen",                "Türkmen"),
    "ky":    ("Kyrgyz",                 "Кыргызча"),
    "tg":    ("Tajik",                  "Тоҷикӣ"),
    "mn":    ("Mongolian",              "Монгол"),
    "be":    ("Belarusian",             "Беларуская"),
    "mt":    ("Maltese",                "Malti"),
    "af":    ("Afrikaans",              "Afrikaans"),
    # Middle East
    "ar":    ("Arabic",                 "العربية"),
    "he":    ("Hebrew",                 "עברית"),
    "fa":    ("Persian",                "فارسی"),
    "ps":    ("Pashto",                 "پښتو"),
    "ku":    ("Kurdish",                "Kurdî"),
    "tr":    ("Turkish",                "Türkçe"),
    # East / SE Asia
    "zh-CN": ("Chinese (Simplified)",   "中文(简体)"),
    "zh-TW": ("Chinese (Traditional)", "中文(繁體)"),
    "ja":    ("Japanese",               "日本語"),
    "ko":    ("Korean",                 "한국어"),
    "th":    ("Thai",                   "ภาษาไทย"),
    "vi":    ("Vietnamese",             "Tiếng Việt"),
    "id":    ("Indonesian",             "Bahasa Indonesia"),
    "ms":    ("Malay",                  "Bahasa Melayu"),
    "tl":    ("Filipino",               "Filipino"),
    "my":    ("Burmese",                "မြန်မာဘာသာ"),
    "km":    ("Khmer",                  "ភាសាខ្មែរ"),
    "lo":    ("Lao",                    "ພາສາລາວ"),
    "jv":    ("Javanese",               "Basa Jawa"),
    "su":    ("Sundanese",              "Basa Sunda"),
    "ceb":   ("Cebuano",                "Cebuano"),
    "hmn":   ("Hmong",                  "Hmoob"),
    # African
    "sw":    ("Swahili",                "Kiswahili"),
    "am":    ("Amharic",                "አማርኛ"),
    "yo":    ("Yoruba",                 "Yorùbá"),
    "ig":    ("Igbo",                   "Igbo"),
    "ha":    ("Hausa",                  "Hausa"),
    "zu":    ("Zulu",                   "isiZulu"),
    "xh":    ("Xhosa",                  "isiXhosa"),
    "st":    ("Sesotho",                "Sesotho"),
    "sn":    ("Shona",                  "chiShona"),
    "so":    ("Somali",                 "Soomaali"),
    "ny":    ("Chichewa",               "Chichewa"),
    "mg":    ("Malagasy",               "Malagasy"),
    # Other
    "ht":    ("Haitian Creole",         "Kreyòl ayisyen"),
    "la":    ("Latin",                  "Latina"),
    "eo":    ("Esperanto",              "Esperanto"),
    "yi":    ("Yiddish",                "ייִדיש"),
}

_GOOGLE_CODE_MAP = {
    "zh-CN": "zh-CN", "zh-TW": "zh-TW",
    "mai": "mai", "bho": "bho", "doi": "doi",
    "kok": "gom", "mni": "mni-Mtei", "sat": "sat",
}

# Language codes that may arrive as Romanized Latin text
_ROMANIZED_LATIN_CODES = ROMANIZED_LATIN_CODES

# Provider quality weights for confidence scoring
_PROVIDER_WEIGHTS = {
    "google_json": 0.97,
    "google": 0.96,
    "libretranslate": 0.88,
    "mymemory": 0.82,
    "fallback": 0.60,
}

# ---------------------------------------------------------------------------
# LRU caches (translation + detection)
# ---------------------------------------------------------------------------
_translation_cache: OrderedDict[str, dict] = OrderedDict()
_detection_cache: OrderedDict[str, dict] = OrderedDict()
_CACHE_MAX = Config.TRANSLATION_CACHE_MAX


def _cache_key(text: str, source: str, target: str, tone: str = "professional") -> str:
    digest = hashlib.md5(
        f"{source}|{target}|{tone}|{text[:300]}".encode("utf-8")
    ).hexdigest()
    return digest


def _detection_cache_key(text: str) -> str:
    return hashlib.md5(text[:500].encode("utf-8")).hexdigest()


def _lru_get(cache: OrderedDict, key: str):
    if key not in cache:
        return None
    cache.move_to_end(key)
    return cache[key]


def _lru_set(cache: OrderedDict, key: str, value: dict, max_size: int) -> None:
    if key in cache:
        cache.move_to_end(key)
    cache[key] = value
    while len(cache) > max_size:
        cache.popitem(last=False)


# ---------------------------------------------------------------------------
# Public API — signatures unchanged for existing routes / frontend
# ---------------------------------------------------------------------------

def get_languages() -> list[dict]:
    result = []
    for code, (name, native) in LANGUAGE_REGISTRY.items():
        if code == "auto":
            display = "Auto Detect"
        elif name == native:
            display = name
        else:
            display = f"{name} ({native})"
        result.append({"code": code, "name": display, "native": native})
    auto = [r for r in result if r["code"] == "auto"]
    rest = sorted([r for r in result if r["code"] != "auto"], key=lambda x: x["name"])
    return auto + rest


def get_language_info(code: str) -> dict:
    normalised = code.lower().replace("_", "-")
    entry = LANGUAGE_REGISTRY.get(code) or LANGUAGE_REGISTRY.get(normalised)
    resolved_code = code
    if not entry:
        for k, v in LANGUAGE_REGISTRY.items():
            if k.lower() == normalised:
                entry = v
                resolved_code = k
                break
    if entry:
        name, native = entry
        display = name if name == native else f"{name} ({native})"
        return {"code": resolved_code, "name": name, "native": native, "display": display}
    return {"code": code, "name": code, "native": code, "display": code}


def detect_language(text: str) -> dict:
    """
    Detect language with Romanized Indian, script, langdetect, and confidence scoring.
    Returns {code, name, native, display, confidence, romanized?}
    """
    if not text or not text.strip():
        return {**get_language_info("en"), "confidence": 0.0}

    dkey = _detection_cache_key(text.strip())
    cached = _lru_get(_detection_cache, dkey)
    if cached:
        return {**cached, "from_cache": True}

    # Strong romanized match beats langdetect (e.g. sat sri akal, ni hao)
    if is_latin_text(text):
        romanized = detect_any_romanized(text)
        if romanized and romanized.get("confidence", 0) >= 0.65:
            _lru_set(_detection_cache, dkey, romanized, _CACHE_MAX // 4)
            return romanized

    result = detect_language_full(text, get_language_info, LANGUAGE_REGISTRY)
    _lru_set(_detection_cache, dkey, result, _CACHE_MAX // 4)
    return result


def translate_text(
    text: str,
    source_lang: str = "auto",
    target_lang: str = "en",
    tone: str = "professional",
) -> dict:
    """
    Translate text with Romanized Indian support, multi-provider fallback, and caching.
    Response shape unchanged: translated_text, detected_lang, detected_lang_info,
    confidence, provider, optional romanized_input, optional from_cache.
    """
    if not text or not text.strip():
        return {
            "translated_text": "",
            "detected_lang": source_lang,
            "detected_lang_info": get_language_info(source_lang),
            "confidence": 0.0,
            "provider": "none",
        }

    text = text.strip()
    if len(text) > 10_000:
        text = text[:10_000]

    source_norm = _normalise_code(source_lang)
    target_norm = _normalise_code(target_lang)
    tone_norm = (tone or "professional").lower()

    cache_key = _cache_key(text, source_norm, target_norm, tone_norm)
    cached = _lru_get(_translation_cache, cache_key)
    if cached:
        logger.debug("Cache hit for %r (%s→%s)", text[:40], source_norm, target_norm)
        return {**cached, "from_cache": True}

    romanized_info = None
    detected_code = source_norm
    detection_confidence = 0.95
    effective_source = source_norm

    if source_norm == "auto":
        romanized_info = detect_any_romanized(text)

        if romanized_info:
            detected_code = romanized_info["code"]
            detection_confidence = romanized_info["confidence"]
            effective_source = detected_code
            logger.info(
                "Romanized detected: lang=%s confidence=%.2f text=%r",
                detected_code, detection_confidence, text[:80],
            )
        else:
            detection = detect_language(text)
            detected_code = detection["code"]
            detection_confidence = detection["confidence"]
            # Keep auto for Google; detected_code is passed separately as a hint
            effective_source = "auto"
            logger.info(
                "Auto-detected: lang=%s confidence=%.2f text=%r",
                detected_code, detection_confidence, text[:80],
            )
    else:
        detected_code = source_norm
        effective_source = source_norm
        if source_norm in _ROMANIZED_LATIN_CODES and is_latin_text(text):
            romanized_info = detect_any_romanized(text)
            if romanized_info and romanized_info["code"] == source_norm:
                logger.info(
                    "Romanized input with explicit source=%s text=%r",
                    source_norm, text[:80],
                )

    logger.info(
        "Translation request: source=%s effective_source=%s target=%s text=%r",
        source_norm, effective_source, target_norm, text[:80],
    )

    text_for_api = _prepare_text_for_api(text, romanized_info, detected_code)

    translated, provider = _translate_with_fallback(
        text_for_api,
        effective_source,
        target_norm,
        original_text=text,
        detected_source=detected_code,
    )

    logger.info(
        "Translation result: provider=%s output=%r",
        provider, translated[:120] if translated else "",
    )

    if tone_norm and tone_norm != "professional":
        translated = _apply_tone_ai(translated, tone_norm, target_norm)

    confidence = round(
        min(
            0.99,
            detection_confidence * _PROVIDER_WEIGHTS.get(provider, 0.75),
        ),
        2,
    )

    result = {
        "translated_text": translated,
        "detected_lang": detected_code,
        "detected_lang_info": romanized_info or get_language_info(detected_code),
        "confidence": confidence,
        "provider": provider,
    }
    if romanized_info:
        result["romanized_input"] = True

    if provider != "fallback" and is_valid_translation(text, translated):
        _lru_set(_translation_cache, cache_key, result, _CACHE_MAX)
    else:
        logger.warning(
            "Skipping cache for unchanged translation: provider=%s text=%r",
            provider, text[:60],
        )
    return result


# ---------------------------------------------------------------------------
# Translation pipeline
# ---------------------------------------------------------------------------

def _prepare_text_for_api(
    text: str,
    romanized_info: dict | None,
    detected_code: str,
) -> str:
    """Convert Romanized Latin text to native script before calling translation APIs."""
    if not is_latin_text(text):
        return text

    lang = (romanized_info or {}).get("code") or detected_code
    if lang not in _ROMANIZED_LATIN_CODES:
        return text

    try:
        normalized = normalize_romanized_text(text, lang)
        if normalized != text:
            logger.info(
                "Normalization (%s): before=%r after=%r",
                lang, text[:80], normalized[:80],
            )
        return normalized
    except Exception as exc:
        logger.warning("Normalization failed (%s): %s", lang, exc)
        return text


def _translate_with_fallback(
    text: str,
    source: str,
    target: str,
    original_text: str | None = None,
    detected_source: str | None = None,
) -> tuple[str, str]:
    """
    Multi-layer provider pipeline:
      1. Google (JSON + scrape, with auto-detect retry)
      2. LibreTranslate
      3. MyMemory (never uses source=auto)
      4. Original text
    """
    if source == target:
        return text, "fallback"

    original = original_text or text

    source_attempts: list[str] = []
    for sl in (source, detected_source, "auto"):
        if sl and sl not in source_attempts and sl != target:
            source_attempts.append(sl)

    def _accept(result_text: str | None, provider_name: str = "") -> bool:
        return bool(result_text) and is_valid_translation(
            original, result_text, provider_name,
        )

    # --- Priority 1: Google ---
    for sl in source_attempts:
        for provider_fn, name in (
            (translate_google_json, "google_json"),
            (translate_google_scrape, "google"),
        ):
            try:
                result = provider_fn(text, sl, target)
                if _accept(result.text, name):
                    logger.info(
                        "Translation succeeded via %s (sl=%s): %r → %r",
                        name, sl, original[:60], (result.text or "")[:60],
                    )
                    return result.text, name  # type: ignore[return-value]
                if result.text:
                    logger.warning(
                        "Translation rejected (%s sl=%s): %r",
                        name, sl, result.text[:60],
                    )
            except ValueError:
                raise
            except Exception as exc:
                logger.warning("%s failed (sl=%s): %s", name, sl, exc)

    # --- Priority 2: LibreTranslate ---
    for sl in source_attempts:
        try:
            result = translate_libre(text, sl, target)
            if _accept(result.text, "libretranslate"):
                logger.info("Translation succeeded via libretranslate (sl=%s)", sl)
                return result.text, "libretranslate"  # type: ignore[return-value]
        except Exception as exc:
            logger.warning("LibreTranslate failed (sl=%s): %s", sl, exc)

    # --- Priority 3: MyMemory (concrete source only) ---
    for sl in source_attempts:
        if sl == "auto":
            continue
        try:
            result = translate_mymemory(text, sl, target)
            if _accept(result.text, "mymemory"):
                logger.info("Translation succeeded via mymemory (sl=%s)", sl)
                return result.text, "mymemory"  # type: ignore[return-value]
        except Exception as exc:
            logger.warning("MyMemory failed (sl=%s): %s", sl, exc)

    logger.error(
        "All providers failed or returned unchanged text: source=%s target=%s text=%r",
        source, target, original[:80],
    )
    return original, "fallback"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _normalise_code(code: str) -> str:
    if not code:
        return "auto"
    code = code.strip()
    mapped = _GOOGLE_CODE_MAP.get(code)
    if mapped:
        return mapped
    if code.lower() in ("zh-cn", "zh_cn", "zh"):
        return "zh-CN"
    if code.lower() in ("zh-tw", "zh_tw"):
        return "zh-TW"
    return code


def _normalize_for_compare(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.lower())
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"[^\w\s]", "", text).strip()


def _is_untranslated(original: str, translated: str) -> bool:
    """True when a provider returned the input unchanged (common for Romanized Indic)."""
    if not translated or not original:
        return True
    if original.strip() == translated.strip():
        return True
    orig_norm = _normalize_for_compare(original)
    trans_norm = _normalize_for_compare(translated)
    if orig_norm and orig_norm == trans_norm:
        return True
    orig_alpha = re.sub(r"[^\w]", "", orig_norm)
    trans_alpha = re.sub(r"[^\w]", "", trans_norm)
    return bool(orig_alpha) and orig_alpha == trans_alpha


def _apply_tone_ai(text: str, tone: str, lang: str) -> str:
    try:
        from services.ai_service import rewrite_tone
        return rewrite_tone(text, tone, lang) or text
    except Exception as exc:
        logger.warning("Tone rewrite failed: %s", exc)
        return text
