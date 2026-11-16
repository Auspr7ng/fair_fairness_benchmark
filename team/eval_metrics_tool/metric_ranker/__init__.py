"""Structured paper -> detected metrics ranked by dictionary evidence."""

from .scoring import WEIGHTS, MetricScore, rank_metrics
from .evidence import MetricEvidence

__all__ = ["WEIGHTS", "MetricScore", "MetricEvidence", "rank_metrics"]
