"""Weighted crawling of metric/value evidence across academic papers.

Scores are transparent heuristics, not calibrated probabilities. Repeated
independent mentions provide statistical support; no training data is required.
"""

import math
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Optional, Union

from team.insert_into_record_tool import MetricsRecord

from team.eval_metrics_tool.eval_metrics.extraction import PaperContent, extract_paper
from team.eval_metrics_tool.eval_metrics.matcher import find_metrics, normalize_metric
from team.eval_metrics_tool.eval_metrics.scoring import rank_metrics
from team.eval_metrics_tool.eval_metrics.sections import split_sections

from .evidence import VALUE_WEIGHTS
from .text_values import _crawl_text
from .table_values import _crawl_tables, _crawl_unruled_table_row
from .value_ranking import _rank_values

MetricValue = Optional[Union[int, float]]


def create_eval_metrics_record(
    pdf_path: str,
    metrics: Optional[Iterable[str]] = None,
    *,
    top_k: int = 5,
    row_label: Optional[str] = None,
    weights: Optional[Mapping[str, float]] = None,
    window: int = 140,
    min_score: float = 4.0,
    min_margin: float = 1.0,
) -> dict[str, MetricValue]:
    """Crawl a PDF or UTF-8 .txt paper and initialize weighted metric values.

    Use supplied metric names (including extract_eval_metrics' output), or
    the existing top_k metric-name ranking. Score nearby numeric candidates
    using proximity, linguistic cues, table alignment, optional section hints
    and logarithmic repetition support. All sections are crawled; headings
    and exact metric/value wording are not required.

    Return None when no candidate meets min_score or the top two candidates
    are separated by less than min_margin. This is heuristic ranking, not a
    calibrated confidence probability or a guarantee of the intended model.
    Optional row_label restricts evidence to exact matching table rows.
    weights overrides entries in VALUE_WEIGHTS. Percentages retain their
    printed scale; the central estimate of an uncertainty interval is used.
    """
    if metrics is None and top_k < 1:
        raise ValueError('top_k must be >= 1')
    if isinstance(metrics, str):
        raise TypeError('metrics must be a collection of names, not a string')
    if window < 1 or not math.isfinite(min_score) or not math.isfinite(min_margin) or min_margin < 0:
        raise ValueError('window must be positive and thresholds must be finite; min_margin must be nonnegative')
    if row_label is not None and not row_label.strip():
        raise ValueError('row_label must not be empty')
    scoring = dict(VALUE_WEIGHTS)
    if weights is not None:
        unknown = set(weights) - scoring.keys()
        if unknown:
            raise ValueError(f'Unknown weight features: {sorted(unknown)}')
        if any(not math.isfinite(v) for v in weights.values()):
            raise ValueError('weights must be finite')
        scoring.update(weights)
    path = Path(pdf_path)
    # pdfplumber's default spacing: the value weights were tuned on it, and the
    # finer spacing exposes figure numbers that the text crawl mistakes for results.
    paper = (PaperContent(split_sections(path.read_text(encoding='utf-8')))
             if path.suffix.lower() == '.txt' else extract_paper(str(path), x_tolerance_ratio=None))
    names = ([score.name for score in rank_metrics(paper)[:top_k]]
             if metrics is None else [normalize_metric(name) or name for name in metrics])
    record = dict.fromkeys(names, None)
    evidence, found_row = _crawl_tables(paper, record, scoring, row_label)
    if row_label is None:
        evidence.extend(_crawl_text(paper, record, scoring, window))
    elif not evidence:
        evidence.extend(_crawl_unruled_table_row(paper, record, scoring, row_label))
        if not found_row and not evidence:
            raise ValueError(f'No table row labeled {row_label!r} was found')
    ranked = _rank_values(evidence, scoring)
    for metric in record:
        values = ranked.get(metric, [])
        if values and values[0][1] >= min_score:
            if len(values) == 1 or values[0][1] - values[1][1] >= min_margin:
                record[metric] = values[0][0]
    return record


def insert_eval_metric(
    record: dict[str, MetricValue], metric: str, value: Union[int, float]
) -> dict[str, MetricValue]:
    """Compatibility adapter for the dedicated record updater.

    Preserve the caller's dictionary identity. Updates require finite numeric
    values; missing values may remain None during initialization only.
    """
    validated = MetricsRecord(record)
    record.update(validated.insert_into_record(metric, value))
    return record
