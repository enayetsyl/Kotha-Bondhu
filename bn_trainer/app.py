from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from rapidfuzz import fuzz

from . import asr, db, normalize, tts

load_dotenv()


def practice(*, seconds: float = 3.0, db_path: Optional[Path] = None) -> None:
    conn = db.get_connection(db_path)
    print(f"🎙️ Speak now (up to {seconds} seconds)...")
    transcript, audio_path = asr.capture_and_transcribe(seconds)
    norm = normalize.normalize_text(transcript)
    print(f"📝 Whisper heard: {transcript}")
    print(f"✅ Standard Bangla: {norm.normalized}")

    db.log_utterance(
        conn,
        role="child",
        transcript=transcript,
        normalized=norm.normalized,
        audio_path=str(audio_path),
    )
    db.log_utterance(
        conn,
        role="system",
        transcript=norm.sylheti_like,
        normalized=norm.normalized,
        meta=json.dumps({"mode": "practice"}, ensure_ascii=False),
    )
    db.upsert_phrase_pair(
        conn,
        sylheti=norm.sylheti_like,
        standard_bn=norm.normalized,
        source="from_child",
    )

    try:
        audio_file = tts.speak(norm.normalized)
        print(f"🔊 Played corrected line ({audio_file})")
    except tts.PiperError as err:
        print(f"⚠️ Piper not configured: {err}")

    print("✨ Logged to database!")


def exam(
    *,
    n: int = 5,
    seconds: float = 3.0,
    pass_mark: int = 85,
    level: Optional[int] = None,
    db_path: Optional[Path] = None,
) -> None:
    conn = db.get_connection(db_path)
    pairs = db.fetch_phrase_pairs(conn, limit=n, difficulty=level)
    if not pairs:
        print("❌ No phrase pairs available. Run practice mode first or insert pairs manually.")
        return

    print("🏁 Exam mode started! Answer in Standard Bangla.")
    total_score = 0.0
    earned_stars = 0

    for idx, pair in enumerate(pairs, start=1):
        prompt = pair["sylheti"]
        answer_key = pair["standard_bn"]
        print(f"\nQuestion {idx}/{len(pairs)}: {prompt}")
        db.log_utterance(
            conn,
            role="system",
            transcript=prompt,
            normalized=answer_key,
            meta=json.dumps({"mode": "exam", "question_index": idx}, ensure_ascii=False),
        )
        try:
            tts.speak(prompt)
        except tts.PiperError:
            print("(TTS unavailable – read the prompt aloud.)")
        transcript, audio_path = asr.capture_and_transcribe(seconds)
        normalized = normalize.normalize_text(transcript).normalized
        score = fuzz.ratio(normalized, answer_key)
        passed = score >= pass_mark
        stars = 1 if passed else 0
        total_score += score
        earned_stars += stars

        print(f"👂 You said: {transcript}")
        print(f"✅ Normalized: {normalized}")
        print(f"🎯 Target: {answer_key}")
        print(f"⭐ Score: {score:.1f} ({'pass' if passed else 'try again'})")

        db.log_utterance(
            conn,
            role="child",
            transcript=transcript,
            normalized=normalized,
            audio_path=str(audio_path),
            meta=json.dumps({"mode": "exam", "question": prompt}, ensure_ascii=False),
        )
        db.store_exam_result(
            conn,
            prompt_id=pair["id"],
            prompt=prompt,
            answer=normalized,
            score=score,
        )

    average = total_score / len(pairs)
    print("\n🏆 Exam finished!")
    print(f"Average score: {average:.1f}")
    print(f"Stars earned: {earned_stars} / {len(pairs)}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Sylheti to Standard Bangla speaking coach")
    parser.add_argument(
        "--db-path",
        type=Path,
        default=None,
        help="Path to the SQLite database (defaults to trainer.sqlite)",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    practice_parser = sub.add_parser("practice", help="Run practice mode")
    practice_parser.add_argument("--seconds", type=float, default=3.0, help="Recording duration")

    exam_parser = sub.add_parser("exam", help="Run exam mode")
    exam_parser.add_argument("-n", type=int, default=5, help="Number of questions")
    exam_parser.add_argument("--seconds", type=float, default=3.0, help="Recording duration")
    exam_parser.add_argument("--pass_mark", type=int, default=85, help="Score threshold for a star")
    exam_parser.add_argument("--level", type=int, help="Filter phrase pairs by difficulty")

    return parser


def main(argv: Optional[list[str]] = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.cmd == "practice":
        practice(seconds=args.seconds, db_path=args.db_path)
    elif args.cmd == "exam":
        exam(
            n=args.n,
            seconds=args.seconds,
            pass_mark=args.pass_mark,
            level=args.level,
            db_path=args.db_path,
        )


if __name__ == "__main__":
    main()
