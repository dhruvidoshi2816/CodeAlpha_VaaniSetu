import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Security — MUST be overridden in production
    SECRET_KEY = os.getenv("SECRET_KEY")
    if not SECRET_KEY:
        import secrets
        SECRET_KEY = secrets.token_hex(32)

    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    TESSERACT_CMD  = os.getenv("TESSERACT_CMD", "")
    DATABASE_PATH  = os.path.join(os.path.dirname(__file__), "VaaniSetu.db")
    CORS_ORIGINS   = os.getenv("CORS_ORIGINS", "*")

    # Translation engine (free providers; no UI impact)
    LIBRETRANSLATE_URL = os.getenv(
        "LIBRETRANSLATE_URL", "https://libretranslate.de"
    ).rstrip("/")
    LIBRETRANSLATE_API_KEY = os.getenv("LIBRETRANSLATE_API_KEY", "")
    TRANSLATION_TIMEOUT = float(os.getenv("TRANSLATION_TIMEOUT", "12"))
    TRANSLATION_MAX_RETRIES = int(os.getenv("TRANSLATION_MAX_RETRIES", "2"))
    TRANSLATION_RETRY_BACKOFF = float(os.getenv("TRANSLATION_RETRY_BACKOFF", "0.45"))
    # Minimum milliseconds between outbound calls per provider (rate-limit guard)
    TRANSLATION_RATE_LIMIT_MS = int(os.getenv("TRANSLATION_RATE_LIMIT_MS", "80"))
    TRANSLATION_CACHE_MAX = int(os.getenv("TRANSLATION_CACHE_MAX", "800"))
