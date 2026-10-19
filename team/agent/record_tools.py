"""LangChain tools bound to one explicitly selected metric record."""

import json
from pathlib import Path

from langchain_core.tools import tool
from pydantic import StrictFloat

from team.insert_into_record_tool import MetricsRecord, update_record_file


def create_record_tools(record_path: str | Path):
    """Return read/update tools that cannot choose a different record path."""
    selected = Path(record_path).expanduser().resolve(strict=True)
    MetricsRecord.load_json(selected)  # Fail before starting the agent if invalid.

    @tool
    def show_current_record() -> str:
        """Show metric names and current values in the selected record."""
        try:
            record = MetricsRecord.load_json(selected)
            return json.dumps({"record": selected.name, "metrics": record.record})
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
            return json.dumps({"record": selected.name, "error": str(exc)})

    @tool
    def update_metric(metric: str, value: StrictFloat) -> str:
        """Set an existing metric to a supplied numeric value in the selected record."""
        try:
            record = update_record_file(selected, metric, value)
            return json.dumps({
                "record": selected.name,
                "updated": {"metric": metric, "value": record.record[metric]},
                "metrics": record.record,
            })
        except (OSError, KeyError, ValueError, TypeError, json.JSONDecodeError) as exc:
            return json.dumps({"record": selected.name, "error": str(exc)})

    update_metric.handle_validation_error = "Error: value must be a number, not a boolean or string."
    return [show_current_record, update_metric]
