from __future__ import annotations

import os
import tempfile
import time
import wave
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import sounddevice as sd
from dotenv import load_dotenv
from faster_whisper import WhisperModel

from .normalize import normalize_text

load_dotenv()

WHISPER_MODEL_SIZE = os.environ.get("WHISPER_MODEL_SIZE", "small")
AUDIO_DIR = Path(
    os.environ.get("AUDIO_INPUT_DIR", Path(__file__).resolve().parent / "data" / "audio")
)
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

_MODEL: Optional[WhisperModel] = None


def get_model() -> WhisperModel:
    global _MODEL
    if _MODEL is None:
        _MODEL = WhisperModel(WHISPER_MODEL_SIZE, device="cpu")
    return _MODEL


def record_audio(seconds: float, *, sample_rate: int = 16000) -> np.ndarray:
    if seconds <= 0:
        raise ValueError("seconds must be positive")
    frames = int(sample_rate * seconds)
    recording = sd.rec(frames, samplerate=sample_rate, channels=1, dtype="float32")
    sd.wait()
    return recording.reshape(-1)


def save_wav(audio: np.ndarray, *, sample_rate: int = 16000, path: Optional[Path] = None) -> Path:
    path = Path(path) if path else AUDIO_DIR / f"child_{int(time.time() * 1000)}.wav"
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes((audio * 32767).astype(np.int16).tobytes())
    return path


def transcribe_audio(audio: np.ndarray, *, sample_rate: int = 16000) -> str:
    model = get_model()
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    save_wav(audio, sample_rate=sample_rate, path=tmp_path)
    segments, _ = model.transcribe(str(tmp_path))
    tmp_path.unlink(missing_ok=True)
    text = " ".join(segment.text.strip() for segment in segments if segment.text)
    return text.strip()


def capture_and_transcribe(seconds: float) -> Tuple[str, Path]:
    audio = record_audio(seconds)
    audio_path = save_wav(audio)
    transcript = transcribe_audio(audio)
    return transcript, audio_path


def normalize_transcript(transcript: str) -> str:
    return normalize_text(transcript).normalized


__all__ = [
    "capture_and_transcribe",
    "get_model",
    "normalize_transcript",
    "record_audio",
    "save_wav",
    "transcribe_audio",
]
