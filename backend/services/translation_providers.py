"""
translation_providers.py — Multi-provider translation backends for VaaniSetu.

Priority order (enforced by translator._translate_with_fallback):
  1. Google Translate (JSON API, then deep-translator scrape)
  2. LibreTranslate (configurable public/self-hosted instance)
  3. MyMemory
  4. Caller returns original text when all fail

Each provider implements: timeout, retries with backoff, rate-limit spacing, structured logging.
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass
from typing import Callable

import requests
from deep_translator import GoogleTranslator, MyMemoryTranslator
from deep_translator.exceptions import LanguageNotSupportedException

from config import Config

logger = logging.getLogger(__name__)

# Locale-style codes for MyMemory
MYMEMORY_CODE_MAP = {
    "gu": "gu-IN", "hi": "hi-IN", "bn": "bn-IN", "ta": "ta-IN",
    "te": "te-IN", "kn": "kn-IN", "ml": "ml-IN", "pa": "pa-IN",
    "mr": "mr-IN", "or": "or-IN", "ur": "ur-PK", "en": "en-GB",
    "es": "es-ES", "fr": "fr-FR", "de": "de-DE", "pt": "pt-PT",
    "ja": "ja-JP", "ko": "ko-KR", "zh-CN": "zh-CN", "zh-TW": "zh-TW",
}

GOOGLE_JSON_URL = "https://translate.googleapis.com/translate_a/single"

_lock = threading.Lock()
_last_call: dict[str, float] = {}


@dataclass
class ProviderResult:
    text: str | None
    provider: str
    error: str | None = None


def _rate_limit_wait(provider_key: str) -> None:
    """Enforce minimum spacing between calls to the same provider."""
    min_gap = Config.TRANSLATION_RATE_LIMIT_MS / 1000.0
    if min_gap <= 0:
        return
    with _lock:
        now = time.monotonic()
        last = _last_call.get(provider_key, 0.0)
        wait = min_gap - (now - last)
        if wait > 0:
            time.sleep(wait)
        _last_call[provider_key] = time.monotonic()


def _with_retries(
    provider_key: str,
    fn: Callable[[], str | None],
) -> str | None:
    """Run provider call with rate limiting and exponential backoff retries."""
    max_attempts = max(1, Config.TRANSLATION_MAX_RETRIES + 1)
    backoff = Config.TRANSLATION_RETRY_BACKOFF

    for attempt in range(max_attempts):
        _rate_limit_wait(provider_key)
        try:
            result = fn()
            if result and result.strip():
                return result.strip()
        except LanguageNotSupportedException:
            raise
        except Exception as exc:
            logger.warning(
                "%s attempt %d/%d failed: %s",
                provider_key, attempt + 1, max_attempts, exc,
            )
        if attempt < max_attempts - 1:
            time.sleep(backoff * (attempt + 1))
    return None


# Provider error patterns — must never be shown as translated text
_PROVIDER_ERROR_PATTERNS = (
    "invalid source language",
    "invalid target language",
    "langpair=",
    "query length limit",
    "mymemory warning",
    "invalid language",
    "language pair",
    "quota exceeded",
    "rate limit",
    "daily limit",
)


def is_provider_error(text: str | None) -> bool:
    """True when text is an API error message, not a real translation."""
    if not text:
        return True
    lower = text.lower().strip()
    if lower.startswith("'") and "invalid" in lower:
        return True
    return any(p in lower for p in _PROVIDER_ERROR_PATTERNS)


def is_valid_translation(
    original: str,
    translated: str | None,
    provider: str = "",
) -> bool:
    """Reject empty, error, or identity translations."""
    if not translated or not translated.strip():
        return False
    if is_provider_error(translated):
        logger.warning("Provider error rejected as translation: %r", translated[:80])
        return False
    orig = original.strip()
    trans = translated.strip()
    if orig == trans:
        return False
    # Google often returns transliterated greetings with different casing only
    # (e.g. sat sri akal → Sat Sri Akal) — accept from trusted providers
    if orig.lower() == trans.lower() and provider in (
        "google_json", "google", "mymemory", "libretranslate",
    ):
        return True
    if orig.lower() == trans.lower():
        return False
    return True


def to_mymemory_code(code: str) -> str:
    return MYMEMORY_CODE_MAP.get(code, code)


def translate_google_json(text: str, source: str, target: str) -> ProviderResult:
    """Primary Google path — unofficial JSON endpoint (closest to Google Translate web)."""

    def _call() -> str | None:
        params = {
            "client": "gtx",
            "sl": source,
            "tl": target,
            "dt": "t",
            "q": text,
        }
        resp = requests.get(
            GOOGLE_JSON_URL,
            params=params,
            timeout=Config.TRANSLATION_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        if not data or not data[0]:
            return None
        parts = [chunk[0] for chunk in data[0] if chunk and chunk[0]]
        return "".join(parts).strip() or None

    try:
        out = _with_retries("google_json", _call)
        return ProviderResult(out, "google_json")
    except LanguageNotSupportedException as exc:
        raise ValueError(f"Language not supported: {exc}") from exc
    except Exception as exc:
        logger.warning("Google JSON failed (sl=%s tl=%s): %s", source, target, exc)
        return ProviderResult(None, "google_json", str(exc))


def translate_google_scrape(text: str, source: str, target: str) -> ProviderResult:
    """Secondary Google path via deep-translator HTML scraper."""

    def _call() -> str | None:
        return GoogleTranslator(source=source, target=target).translate(text)

    try:
        out = _with_retries("google", _call)
        return ProviderResult(out, "google")
    except LanguageNotSupportedException as exc:
        raise ValueError(f"Language not supported: {exc}") from exc
    except Exception as exc:
        logger.warning("Google scrape failed (sl=%s tl=%s): %s", source, target, exc)
        return ProviderResult(None, "google", str(exc))


def translate_libre(text: str, source: str, target: str) -> ProviderResult:
    """LibreTranslate REST API (Priority 2)."""
    base = Config.LIBRETRANSLATE_URL
    if not base:
        return ProviderResult(None, "libretranslate", "LIBRETRANSLATE_URL not set")

    url = f"{base}/translate"
    sl = source if source != "auto" else "auto"
    payload: dict = {
        "q": text,
        "source": sl,
        "target": target,
        "format": "text",
    }
    if Config.LIBRETRANSLATE_API_KEY:
        payload["api_key"] = Config.LIBRETRANSLATE_API_KEY

    def _call() -> str | None:
        resp = requests.post(
            url,
            json=payload,
            timeout=Config.TRANSLATION_TIMEOUT,
            headers={"Content-Type": "application/json"},
        )
        if resp.status_code == 429:
            logger.warning("LibreTranslate rate limited (429)")
            return None
        resp.raise_for_status()
        data = resp.json()
        translated = data.get("translatedText") or data.get("translation")
        return (translated or "").strip() or None

    try:
        out = _with_retries("libretranslate", _call)
        return ProviderResult(out, "libretranslate")
    except Exception as exc:
        logger.warning("LibreTranslate failed (sl=%s tl=%s): %s", source, target, exc)
        return ProviderResult(None, "libretranslate", str(exc))


def translate_mymemory(text: str, source: str, target: str) -> ProviderResult:
    """MyMemory aggregator (Priority 3). Never accepts source=auto."""
    if source == "auto":
        logger.debug("MyMemory skipped — source=auto is unsupported")
        return ProviderResult(None, "mymemory", "auto source not supported")

    mm_source = to_mymemory_code(source)
    mm_target = to_mymemory_code(target)

    def _call() -> str | None:
        result = MyMemoryTranslator(source=mm_source, target=mm_target).translate(text)
        if result and is_provider_error(result):
            logger.warning("MyMemory returned error text: %r", result[:80])
            return None
        return result

    try:
        out = _with_retries("mymemory", _call)
        return ProviderResult(out, "mymemory")
    except Exception as exc:
        logger.warning(
            "MyMemory failed (sl=%s tl=%s): %s", mm_source, mm_target, exc,
        )
        return ProviderResult(None, "mymemory", str(exc))


def detect_language_google(text: str) -> tuple[str | None, float]:
    """
    Lightweight detection via Google translate endpoint (sl=auto).
    Returns (language_code, confidence_estimate) or (None, 0).
    """
    try:
        _rate_limit_wait("google_detect")
        params = {
            "client": "gtx",
            "sl": "auto",
            "tl": "en",
            "dt": "t",
            "q": text[:500],
        }
        resp = requests.get(
            GOOGLE_JSON_URL,
            params=params,
            timeout=min(Config.TRANSLATION_TIMEOUT, 8),
        )
        resp.raise_for_status()
        data = resp.json()
        if len(data) > 2 and data[2]:
            code = str(data[2]).lower()
            # Google sometimes returns zh-CN style codes
            return code, 0.78
    except Exception as exc:
        logger.debug("Google detect failed: %s", exc)
    return None, 0.0
