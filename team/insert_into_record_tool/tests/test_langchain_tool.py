
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from team.insert_into_record_tool import MetricsRecord
from team.insert_into_record_tool.langchain_tool import update_metric_record


class TestLangChainTool(unittest.TestCase):

    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)

        self.path = Path(self.folder.name) / "metrics.json"

        self.path_patch = patch(
            "team.insert_into_record_tool.langchain_tool.RECORD_PATH",
            self.path
        )
        self.path_patch.start()
        self.addCleanup(self.path_patch.stop)

    def invoke_update(self, metric, value):
        return update_metric_record.invoke({
            "metric": metric,
            "value": value
        })

    def test_successful_update(self):
        MetricsRecord({
            "Accuracy": 92.0,
            "F1": None
        }).save_json(self.path)

        result = self.invoke_update("F1", 0.87)
        loaded = MetricsRecord.load_json(self.path)

        self.assertIn("Successfully updated", result)
        self.assertEqual(loaded.record["F1"], 0.87)
        self.assertEqual(loaded.record["Accuracy"], 92.0)

    def test_missing_record(self):
        result = self.invoke_update("F1", 0.87)

        self.assertIn("No active metrics record", result)

    def test_unknown_metric(self):
        MetricsRecord({
            "F1": None
        }).save_json(self.path)

        result = self.invoke_update("Accuracy", 0.90)
        loaded = MetricsRecord.load_json(self.path)

        self.assertIn("Error", result)
        self.assertIsNone(loaded.record["F1"])

    def test_invalid_value(self):
        MetricsRecord({
            "F1": None
        }).save_json(self.path)

        result = self.invoke_update("F1", float("nan"))
        loaded = MetricsRecord.load_json(self.path)

        self.assertIn("Error", result)
        self.assertIsNone(loaded.record["F1"])


if __name__ == "__main__":
    unittest.main()
