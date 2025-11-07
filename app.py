"""CLI entry point for the Sylheti → Standard Bangla speaking coach."""
from __future__ import annotations

import argparse
import logging
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from rapidfuzz import fuzz

import db
from asr import ASREngine, TranscriptionResult, pretty_segments, record_audio, save_wave
from db import PhrasePair, Utterance
from normalize import normalize_to_standard, to_sylheti_like
from tts import speak

LOGGER = logging.getLogger(__name__)


@dataclass
class Settings:
    whisper_model_size: str = "small"
    whisper_compute_type: str = "int8"
    db_path: Path = Path("trainer.sqlite")
    save_audio: bool = True
    audio_dir: Path = Path("data/audio")
    piper_bin: Optional[Path] = None
    piper_model: Optional[Path] = None
    piper_config: Optional[Path] = None
    pass_mark: int = 85


def load_settings() -> Settings:
    load_dotenv()
    settings = Settings()
    settings.whisper_model_size = os.getenv("WHISPER_MODEL_SIZE", settings.whisper_model_size)
    settings.whisper_compute_type = os.getenv("WHISPER_COMPUTE_TYPE", settings.whisper_compute_type)
    settings.db_path = Path(os.getenv("DB_PATH", str(settings.db_path)))
    settings.save_audio = os.getenv("SAVE_AUDIO", "true").lower() in {"1", "true", "yes"}
    settings.audio_dir = Path(os.getenv("AUDIO_DIR", str(settings.audio_dir)))
    piper_bin = os.getenv("PIPER_BIN")
    piper_model = os.getenv("PIPER_MODEL")
    piper_config = os.getenv("PIPER_CONFIG")
    if piper_bin and piper_model and piper_config:
        settings.piper_bin = Path(piper_bin)
        settings.piper_model = Path(piper_model)
        settings.piper_config = Path(piper_config)
    settings.pass_mark = int(os.getenv("PASS_MARK", settings.pass_mark))
    return settings


def ensure_db(settings: Settings) -> None:
    LOGGER.debug("Ensuring database exists at %s", settings.db_path)
    db.init_db(settings.db_path)


def ensure_tts_ready(settings: Settings) -> bool:
    if not (settings.piper_bin and settings.piper_model and settings.piper_config):
        LOGGER.warning("Piper paths missing. Configure PIPER_BIN, PIPER_MODEL, PIPER_CONFIG in .env to enable speech playback.")
        return False
    return True


def transcribe_once(engine: ASREngine, seconds: float, *, save_path: Optional[Path]) -> tuple[TranscriptionResult, Optional[Path]]:
    LOGGER.info("Listening for %.1f seconds...", seconds)
    audio = record_audio(seconds)
    wav_path: Optional[Path] = None
    if save_path:
        wav_path = save_path
        save_wave(audio, wav_path)
    result = engine.transcribe(audio)
    LOGGER.info("Heard: %s", result.text)
    return result, wav_path


def practice(seconds: float, settings: Settings) -> None:
    ensure_db(settings)
    engine = ASREngine(settings.whisper_model_size, settings.whisper_compute_type)
    audio_path = (
        settings.audio_dir / "practice" / f"utterance_{settings.db_path.stem}_{int(time.time())}.wav"
        if settings.save_audio
        else None
    )
    result, wav_path = transcribe_once(engine, seconds, save_path=audio_path)
    print(pretty_segments(result))
    normalized = normalize_to_standard(result.text)
    print(f"→ Normalized: {normalized}")
    utterance_id = db.log_utterance(
        Utterance(
            role="child",
            transcript=result.text,
            normalized=normalized,
            audio_path=str(wav_path) if wav_path else None,
        ),
        db_path=settings.db_path,
    )
    print(f"Logged utterance #{utterance_id}")
    syl_guess = to_sylheti_like(normalized)
    db.upsert_phrase_pair(
        PhrasePair(sylheti=syl_guess, standard_bn=normalized, source="from_child", difficulty=1),
        db_path=settings.db_path,
    )
    if ensure_tts_ready(settings):
        speak(
            normalized,
            piper_bin=settings.piper_bin,
            model_path=settings.piper_model,
            config_path=settings.piper_config,
        )



def exam(n: int, seconds: float, pass_mark: int, settings: Settings) -> None:
    ensure_db(settings)
    tts_available = ensure_tts_ready(settings)
    pairs = db.get_phrase_pairs(db_path=settings.db_path, limit=n)
    if not pairs:
        raise RuntimeError("No phrase pairs found. Run a few practice sessions first or insert pairs manually.")
    engine = ASREngine(settings.whisper_model_size, settings.whisper_compute_type)
    exam_id = db.create_exam(total_questions=n, pass_mark=pass_mark, db_path=settings.db_path)
    print(f"Starting exam #{exam_id} with {n} questions. Pass mark: {pass_mark}")
    total_score = 0
    for idx, pair in enumerate(pairs, start=1):
        sylheti = pair["sylheti"]
        expected = pair["standard_bn"]
        print(f"Question {idx}/{n}: {sylheti}")
        if tts_available and settings.piper_bin and settings.piper_model and settings.piper_config:
            speak(
                sylheti,
                piper_bin=settings.piper_bin,
                model_path=settings.piper_model,
                config_path=settings.piper_config,
                playback=True,
            )
        else:
            print("(TTS disabled)")
        print("Speak now!")
        result, wav_path = transcribe_once(
            engine,
            seconds,
            save_path=settings.audio_dir / "exam" / f"exam_{exam_id}_q{idx}.wav" if settings.save_audio else None,
        )
        normalized = normalize_to_standard(result.text)
        score = fuzz.ratio(normalized, expected)
        total_score += score
        passed = score >= pass_mark
        print(f"Heard: {normalized} (score={score:0.1f}) -> {'PASS' if passed else 'retry'}")
        db.log_exam_result(
            exam_id,
            question=sylheti,
            expected_answer=expected,
            user_answer=normalized,
            score=score,
            is_pass=passed,
            db_path=settings.db_path,
        )
        db.log_utterance(
            Utterance(
                role="child",
                transcript=result.text,
                normalized=normalized,
                audio_path=str(wav_path) if wav_path else None,
                meta={"exam_id": exam_id, "question": idx},
            ),
            db_path=settings.db_path,
        )
    average_score = int(total_score / n) if n else 0
    db.finalize_exam(exam_id, score=average_score, db_path=settings.db_path)
    print(f"Exam complete! Average score: {average_score}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    practice_parser = subparsers.add_parser("practice", help="Run practice mode")
    practice_parser.add_argument("--seconds", type=float, default=3, help="Recording window in seconds")

    exam_parser = subparsers.add_parser("exam", help="Run exam mode")
    exam_parser.add_argument("-n", type=int, default=5, help="Number of questions")
    exam_parser.add_argument("--seconds", type=float, default=3, help="Recording window in seconds")
    exam_parser.add_argument("--pass_mark", type=int, help="Score threshold per question")

    parser.add_argument("--log-level", default="INFO", help="Python logging level (e.g. INFO, DEBUG)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))
    settings = load_settings()
    if args.command == "practice":
        practice(args.seconds, settings)
    elif args.command == "exam":
        pass_mark = args.pass_mark or settings.pass_mark
        exam(args.n, args.seconds, pass_mark, settings)
    else:  # pragma: no cover - argparse enforces commands
        raise ValueError(f"Unknown command {args.command}")


if __name__ == "__main__":
    main()
