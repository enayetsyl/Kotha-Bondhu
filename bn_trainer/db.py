from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import List, Optional

SCHEMA_PATH = Path(__file__).with_name("schema.sql")
DEFAULT_DB_PATH = Path(__file__).with_name("trainer.sqlite")


def get_connection(db_path: Path | str | None = None) -> sqlite3.Connection:
    path = Path(db_path) if db_path else DEFAULT_DB_PATH
    should_init = not path.exists()
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    if should_init:
        init_db(conn)
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    conn.executescript(schema_sql)
    conn.commit()


def log_utterance(
    conn: sqlite3.Connection,
    *,
    role: str,
    transcript: str,
    normalized: Optional[str] = None,
    audio_path: Optional[str] = None,
    meta: Optional[str] = None,
) -> int:
    cur = conn.execute(
        """
        INSERT INTO utterances (role, transcript, normalized, audio_path, meta)
        VALUES (?, ?, ?, ?, ?)
        """,
        (role, transcript, normalized, audio_path, meta),
    )
    conn.commit()
    return int(cur.lastrowid)


def upsert_phrase_pair(
    conn: sqlite3.Connection,
    *,
    sylheti: str,
    standard_bn: str,
    source: str = "from_child",
    difficulty: int = 1,
) -> int:
    cur = conn.execute(
        """
        INSERT INTO phrase_pairs (sylheti, standard_bn, source, difficulty)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(sylheti, standard_bn)
        DO UPDATE SET source=excluded.source, difficulty=excluded.difficulty
        """,
        (sylheti, standard_bn, source, difficulty),
    )
    conn.commit()
    return int(cur.lastrowid if cur.lastrowid else conn.execute(
        "SELECT id FROM phrase_pairs WHERE sylheti=? AND standard_bn=?",
        (sylheti, standard_bn),
    ).fetchone()[0])


def fetch_phrase_pairs(
    conn: sqlite3.Connection,
    *,
    limit: Optional[int] = None,
    difficulty: Optional[int] = None,
) -> List[sqlite3.Row]:
    query = "SELECT * FROM phrase_pairs"
    params: List[object] = []
    clauses: List[str] = []
    if difficulty is not None:
        clauses.append("difficulty=?")
        params.append(difficulty)
    if clauses:
        query += " WHERE " + " AND ".join(clauses)
    query += " ORDER BY RANDOM()"
    if limit:
        query += " LIMIT ?"
        params.append(limit)
    cur = conn.execute(query, params)
    return list(cur.fetchall())


def store_exam_result(
    conn: sqlite3.Connection,
    *,
    prompt_id: Optional[int],
    prompt: str,
    answer: str,
    score: float,
) -> int:
    cur = conn.execute(
        """
        INSERT INTO exam_results (prompt_id, prompt, answer, score)
        VALUES (?, ?, ?, ?)
        """,
        (prompt_id, prompt, answer, score),
    )
    conn.commit()
    return int(cur.lastrowid)


def fetch_recent_exams(
    conn: sqlite3.Connection,
    *,
    limit: int = 20,
) -> List[sqlite3.Row]:
    cur = conn.execute(
        "SELECT * FROM exam_results ORDER BY created_at DESC LIMIT ?",
        (limit,),
    )
    return list(cur.fetchall())


__all__ = [
    "DEFAULT_DB_PATH",
    "fetch_phrase_pairs",
    "fetch_recent_exams",
    "get_connection",
    "init_db",
    "log_utterance",
    "store_exam_result",
    "upsert_phrase_pair",
]
