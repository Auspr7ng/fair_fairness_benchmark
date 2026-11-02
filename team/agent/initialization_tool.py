"""Initialization tool bound to the record explicitly selected at startup."""
import json
from langchain_core.tools import tool
from team.paper_pipeline import run_pipeline
from team.eval_metrics_tool.eval_metrics import PDFReadError


def create_initialization_tool(record_path):
    @tool
    def initialize_current_record(pdf_path: str, metrics: list[str], row_label: str | None = None) -> str:
        """Replace the selected record from paper evidence only when explicitly requested.

        Supply names found by find_eval_metrics; unresolved values remain null.
        """
        try:
            return json.dumps(run_pipeline(pdf_path, record_path, metrics=metrics,
                                           row_label=row_label, overwrite=True))
        except (OSError, ValueError, TypeError, PDFReadError) as exc:
            return json.dumps({'record': str(record_path), 'error': str(exc)})
    return initialize_current_record
