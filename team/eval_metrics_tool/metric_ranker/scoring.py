"""Rank metrics from sections and tables. Pure functions over plain data."""

import re
from collections import Counter
from dataclasses import dataclass, field

from team.eval_metrics_tool.metric_matcher import find_metrics, find_requested_metrics
from .evidence import MetricEvidence, use_evidence
from team.eval_metrics_tool.section_splitter import (ABSTRACT, RELATED, REFERENCES, RESULTS,
                                                     PaperContent, Section, Table)

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
    reported: bool = False
    evidence: list[MetricEvidence] = field(default_factory=list)


def _record(scores: dict, metric: str, location: str, weight: int, evidence: MetricEvidence):
    if weight <= 0:
        return
    s = scores.setdefault(metric, MetricScore(metric))
    s.score += weight
    s.where[location] += 1
    s.example = s.example or evidence.text
    s.reported = s.reported or evidence.reported
    if evidence not in s.evidence:
        s.evidence.append(evidence)


def _score_prose(section: Section, scores: dict, requested=()):
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
        matches = (find_requested_metrics(line, requested, context_given=False)
                 if requested else find_metrics(line))
        for m in matches:
            evidence = use_evidence(line, m, section.kind, loc)
            if evidence is not None:
                _record(scores, m.metric, loc, weight, evidence)
        i += 1


def _header_row_count(rows: list[list[str]]) -> int:
    n = 0
    for row in rows[:3]:
        if any(_NUMERIC_CELL.match(c) for c in row):
            break
        n += 1
    return max(n, 1)


def _score_table(table: Table, scores: dict, requested=()):
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
            matches = (find_requested_metrics(cell, requested) if requested
                       else find_metrics(cell, context_given=True))
            for m in matches:
                # Row labels (first column) only count if the cell *is* the metric.
                if c == 0 and r >= n_header and len(cell) > m.end - m.start + 12:
                    continue
                values = any(_NUMERIC_CELL.match(data[c]) for data in table.rows[n_header:]
                             if c < len(data))
                if c == 0 and r >= n_header:
                    values = any(_NUMERIC_CELL.match(v) for v in row[1:])
                evidence = use_evidence(cell, m, table.section, loc, page=table.page or None,
                                        row=r+1, column=c+1, table_has_values=values)
                if evidence is not None:
                    _record(scores, m.metric, loc, weight, evidence)


def rank_metrics(content: PaperContent, *, requested=()) -> list[MetricScore]:
    """Candidates with evidence; reported uses precede unconfirmed mentions.

    Within each group, sort by weighted score then name. ``requested`` allows
    evidence checks for exact custom metric names proposed by a model.
    """
    scores: dict[str, MetricScore] = {}
    for section in content.sections:
        _score_prose(section, scores, requested)
    for table in content.tables:
        _score_table(table, scores, requested)
    return sorted(scores.values(), key=lambda s: (-s.reported, -s.score, s.name))
