"""Check the paper-metric agent tool without a PDF, a network, or Ollama."""

import json
import os
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage, ToolMessage

from team.agent import paper_tools
from team.agent.basic_agent import build_agent
from team.eval_metrics_tool.eval_metrics import PaperContent, llm
from team.eval_metrics_tool.eval_metrics.sections import split_sections

PAPER = PaperContent(split_sections(
    "Abstract\nWe report accuracy.\n4 Experiments\nTable 1: Accuracy and F1 on Adult.\n"))
REAL_EXTRACT = paper_tools.extract_paper


class FakeLiteLLM:
    """Stands in for the litellm module: records calls, returns a canned reply."""

    def __init__(self, reply):
        self.calls, self.reply = [], reply

    def completion(self, **kwargs):
        self.calls.append(kwargs)
        msg = SimpleNamespace(content=self.reply)
        return SimpleNamespace(choices=[SimpleNamespace(message=msg)])


class ScriptedToolModel(FakeMessagesListChatModel):
    def bind_tools(self, tools, **kwargs):
        return self


class PaperToolTests(unittest.TestCase):
    def setUp(self):
        # Never read the developer's .env or shell settings for the extractor's LLM.
        env = patch.dict(os.environ)
        env.start()
        self.addCleanup(env.stop)
        for name in (llm.MODEL_ENV, llm.API_BASE_ENV):
            os.environ.pop(name, None)
        no_dotenv = patch.object(llm, "find_env_file", return_value=None)
        no_dotenv.start()
        self.addCleanup(no_dotenv.stop)
        llm.load_env.cache_clear()
        self.addCleanup(llm.load_env.cache_clear)
        pdf = patch.object(paper_tools, "extract_paper", return_value=PAPER)
        self.extract = pdf.start()
        self.addCleanup(pdf.stop)

    def test_without_model_uses_dictionary_and_says_why(self):
        result = json.loads(paper_tools.find_eval_metrics.invoke({"pdf_path": "paper.pdf", "top_k": 2}))
        self.assertEqual(result["source"], "dictionary")
        self.assertEqual(result["metrics"], ["Accuracy", "F1"])
        self.assertIn("no LLM model set", result["note"])
        self.extract.assert_called_once_with("paper.pdf")

    def test_model_from_env_is_used(self):
        os.environ[llm.MODEL_ENV] = "ollama/test"
        fake = FakeLiteLLM('["accuracy", "F1 score"]')
        with patch.dict(sys.modules, {"litellm": fake}):
            result = json.loads(paper_tools.find_eval_metrics.invoke({"pdf_path": "paper.pdf"}))
        self.assertEqual(result, {"pdf": "paper.pdf", "source": "llm",
                                  "metrics": ["accuracy", "F1 score"]})
        self.assertEqual(fake.calls[0]["model"], "ollama/test")
        self.assertIn("Table 1: Accuracy and F1", fake.calls[0]["messages"][1]["content"])

    def test_bad_input_returns_error_instead_of_raising(self):
        self.extract.side_effect = REAL_EXTRACT
        result = json.loads(paper_tools.find_eval_metrics.invoke({"pdf_path": "/nonexistent/paper.pdf"}))
        self.assertEqual(result, {"pdf": "/nonexistent/paper.pdf",
                                  "error": "PDF not found: /nonexistent/paper.pdf"})
        result = json.loads(paper_tools.find_eval_metrics.invoke({"pdf_path": "paper.pdf", "top_k": 0}))
        self.assertIn("top_k", result["error"])

    def test_agent_graph_calls_tool(self):
        model = ScriptedToolModel(responses=[
            AIMessage(content="", tool_calls=[{
                "name": "find_eval_metrics", "args": {"pdf_path": "paper.pdf", "top_k": 1}, "id": "1"}]),
            AIMessage(content="The paper reports Accuracy."),
        ])
        result = build_agent(model=model).invoke(
            {"messages": [{"role": "user", "content": "Which metrics does paper.pdf report?"}]})
        reply = next(m for m in result["messages"] if isinstance(m, ToolMessage))
        self.assertEqual(json.loads(reply.content)["metrics"], ["Accuracy"])
        self.assertEqual(result["messages"][-1].content, "The paper reports Accuracy.")


if __name__ == "__main__":
    unittest.main()
