"""Banned-words sanitizer for any LLM output, alert copy, or user-facing
event description per docs/PRIVACY_RULES.md.

Two-strike rule: caller may regenerate twice; on third violation, fall back
to a deterministic safe template (caller's responsibility).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

BANNED_TERMS: tuple[str, ...] = (
    "stole", "stolen", "theft", "thief", "thieves",
    "guilty", "caught", "criminal",
    "confirmed theft", "employee stealing", "customer stealing",
    "said", "saying", "told", "spoke",
    "conversation", "argument", "fight",
    "threat confirmed", "admitted", "confessed",
)

DEMOGRAPHIC_ADJECTIVES: tuple[str, ...] = (
    "black", "white", "asian", "hispanic", "latino", "latina", "middle eastern",
    "young", "old", "elderly", "teenage", "teenaged",
)
PERSON_NOUNS: tuple[str, ...] = (
    "man", "woman", "person", "customer", "employee", "kid", "teen", "guy", "lady",
)

_BANNED_RE = re.compile(
    r"\b(" + "|".join(re.escape(t) for t in BANNED_TERMS) + r")\b",
    flags=re.IGNORECASE,
)
_DEMOGRAPHIC_RE = re.compile(
    r"\b(" + "|".join(DEMOGRAPHIC_ADJECTIVES) + r")\s+(" + "|".join(PERSON_NOUNS) + r")\b",
    flags=re.IGNORECASE,
)


@dataclass
class SanitizerResult:
    ok: bool
    violations: list[str]


def check(text: str) -> SanitizerResult:
    violations: list[str] = []
    for m in _BANNED_RE.finditer(text):
        violations.append(m.group(1).lower())
    for m in _DEMOGRAPHIC_RE.finditer(text):
        violations.append(f"demographic:{m.group(0).lower()}")
    return SanitizerResult(ok=not violations, violations=violations)


def assert_clean(text: str) -> None:
    r = check(text)
    if not r.ok:
        raise ValueError(f"copy contains banned terms: {sorted(set(r.violations))}")
