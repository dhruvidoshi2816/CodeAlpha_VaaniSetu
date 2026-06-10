"""
ocr_lang_map.py — Map VaaniSetu ISO language codes to Tesseract OCR codes.

The frontend sends source_lang as ISO codes (hi, gu, en, auto).
Tesseract expects 3-letter codes (hin, guj, eng) or composites (eng+hin).
"""

from __future__ import annotations

# ISO / app code → Tesseract traineddata code
ISO_TO_TESSERACT: dict[str, str] = {
    "auto": "",
    "en": "eng",
    "hi": "hin",
    "gu": "guj",
    "mr": "mar",
    "bn": "ben",
    "pa": "pan",
    "ta": "tam",
    "te": "tel",
    "kn": "kan",
    "ml": "mal",
    "ur": "urd",
    "or": "ori",
    "as": "asm",
    "ne": "nep",
    "si": "sin",
    "sa": "san",
    "ar": "ara",
    "he": "heb",
    "fa": "fas",
    "tr": "tur",
    "ru": "rus",
    "uk": "ukr",
    "de": "deu",
    "fr": "fra",
    "es": "spa",
    "it": "ita",
    "pt": "por",
    "nl": "nld",
    "pl": "pol",
    "sv": "swe",
    "da": "dan",
    "fi": "fin",
    "no": "nor",
    "cs": "ces",
    "sk": "slk",
    "hr": "hrv",
    "sr": "srp",
    "bg": "bul",
    "ro": "ron",
    "hu": "hun",
    "el": "ell",
    "zh-CN": "chi_sim",
    "zh-TW": "chi_tra",
    "ja": "jpn",
    "ko": "kor",
    "th": "tha",
    "vi": "vie",
    "id": "ind",
    "ms": "msa",
    "tl": "fil",
    "my": "mya",
    "km": "khm",
    "lo": "lao",
    "sw": "swa",
    "am": "amh",
    "af": "afr",
    "sq": "sqi",
    "hy": "hye",
    "ka": "kat",
    "az": "aze",
    "kk": "kaz",
    "uz": "uzb",
    "mn": "mon",
    "be": "bel",
    "lt": "lit",
    "lv": "lav",
    "et": "est",
    "is": "isl",
    "ga": "gle",
    "cy": "cym",
    "eu": "eus",
    "ca": "cat",
    "gl": "glg",
    "mk": "mkd",
    "bs": "bos",
    "sl": "slv",
    "mt": "mlt",
    "ht": "hat",
    "eo": "epo",
    "yi": "yid",
    "ps": "pus",
    "ku": "kur",
    "jv": "jav",
    "su": "sun",
    "ceb": "ceb",
    "ny": "nya",
    "mg": "mlg",
    "la": "lat",
}

# Composite used when source is auto-detect (covers most user uploads)
AUTO_TESSERACT_LANGS = "+".join([
    "eng", "hin", "guj", "mar", "ben", "pan", "tam", "tel", "kan", "mal", "urd",
    "ara", "chi_sim", "jpn", "kor", "fra", "deu", "spa", "rus", "por", "ita",
    "tha", "vie", "tur", "nld", "pol", "ces", "swe", "nor",
])

# Aliases users / Tesseract installers may send directly
_TESSERACT_ALIASES = {
    "eng", "hin", "guj", "mar", "ben", "pan", "tam", "tel", "kan", "mal", "urd",
    "chi_sim", "chi_tra", "jpn", "kor", "ara", "fra", "deu", "spa", "ita", "por",
    "rus", "tha", "vie", "tur", "nld", "pol", "ces", "osd",
}


def resolve_tesseract_lang(
    explicit_lang: str | None = None,
    source_lang: str | None = None,
) -> str:
    """
    Resolve the Tesseract language string from form fields.

    Priority:
      1. explicit `lang` form field (only when client sends it)
      2. `source_lang` ISO code mapped to Tesseract
      3. auto — empty string triggers multi-candidate Indic detection
    """
    if explicit_lang and explicit_lang.strip():
        lang = explicit_lang.strip().lower().replace("_", "-")
        if lang in _TESSERACT_ALIASES or "+" in lang:
            return lang
        mapped = ISO_TO_TESSERACT.get(lang) or ISO_TO_TESSERACT.get(lang.upper())
        if mapped:
            return mapped
        return explicit_lang.strip()

    if source_lang and source_lang.strip().lower() not in ("auto", ""):
        code = source_lang.strip()
        mapped = ISO_TO_TESSERACT.get(code) or ISO_TO_TESSERACT.get(code.lower())
        if mapped:
            return mapped

    # Empty → multi-candidate mode in ocr_service
    return "auto"
