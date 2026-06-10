"""
document_service.py — Document extraction orchestration and long-text translation.
"""

from __future__ import annotations

import logging
import re

from services.translator import translate_text

logger = logging.getLogger(__name__)

MAX_CHUNK = 8_000
MAX_DOCUMENT_CHARS = 200_000


def _split_into_chunks(text: str, max_size: int = MAX_CHUNK) -> list[str]:
    """Split text on paragraph boundaries for translation chunks."""
    text = text.strip()
    if len(text) <= max_size:
        return [text]

    paragraphs = re.split(r"\n\s*\n", text)
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        extra = len(para) + (2 if current else 0)
        if current_len + extra > max_size and current:
            chunks.append("\n\n".join(current))
            current = [para]
            current_len = len(para)
        else:
            current.append(para)
            current_len += extra

    if current:
        chunks.append("\n\n".join(current))

    # Hard-split any chunk that is still too large (no paragraph breaks)
    final: list[str] = []
    for chunk in chunks:
        if len(chunk) <= max_size:
            final.append(chunk)
            continue
        for i in range(0, len(chunk), max_size):
            final.append(chunk[i : i + max_size])

    return final or [text[:max_size]]


def translate_document_text(
    text: str,
    source_lang: str = "auto",
    target_lang: str = "en",
) -> dict:
    """
    Translate document text, chunking long content while preserving API shape.
    """
    text = text.strip()
    if not text:
        raise ValueError("Document contains no text")

    if len(text) > MAX_DOCUMENT_CHARS:
        logger.warning(
            "Document truncated from %d to %d chars", len(text), MAX_DOCUMENT_CHARS,
        )
        text = text[:MAX_DOCUMENT_CHARS]

    chunks = _split_into_chunks(text)
    logger.info("Translating document in %d chunk(s), %d total chars", len(chunks), len(text))

    if len(chunks) == 1:
        return translate_text(chunks[0], source_lang, target_lang)

    translated_parts: list[str] = []
    first_result: dict | None = None
    total_confidence = 0.0

    for idx, chunk in enumerate(chunks):
        result = translate_text(chunk, source_lang, target_lang)
        translated_parts.append(result["translated_text"])
        total_confidence += result.get("confidence", 0.0)
        if first_result is None:
            first_result = result
        logger.debug("Chunk %d/%d translated via %s", idx + 1, len(chunks), result.get("provider"))

    merged = {
        **(first_result or {}),
        "translated_text": "\n\n".join(translated_parts),
        "confidence": round(total_confidence / len(chunks), 2),
        "chunks": len(chunks),
    }
    return merged
