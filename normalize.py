"""Text normalization helpers for Sylheti ↔ Standard Bangla.

These starter rules are intentionally small so families can grow
and customize them over time. Extend ``SYL2STD`` with the phrases
that matter to you and they will automatically flow through both
practice and exam modes.
"""
from __future__ import annotations

from typing import Dict

# Minimal starter rules. Add your family's common phrases here.
SYL2STD: Dict[str, str] = {
    "খামু": "খাবো",
    "যামু": "যাবো",
    "আইসা": "এসে",
    "কিতা": "কি",
    "তু": "তুমি",
    "অয়": "হয়",
    "মাইনষ": "মানুষ",
    "লাইমু": "আনব",
    "কিদা": "কী",
}


def to_standard_bn(text: str) -> str:
    """Normalize Sylheti-flavoured Bangla into Standard Bangla.

    Parameters
    ----------
    text:
        Raw transcript from Whisper/Faster-Whisper.

    Returns
    -------
    str
        Standard Bangla text after applying simple replacements.
    """

    out = (text or "").strip()
    for sylheti, standard in SYL2STD.items():
        out = out.replace(sylheti, standard)

    # Basic whitespace clean-up to keep things tidy.
    while "  " in out:
        out = out.replace("  ", " ")
    return out


# Optional: produce a Sylheti-like variant from Standard Bangla.
STD2SYL: Dict[str, str] = {standard: sylheti for sylheti, standard in SYL2STD.items()}


def to_sylheti_like(text: str) -> str:
    """Generate a Sylheti-sounding variant from Standard Bangla.

    This is a heuristic helper so the app can auto-grow the exam
    phrase bank from practice sessions. Feel free to replace it
    with a curated lookup if you prefer finer control.
    """

    out = (text or "").strip()
    for standard, sylheti in STD2SYL.items():
        out = out.replace(standard, sylheti)
    return out


__all__ = ["SYL2STD", "STD2SYL", "to_standard_bn", "to_sylheti_like"]
