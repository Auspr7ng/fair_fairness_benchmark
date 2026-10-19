"""Run the real agent graph with deterministic model tool calls, without Ollama."""
import json
import tempfile
import unittest
from pathlib import Path

from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage, ToolMessage

from team.agent.basic_agent import build_agent
from team.insert_into_record_tool import MetricsRecord


class ScriptedToolModel(FakeMessagesListChatModel):
    def bind_tools(self, tools, **kwargs):
        return self


class AgentWorkflowTests(unittest.TestCase):
    def test_read_update_read_through_real_graph(self):
        with tempfile.TemporaryDirectory() as folder:
            selected = Path(folder) / 'selected.json'
            other = Path(folder) / 'other.json'
            MetricsRecord({'F1': None, 'Accuracy': 92}).save_json(selected)
            MetricsRecord({'F1': 0.5}).save_json(other)
            original_other = other.read_bytes()
            calls = [
                ('show_current_record', {}),
                ('update_metric', {'metric': 'F1', 'value': 0.91}),
                ('show_current_record', {}),
            ]
            model = ScriptedToolModel(responses=[
                AIMessage(content='', tool_calls=[{'name': name, 'args': args, 'id': str(i)}])
                for i, (name, args) in enumerate(calls)
            ] + [AIMessage(content='Finished.')])
            result = build_agent(selected, model=model).invoke({
                'messages': [{'role': 'user', 'content': 'Show the record, update F1 to 0.91, then read it back.'}]
            })
            replies = [json.loads(m.content) for m in result['messages'] if isinstance(m, ToolMessage)]
            self.assertEqual(len(replies), 3)
            self.assertIsNone(replies[0]['metrics']['F1'])
            self.assertEqual(replies[1]['updated'], {'metric': 'F1', 'value': 0.91})
            self.assertEqual(replies[2]['metrics'], {'F1': 0.91, 'Accuracy': 92})
            self.assertEqual(MetricsRecord.load_json(selected).record, replies[2]['metrics'])
            self.assertEqual(other.read_bytes(), original_other)

    def test_failed_update_through_graph_preserves_record(self):
        with tempfile.TemporaryDirectory() as folder:
            selected = Path(folder) / 'record.json'
            MetricsRecord({'F1': None}).save_json(selected)
            original = selected.read_bytes()
            model = ScriptedToolModel(responses=[
                AIMessage(content='', tool_calls=[{'name': 'update_metric', 'args': {'metric': 'Unknown', 'value': .8}, 'id': 'bad'}]),
                AIMessage(content='Update failed.')
            ])
            result = build_agent(selected, model=model).invoke({'messages': [('user', 'Update Unknown to 0.8')]})
            reply = next(m for m in result['messages'] if isinstance(m, ToolMessage))
            self.assertIn('error', json.loads(reply.content))
            self.assertEqual(selected.read_bytes(), original)
