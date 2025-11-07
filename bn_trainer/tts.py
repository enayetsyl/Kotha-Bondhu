from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

PIPER_BIN = os.environ.get("PIPER_BIN", "").strip()
PIPER_MODEL = os.environ.get("PIPER_MODEL", "").strip()
PIPER_CONFIG = os.environ.get("PIPER_CONFIG", "").strip()
default_output_dir = Path(__file__).resolve().parent / "data" / "audio"
OUTPUT_DIR = Path(os.environ.get("AUDIO_OUTPUT_DIR", default_output_dir)).expanduser()
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


class PiperError(RuntimeError):
    pass


def speak_to_file(text: str, *, output_path: Optional[Path] = None) -> Path:
    if not text.strip():
        raise ValueError("Text is empty")
    if not PIPER_BIN:
        raise PiperError("PIPER_BIN is not configured. Set it in the .env file.")
    if not PIPER_MODEL:
        raise PiperError("PIPER_MODEL is not configured. Set it in the .env file.")
    if not PIPER_CONFIG:
        raise PiperError("PIPER_CONFIG is not configured. Set it in the .env file.")

    output_path = Path(output_path) if output_path else OUTPUT_DIR / "tts_output.wav"
    cmd = [
        PIPER_BIN,
        "-m",
        str(Path(PIPER_MODEL).expanduser()),
        "-c",
        str(Path(PIPER_CONFIG).expanduser()),
        "-f",
        str(output_path),
    ]
    try:
        subprocess.run(cmd, input=text.encode("utf-8"), check=True)
    except FileNotFoundError as exc:
        raise PiperError(f"Piper executable not found: {PIPER_BIN}") from exc
    except subprocess.CalledProcessError as exc:
        raise PiperError(f"Piper failed with exit code {exc.returncode}") from exc
    return output_path


def speak(text: str) -> Path:
    return speak_to_file(text)


__all__ = ["PiperError", "speak", "speak_to_file"]
