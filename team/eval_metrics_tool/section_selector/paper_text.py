"""Choose paper sections for model input without calling a model."""

from team.eval_metrics_tool.section_splitter import REFERENCES, RESULTS, PaperContent


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
