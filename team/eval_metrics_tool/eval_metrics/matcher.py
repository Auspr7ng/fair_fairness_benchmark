"""Find canonical metric mentions in a string (no PDFs involved)."""

import re
from dataclasses import dataclass
from functools import lru_cache

from .metrics_dictionary import METRICS

# In running text, a context-only acronym counts only if a number follows:
# "EM = 85.2", "AP of 41", "EM 85.2", "EM 85%". Not "it IS shown", "R2 region".
_NUMBER_AFTER = (
    r"(?=\s*(?:[:=]|\b(?:of|is|was|at|score(?:\s+of)?)\b)\s*[-+]?\.?\d"
    r"|\s+[-+]?\d+\.\d+"
    r"|\s+[-+]?\d+(?:\.\d+)?\s*%)"
)


@dataclass(frozen=True)
class Match:
    metric: str
    start: int
    end: int
    text: str


def _bounded(patterns, suffix=""):
    return "(?<!\\w)(?:" + "|".join(patterns) + ")(?!\\w)" + suffix


@lru_cache(maxsize=1)
def _compiled():
    """[(metric, regex, needs_context)] built once from the dictionary."""
    out = []
    for spec in METRICS:
        if spec.patterns:
            out.append((spec.name, re.compile(_bounded(spec.patterns), re.I), False))
        if spec.cs_patterns:
            out.append((spec.name, re.compile(_bounded(spec.cs_patterns)), False))
        if spec.context_patterns:
            out.append((spec.name, re.compile(_bounded(spec.context_patterns)), True))
    return out


def find_metrics(text: str, context_given: bool = False) -> list[Match]:
    """Return non-overlapping metric mentions in ``text``, in text order.

    ``context_given=True`` (table cells) accepts short acronyms without a
    following number. Overlaps are resolved in favour of the longest match.
    """
    candidates = []
    for name, regex, needs_context in _compiled():
        if needs_context and not context_given:
            # Rebuild with the number lookahead; cheap relative to PDF work.
            regex = _with_context(regex)
        for m in regex.finditer(text):
            candidates.append(Match(name, m.start(), m.end(), m.group()))
    candidates.sort(key=lambda m: (-(m.end - m.start), m.start))
    chosen: list[Match] = []
    for c in candidates:
        if all(c.end <= k.start or c.start >= k.end for k in chosen):
            chosen.append(c)
    return sorted(chosen, key=lambda m: m.start)


@lru_cache(maxsize=None)
def _with_context(regex: re.Pattern) -> re.Pattern:
    return re.compile(regex.pattern + _NUMBER_AFTER, regex.flags)


def normalize_metric(name: str) -> str | None:
    """Map a metric alias ("F-measure", "macro-F1") to its canonical name.

    Returns None unless the whole string is a single known metric mention.
    """
    s = name.strip()
    matches = find_metrics(s, context_given=True)
    if len(matches) == 1 and matches[0].start == 0 and matches[0].end == len(s):
        return matches[0].metric
    return None
