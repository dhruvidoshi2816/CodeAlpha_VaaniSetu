"""
ai_service.py — OpenAI-powered utilities for VaaniSetu.

Additions over original:
- rewrite_tone() — actually rewrites translated text in the requested tone
- All functions degrade gracefully when OPENAI_API_KEY is absent
- Timeout protection on every API call
- Structured error logging
"""

import logging
from config import Config

logger = logging.getLogger(__name__)

try:
    from openai import OpenAI
    _OPENAI_AVAILABLE = True
except ImportError:
    OpenAI = None
    _OPENAI_AVAILABLE = False


def _get_client():
    if not _OPENAI_AVAILABLE or not Config.OPENAI_API_KEY:
        return None
    try:
        # OpenAI v1.0+ has removed deprecated parameters like 'proxies'
        # Use modern SDK with stable httpx version
        return OpenAI(
            api_key=Config.OPENAI_API_KEY,
            timeout=30.0,
            max_retries=2,
        )
    except Exception as exc:
        logger.warning("Failed to initialize OpenAI client: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Grammar correction
# ---------------------------------------------------------------------------

def correct_grammar(text: str) -> dict:
    client = _get_client()
    if not client:
        return {
            "corrected_text": text,
            "used_ai": False,
            "message": "OpenAI API key not configured — grammar check skipped",
        }
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a grammar and spelling correction assistant. "
                        "Fix all grammar, spelling, and punctuation errors. "
                        "Preserve the original meaning, tone, and language. "
                        "Return ONLY the corrected text — no explanations."
                    ),
                },
                {"role": "user", "content": text},
            ],
            temperature=0.1,
            max_tokens=1024,
        )
        corrected = response.choices[0].message.content.strip()
        return {"corrected_text": corrected, "used_ai": True}
    except Exception as exc:
        logger.warning("Grammar correction failed: %s", exc)
        return {"corrected_text": text, "used_ai": False, "message": str(exc)}


# ---------------------------------------------------------------------------
# Summarisation
# ---------------------------------------------------------------------------

def summarize_text(text: str, max_sentences: int = 3) -> dict:
    client = _get_client()
    if not client:
        # Simple extractive fallback: first N sentences
        import re
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        summary = " ".join(sentences[:max_sentences])
        return {"summary": summary, "used_ai": False, "message": "OpenAI not configured"}
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"Summarise the following text in {max_sentences} sentences or fewer. "
                        "Preserve the key information. Return ONLY the summary."
                    ),
                },
                {"role": "user", "content": text},
            ],
            temperature=0.3,
            max_tokens=512,
        )
        summary = response.choices[0].message.content.strip()
        return {"summary": summary, "used_ai": True}
    except Exception as exc:
        logger.warning("Summarisation failed: %s", exc)
        import re
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        return {
            "summary": " ".join(sentences[:max_sentences]),
            "used_ai": False,
            "message": str(exc),
        }


# ---------------------------------------------------------------------------
# Tone rewriting  (NEW — was a stub before)
# ---------------------------------------------------------------------------

_TONE_SYSTEM_PROMPTS = {
    "formal": (
        "Rewrite the following text in a formal, polished tone. "
        "Use proper grammar, avoid contractions, and maintain a respectful register. "
        "Preserve the original meaning and language. Return ONLY the rewritten text."
    ),
    "casual": (
        "Rewrite the following text in a casual, conversational tone. "
        "Use natural everyday language, contractions are fine. "
        "Preserve the original meaning and language. Return ONLY the rewritten text."
    ),
    "friendly": (
        "Rewrite the following text in a warm, friendly, and approachable tone. "
        "Sound encouraging and positive. "
        "Preserve the original meaning and language. Return ONLY the rewritten text."
    ),
    "professional": (
        "Rewrite the following text in a clear, professional business tone. "
        "Be concise and direct. "
        "Preserve the original meaning and language. Return ONLY the rewritten text."
    ),
}


def rewrite_tone(text: str, tone: str, lang: str = "en") -> str:
    """
    Rewrite `text` in the requested tone.
    Returns the rewritten text, or the original if AI is unavailable.
    """
    client = _get_client()
    if not client:
        return text

    system_prompt = _TONE_SYSTEM_PROMPTS.get(tone, _TONE_SYSTEM_PROMPTS["professional"])

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text},
            ],
            temperature=0.4,
            max_tokens=1024,
        )
        return response.choices[0].message.content.strip()
    except Exception as exc:
        logger.warning("Tone rewrite failed (tone=%s): %s", tone, exc)
        return text


# ---------------------------------------------------------------------------
# Slang polishing
# ---------------------------------------------------------------------------

def polish_slang_with_ai(original: str, dictionary_result: str, mode: str) -> dict:
    client = _get_client()
    if not client:
        return {"polished_text": dictionary_result, "used_ai": False}

    if mode == "genz_to_plain":
        system = (
            "You translate Gen Z and internet slang into clear, plain English that parents "
            "and people from older generations can easily understand. "
            "Keep the same meaning and emotional intent. "
            "Do NOT add explanations or brackets. Return ONLY the translated text."
        )
    else:
        system = (
            "You rephrase plain, formal English into natural Gen Z friendly language that "
            "teens and young adults use today. Keep it authentic — not overdone or cringey. "
            "Use slang sparingly and naturally. Return ONLY the translated text."
        )

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {
                    "role": "user",
                    "content": (
                        f"Original:\n{original}\n\n"
                        f"Draft translation:\n{dictionary_result}"
                    ),
                },
            ],
            temperature=0.4,
            max_tokens=512,
        )
        polished = response.choices[0].message.content.strip()
        return {"polished_text": polished, "used_ai": True}
    except Exception as exc:
        logger.warning("Slang AI polish failed: %s", exc)
        return {"polished_text": dictionary_result, "used_ai": False}
