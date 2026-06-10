"""
romanized_global.py — Romanized detection & normalization for Korean, Chinese,
Arabic, Thai, Vietnamese, Turkish, and common European greetings.

Google Translate fails on raw romanization (e.g. annyeonghaseyo, ni hao).
This module maps known phrases to native script before translation, and
detects European greetings so the correct source language is used.
"""

from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

_MIN_SCORE = 8
_DECISIVE_RATIO = 1.4

# lang_code → config
_REGISTRY: dict[str, dict] = {
    "ko": {
        "name": "Korean",
        "native": "한국어",
        "markers": [
            ("annyeonghaseyo", 12), ("annyeong", 10), ("anyeonghaseyo", 12),
            ("saranghae", 12), ("saranghaeyo", 12), ("saranghamnida", 12),
            ("kamsahamnida", 12), ("gamsahamnida", 12), ("gomawo", 10),
            ("mianhae", 10), ("mianhamnida", 11), ("joesonghamnida", 11),
            ("eotteoke", 9), ("jigeum", 8), ("joa", 8), ("jal jinaeseyo", 11),
            ("bangapda", 9), ("oppa", 9), ("unnie", 9), ("hyung", 8),
            ("noona", 8), ("daebak", 10), ("aigoo", 10), ("hwaiting", 10),
            ("jjang", 9), ("chingu", 9), ("hanguk", 10), ("hangugeo", 10),
        ],
        "phrases": {
            "annyeonghaseyo": "안녕하세요",
            "annyeong": "안녕",
            "anyeonghaseyo": "안녕하세요",
            "saranghae": "사랑해",
            "saranghaeyo": "사랑해요",
            "saranghamnida": "사랑합니다",
            "kamsahamnida": "감사합니다",
            "gamsahamnida": "감사합니다",
            "gomawo": "고마워",
            "mianhae": "미안해",
            "mianhamnida": "미안합니다",
            "joesonghamnida": "죄송합니다",
            "jal jinaeseyo": "잘 지내세요",
        },
    },
    "zh-CN": {
        "name": "Chinese (Simplified)",
        "native": "中文(简体)",
        "markers": [
            ("ni hao", 12), ("nihao", 12), ("xie xie", 12), ("xiexie", 11),
            ("wo ai ni", 12), ("zaijian", 11), ("zai jian", 11),
            ("duibuqi", 10), ("bu keqi", 10), ("meiguanxi", 10),
            ("qing wen", 10), ("zao shang hao", 11), ("wan an", 10),
            ("gong xi", 10), ("shenme", 8), ("weishenme", 9), ("zenme", 8),
            ("pinyin", 9), ("zhongwen", 10), ("zhong guo", 10),
        ],
        "phrases": {
            "ni hao": "你好",
            "nihao": "你好",
            "xie xie": "谢谢",
            "xiexie": "谢谢",
            "wo ai ni": "我爱你",
            "zaijian": "再见",
            "zai jian": "再见",
            "duibuqi": "对不起",
            "bu keqi": "不客气",
            "meiguanxi": "没关系",
            "zao shang hao": "早上好",
            "wan an": "晚安",
        },
    },
    "ar": {
        "name": "Arabic",
        "native": "العربية",
        "markers": [
            ("marhaba", 11), ("marhaban", 11), ("shukran", 11), ("shukran jazilan", 12),
            ("salam alaikum", 12), ("assalamu alaikum", 12), ("wa alaikum assalam", 12),
            ("inshallah", 11), ("mashallah", 11), ("alhamdulillah", 11),
            ("afwan", 10), ("min fadlak", 11), ("keif halak", 11), ("keif halik", 11),
            ("sabah al khair", 11), ("masa al khair", 11), ("naam", 8), ("la", 6),
            ("habibi", 10), ("yalla", 10), ("khalas", 9), ("wallah", 9),
        ],
        "phrases": {
            "marhaba": "مرحبا",
            "marhaban": "مرحباً",
            "shukran": "شكرا",
            "shukran jazilan": "شكرا جزيلا",
            "salam alaikum": "السلام عليكم",
            "assalamu alaikum": "السلام عليكم",
            "wa alaikum assalam": "وعليكم السلام",
            "inshallah": "إن شاء الله",
            "mashallah": "ما شاء الله",
            "alhamdulillah": "الحمد لله",
            "afwan": "عفواً",
            "min fadlak": "من فضلك",
            "keif halak": "كيف حالك",
            "keif halik": "كيف حالك",
            "sabah al khair": "صباح الخير",
            "masa al khair": "مساء الخير",
            "habibi": "حبيبي",
            "yalla": "يلا",
        },
    },
    "th": {
        "name": "Thai",
        "native": "ภาษาไทย",
        "markers": [
            ("sawadee ka", 12), ("sawadee krub", 12), ("sawatdee ka", 12),
            ("sawatdee krub", 12),             ("khob khun ka", 12), ("khob khun krub", 12), ("khob khun", 12),
            ("khop khun", 11), ("sabai dee mai", 11), ("mai pen rai", 11),
            ("aroi", 9), ("aroi mak", 10), ("pom", 7), ("chan", 7),
            ("krung thep", 10), ("phuket", 8),
        ],
        "phrases": {
            "sawadee ka": "สวัสดีค่ะ",
            "sawadee krub": "สวัสดีครับ",
            "sawatdee ka": "สวัสดีค่ะ",
            "sawatdee krub": "สวัสดีครับ",
            "khob khun ka": "ขอบคุณค่ะ",
            "khob khun krub": "ขอบคุณครับ",
            "khob khun": "ขอบคุณ",
            "khop khun": "ขอบคุณ",
            "sabai dee mai": "สบายดีไหม",
            "mai pen rai": "ไม่เป็นไร",
            "aroi mak": "อร่อยมาก",
        },
    },
    "vi": {
        "name": "Vietnamese",
        "native": "Tiếng Việt",
        "markers": [
            ("xin chao", 12), ("cam on", 11), ("camon", 11), ("cam on ban", 12),
            ("xin loi", 10), ("khong co gi", 11), ("khong sao dau", 11),
            ("ban khoe khong", 11), ("toi yeu ban", 12), ("rat vui duoc gap ban", 12),
            ("tam biet", 10), ("chuc ngu ngon", 11),
        ],
        "phrases": {
            "xin chao": "xin chào",
            "cam on": "cảm ơn",
            "camon": "cảm ơn",
            "cam on ban": "cảm ơn bạn",
            "xin loi": "xin lỗi",
            "khong co gi": "không có gì",
            "toi yeu ban": "tôi yêu bạn",
            "tam biet": "tạm biệt",
        },
    },
    "tr": {
        "name": "Turkish",
        "native": "Türkçe",
        "markers": [
            ("merhaba", 11), ("selam", 10), ("tesekkurler", 11), ("tesekkur ederim", 12),
            ("sagol", 9), ("hos geldiniz", 11), ("gule gule", 10), ("iyi gunler", 11),
            ("gunaydin", 11), ("iyi aksamlar", 11), ("lutfen", 10), ("ozur dilerim", 11),
            ("evet", 8), ("hayir", 8), ("tamam", 9), ("naber", 10), ("nasilsin", 11),
        ],
        "phrases": {
            "merhaba": "merhaba",
            "tesekkurler": "teşekkürler",
            "tesekkur ederim": "teşekkür ederim",
            "hos geldiniz": "hoş geldiniz",
            "gule gule": "güle güle",
            "iyi gunler": "iyi günler",
            "gunaydin": "günaydın",
            "nasilsin": "nasılsın",
        },
    },
    # European — detection + source hint (ASCII input, no script conversion needed)
    "fr": {
        "name": "French",
        "native": "Français",
        "markers": [
            ("bonjour", 11), ("bonsoir", 10), ("salut", 9), ("merci", 10),
            ("merci beaucoup", 12), ("s il vous plait", 11), ("au revoir", 11),
            ("comment allez vous", 12), ("ca va", 10), ("excusez moi", 11),
            ("je t aime", 11), ("oui", 7), ("non", 7),
        ],
        "phrases": {},
    },
    "de": {
        "name": "German",
        "native": "Deutsch",
        "markers": [
            ("guten tag", 12), ("guten morgen", 11), ("guten abend", 11),
            ("danke", 10), ("danke schon", 11), ("bitte", 9), ("auf wiedersehen", 12),
            ("wie geht es", 11), ("ich liebe dich", 11), ("entschuldigung", 10),
        ],
        "phrases": {},
    },
    "es": {
        "name": "Spanish",
        "native": "Español",
        "markers": [
            ("hola", 10), ("buenos dias", 11), ("buenas noches", 11),
            ("gracias", 10), ("muchas gracias", 12), ("por favor", 10),
            ("de nada", 10), ("como estas", 11), ("lo siento", 10),
            ("te amo", 10), ("adios", 10),
        ],
        "phrases": {},
    },
    "it": {
        "name": "Italian",
        "native": "Italiano",
        "markers": [
            ("ciao", 10), ("buongiorno", 11), ("buonasera", 11),
            ("grazie", 10), ("grazie mille", 12), ("prego", 9),
            ("arrivederci", 11), ("come stai", 11), ("ti amo", 10),
            ("scusa", 9), ("per favore", 10),
        ],
        "phrases": {},
    },
    "ru": {
        "name": "Russian",
        "native": "Русский",
        "markers": [
            ("privet", 11), ("zdravstvuyte", 12), ("spasibo", 11),
            ("spasiba", 10), ("pozhaluysta", 11), ("do svidaniya", 12),
            ("kak dela", 11), ("ya tebya lyublyu", 12), ("izvinite", 10),
        ],
        "phrases": {
            "privet": "привет",
            "zdravstvuyte": "здравствуйте",
            "spasibo": "спасибо",
            "spasiba": "спасибо",
            "do svidaniya": "до свидания",
            "kak dela": "как дела",
        },
    },
    "pt": {
        "name": "Portuguese",
        "native": "Português",
        "markers": [
            ("obrigado", 11), ("obrigada", 11), ("bom dia", 11),
            ("boa noite", 10), ("boa tarde", 10), ("por favor", 9),
            ("de nada", 9), ("como vai", 10), ("te amo", 9),
        ],
        "phrases": {},
    },
}


def _clean(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _marker_matches(clean: str, phrase: str) -> bool:
    pattern = r"\b" + re.escape(phrase.lower()) + r"\b"
    return bool(re.search(pattern, clean))


def _score_language(clean: str, markers: list[tuple[str, int]]) -> float:
    total = 0.0
    for phrase, weight in markers:
        if _marker_matches(clean, phrase):
            multiplier = 1.5 if " " in phrase else 1.0
            total += weight * multiplier
    return total


def detect_romanized_global(text: str) -> dict | None:
    """Detect romanized Korean, Chinese, Arabic, Thai, etc. from Latin input."""
    if not text or not text.strip():
        return None

    clean = _clean(text)
    if not clean or not re.match(r"^[a-z\s]+$", clean):
        return None

    scores: dict[str, float] = {}
    for code, cfg in _REGISTRY.items():
        score = _score_language(clean, cfg["markers"])
        if clean in cfg.get("phrases", {}):
            score = max(score, 14.0)
        if score > 0:
            scores[code] = score

    if not scores:
        return None

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    best_code, best_score = ranked[0]
    if best_score < _MIN_SCORE:
        return None

    if len(ranked) > 1:
        second = ranked[1][1]
        if second > 0 and (best_score / second) < _DECISIVE_RATIO:
            confidence = 0.58
        else:
            confidence = min(0.93, 0.68 + best_score * 0.008)
    else:
        confidence = min(0.93, 0.68 + best_score * 0.008)

    cfg = _REGISTRY[best_code]
    display = f"{cfg['name']} ({cfg['native']})"
    logger.info(
        "Global romanized detection: %r → %s (score=%.1f)",
        text[:50], best_code, best_score,
    )
    return {
        "code": best_code,
        "name": cfg["name"],
        "native": cfg["native"],
        "display": display,
        "confidence": round(confidence, 2),
        "score": best_score,
        "romanized": True,
    }


def _has_native_script(text: str, lang_code: str) -> bool:
    for ch in text:
        cp = ord(ch)
        if lang_code == "ko" and 0xAC00 <= cp <= 0xD7AF:
            return True
        if lang_code.startswith("zh") and 0x4E00 <= cp <= 0x9FFF:
            return True
        if lang_code == "ar" and (0x0600 <= cp <= 0x06FF or 0xFB50 <= cp <= 0xFDFF):
            return True
        if lang_code == "th" and 0x0E00 <= cp <= 0x0E7F:
            return True
        if lang_code == "ru" and 0x0400 <= cp <= 0x04FF:
            return True
    return False


def normalize_global_text(text: str, lang_code: str) -> str:
    """Convert romanized text to native script when a mapping exists."""
    if not text or lang_code not in _REGISTRY:
        return text

    cfg = _REGISTRY[lang_code]
    phrases: dict[str, str] = cfg.get("phrases", {})
    if not phrases:
        return text.strip()

    clean = _clean(text)
    if clean in phrases:
        return phrases[clean]

    result = text
    for phrase, native in sorted(phrases.items(), key=lambda x: -len(x[0])):
        pattern = re.compile(re.escape(phrase), re.IGNORECASE)
        if pattern.search(_clean(result)):
            result = pattern.sub(native, result, count=1)
            break

    if _has_native_script(result, lang_code):
        logger.debug("Global normalize (%s): %r → %r", lang_code, text[:40], result[:40])
        return result.strip()

    return text.strip()


def get_global_lang_codes() -> frozenset[str]:
    return frozenset(_REGISTRY.keys())
