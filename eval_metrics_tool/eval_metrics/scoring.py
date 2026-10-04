"""Rank metrics from sections and tables. Pure functions over plain data."""

import re
from collections import Counter
from dataclasses import dataclass, field

from .extraction import PaperContent, Table
from .matcher import find_metrics
from .sections import ABSTRACT, RELATED, REFERENCES, RESULTS, Section

# Heuristic weights, meant to be tuned. Higher = stronger evidence that a metric
# is one the paper actually reports. A weight of 0 ignores that location.
WEIGHTS = {
    "table_header": 5,    # column/row label of a table
    "table_cell": 3,      # any other table cell
    "caption": 3,         # "Table 2: ..." / "Figure 3: ..." lines
    "abstract": 3,
    "results": 2,         # Experiments / Results / Evaluation sections
    "other": 1,           # anywhere else
    RELATED: 0,           # Related Work: other people's metrics
    REFERENCES: 0,
}

# Section kind -> weights key for ordinary prose.
_SECTION_KEY = {ABSTRACT: "abstract", RESULTS: "results",
                RELATED: RELATED, REFERENCES: REFERENCES}

_CAPTION = re.compile(r"^\s*(?:table|fig\.?|figure)\s*\d+\s*[:.|—-]", re.I)
_NUMERIC_CELL = re.compile(r"^[-+]?\.?\d+(?:\.\d+)?\s*%?(?:\s*(?:±|\+/-).*)?$")


@dataclass
class MetricScore:
    name: str
    score: int = 0
    where: Counter = field(default_factory=Counter)  # location -> mention count
    example: str = ""


def _record(scores: dict, metric: str, location: str, weight: int, snippet: str):
    if weight <= 0:
        return
    s = scores.setdefault(metric, MetricScore(metric))
    s.score += weight
    s.where[location] += 1
    s.example = s.example or snippet.strip()[:80]


def _score_prose(section: Section, scores: dict):
    key = _SECTION_KEY.get(section.kind, "other")
    lines = section.text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        in_caption = bool(_CAPTION.match(line))
        if in_caption:  # caption continues until a line ending in "."; max 3 lines
            block = [line]
            while not block[-1].rstrip().endswith(".") and len(block) < 3 and i + 1 < len(lines):
                i += 1
                block.append(lines[i])
            line = " ".join(block)
        loc, weight = ("caption", WEIGHTS["caption"]) if in_caption else (key, WEIGHTS[key])
        if WEIGHTS[key] == 0:
            weight = 0
        for m in find_metrics(line):
            _record(scores, m.metric, loc, weight, line)
        i += 1


def _header_row_count(rows: list[list[str]]) -> int:
    n = 0
    for row in rows[:3]:
        if any(_NUMERIC_CELL.match(c) for c in row):
            break
        n += 1
    return max(n, 1)


def _score_table(table: Table, scores: dict):
    if WEIGHTS[_SECTION_KEY.get(table.section, "other")] == 0:
        return
    n_header = _header_row_count(table.rows)
    for r, row in enumerate(table.rows):
        for c, cell in enumerate(row):
            if not cell:
                continue
            is_header = r < n_header or (c == 0 and len(table.rows) > 1)
            loc, weight = (("table_header", WEIGHTS["table_header"]) if is_header
                           else ("table_cell", WEIGHTS["table_cell"]))
            for m in find_metrics(cell, context_given=True):
                # Row labels (first column) only count if the cell *is* the metric.
                if c == 0 and r >= n_header and len(cell) > m.end - m.start + 12:
                    continue
                _record(scores, m.metric, loc, weight, cell)


def rank_metrics(content: PaperContent) -> list[MetricScore]:
    """All detected metrics, best first; ties broken alphabetically."""
    scores: dict[str, MetricScore] = {}
    for section in content.sections:
        _score_prose(section, scores)
    for table in content.tables:
        _score_table(table, scores)
    return sorted(scores.values(), key=lambda s: (-s.score, s.name))
