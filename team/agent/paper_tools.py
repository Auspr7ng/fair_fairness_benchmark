"""LangChain tool that lists the evaluation metrics a paper PDF reports."""

import json
from pathlib import Path

from langchain_core.tools import tool

from team.eval_metrics_tool.eval_metrics import (PDFReadError, extract_paper, select_metrics)


@tool
def find_eval_metrics(pdf_path: str, top_k: int = 5) -> str:
    """List the main evaluation metrics a research paper PDF reports, most important first.

    Args:
        pdf_path: Path to the paper's PDF file.
        top_k: Maximum number of metric names to return.
    """
    try:
        if top_k < 1:
            raise ValueError("top_k must be >= 1")
        content = extract_paper(pdf_path)
    except (FileNotFoundError, PDFReadError, ValueError) as exc:
        return json.dumps({"pdf": pdf_path, "error": str(exc)})

    selection = select_metrics(content, top_k)
    result = {"pdf": Path(pdf_path).name, "source": selection.source,
              "metrics": selection.names}
    if selection.reason:
        result["note"] = selection.reason
    return json.dumps(result)
