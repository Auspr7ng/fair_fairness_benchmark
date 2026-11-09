"""Paper text -> the metric names an LLM reports (any LiteLLM provider)."""

from .llm import API_BASE_ENV, MODEL_ENV, LLMError, ask_llm, resolve_model

__all__ = ["API_BASE_ENV", "MODEL_ENV", "LLMError", "ask_llm", "resolve_model"]
