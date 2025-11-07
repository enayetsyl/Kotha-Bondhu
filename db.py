"""SQLite helpers for the Sylheti ↔ Standard Bangla coach."""
from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import Iterable, Optional

DB_PATH = os.getenv("TRAINER_DB", "trainer.sqlite")


def get_conn() -> sqlite3.Connection:
    """Return a SQLite connection, creating tables on first run."""

    path = Path(DB_PATH)
    need_init = not path.exists()
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row

    if need_init:
        schema_path = Path(__file__).with_name("schema.sql")
        with schema_path.open("r", encoding="utf-8") as fh:
            conn.executescript(fh.read())
    return conn


def insert_utterance(
    conn: sqlite3.Connection,
    *,
    mode: str,
    speaker: str,
    audio_path: Optional[str],
    transcript_raw: Optional[str],
    normalized_bn: Optional[str],
    sylheti_guess: Optional[str],
    score: Optional[int],
    meta: Optional[str],
) -> None:
    """Insert a single utterance row."""

    keys = (
        "mode",
        "speaker",
        "audio_path",
        "transcript_raw",
        "normalized_bn",
        "sylheti_guess",
        "score",
        "meta",
    )
    values = [locals()[key] for key in keys]

    conn.execute(
        f"INSERT INTO utterances ({','.join(keys)}) VALUES (?,?,?,?,?,?,?,?)",
        values,
    )
    conn.commit()


def upsert_pair(
    conn: sqlite3.Connection,
    syl: str,
    std: str,
    *,
    source: str = "from_child",
) -> None:
    """Insert a Sylheti/Standard pair if it does not already exist."""

    try:
        conn.execute(
            "INSERT INTO phrase_pairs (sylheti, standard_bn, source) VALUES (?,?,?)",
            (syl, std, source),
        )
    except sqlite3.IntegrityError:
        pass
    conn.commit()


def sample_pairs_for_exam(
    conn: sqlite3.Connection,
    *,
    n: int = 10,
    level: Optional[int] = None,
) -> Iterable[sqlite3.Row]:
    """Return ``n`` phrase pairs ordered by least seen count."""

    query = "SELECT id, sylheti, standard_bn FROM phrase_pairs "
    params: tuple[object, ...] = ()

    if level:
        query += "WHERE difficulty=? "
        params = (level,)

    query += "ORDER BY seen_count ASC, id ASC LIMIT ?"
    params += (n,)

    rows = conn.execute(query, params).fetchall()
    ids = [row["id"] for row in rows]

    if ids:
        conn.executemany(
            "UPDATE phrase_pairs SET seen_count = seen_count + 1 WHERE id=?",
            [(i,) for i in ids],
        )
        conn.commit()

    return rows


__all__ = [
    "DB_PATH",
    "get_conn",
    "insert_utterance",
    "upsert_pair",
    "sample_pairs_for_exam",
]
