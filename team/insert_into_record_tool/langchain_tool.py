
"""LangChain integration for updating evaluation metric records."""

from pathlib import Path

from langchain_core.tools import tool
from pydantic import StrictFloat

from team.insert_into_record_tool import update_record_file


REPO_ROOT = Path(__file__).resolve().parents[2]
RECORD_PATH = REPO_ROOT / "metrics_record.json"


@tool
def update_metric_record(metric: str, value: StrictFloat) -> str:
    """Update an existing metric in the active evaluation record.

    Args:
        metric: Name of an already initialized metric.
        value: New numerical value for that metric.
    """
    if not RECORD_PATH.is_file():
        return "Error: No active metrics record exists."

    try:
        update_record_file(RECORD_PATH, metric, value)

        return f"Successfully updated {metric} to {value}."

    except (KeyError, TypeError, ValueError, OSError) as error:
        return f"Error: {error}"


update_metric_record.handle_validation_error = "Error: metric must be text and value must be a number (not a boolean or string)."
