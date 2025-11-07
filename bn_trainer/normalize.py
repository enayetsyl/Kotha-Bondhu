from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass(slots=True)
class NormalizationResult:
    normalized: str
    sylheti_like: str


SYL2STD: Dict[str, str] = {
    "আমরা": "আমরা",
    "তুমি": "তুমি",
    "খামু": "খাবো",
    "খাইতাম": "খেতাম",
    "খাইমু": "খাবো",
    "যামু": "যাবো",
    "আসাম": "আসছি",
    "দিমু": "দেবো",
    "করমু": "করবো",
    "বাই" : "বাড়ি",
}


def normalize_text(text: str) -> NormalizationResult:
    words = text.strip().split()
    normalized_words = [SYL2STD.get(word, word) for word in words]
    normalized = " ".join(normalized_words)
    sylheti_like = to_sylheti_like(normalized)
    return NormalizationResult(normalized=normalized, sylheti_like=sylheti_like)


def to_sylheti_like(text: str) -> str:
    reverse_map = {std: syl for syl, std in SYL2STD.items()}
    words = text.strip().split()
    syl_words = [reverse_map.get(word, _approximate_sylheti(word)) for word in words]
    return " ".join(syl_words)


def _approximate_sylheti(word: str) -> str:
    replacements = {
        "ভা": "ভা",
        "বা": "বা",
        "ছি": "সি",
        "বো": "মু",
        "ছে": "সে",
        "য়": "",
    }
    result = word
    for src, dst in replacements.items():
        result = result.replace(src, dst)
    return result


__all__ = ["NormalizationResult", "SYL2STD", "normalize_text", "to_sylheti_like"]
