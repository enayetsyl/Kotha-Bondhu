"""Audio recording and transcription helpers."""
from __future__ import annotations

import os
from functools import lru_cache
from typing import Tuple

import numpy as np
import sounddevice as sd
from dotenv import load_dotenv
from faster_whisper import WhisperModel

load_dotenv()

WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE")
WHISPER_MODEL_DIR = os.getenv("WHISPER_MODEL_DIR")


@lru_cache(maxsize=1)
def _load_model() -> WhisperModel:
    """Load (and memoise) the Whisper model."""

    if WHISPER_MODEL_DIR:
        return WhisperModel(WHISPER_MODEL_DIR, device="cpu", compute_type="int8")
    return WhisperModel(WHISPER_MODEL_SIZE or "medium", device="cpu", compute_type="int8")


def record(seconds: int = 3, fs: int = 16_000) -> Tuple[np.ndarray, int]:
    """Record a mono audio clip using the default microphone."""

    audio = sd.rec(int(seconds * fs), samplerate=fs, channels=1, dtype="float32")
    sd.wait()
    return audio.squeeze(), fs


def transcribe(audio: np.ndarray, *, language: str = "bn") -> str:
    """Transcribe audio into text using Faster-Whisper."""

    model = _load_model()
    segments, _ = model.transcribe(audio, language=language)
    return "".join(segment.text for segment in segments).strip()


__all__ = ["record", "transcribe"]
