"""
utils/validators.py
───────────────────
Lightweight heuristic helpers for SMART-criteria checking.
These supplement (not replace) the LLM validation in phase1_interview.py
and are used to surface quick flags in the UI.
"""
from __future__ import annotations

import re

_VAGUE_TERMS = frozenset(
    ["improve", "better", "more", "less", "good", "fast", "enhance",
     "optimize", "increase", "decrease", "boost", "strengthen"]
)

_MEASURABLE_RE = re.compile(
    r"\d+\s*%|\d+\s*(days?|weeks?|months?|hours?|users?|calls?|items?|"
    r"dollars?|\$|€|£|k|million|units?|points?|tickets?|requests?)",
    re.IGNORECASE,
)

_TIME_BOUND_RE = re.compile(
    r"\b(Q[1-4]\s*\d{4}|\d{4}|by\s+\w+\s+\d+|deadline|due\s+date|"
    r"end\s+of\s+(year|quarter|month)|"
    r"January|February|March|April|May|June|July|August|"
    r"September|October|November|December)\b",
    re.IGNORECASE,
)


def check_smart(text: str) -> dict:
    """
    Return a dict with boolean flags for three auto-detectable SMART criteria
    and a composite score (0–3).

    'achievable' and 'relevant' are not reliably machine-assessable from text
    alone and are therefore omitted from the heuristic.
    """
    words = text.lower().split()
    vague_hits = sum(1 for w in words if w.rstrip("s") in _VAGUE_TERMS)

    specific = len(words) >= 12 and vague_hits <= 2
    measurable = bool(_MEASURABLE_RE.search(text))
    time_bound = bool(_TIME_BOUND_RE.search(text))

    return {
        "specific": specific,
        "measurable": measurable,
        "time_bound": time_bound,
        "score": sum([specific, measurable, time_bound]),  # 0–3
    }


def minimum_length_ok(text: str, min_words: int = 10) -> bool:
    return len(text.split()) >= min_words


def contains_vague_only(text: str) -> bool:
    """True if the response is nothing but high-level filler words."""
    words = set(text.lower().split())
    vague_hits = len(words & _VAGUE_TERMS)
    return vague_hits > 0 and len(words) < 8
