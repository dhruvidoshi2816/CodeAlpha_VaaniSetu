"""
tessdata_manager.py — Auto-download missing Tesseract language packs.

When Gujarati/Hindi OCR packs are not installed with Tesseract, this module
downloads them from the official tessdata_fast repository into backend/tessdata/
and configures TESSDATA_PREFIX so OCR works without manual installer steps.
"""

from __future__ import annotations

import logging
import os
import shutil
from pathlib import Path

import requests

from config import Config

logger = logging.getLogger(__name__)

# Official lightweight traineddata (Google / Tesseract project)
_TESSDATA_BASE_URL = "https://github.com/tesseract-ocr/tessdata_fast/raw/main"

# Bundled tessdata lives at backend/tessdata/*.traineddata
_BACKEND_DIR = Path(__file__).resolve().parent.parent
_BUNDLED_TESSDATA = _BACKEND_DIR / "tessdata"

# Languages to pre-fetch for Indian document OCR (auto mode)
_INDIC_TESSDATA = (
    "eng", "guj", "hin", "mar", "ben", "pan", "tam", "tel", "kan", "mal", "urd", "ori",
)


def _system_tessdata_dir() -> Path | None:
    """Return the system tessdata directory if Tesseract is installed."""
    candidates: list[Path] = []
    if Config.TESSERACT_CMD:
        candidates.append(Path(Config.TESSERACT_CMD).resolve().parent / "tessdata")
    which = shutil.which("tesseract")
    if which:
        candidates.append(Path(which).resolve().parent / "tessdata")
    candidates.append(Path(r"C:\Program Files\Tesseract-OCR\tessdata"))

    for path in candidates:
        if path.is_dir() and any(path.glob("*.traineddata")):
            return path
    return None


def _download_traineddata(lang: str, dest: Path) -> bool:
    """Download a single .traineddata file. Returns True on success."""
    url = f"{_TESSDATA_BASE_URL}/{lang}.traineddata"
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(".traineddata.part")

    try:
        logger.info("Downloading Tesseract language pack: %s → %s", lang, dest)
        resp = requests.get(url, timeout=120, stream=True)
        resp.raise_for_status()

        with open(tmp, "wb") as fh:
            for chunk in resp.iter_content(chunk_size=65536):
                if chunk:
                    fh.write(chunk)

        if tmp.stat().st_size < 1024:
            tmp.unlink(missing_ok=True)
            logger.error("Downloaded %s traineddata is too small — corrupt?", lang)
            return False

        tmp.replace(dest)
        logger.info("Installed Tesseract pack: %s (%.1f MB)", lang, dest.stat().st_size / 1e6)
        return True
    except Exception as exc:
        logger.error("Failed to download %s traineddata: %s", lang, exc)
        tmp.unlink(missing_ok=True)
        return False


def _has_traineddata(directory: Path, lang: str) -> bool:
    path = directory / f"{lang}.traineddata"
    return path.is_file() and path.stat().st_size > 1024


def ensure_tesseract_langs(tess_langs: set[str]) -> None:
    """
    Ensure requested Tesseract language packs exist.
    Tries system tessdata first, then downloads to backend/tessdata/.
    """
    needed = {l for l in tess_langs if l and l != "osd"}
    if not needed:
        return

    system_dir = _system_tessdata_dir()
    missing = set()

    for lang in needed:
        if system_dir and _has_traineddata(system_dir, lang):
            continue
        if _has_traineddata(_BUNDLED_TESSDATA, lang):
            continue
        missing.add(lang)

    if not missing:
        _sync_system_packs_to_bundled(system_dir, needed)
        _apply_tessdata_prefix(system_dir, _BUNDLED_TESSDATA)
        return

    # Try writing to system dir (installer location) when permitted
    for lang in list(missing):
        if system_dir:
            dest = system_dir / f"{lang}.traineddata"
            try:
                if _download_traineddata(lang, dest):
                    missing.discard(lang)
                    continue
            except PermissionError:
                logger.info("No write access to system tessdata — using bundled folder")

    # Download remaining to bundled tessdata
    for lang in list(missing):
        dest = _BUNDLED_TESSDATA / f"{lang}.traineddata"
        if _download_traineddata(lang, dest):
            missing.discard(lang)

    # When using bundled data, ensure eng is present (required baseline)
    if missing and not _has_traineddata(_BUNDLED_TESSDATA, "eng"):
        _download_traineddata("eng", _BUNDLED_TESSDATA / "eng.traineddata")

    _sync_system_packs_to_bundled(system_dir, needed)
    _apply_tessdata_prefix(system_dir, _BUNDLED_TESSDATA)

    if missing:
        logger.warning("Could not obtain Tesseract packs: %s", ", ".join(sorted(missing)))


def _sync_system_packs_to_bundled(system_dir: Path | None, langs: set[str]) -> None:
    """Copy packs from system tessdata into bundled folder when missing there."""
    if not system_dir or not system_dir.is_dir():
        return
    _BUNDLED_TESSDATA.mkdir(parents=True, exist_ok=True)
    for lang in langs:
        if _has_traineddata(_BUNDLED_TESSDATA, lang):
            continue
        src = system_dir / f"{lang}.traineddata"
        if src.is_file():
            try:
                shutil.copy2(src, _BUNDLED_TESSDATA / f"{lang}.traineddata")
                logger.info("Copied system tessdata pack: %s", lang)
            except Exception as exc:
                logger.debug("Could not copy %s: %s", lang, exc)


def _apply_tessdata_prefix(system_dir: Path | None, bundled_dir: Path) -> None:
    """
    Point Tesseract at bundled tessdata when it has packs the system dir lacks.

    On Windows (UB Mannheim) builds, TESSDATA_PREFIX must be the folder that
    directly contains *.traineddata files (e.g. backend/tessdata/), not its parent.
    """
    if not bundled_dir.is_dir() or not any(bundled_dir.glob("*.traineddata")):
        return

    bundled_langs = {p.stem for p in bundled_dir.glob("*.traineddata")}
    system_langs = set()
    if system_dir and system_dir.is_dir():
        system_langs = {p.stem for p in system_dir.glob("*.traineddata")}

    # Use bundled prefix when it adds languages beyond system install
    if bundled_langs - system_langs:
        prefix = str(bundled_dir.resolve())
        os.environ["TESSDATA_PREFIX"] = prefix
        logger.info(
            "Using bundled tessdata at %s (packs: %s)",
            bundled_dir, ", ".join(sorted(bundled_langs)[:8]),
        )
    elif "TESSDATA_PREFIX" in os.environ and Path(os.environ["TESSDATA_PREFIX"]).resolve() == bundled_dir.resolve():
        # System install now covers everything — drop override
        del os.environ["TESSDATA_PREFIX"]


def ensure_for_ocr(source_lang: str | None = None) -> None:
    """Download language packs needed for a given OCR request."""
    from services.ocr_lang_map import ISO_TO_TESSERACT

    langs = set(_INDIC_TESSDATA)

    if source_lang and source_lang.strip().lower() not in ("auto", ""):
        mapped = ISO_TO_TESSERACT.get(source_lang.strip())
        if mapped:
            langs.add(mapped)

    ensure_tesseract_langs(langs)


def invalidate_lang_cache() -> None:
    """Clear cached installed-language list (call after downloading packs)."""
    try:
        from services import ocr_service
        ocr_service._INSTALLED_LANGS = None
    except Exception:
        pass
