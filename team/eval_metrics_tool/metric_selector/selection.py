"""Shared metric selection and model-to-dictionary fallback policy."""

from dataclasses import dataclass, field

from team.eval_metrics_tool.llm_metric_finder import LLMError, ask_llm, resolve_model
from team.eval_metrics_tool.metric_ranker import MetricScore, rank_metrics
from team.eval_metrics_tool.metric_ranker.evidence import MetricEvidence
from team.eval_metrics_tool.metric_matcher import normalize_metric
from team.eval_metrics_tool.section_selector import llm_text
from team.eval_metrics_tool.section_splitter import PaperContent


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
    evidence: dict[str, list[MetricEvidence]] = field(default_factory=dict)


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
            if not names:
                reason = ("the LLM returned no evaluation metrics; this does not confirm "
                          "the paper has none. Check the extracted text and section "
                          "selection before using this result")
                return MetricSelection(names, "llm", reason)
            supported = {s.name: s for s in rank_metrics(content, requested=names) if s.reported}
            accepted = [n for n in names if (normalize_metric(n) or n) in supported]
            rejected = [n for n in names if n not in accepted]
            if rejected:
                reason = "no reported-use evidence for model names: " + ", ".join(rejected)
            if accepted:
                evidence = {n: supported[normalize_metric(n) or n].evidence for n in accepted}
                return MetricSelection(accepted, "llm", reason, evidence=evidence)
            reason = (reason or "no supported model names") + "; using dictionary ranking"
    scores = [s for s in rank_metrics(content) if s.reported][:top_k]
    return MetricSelection([s.name for s in scores], "dictionary", reason, scores,
                           {s.name: s.evidence for s in scores})

