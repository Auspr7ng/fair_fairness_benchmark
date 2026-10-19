
"""LangChain integration for updating evaluation metric records."""

from pathlib import Path

from langchain_core.tools import tool

from team.insert_into_record_tool import MetricsRecord


REPO_ROOT = Path(__file__).resolve().parents[2]
RECORD_PATH = REPO_ROOT / "metrics_record.json"


@tool
def update_metric_record(metric: str, value: float) -> str:
    """Update an existing metric in the active evaluation record.

    Args:
        metric: Name of an already initialized metric.
        value: New numerical value for that metric.
    """
    if not RECORD_PATH.is_file():
        return "Error: No active metrics record exists."

    try:
        record = MetricsRecord.load_json(RECORD_PATH)
        record.insert_into_record(metric, value)
        record.save_json(RECORD_PATH, overwrite=True)

        return f"Successfully updated {metric} to {value}."

    except (KeyError, TypeError, ValueError, OSError) as error:
        return f"Error: {error}"
