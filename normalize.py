"""Heuristics for mapping Sylheti-accented Bangla to Standard Bangla."""
from __future__ import annotations

import re
from typing import Iterable

SYL2STD = {
    "খামু": "খাবো",
    "যামু": "যাবো",
    "করমু": "করবো",
    "আই": "আমি",
    "তুই": "তুমি",
    "গো": "গিয়ে",
    "আছস": "আছ",
}

STD2SYL = {v: k for k, v in SYL2STD.items()}

TOKEN_SPLIT_RE = re.compile(r"([\s,.;?!]+)")


def normalize_to_standard(text: str) -> str:
    tokens = TOKEN_SPLIT_RE.split(text.strip())
    normalized: list[str] = []
    for token in tokens:
        lower = token.lower()
        replacement = SYL2STD.get(lower, None)
        if replacement is None:
            normalized.append(token)
        else:
            if token.isupper():
                normalized.append(replacement.upper())
            elif token.istitle():
                normalized.append(replacement.title())
            else:
                normalized.append(replacement)
    return "".join(normalized)


def to_sylheti_like(text: str) -> str:
    tokens = TOKEN_SPLIT_RE.split(text.strip())
    converted: list[str] = []
    for token in tokens:
        lower = token.lower()
        replacement = STD2SYL.get(lower, None)
        if replacement is None:
            converted.append(token)
        else:
            if token.isupper():
                converted.append(replacement.upper())
            elif token.istitle():
                converted.append(replacement.title())
            else:
                converted.append(replacement)
    return "".join(converted)


def harvest_new_pairs(pairs: Iterable[tuple[str, str]]) -> None:
    for syl, std in pairs:
        if syl not in SYL2STD:
            SYL2STD[syl] = std
            STD2SYL.setdefault(std, syl)
