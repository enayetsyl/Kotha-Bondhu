"""Text-to-speech wrapper for Piper."""
from __future__ import annotations

import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Iterable, Sequence

try:
    import simpleaudio as sa
except Exception:  # pragma: no cover - optional dependency
    sa = None  # type: ignore

LOGGER = logging.getLogger(__name__)


def _ensure_executable(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Piper binary not found: {path}")
    if not path.is_file():
        raise FileNotFoundError(f"Piper binary is not a file: {path}")


def synthesize_to_wav(
    text: str,
    output_path: Path,
    *,
    piper_bin: Path,
    model_path: Path,
    config_path: Path,
    extra_args: Sequence[str] | None = None,
) -> Path:
    _ensure_executable(piper_bin)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd: list[str] = [str(piper_bin), "-m", str(model_path), "-c", str(config_path), "-f", str(output_path)]
    if extra_args:
        cmd.extend(extra_args)
    LOGGER.debug("Running Piper command: %s", " ".join(cmd))
    process = subprocess.run(cmd, input=text.encode("utf-8"), check=True)
    LOGGER.debug("Piper synthesis completed with return code %s", process.returncode)
    return output_path


def speak(
    text: str,
    *,
    piper_bin: Path,
    model_path: Path,
    config_path: Path,
    extra_args: Sequence[str] | None = None,
    playback: bool = True,
) -> Path:
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        wav_path = Path(tmp.name)
    synthesize_to_wav(
        text,
        wav_path,
        piper_bin=piper_bin,
        model_path=model_path,
        config_path=config_path,
        extra_args=extra_args,
    )
    if playback:
        if sa is None:
            LOGGER.warning("simpleaudio not installed; skipping playback. WAV saved at %s", wav_path)
        else:
            LOGGER.debug("Playing audio via simpleaudio: %s", wav_path)
            wave_obj = sa.WaveObject.from_wave_file(str(wav_path))
            play_obj = wave_obj.play()
            play_obj.wait_done()
    return wav_path


def batch_speak(lines: Iterable[str], **kwargs) -> list[Path]:
    return [speak(line, **kwargs) for line in lines]
