"""Check the selected-record agent tools without a running Ollama model."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from team.agent import basic_agent
from team.agent.record_tools import create_record_tools
from team.insert_into_record_tool import MetricsRecord


class RecordToolsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.selected = Path(self.temp.name) / "selected.json"
        self.other = Path(self.temp.name) / "other.json"
        MetricsRecord({"Accuracy": 92.0, "F1": None}).save_json(self.selected)
        MetricsRecord({"Accuracy": 75.0, "F1": 0.7}).save_json(self.other)

    def test_tools_update_only_selected_record_and_read_back(self):
        show, update = create_record_tools(self.selected)
        before = json.loads(show.invoke({}))
        self.assertEqual(before["metrics"], {"Accuracy": 92.0, "F1": None})

        result = json.loads(update.invoke({"metric": "F1", "value": 0.91}))
        self.assertEqual(result["updated"], {"metric": "F1", "value": 0.91})
        self.assertEqual(result["metrics"], {"Accuracy": 92.0, "F1": 0.91})
        self.assertEqual(json.loads(show.invoke({}))["metrics"], result["metrics"])
        self.assertEqual(MetricsRecord.load_json(self.other).record,
                         {"Accuracy": 75.0, "F1": 0.7})

    def test_invalid_update_reports_error_without_writing(self):
        _, update = create_record_tools(self.selected)
        original = self.selected.read_bytes()

        result = json.loads(update.invoke({"metric": "Unknown", "value": 0.8}))
        self.assertIn("error", result)
        self.assertEqual(self.selected.read_bytes(), original)

    def test_coerced_values_cannot_bypass_numeric_validation(self):
        _, update = create_record_tools(self.selected)
        original = self.selected.read_bytes()
        for value in (True, False, "0.91", float("inf"), float("nan")):
            with self.subTest(value=value):
                result = update.invoke({"metric": "F1", "value": value})
                self.assertIn("error", result.lower())
                self.assertEqual(self.selected.read_bytes(), original)

    def test_invalid_record_rejected_before_agent_starts(self):
        with self.assertRaises(FileNotFoundError):
            create_record_tools(Path(self.temp.name) / "missing.json")

    def test_agent_registers_selected_record_tools_without_ollama(self):
        fake_model = object()
        with patch.object(basic_agent, "create_deep_agent") as create_agent:
            basic_agent.build_agent(self.selected, model=fake_model)

        kwargs = create_agent.call_args.kwargs
        self.assertIs(kwargs["model"], fake_model)
        self.assertEqual([item.name for item in kwargs["tools"]], [
            "list_reproduction_scripts", "find_eval_metrics", "show_current_record", "update_metric",
        ])
        self.assertIn("Never invent a metric value", kwargs["system_prompt"])


if __name__ == "__main__":
    unittest.main()
