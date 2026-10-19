"""Validate and update one metric in an initialized record."""

import json
import math
from pathlib import Path


class MetricsRecord:
    """Manage and persist a record of evaluation metrics."""

    def __init__(self, record: dict[str, float | int | None]):
        if not isinstance(record, dict):
            raise TypeError("Record must be a dictionary.")

        self.record = {}

        for metric, value in record.items():
            self._validate_metric(metric)
            if value is not None:
                self._validate_value(value)
            self.record[metric] = value

    @staticmethod
    def _validate_metric(metric):
        if not isinstance(metric, str) or not metric.strip():
            raise ValueError("Metric must be a non-empty string.")

    @staticmethod
    def _validate_value(value):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError("Metric value must be numeric.")

        if not math.isfinite(value):
            raise ValueError("Metric value must be finite.")

    def insert_into_record(self, metric: str, value: float | int):
        """Update an initialized metric with a validated value."""
        self._validate_metric(metric)
        self._validate_value(value)
        if metric not in self.record:
            raise KeyError(f"Metric {metric!r} is not initialized in the record")
        self.record[metric] = value
        return self.record

    def save_json(self, file_path: str, overwrite: bool = False):
        """Save the record without accidentally overwriting an existing file."""
        path = Path(file_path)

        mode = "w" if overwrite else "x"

        with path.open(mode, encoding="utf-8") as file:
            json.dump(self.record, file, indent=4, allow_nan=False)

    @classmethod
    def load_json(cls, file_path: str):
        """Load a previously saved metrics record."""
        path = Path(file_path)

        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        return cls(data)


def update_record_file(file_path: str | Path, metric: str, value: float | int) -> MetricsRecord:
    """Select a saved record, update one initialized metric, and persist it."""
    record = MetricsRecord.load_json(file_path)
    record.insert_into_record(metric, value)
    record.save_json(file_path, overwrite=True)
    return record
