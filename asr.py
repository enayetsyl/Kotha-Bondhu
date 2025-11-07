"""Audio recording and transcription helpers."""
from __future__ import annotations

import logging
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np

try:
    import sounddevice as sd
except Exception:  # pragma: no cover - optional dependency at runtime
    sd = None  # type: ignore

try:
    from faster_whisper import WhisperModel
except Exception:  # pragma: no cover - optional dependency at runtime
    WhisperModel = None  # type: ignore

LOGGER = logging.getLogger(__name__)
DEFAULT_SAMPLE_RATE = 16_000


@dataclass
class TranscriptionResult:
    text: str
    segments: list[tuple[float, float, str]]
    language: str


def record_audio(seconds: float, samplerate: int = DEFAULT_SAMPLE_RATE, channels: int = 1) -> np.ndarray:
    if sd is None:
        raise RuntimeError(
            "sounddevice is required to record audio. Install it and ensure microphone access is granted."
        )
    LOGGER.debug("Recording audio: seconds=%s samplerate=%s channels=%s", seconds, samplerate, channels)
    frames = int(seconds * samplerate)
    recording = sd.rec(frames, samplerate=samplerate, channels=channels, dtype=np.float32)
    sd.wait()
    return np.squeeze(recording)


def save_wave(audio: np.ndarray, path: Path, samplerate: int = DEFAULT_SAMPLE_RATE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = np.int16(audio / np.max(np.abs(audio)) * 32767) if np.max(np.abs(audio)) else np.int16(audio)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(samplerate)
        wf.writeframes(normalized.tobytes())
    LOGGER.debug("Saved WAV to %s", path)


class ASREngine:
    def __init__(self, model_size: str = "small", compute_type: str = "int8") -> None:
        self.model_size = model_size
        self.compute_type = compute_type
        self._model: Optional[WhisperModel] = None

    @property
    def model(self) -> WhisperModel:
        if WhisperModel is None:
            raise RuntimeError(
                "faster-whisper is not installed. Install it to use offline transcription."
            )
        if self._model is None:
            LOGGER.info("Loading Whisper model %s", self.model_size)
            self._model = WhisperModel(self.model_size, compute_type=self.compute_type)
        return self._model

    def transcribe(
        self,
        audio: np.ndarray,
        samplerate: int = DEFAULT_SAMPLE_RATE,
        language: str = "bn",
    ) -> TranscriptionResult:
        LOGGER.debug("Transcribing audio: seconds=%s language=%s", len(audio) / samplerate, language)
        segments, info = self.model.transcribe(audio, language=language)
        collected: list[tuple[float, float, str]] = []
        full_text: list[str] = []
        for segment in segments:
            collected.append((segment.start, segment.end, segment.text.strip()))
            full_text.append(segment.text.strip())
        return TranscriptionResult(" ".join(full_text).strip(), collected, info.language or language)


def pretty_segments(result: TranscriptionResult) -> str:
    lines = ["Transcription:", result.text]
    for start, end, text in result.segments:
        lines.append(f"  [{start:0.2f} → {end:0.2f}]: {text}")
    return "\n".join(lines)
