"""Extract the main evaluation metrics from a paper PDF.

By default the paper's Experiments section (or, without one, the paper body) is
sent to an LLM (any LiteLLM provider, including local Ollama). Without a model,
or if the call fails, the rule-based dictionary ranking is used instead.
"""

import warnings

from .extraction import PaperContent, PDFReadError, extract_paper
from .llm import LLMError
from .scoring import MetricScore, rank_metrics
from .paper_text import experiments_section, llm_text
from .selection import MetricSelection, llm_metrics, select_metrics

__all__ = ["extract_eval_metrics", "rank_pdf", "PDFReadError", "LLMError", "MetricScore"]


def rank_pdf(pdf_path: str) -> list[MetricScore]:
    """Every detected metric with its score and evidence, best first (dictionary only)."""
    return rank_metrics(extract_paper(pdf_path))


def extract_eval_metrics(pdf_path: str, top_k: int = 5, model: str | None = None,
                         api_base: str | None = None, api_key: str | None = None,
                         use_llm: bool = True) -> list[str]:
    """Names of the paper's most important metrics, most important first.

    With an LLM, names are as the LLM reports them; with the dictionary
    fallback (``use_llm=False``, no model, or a failed call) they are canonical
    dictionary names. ``model`` is a LiteLLM model string and defaults to the
    EVAL_METRICS_MODEL environment variable.

    Returns [] if none are found. Raises FileNotFoundError if the file is
    missing and PDFReadError if it is not a readable PDF.
    """
    if top_k < 1:
        raise ValueError("top_k must be >= 1")
    content = extract_paper(pdf_path)
    result = select_metrics(content, top_k, model, api_base, api_key, use_llm)
    if result.reason:
        warnings.warn(result.reason, stacklevel=2)
    return result.names
