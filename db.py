"""SQLite helpers for the Sylheti → Standard Bangla speaking coach."""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Generator, Iterable, Optional

SCHEMA_FILE = Path(__file__).with_name("schema.sql")
DEFAULT_DB_PATH = Path("trainer.sqlite")


@dataclass
class Utterance:
    role: str
    transcript: str
    normalized: Optional[str] = None
    audio_path: Optional[str] = None
    meta: Optional[dict] = None


@dataclass
class PhrasePair:
    sylheti: str
    standard_bn: str
    source: str = "manual"
    difficulty: int = 1


@contextmanager
def connect(db_path: Path | str = DEFAULT_DB_PATH) -> Generator[sqlite3.Connection, None, None]:
    path = Path(db_path)
    conn = sqlite3.connect(path)
    try:
        conn.row_factory = sqlite3.Row
        yield conn
    finally:
        conn.commit()
        conn.close()


def init_db(db_path: Path | str = DEFAULT_DB_PATH) -> None:
    with connect(db_path) as conn:
        schema_sql = SCHEMA_FILE.read_text(encoding="utf-8")
        conn.executescript(schema_sql)


def log_utterance(utterance: Utterance, db_path: Path | str = DEFAULT_DB_PATH) -> int:
    with connect(db_path) as conn:
        cur = conn.execute(
            """
            INSERT INTO utterances (role, transcript, normalized, audio_path, meta)
            VALUES (:role, :transcript, :normalized, :audio_path, :meta)
            """,
            {
                "role": utterance.role,
                "transcript": utterance.transcript,
                "normalized": utterance.normalized,
                "audio_path": utterance.audio_path,
                "meta": json.dumps(utterance.meta) if utterance.meta else None,
            },
        )
        return int(cur.lastrowid)


def upsert_phrase_pair(pair: PhrasePair, db_path: Path | str = DEFAULT_DB_PATH) -> int:
    with connect(db_path) as conn:
        cur = conn.execute(
            """
            INSERT INTO phrase_pairs (sylheti, standard_bn, source, difficulty)
            VALUES (:sylheti, :standard_bn, :source, :difficulty)
            ON CONFLICT(sylheti, standard_bn) DO UPDATE SET
                source=excluded.source,
                difficulty=excluded.difficulty
            """,
            {
                "sylheti": pair.sylheti,
                "standard_bn": pair.standard_bn,
                "source": pair.source,
                "difficulty": pair.difficulty,
            },
        )
        return int(cur.lastrowid)


def get_phrase_pairs(db_path: Path | str = DEFAULT_DB_PATH, limit: Optional[int] = None) -> list[sqlite3.Row]:
    with connect(db_path) as conn:
        query = "SELECT * FROM phrase_pairs ORDER BY RANDOM()"
        if limit is not None:
            query += " LIMIT ?"
            rows = conn.execute(query, (limit,)).fetchall()
        else:
            rows = conn.execute(query).fetchall()
        return list(rows)


def create_exam(total_questions: int, pass_mark: int, db_path: Path | str = DEFAULT_DB_PATH) -> int:
    with connect(db_path) as conn:
        cur = conn.execute(
            "INSERT INTO exams (total_questions, pass_mark) VALUES (?, ?)",
            (total_questions, pass_mark),
        )
        return int(cur.lastrowid)


def finalize_exam(exam_id: int, score: int, notes: str | None = None, db_path: Path | str = DEFAULT_DB_PATH) -> None:
    with connect(db_path) as conn:
        conn.execute(
            "UPDATE exams SET score = ?, notes = ? WHERE id = ?",
            (score, notes, exam_id),
        )


def log_exam_result(
    exam_id: int,
    question: str,
    expected_answer: str,
    user_answer: str,
    score: float,
    is_pass: bool,
    db_path: Path | str = DEFAULT_DB_PATH,
) -> int:
    with connect(db_path) as conn:
        cur = conn.execute(
            """
            INSERT INTO exam_results (exam_id, question, expected_answer, user_answer, score, is_pass)
            VALUES (:exam_id, :question, :expected_answer, :user_answer, :score, :is_pass)
            """,
            {
                "exam_id": exam_id,
                "question": question,
                "expected_answer": expected_answer,
                "user_answer": user_answer,
                "score": score,
                "is_pass": 1 if is_pass else 0,
            },
        )
        return int(cur.lastrowid)


def recent_utterances(limit: int = 10, db_path: Path | str = DEFAULT_DB_PATH) -> Iterable[sqlite3.Row]:
    with connect(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM utterances ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return list(rows)
