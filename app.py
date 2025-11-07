"""Command line interface for the Sylheti → Standard Bangla speaking coach."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict, Iterable

from dotenv import load_dotenv
from rapidfuzz import fuzz

from asr import record, transcribe
from db import get_conn, insert_utterance, sample_pairs_for_exam, upsert_pair
from normalize import to_standard_bn, to_sylheti_like
from tts import PiperConfigurationError, speak_and_save

load_dotenv()

AUDIO_DIR = Path(os.getenv("AUDIO_DIR", "./data/audio"))
AUDIO_DIR.mkdir(parents=True, exist_ok=True)


def save_child_take(
    raw_bn: str,
    norm_bn: str,
    *,
    audio_path: str | None = None,
    meta: Dict[str, Any] | None = None,
) -> None:
    """Persist a child's practice utterance and grow the phrase bank."""

    conn = get_conn()

    insert_utterance(
        conn,
        mode="practice",
        speaker="child",
        audio_path=audio_path,
        transcript_raw=raw_bn,
        normalized_bn=norm_bn,
        sylheti_guess=None,
        score=None,
        meta=json.dumps(meta or {}),
    )

    syl_guess = to_sylheti_like(norm_bn)
    upsert_pair(conn, syl_guess, norm_bn, source="from_child")


def practice(seconds: int = 3) -> None:
    """Run the practice loop."""

    print("🎤 বলুন… (মাইকে ৩ সেকেন্ড)")
    audio, fs = record(seconds)
    raw = transcribe(audio, language="bn")
    if not raw:
        print("কিছুই ধরা পড়েনি, আবার বলুন.")
        return

    norm = to_standard_bn(raw)
    print(f"আপনি বললেন (ASR): {raw}\nপ্রমিত রূপ: {norm}")

    try:
        speak_and_save(norm, prefix="practice")
    except PiperConfigurationError as exc:  # pragma: no cover - runtime config
        print(f"[TTS unavailable] {exc}")

    save_child_take(raw, norm, meta={"fs": fs})


def _log_exam_turn(
    *,
    syl_prompt: str,
    expected: str,
    heard: str,
    normalized: str,
    score: int,
    prompt_audio: Path | None,
) -> None:
    conn = get_conn()

    insert_utterance(
        conn,
        mode="exam",
        speaker="system",
        audio_path=str(prompt_audio) if prompt_audio else None,
        transcript_raw=syl_prompt,
        normalized_bn=None,
        sylheti_guess=None,
        score=None,
        meta=json.dumps({}),
    )
    insert_utterance(
        conn,
        mode="exam",
        speaker="child",
        audio_path=None,
        transcript_raw=heard,
        normalized_bn=normalized,
        sylheti_guess=syl_prompt,
        score=score,
        meta=json.dumps({"expected": expected}),
    )


def exam(
    *,
    n: int = 5,
    level: int | None = None,
    seconds: int = 3,
    pass_mark: int = 85,
) -> None:
    """Conduct an exam session using stored phrase pairs."""

    conn = get_conn()
    items = sample_pairs_for_exam(conn, n=n, level=level)
    if not items:
        print("ফ্রেইজ ব্যাংক খালি। আগে প্র্যাকটিস করুন বা ম্যানুয়ালি কিছু pair যোগ করুন.")
        return

    total = 0
    for index, row in enumerate(items, start=1):
        syl = row["sylheti"]
        std = row["standard_bn"]

        print("\nপ্রশ্ন {}/{}".format(index, n))
        print("সিলেটি শোনান হচ্ছে… (প্রমিত বাংলায় বলুন)")
        prompt_audio = None
        try:
            prompt_audio = speak_and_save(syl, prefix="exam")
        except PiperConfigurationError as exc:  # pragma: no cover - runtime config
            print(f"[TTS unavailable] {exc}")

        audio, _ = record(seconds)
        heard = transcribe(audio, language="bn")
        norm = to_standard_bn(heard)

        score = int(fuzz.token_set_ratio(norm, std))
        badge = "⭐" if score >= pass_mark else ("✅" if score >= 70 else "🙂")

        print(f"আপনি বললেন: {norm}")
        print(f"উত্তর হওয়া উচিত: {std}")
        print(f"স্কোর: {score} {badge}")

        total += score
        _log_exam_turn(
            syl_prompt=syl,
            expected=std,
            heard=heard,
            normalized=norm,
            score=score,
            prompt_audio=prompt_audio,
        )

    avg = round(total / max(1, len(items)), 1)
    print(f"\nমোট গড় স্কোর: {avg}")


def main(argv: Iterable[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Sylheti→Standard Bangla Coach")
    sub = parser.add_subparsers(dest="cmd")

    practice_parser = sub.add_parser("practice")
    practice_parser.add_argument("--seconds", type=int, default=3)

    exam_parser = sub.add_parser("exam")
    exam_parser.add_argument("-n", type=int, default=5)
    exam_parser.add_argument("--level", type=int, choices=[1, 2, 3])
    exam_parser.add_argument("--seconds", type=int, default=3)
    exam_parser.add_argument("--pass_mark", type=int, default=85)

    args = parser.parse_args(argv)
    if args.cmd == "exam":
        exam(n=args.n, level=args.level, seconds=args.seconds, pass_mark=args.pass_mark)
    else:
        practice(seconds=getattr(args, "seconds", 3))


if __name__ == "__main__":
    main()
