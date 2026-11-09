"""Structured paper -> detected metrics ranked by dictionary evidence."""

from .scoring import WEIGHTS, MetricScore, rank_metrics

__all__ = ["WEIGHTS", "MetricScore", "rank_metrics"]
