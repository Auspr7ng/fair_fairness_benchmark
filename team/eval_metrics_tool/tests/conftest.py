import sys
from types import SimpleNamespace

import pytest


class FakeLiteLLM:
    """Stands in for the litellm module: records calls, returns a canned reply."""

    def __init__(self):
        self.calls, self.reply, self.error = [], "[]", None

    def completion(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        msg = SimpleNamespace(content=self.reply)
        return SimpleNamespace(choices=[SimpleNamespace(message=msg)])


@pytest.fixture(autouse=True)
def no_dotenv(monkeypatch):
    """Never read the developer's real .env during tests."""
    from eval_metrics import llm
    llm.load_env.cache_clear()
    monkeypatch.setattr(llm, "find_env_file", lambda: None)
    yield
    llm.load_env.cache_clear()


@pytest.fixture
def fake_litellm(monkeypatch):
    fake = FakeLiteLLM()
    monkeypatch.setitem(sys.modules, "litellm", fake)
    return fake
