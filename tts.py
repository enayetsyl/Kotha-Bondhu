"""Piper text-to-speech helper utilities."""
from __future__ import annotations

import os
import subprocess
import uuid
from pathlib import Path

import simpleaudio as sa
from dotenv import load_dotenv

load_dotenv()

AUDIO_DIR = Path(os.getenv("AUDIO_DIR", "./data/audio"))
PIPER_BIN = os.getenv("PIPER_BIN")
PIPER_MODEL = os.getenv("PIPER_MODEL")
PIPER_CFG = os.getenv("PIPER_CFG")

AUDIO_DIR.mkdir(parents=True, exist_ok=True)


class PiperConfigurationError(RuntimeError):
    """Raised when the Piper executable or model are missing."""


def _ensure_paths() -> None:
    if not PIPER_BIN or not Path(PIPER_BIN).exists():
        raise PiperConfigurationError(
            "PIPER_BIN is not set or does not point to a valid executable."
        )
    if not PIPER_MODEL or not Path(PIPER_MODEL).exists():
        raise PiperConfigurationError("PIPER_MODEL is not set correctly.")
    if not PIPER_CFG or not Path(PIPER_CFG).exists():
        raise PiperConfigurationError("PIPER_CFG is not set correctly.")


def speak_and_save(text: str, *, prefix: str = "sys", play: bool = True) -> Path:
    """Generate speech with Piper, save it, and optionally play it."""

    _ensure_paths()

    out_wav = AUDIO_DIR / f"{prefix}_{uuid.uuid4().hex}.wav"
    cmd = [PIPER_BIN, "-m", PIPER_MODEL, "-c", PIPER_CFG, "-f", str(out_wav)]
    process = subprocess.Popen(cmd, stdin=subprocess.PIPE, text=True)
    process.communicate(input=text or "")
    process.wait()

    if play:
        wave_obj = sa.WaveObject.from_wave_file(str(out_wav))
        play_obj = wave_obj.play()
        play_obj.wait_done()

    return out_wav


__all__ = ["speak_and_save", "PiperConfigurationError"]
