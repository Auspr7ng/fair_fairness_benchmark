"""Shared metric selection and model-to-dictionary fallback policy."""

from dataclasses import dataclass

from .extraction import PaperContent
from .llm import LLMError, ask_llm, resolve_model
from .paper_text import llm_text
from .scoring import MetricScore, rank_metrics


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


