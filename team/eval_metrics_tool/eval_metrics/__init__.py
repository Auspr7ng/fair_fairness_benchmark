"""Extract the main evaluation metrics from a paper PDF.

By default the paper's Experiments section (or, without one, the paper body) is
sent to an LLM (any LiteLLM provider, including local Ollama). Without a model,
or if the call fails, the rule-based dictionary ranking is used instead.
"""

import warnings
from dataclasses import dataclass

from .extraction import PaperContent, PDFReadError, extract_paper
from .llm import LLMError, ask_llm, resolve_model
from .scoring import MetricScore, rank_metrics
from .sections import REFERENCES, RESULTS

__all__ = ["extract_eval_metrics", "rank_pdf", "PDFReadError", "LLMError", "MetricScore"]


def rank_pdf(pdf_path: str) -> list[MetricScore]:
    """Every detected metric with its score and evidence, best first (dictionary only)."""
    return rank_metrics(extract_paper(pdf_path))


def experiments_section(content: PaperContent) -> str:
    """Text of the Experiments section ("" if no such heading was found).

    Headings like "Experiments", "Results", "Evaluation" all count; if the paper
    has several (e.g. "5 Experiments" then "5.2 Results"), they are joined.
    """
    return "\n".join(s.text for s in content.sections if s.kind == RESULTS).strip()


def llm_text(content: PaperContent) -> str:
    """Text sent to the LLM: the Experiments section, or else the paper body.

    Many papers title their experiments by topic ("5 Benchmarking Fairness
    Methods"), so without an Experiments heading everything but References is
    sent. Related Work stays in: an unrecognised heading after it would
    otherwise drop the experiments with it, and the prompt tells the model to
    ignore other people's metrics.
    """
    return experiments_section(content) or "\n".join(
        s.text for s in content.sections if s.kind != REFERENCES).strip()


def llm_metrics(content: PaperContent, top_k: int, model: str | None,
                api_base: str | None = None,
                api_key: str | None = None) -> tuple[list[str] | None, str | None]:
    """(names, None) from the LLM, or (None, reason) when the dictionary should be used."""
    model = resolve_model(model)
    if not model:
        return None, ("no LLM model set (pass model= / --model or set "
                      "EVAL_METRICS_MODEL); using dictionary ranking")
    text = llm_text(content)
    if not text:
        return None, "no text found in the PDF; using dictionary ranking"
    try:
        return ask_llm(text, model, top_k, api_base=api_base, api_key=api_key), None
    except LLMError as exc:
        return None, f"{exc}; using dictionary ranking"


@dataclass
class MetricSelection:
    """One shared extraction decision, with evidence for dictionary results."""
    names: list[str]
    source: str
    reason: str | None = None
    scores: list[MetricScore] | None = None


def select_metrics(content: PaperContent, top_k: int = 5, model: str | None = None,
                   api_base: str | None = None, api_key: str | None = None,
                   use_llm: bool = True) -> MetricSelection:
    """Select names once for the Python API, CLI, and agent tool."""
    if top_k < 1:
        raise ValueError("top_k must be >= 1")
    reason = None
    if use_llm:
        names, reason = llm_metrics(content, top_k, model, api_base, api_key)
        if names is not None:
            return MetricSelection(names, "llm")
    scores = rank_metrics(content)[:top_k]
    return MetricSelection([s.name for s in scores], "dictionary", reason, scores)


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
