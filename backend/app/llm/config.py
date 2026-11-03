"""The configuration the LLM layer needs.

A Protocol rather than the app's Settings class, so this layer depends only on
the fields it uses (interface segregation) and tests can pass a simple object.
"""

from typing import Protocol


class LLMConfig(Protocol):
    app_env: str
    llm_provider: str
    groq_api_key: str
    groq_model: str
    gemini_api_key: str
    gemini_model: str
    gemini_paid_tier: bool
    ollama_url: str
    ollama_model: str
