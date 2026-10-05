"""Rule-based extraction of the main evaluation metrics from a paper PDF."""

from .extraction import PDFReadError, extract_paper
from .scoring import MetricScore, rank_metrics

__all__ = ["extract_eval_metrics", "rank_pdf", "PDFReadError", "MetricScore"]


def rank_pdf(pdf_path: str) -> list[MetricScore]:
    """Every detected metric with its score and evidence, best first."""
    return rank_metrics(extract_paper(pdf_path))


def extract_eval_metrics(pdf_path: str, top_k: int = 5) -> list[str]:
    """Canonical names of the paper's most important metrics, most important first.

    Returns [] if none are found. Raises FileNotFoundError if the file is
    missing and PDFReadError if it is not a readable PDF.
    """
    if top_k < 1:
        raise ValueError("top_k must be >= 1")
    return [s.name for s in rank_pdf(pdf_path)[:top_k]]
