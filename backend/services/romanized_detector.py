"""
romanized_detector.py — Detect and handle Romanized Indian languages.

Google Translate cannot detect "kem cho" as Gujarati or "kaise ho" as Hindi
because they look like English to the API. This module:
1. Detects the likely Indian language from Romanized text using phrase/word dictionaries
2. Returns the language code + confidence so the translator can handle it correctly
3. Provides a transliteration hint so the translation is accurate

Strategy: dictionary-based phrase matching with confidence scoring.
No external dependencies — pure Python.
"""

import re
import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Romanized phrase dictionaries per language
# Each entry: (romanized_phrase, weight)
# Higher weight = stronger signal for that language
# ---------------------------------------------------------------------------

_GUJARATI_MARKERS = [
    # Greetings / common phrases
    ("tame kem cho", 11), ("kem cho", 10), ("kem chho", 10), ("majama", 9), ("maja ma", 9),
    ("shu karo cho", 9), ("tamne", 8), ("tamaro", 8), ("tamari", 8),
    ("hu", 5), ("ame", 6), ("tame", 7), ("aavjo", 9), ("aavjo ne", 9),
    ("shu", 6), ("chhe", 8), ("chho", 8), ("nathi", 8), ("nahi", 5),
    ("haan", 5), ("na", 4), ("pan", 5), ("ane", 6), ("ke", 4),
    ("mane", 7), ("tane", 7), ("ane", 5), ("pachi", 7), ("pehla", 6),
    ("ghanu", 8), ("saras", 8), ("badhuj", 8), ("badhu", 7),
    ("tamne gamyu", 9), ("shu naam chhe", 9), ("maru naam", 8),
    ("kem nathi", 9), ("thodu", 7), ("thodi", 7), ("vaar", 6),
    ("aavyo", 8), ("gayu", 7), ("karyo", 7), ("joyu", 7),
    ("khavanu", 8), ("pivanu", 8), ("jaavu", 8), ("aavvu", 8),
    ("shu vaatu", 9), ("kevi rite", 8), ("kyare", 7), ("kyathi", 7),
    ("shu thayu", 9), ("thayo", 7), ("thayi", 7),
]

_HINDI_MARKERS = [
    ("kaise ho", 10), ("kaise hain", 10), ("kya haal hai", 10),
    ("namaste", 8), ("namaskar", 8), ("shukriya", 8), ("dhanyawad", 9),
    ("aap", 7), ("main", 6), ("hum", 6), ("tum", 6), ("woh", 6),
    ("kya", 6), ("kyun", 7), ("kahan", 7), ("kab", 6), ("kaun", 7),
    ("mujhe", 8), ("tumhe", 8), ("unhe", 7), ("inhe", 7),
    ("hai", 5), ("hain", 6), ("tha", 5), ("thi", 5), ("the", 5),
    ("nahi", 5), ("nahin", 6), ("haan", 5), ("bilkul", 7),
    ("bahut", 7), ("thoda", 7), ("zyada", 7), ("kam", 5),
    ("achha", 7), ("accha", 7), ("theek", 7), ("theek hai", 9),
    ("kya kar rahe ho", 10), ("aap kya kar rahe hain", 10),
    ("mera naam", 8), ("tera naam", 8), ("apka naam", 8),
    ("khana", 7), ("paani", 7), ("ghar", 7), ("kaam", 6),
    ("bhai", 6), ("yaar", 6), ("dost", 6), ("pyaar", 7),
    ("suniye", 8), ("dekhiye", 8), ("samjhe", 7), ("batao", 7),
    ("chaliye", 8), ("chalo", 7), ("ruko", 7), ("aao", 7),
    ("kal", 6), ("aaj", 6), ("abhi", 7), ("phir", 6),
    ("lekin", 7), ("aur", 5), ("ya", 4), ("toh", 5), ("par", 5),
    ("matlab", 7), ("samajh", 7), ("pata", 6), ("malum", 7),
    ("sab theek", 9), ("kuch nahi", 8), ("koi baat nahi", 9),
]

_TAMIL_MARKERS = [
    ("vanakkam", 10), ("nandri", 10), ("eppadi irukkeenga", 10),
    ("eppadi irukeenga", 10), ("eppadi irukkinga", 10),
    ("naan", 8), ("nee", 7), ("avan", 7), ("aval", 7), ("avanga", 8),
    ("enna", 8), ("yenna", 8), ("enge", 8), ("eppo", 8), ("yeppo", 8),
    ("sollu", 8), ("paarunga", 8), ("vaanga", 8), ("poonga", 8),
    ("romba", 9), ("konjam", 8), ("nalla", 8), ("illa", 7),
    ("aamaa", 8), ("illai", 8), ("seri", 7), ("sari", 6),
    ("ungaluku", 9), ("enakku", 8), ("avanukku", 8),
    ("padam", 7), ("veedu", 7), ("ooru", 7), ("kadai", 7),
    ("saapadu", 8), ("thanni", 7), ("thambi", 8), ("akka", 7),
    ("anna", 6), ("amma", 6), ("appa", 6),
    ("theriyum", 8), ("theriyathu", 8), ("puriyuthu", 8),
]

_TELUGU_MARKERS = [
    ("namaskaram", 10), ("ela unnaru", 10), ("ela unnav", 10),
    ("meeru", 8), ("nenu", 8), ("vaadu", 7), ("aame", 7),
    ("emi", 7), ("ekkada", 8), ("eppudu", 8), ("ela", 6),
    ("cheppandi", 9), ("chudandi", 9), ("raandi", 8), ("velandi", 8),
    ("chala", 8), ("kooda", 7), ("ledu", 7), ("undi", 7),
    ("avunu", 8), ("kaadu", 8), ("sare", 7), ("okay", 4),
    ("meeru ela unnaru", 10), ("nenu bagunnanu", 9),
    ("mee peru", 8), ("naa peru", 8),
    ("intiki", 8), ("pani", 6), ("tindi", 7), ("neellu", 7),
    ("anna", 6), ("akka", 6), ("amma", 6), ("naanna", 7),
    ("telugu", 9), ("andhra", 8),
]

_KANNADA_MARKERS = [
    ("namaskara", 10), ("hegiddira", 10), ("hegiddeera", 10),
    ("nanu", 8), ("neevu", 8), ("avanu", 7), ("avalu", 7),
    ("enu", 7), ("elli", 8), ("yaavaga", 8), ("hege", 7),
    ("helri", 9), ("nodri", 9), ("banni", 8), ("hogi", 8),
    ("thumba", 9), ("swalpa", 8), ("illa", 7), ("ide", 7),
    ("haudu", 8), ("illa", 7), ("sari", 6), ("okay", 4),
    ("nimma", 8), ("nanna", 8), ("avana", 7),
    ("mane", 7), ("kelasa", 8), ("niru", 7), ("oota", 7),
    ("anna", 6), ("akka", 6), ("amma", 6), ("appa", 6),
    ("kannada", 9), ("karnataka", 8),
]

_MALAYALAM_MARKERS = [
    ("namaskaram", 10), ("sughamano", 10), ("sughamaano", 10),
    ("njan", 9), ("ningal", 9), ("avan", 7), ("aval", 7),
    ("enthu", 8), ("evide", 8), ("eppo", 7), ("engane", 8),
    ("paranju", 9), ("nokku", 8), ("vaa", 7), ("po", 6),
    ("valare", 9), ("oru", 6), ("illa", 7), ("und", 7),
    ("athe", 8), ("alla", 7), ("ente", 8), ("ningalude", 9),
    ("veedu", 7), ("pani", 6), ("vellam", 8), ("choru", 8),
    ("chechi", 8), ("chettan", 8), ("amma", 6), ("achan", 7),
    ("malayalam", 9), ("kerala", 8),
]

_PUNJABI_MARKERS = [
    ("sat sri akal", 12), ("sat shri akal", 12), ("kiddan", 10), ("ki haal hai", 10),
    ("tussi", 9), ("main", 6), ("oh", 5), ("assi", 8),
    ("ki", 5), ("kithe", 8), ("kaddon", 8), ("kaun", 7),
    ("dasso", 9), ("dekho", 8), ("aao", 7), ("jao", 7),
    ("bahut", 7), ("thoda", 7), ("nahi", 5), ("haan", 5),
    ("channga", 9), ("theek", 7), ("vadiya", 9),
    ("tera", 7), ("mera", 7), ("saada", 8), ("tuhada", 9),
    ("ghar", 7), ("kaam", 6), ("khana", 7), ("paani", 7),
    ("bhai", 6), ("yaar", 6), ("veere", 9), ("paaji", 9),
    ("punjabi", 9), ("punjab", 8),
]

_BENGALI_MARKERS = [
    ("namaskar", 9), ("kemon acho", 10), ("kemon achho", 10),
    ("ami", 8), ("tumi", 8), ("se", 6), ("apni", 8),
    ("ki", 5), ("kothay", 8), ("kokhon", 8), ("kemon", 8),
    ("bolo", 8), ("dekho", 7), ("esho", 8), ("jao", 7),
    ("onek", 8), ("ektu", 8), ("nei", 7), ("ache", 7),
    ("haan", 5), ("na", 4), ("thik", 7), ("thik ache", 9),
    ("tomar", 8), ("amar", 8), ("tar", 6),
    ("bari", 7), ("kaj", 6), ("khabar", 7), ("jol", 7),
    ("dada", 7), ("didi", 7), ("ma", 5), ("baba", 6),
    ("bangla", 9), ("bangladesh", 8), ("bengali", 8),
]

_URDU_MARKERS = [
    ("assalamu alaikum", 10), ("walaikum assalam", 10),
    ("aap kaise hain", 9), ("shukriya", 8), ("meherbani", 9),
    ("main", 6), ("aap", 7), ("woh", 6), ("hum", 6),
    ("kya", 6), ("kyun", 7), ("kahan", 7), ("kab", 6),
    ("nahi", 5), ("haan", 5), ("bilkul", 7), ("zaroor", 8),
    ("bahut", 7), ("thoda", 7), ("zyada", 7),
    ("achha", 7), ("theek", 7), ("theek hai", 9),
    ("khuda hafiz", 10), ("allah", 8), ("inshallah", 9),
    ("mashallah", 9), ("alhamdulillah", 9),
    ("janab", 9), ("sahib", 8), ("begum", 8),
    ("urdu", 9), ("pakistan", 8), ("lahore", 7),
]

_MARATHI_MARKERS = [
    ("kasa ahes", 10), ("tum kasa ahes", 10), ("tu kasa ahes", 10),
    ("tumhi kasa aahat", 10), ("kasa aahes", 10), ("kasa aahat", 10),
    ("namaskar", 8), ("dhanyawad", 8), ("aabhar", 9),
    ("mi", 7), ("tu", 6), ("tumhi", 8), ("aamhi", 9), ("to", 5),
    ("ahes", 9), ("aahes", 9), ("aahat", 8), ("hotay", 8), ("hoti", 7),
    ("kay", 8), ("kay karat ahes", 10), ("kay challey", 9),
    ("kuthe", 9), ("kadhi", 8), ("kasa", 8), ("kiti", 8),
    ("mala", 9), ("tula", 9), ("tyala", 8), ("tila", 8),
    ("nahi", 5), ("ho", 5), ("pan", 6), ("mhanun", 8),
    ("chala", 7), ("yeto", 8), ("jato", 7), ("bol", 7),
    ("bagh", 8), ("aik", 8), ("samajla", 8), ("samajli", 8),
    ("thik aahe", 9), ("sagla thik", 9), ("barach changla", 9),
    ("majha", 8), ("tujha", 8), ("majhi", 8), ("ghar", 6),
    ("marathi", 9), ("maharashtra", 8), ("pune", 7), ("mumbai", 6),
]

# Map language code → (markers_list, display_name, native_script)
_LANGUAGE_MARKERS = {
    "gu": (_GUJARATI_MARKERS, "Gujarati", "ગુજરાતી"),
    "hi": (_HINDI_MARKERS,    "Hindi",    "हिन्दी"),
    "mr": (_MARATHI_MARKERS,  "Marathi",  "मराठी"),
    "ta": (_TAMIL_MARKERS,    "Tamil",    "தமிழ்"),
    "te": (_TELUGU_MARKERS,   "Telugu",   "తెలుగు"),
    "kn": (_KANNADA_MARKERS,  "Kannada",  "ಕನ್ನಡ"),
    "ml": (_MALAYALAM_MARKERS,"Malayalam","മലയാളം"),
    "pa": (_PUNJABI_MARKERS,  "Punjabi",  "ਪੰਜਾਬੀ"),
    "bn": (_BENGALI_MARKERS,  "Bengali",  "বাংলা"),
    "ur": (_URDU_MARKERS,     "Urdu",     "اردو"),
}

# Minimum score to consider a detection valid
_MIN_SCORE = 8
# Minimum confidence ratio vs second-best to be decisive
_DECISIVE_RATIO = 1.5

# Common English words that overlap with Indic romanized tokens — whole-word only
_AMBIGUOUS_TOKENS = frozenset({
    "to", "is", "mi", "ho", "tu", "na", "ke", "pan", "or", "so", "no", "he", "we",
    "as", "at", "in", "on", "an", "am", "be", "do", "go", "ok", "okay",
})


def _marker_matches(clean: str, phrase: str) -> bool:
    """
    Match marker phrases using word boundaries to avoid false positives
    (e.g. 'mi' inside 'programming', 'is' inside 'this').
    """
    phrase = phrase.lower().strip()
    if not phrase:
        return False
    words = phrase.split()
    if len(words) == 1 and words[0] in _AMBIGUOUS_TOKENS:
        clean_words = set(clean.split())
        return words[0] in clean_words
    pattern = r"\b" + re.escape(phrase) + r"\b"
    return bool(re.search(pattern, clean))


def _looks_like_english_prose(text: str, best_score: float) -> bool:
    """Skip romanized detection for long English paragraphs unless score is very strong."""
    words = text.split()
    if len(words) < 6 or best_score >= 18:
        return False
    try:
        from langdetect import DetectorFactory, detect_langs
        DetectorFactory.seed = 0
        langs = detect_langs(text)
        if langs and langs[0].lang == "en" and float(langs[0].prob) > 0.88:
            return True
    except Exception:
        pass
    return False


def detect_romanized_language(text: str) -> dict | None:
    """
    Detect if `text` is Romanized Indian language.

    Returns dict with {code, name, native, display, confidence, score}
    or None if no Indian language detected with sufficient confidence.
    """
    if not text or not text.strip():
        return None

    text_lower = text.lower().strip()
    # Remove punctuation for matching
    clean = re.sub(r"[^\w\s]", " ", text_lower)
    clean = re.sub(r"\s+", " ", clean).strip()

    scores: dict[str, float] = {}

    for lang_code, (markers, name, native) in _LANGUAGE_MARKERS.items():
        total_score = 0.0
        for phrase, weight in markers:
            if _marker_matches(clean, phrase):
                # Multi-word phrases are stronger signals
                multiplier = 1.5 if " " in phrase else 1.0
                total_score += weight * multiplier

        if total_score > 0:
            scores[lang_code] = total_score

    if not scores:
        return None

    # Sort by score descending
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    best_code, best_score = ranked[0]

    if best_score < _MIN_SCORE:
        return None

    if _looks_like_english_prose(text, best_score):
        logger.debug(
            "Romanized detection skipped — English prose: %r (score=%.1f)",
            text[:50], best_score,
        )
        return None

    # Check decisiveness
    if len(ranked) > 1:
        second_score = ranked[1][1]
        if second_score > 0 and (best_score / second_score) < _DECISIVE_RATIO:
            # Ambiguous — lower confidence
            confidence = 0.55
        else:
            confidence = min(0.92, 0.65 + best_score * 0.008)
    else:
        confidence = min(0.92, 0.65 + best_score * 0.008)

    name, native = _LANGUAGE_MARKERS[best_code][1], _LANGUAGE_MARKERS[best_code][2]
    display = f"{name} ({native})"

    logger.info(
        "Romanized detection: %r → %s (score=%.1f, confidence=%.2f)",
        text[:50], best_code, best_score, confidence
    )

    return {
        "code":       best_code,
        "name":       name,
        "native":     native,
        "display":    display,
        "confidence": round(confidence, 2),
        "score":      best_score,
        "romanized":  True,
    }


def is_likely_romanized_indian(text: str) -> bool:
    """Quick check — returns True if text looks like Romanized Indian language."""
    return detect_romanized_language(text) is not None


# Common Romanized phrases → native script (improves Google Translate accuracy)
_PHRASE_NATIVE = {
    # Gujarati
    "tame kem cho":         "તમે કેમ છો",
    "kem cho":              "કેમ છો",
    "kem chho":             "કેમ છો",
    "majama":               "મજામાં",
    "maja ma":              "મજામાં",
    "shu karo cho":         "શું કરો છો",
    "tamne gamyu":          "તમને ગમ્યું",
    "shu naam chhe":        "શું નામ છે",
    "maru naam":            "મારું નામ",
    "kem nathi":            "કેમ નથી",
    "shu thayu":            "શું થયું",
    "ghanu saras":          "ઘણું સારસ",
    "aavjo":                "આવજો",
    "badhuj saras":         "બધુ જ સારસ",
    # Hindi
    "kaise ho":             "कैसे हो",
    "kaise hain":           "कैसे हैं",
    "kya haal hai":         "क्या हाल है",
    "namaste":              "नमस्ते",
    "namaskar":             "नमस्कार",
    "shukriya":             "शुक्रिया",
    "dhanyawad":            "धन्यवाद",
    "kya kar rahe ho":      "क्या कर रहे हो",
    # Marathi
    "tum kasa ahes":        "तुम कसा आहेस",
    "kasa ahes":            "कसा आहेस",
    "tumhi kasa aahat":     "तुम्ही कसे आहात",
    "kay karat ahes":       "काय करत आहेस",
    "thik aahe":            "ठीक आहे",
    "aap kya kar rahe ho":  "आप क्या कर रहे हो",
    "aap kya kar rahe hain":"आप क्या कर रहे हैं",
    "mera naam":            "मेरा नाम",
    "theek hai":            "ठीक है",
    "sab theek":            "सब ठीक",
    "kuch nahi":            "कुछ नहीं",
    "koi baat nahi":        "कोई बात नहीं",
    "bahut achha":          "बहुत अच्छा",
    "bahut badhiya":        "बहुत बढ़िया",
    "chaliye":              "चलिए",
    "suniye":               "सुनिए",
    "dekhiye":              "देखिए",
    # Tamil
    "vanakkam":             "வணக்கம்",
    "nandri":               "நன்றி",
    "romba nandri":         "ரொம்ப நன்றி",
    "eppadi irukkeenga":    "எப்படி இருக்கீங்க",
    "nalla irukken":        "நல்லா இருக்கேன்",
    # Telugu
    "namaskaram":           "నమస్కారం",
    "ela unnaru":           "ఎలా ఉన్నారు",
    "nenu bagunnanu":       "నేను బాగున్నాను",
    "dhanyavaadalu":        "ధన్యవాదాలు",
    # Kannada
    "hegiddira":            "ಹೇಗಿದ್ದೀರ",
    "chennagiddini":        "ಚೆನ್ನಾಗಿದ್ದೀನಿ",
    "dhanyavadagalu":       "ಧನ್ಯವಾದಗಳು",
    # Malayalam
    "sughamano":            "സുഖമാണോ",
    "njan sughamayi":       "ഞാൻ സുഖമായി",
    "nandri":               "നന്ദി",
    # Punjabi
    "sat sri akal":         "ਸਤ ਸ੍ਰੀ ਅਕਾਲ",
    "kiddan":               "ਕਿੱਦਾਂ",
    "channga":              "ਚੰਗਾ",
    "shukriya":             "ਸ਼ੁਕਰੀਆ",
    # Bengali
    "kemon acho":           "কেমন আছো",
    "kemon achho":          "কেমন আছো",
    "bhalo achi":           "ভালো আছি",
    "dhonnobad":            "ধন্যবাদ",
    "ami tomake bhalo bhashi": "আমি তোমাকে ভালোবাসি",
    "ami tomake bhalobashi": "আমি তোমাকে ভালোবাসি",
}

# Language code → indic-transliteration script constant
_LANG_TO_SCRIPT = {
    "gu": "gujarati",
    "hi": "devanagari",
    "mr": "devanagari",
    "ne": "devanagari",
    "sa": "devanagari",
    "bn": "bengali",
    "pa": "gurmukhi",
    "ta": "tamil",
    "te": "telugu",
    "kn": "kannada",
    "ml": "malayalam",
    "or": "oriya",
    "ur": "urdu",
}


def _is_still_romanized(text: str) -> bool:
    """True when text has no native Indic script characters."""
    return not any(0x0900 <= ord(c) <= 0x0D7F for c in text)


def romanize_to_native(text: str, lang_code: str) -> str:
    """
    Convert Romanized (ITRANS-style) text to native script using indic-transliteration.
    Returns original text when conversion is unavailable or fails.
    """
    if not text or not lang_code:
        return text
    script_name = _LANG_TO_SCRIPT.get(lang_code)
    if not script_name:
        return text
    try:
        from indic_transliteration import sanscript
        from indic_transliteration.sanscript import transliterate

        script_const = getattr(sanscript, script_name.upper(), None)
        if not script_const:
            return text
        native = transliterate(text, sanscript.ITRANS, script_const)
        if native and native.strip() and not _is_still_romanized(native):
            logger.debug(
                "ITRANS transliteration (%s): %r → %r",
                lang_code, text[:60], native[:60],
            )
            return native.strip()
    except ImportError:
        logger.warning("indic-transliteration not installed — skipping ITRANS conversion")
    except Exception as exc:
        logger.warning("ITRANS transliteration failed for %s: %s", lang_code, exc)
    return text


def normalize_romanized_text(text: str, lang_code: str | None = None) -> str:
    """
    Convert Romanized Indian text to native script before calling the translation API.

    Strategy:
    1. Exact / partial phrase dictionary lookup (highest accuracy for known phrases)
    2. ITRANS transliteration via indic-transliteration (covers arbitrary Romanized text)
    """
    if not text:
        return text
    lower = text.lower().strip()
    clean = re.sub(r"[^\w\s]", " ", lower)
    clean = re.sub(r"\s+", " ", clean).strip()

    # Exact full-text match first
    if clean in _PHRASE_NATIVE:
        result = _PHRASE_NATIVE[clean]
        logger.debug("Phrase dict (exact): %r → %r", text[:60], result[:60])
        return result

    # Partial phrase replacement (longest first)
    result = text
    replaced = False
    for phrase, native in sorted(_PHRASE_NATIVE.items(), key=lambda x: -len(x[0])):
        pattern = re.compile(re.escape(phrase), re.IGNORECASE)
        if pattern.search(result):
            result = pattern.sub(native, result)
            replaced = True

    if replaced and not _is_still_romanized(result):
        logger.debug("Phrase dict (partial): %r → %r", text[:60], result[:60])
        return result.strip() or text

    # ITRANS transliteration fallback for arbitrary Romanized text
    if lang_code and _is_still_romanized(result):
        transliterated = romanize_to_native(result, lang_code)
        if transliterated != result:
            logger.info(
                "Romanized → native script (%s): %r → %r",
                lang_code, text[:60], transliterated[:60],
            )
            return transliterated

    return result.strip() or text
