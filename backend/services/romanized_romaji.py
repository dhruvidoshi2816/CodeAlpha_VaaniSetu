"""
romanized_romaji.py — Detect and normalize Romanized Japanese (romaji) text.

Google Translate cannot translate raw romaji like "aishteru" or "arigato" — it
returns the input unchanged. This module:
  1. Detects likely Japanese from romaji phrase/word markers
  2. Maps common phrases (and typo variants) to native script before translation
  3. Falls back to pykakasi romaji → hiragana when installed

Examples:
  aishteru  → 愛してる → "I love you"
  arigato   → ありがとう → "Thank you"
  konnichiwa → こんにちは → "Hello"
"""

from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

# (romaji phrase, weight) — higher weight = stronger Japanese signal
_JAPANESE_MARKERS = [
    ("aishiteru", 12), ("aishteru", 12), ("ai shiteru", 11), ("ai shiteru", 11),
    ("daisuki", 11), ("suki desu", 11), ("suki da", 10), ("anata", 9),
    ("arigato", 11), ("domo arigato", 12), ("arigato gozaimasu", 12),
    ("konnichiwa", 12), ("konbanwa", 11), ("ohayou", 10), ("ohayo", 10),
    ("sayonara", 11), ("mata ne", 10), ("jaa ne", 9), ("itadakimasu", 11),
    ("gochisousama", 11), ("sumimasen", 10), ("gomen nasai", 11), ("gomen", 9),
    ("onegaishimasu", 11), ("onegai", 9), ("kudasai", 9),
    ("daijoubu", 10), ("daijobu", 10), ("genki", 9), ("genki desu", 11),
    ("watashi", 9), ("boku", 8), ("ore", 7), ("kimi", 8), ("anata", 8),
    ("desu", 7), ("masu", 6), ("kawaii", 10), ("kowai", 9), ("tanoshii", 9),
    ("samui", 8), ("atsui", 8), ("oishii", 10), ("oishi", 9),
    ("nihongo", 10), ("nihon", 9), ("nihonjin", 10),
    ("sensei", 9), ("senpai", 10), ("kohai", 9), ("chan", 6), ("kun", 6), ("san", 5),
    ("tomodachi", 10), ("kazoku", 9), ("okaasan", 9), ("otousan", 9),
    ("onii chan", 10), ("onee chan", 10), ("imouto", 9), ("otouto", 9),
    ("mou ichido", 10), ("chotto matte", 11), ("yatta", 9),     ("yabai", 10), ("baka", 11), ("baka ya", 12), ("aho", 10), ("urusai", 10),
    ("shinjiru", 9), ("shinu", 8), ("ikiru", 8), ("iku", 7), ("kuru", 7),
    ("taberu", 8), ("nomu", 7), ("miru", 7), ("kiku", 7), ("yomu", 7),
    ("wakarimasen", 11), ("wakatta", 10), ("shitteru", 9), ("shiranai", 9),
    ("hajimemashite", 11), ("yoroshiku", 10), ("omedetou", 10),
]

# Romaji (lowercase, normalized) → native Japanese script
_PHRASE_NATIVE: dict[str, str] = {
    "aishiteru": "愛してる",
    "aishteru": "愛してる",
    "ai shiteru": "愛してる",
    "daisuki": "大好き",
    "suki desu": "好きです",
    "suki da": "好きだ",
    "arigato": "ありがとう",
    "domo arigato": "どうもありがとう",
    "arigato gozaimasu": "ありがとうございます",
    "konnichiwa": "こんにちは",
    "konbanwa": "こんばんは",
    "ohayou": "おはよう",
    "ohayo": "おはよう",
    "sayonara": "さようなら",
    "mata ne": "またね",
    "jaa ne": "じゃあね",
    "itadakimasu": "いただきます",
    "gochisousama": "ごちそうさま",
    "sumimasen": "すみません",
    "gomen nasai": "ごめんなさい",
    "gomen": "ごめん",
    "onegaishimasu": "お願いします",
    "onegai": "お願い",
    "kudasai": "ください",
    "daijoubu": "大丈夫",
    "daijobu": "大丈夫",
    "genki desu": "元気です",
    "genki": "元気",
    "watashi": "私",
    "kawaii": "可愛い",
    "oishii": "美味しい",
    "oishi": "美味しい",
    "wakarimasen": "分かりません",
    "wakatta": "分かった",
    "hajimemashite": "初めまして",
    "yoroshiku": "よろしく",
    "omedetou": "おめでとう",
    "tomodachi": "友達",
    "nihongo": "日本語",
    "sensei": "先生",
    "senpai": "先輩",
    "chotto matte": "ちょっと待って",
    "mou ichido": "もう一度",
    "yabai": "やばい",
    "baka": "馬鹿",
    "baka ya": "馬鹿野郎",
    "aho": "阿呆",
    "urusai": "うるさい",
}

_MIN_SCORE = 8
_DECISIVE_RATIO = 1.4


def _clean(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _marker_matches(clean: str, phrase: str) -> bool:
    pattern = r"\b" + re.escape(phrase.lower()) + r"\b"
    return bool(re.search(pattern, clean))


def detect_romanized_japanese(text: str) -> dict | None:
    """Return language info dict if text looks like romaji Japanese."""
    if not text or not text.strip():
        return None

    clean = _clean(text)
    if not clean or not re.match(r"^[a-z\s]+$", clean):
        return None

    total_score = 0.0
    for phrase, weight in _JAPANESE_MARKERS:
        if _marker_matches(clean, phrase):
            multiplier = 1.5 if " " in phrase else 1.0
            total_score += weight * multiplier

    # Exact dictionary hit is a strong signal even if score is borderline
    if clean in _PHRASE_NATIVE:
        total_score = max(total_score, 14.0)

    if total_score < _MIN_SCORE:
        return None

    confidence = min(0.93, 0.68 + total_score * 0.008)

    logger.info(
        "Romaji detection: %r → ja (score=%.1f, confidence=%.2f)",
        text[:50], total_score, confidence,
    )
    return {
        "code": "ja",
        "name": "Japanese",
        "native": "日本語",
        "display": "Japanese (日本語)",
        "confidence": round(confidence, 2),
        "score": total_score,
        "romanized": True,
    }


def _is_japanese_script(text: str) -> bool:
    for ch in text:
        cp = ord(ch)
        if 0x3040 <= cp <= 0x30FF or 0x4E00 <= cp <= 0x9FFF:
            return True
    return False


def _romaji_to_hiragana(text: str) -> str | None:
    """Convert romaji to hiragana using pykakasi when available."""
    try:
        import pykakasi
        kks = pykakasi.kakasi()
        converted = kks.convert(text)
        hira = "".join(item.get("hira", "") for item in converted).strip()
        if hira and _is_japanese_script(hira):
            logger.debug("pykakasi: %r → %r", text[:40], hira[:40])
            return hira
    except ImportError:
        logger.debug("pykakasi not installed — skipping romaji transliteration")
    except Exception as exc:
        logger.warning("pykakasi failed: %s", exc)
    return None


def normalize_romaji_text(text: str) -> str:
    """
    Convert romaji to native Japanese script for translation APIs.
    Order: exact phrase dict → partial phrase replace → pykakasi hiragana.
    """
    if not text or not text.strip():
        return text

    lower = text.lower().strip()
    clean = _clean(text)

    if clean in _PHRASE_NATIVE:
        result = _PHRASE_NATIVE[clean]
        logger.debug("Romaji dict (exact): %r → %r", text[:40], result[:40])
        return result

    result = text
    replaced = False
    for phrase, native in sorted(_PHRASE_NATIVE.items(), key=lambda x: -len(x[0])):
        pattern = re.compile(re.escape(phrase), re.IGNORECASE)
        if pattern.search(result.lower()):
            result = pattern.sub(native, result, count=1)
            replaced = True
            break

    if replaced and _is_japanese_script(result):
        logger.debug("Romaji dict (partial): %r → %r", text[:40], result[:40])
        return result.strip()

    if re.match(r"^[a-zA-Z\s]+$", text.strip()):
        hira = _romaji_to_hiragana(text.strip())
        if hira:
            logger.info("Romaji → hiragana: %r → %r", text[:40], hira[:40])
            return hira

    return text.strip()
