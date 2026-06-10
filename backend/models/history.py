"""
models/history.py — SQLite persistence for VaaniSetu translation history.

Improvements:
- clear_all_translations() is now a proper model function (no inline import in route)
- get_all_translations() supports limit/offset pagination
- Thread-safe connection handling (check_same_thread=False)
- Consistent use of parameterised queries throughout
"""

import sqlite3
from datetime import datetime
from config import Config


def get_connection():
    conn = sqlite3.connect(Config.DATABASE_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS translations (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            original_text   TEXT    NOT NULL,
            translated_text TEXT    NOT NULL,
            source_lang     TEXT    NOT NULL,
            target_lang     TEXT    NOT NULL,
            tone            TEXT    DEFAULT 'professional',
            is_favorite     INTEGER DEFAULT 0,
            confidence      REAL    DEFAULT 0.95,
            created_at      TEXT    NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def _is_duplicate(conn, data: dict) -> bool:
    """Skip saving identical translation within the last 2 minutes."""
    row = conn.execute(
        """
        SELECT id FROM translations
        WHERE original_text = ? AND translated_text = ?
          AND source_lang = ? AND target_lang = ?
          AND datetime(created_at) > datetime('now', '-2 minutes')
        LIMIT 1
        """,
        (
            data["original_text"],
            data["translated_text"],
            data["source_lang"],
            data["target_lang"],
        ),
    ).fetchone()
    return row is not None


def save_translation(data: dict) -> int:
    conn = get_connection()
    if _is_duplicate(conn, data):
        conn.close()
        return 0
    cursor = conn.execute(
        """
        INSERT INTO translations
            (original_text, translated_text, source_lang, target_lang, tone, confidence, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            data["original_text"],
            data["translated_text"],
            data["source_lang"],
            data["target_lang"],
            data.get("tone", "professional"),
            data.get("confidence", 0.95),
            datetime.utcnow().isoformat(),
        ),
    )
    conn.commit()
    row_id = cursor.lastrowid
    conn.close()
    return row_id


def get_all_translations(
    search: str = "",
    favorite_only: bool = False,
    limit: int = 100,
    offset: int = 0,
) -> list[dict]:
    conn = get_connection()
    query = "SELECT * FROM translations WHERE 1=1"
    params: list = []

    if search:
        query += " AND (original_text LIKE ? OR translated_text LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])

    if favorite_only:
        query += " AND is_favorite = 1"

    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def toggle_favorite(translation_id: int):
    conn = get_connection()
    row = conn.execute(
        "SELECT is_favorite FROM translations WHERE id = ?", (translation_id,)
    ).fetchone()
    if not row:
        conn.close()
        return None
    new_value = 0 if row["is_favorite"] else 1
    conn.execute(
        "UPDATE translations SET is_favorite = ? WHERE id = ?",
        (new_value, translation_id),
    )
    conn.commit()
    conn.close()
    return new_value


def delete_translation(translation_id: int) -> None:
    conn = get_connection()
    conn.execute("DELETE FROM translations WHERE id = ?", (translation_id,))
    conn.commit()
    conn.close()


def clear_all_translations() -> int:
    """Delete all history rows. Returns the number of rows deleted."""
    conn = get_connection()
    cursor = conn.execute("DELETE FROM translations")
    count = cursor.rowcount
    conn.commit()
    conn.close()
    return count
