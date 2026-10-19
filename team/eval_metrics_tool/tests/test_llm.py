import pytest

from eval_metrics.llm import LLMError, _parse, ask_llm, find_env_file  # real one, before stubbing


def test_parse_plain_array():
    assert _parse('["F1", "Accuracy"]') == ["F1", "Accuracy"]


def test_parse_strips_think_and_prose():
    reply = '<think>maybe ["wrong"]</think>Sure! Here you go:\n```json\n["BLEU", "chrF"]\n```'
    assert _parse(reply) == ["BLEU", "chrF"]


def test_parse_dedupes_and_drops_non_strings():
    assert _parse('["F1", "f1", " ", 3, "Equalized  Odds"]') == ["F1", "Equalized Odds"]


def test_parse_errors():
    with pytest.raises(LLMError):
        _parse("I could not find any metrics.")
    with pytest.raises(LLMError):
        _parse("[F1, BLEU]")


def test_ask_llm_truncates_and_passes_options(fake_litellm):
    fake_litellm.reply = '["a", "b", "c"]'
    assert ask_llm("text", "ollama/x", top_k=2, api_key="k") == ["a", "b"]
    call = fake_litellm.calls[0]
    assert call["temperature"] == 0 and call["api_key"] == "k"
    assert "at most 2 metrics" in call["messages"][1]["content"]


def test_ask_llm_wraps_provider_errors(fake_litellm):
    fake_litellm.error = ValueError("bad key")
    with pytest.raises(LLMError, match="bad key"):
        ask_llm("text", "gpt-x")


def test_env_file_supplies_model_and_api_base(tmp_path, monkeypatch, fake_litellm):
    from eval_metrics import llm
    env = tmp_path / ".env"
    env.write_text("EVAL_METRICS_MODEL=ollama/from-env\nEVAL_METRICS_API_BASE=http://box:11434\n")
    monkeypatch.setattr(llm, "find_env_file", lambda: env)
    monkeypatch.delenv("EVAL_METRICS_MODEL", raising=False)
    monkeypatch.delenv("EVAL_METRICS_API_BASE", raising=False)
    assert llm.resolve_model(None) == "ollama/from-env"
    ask_llm("text", "ollama/from-env")
    assert fake_litellm.calls[0]["api_base"] == "http://box:11434"


def test_shell_env_beats_env_file(tmp_path, monkeypatch):
    from eval_metrics import llm
    env = tmp_path / ".env"
    env.write_text("EVAL_METRICS_MODEL=from-file\n")
    monkeypatch.setattr(llm, "find_env_file", lambda: env)
    monkeypatch.setenv("EVAL_METRICS_MODEL", "from-shell")
    assert llm.resolve_model(None) == "from-shell"
    assert llm.resolve_model("from-arg") == "from-arg"


def test_find_env_file_walks_up(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text("")
    sub = tmp_path / "a" / "b"
    sub.mkdir(parents=True)
    monkeypatch.chdir(sub)
    assert find_env_file() == tmp_path / ".env"
