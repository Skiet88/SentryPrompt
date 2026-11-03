"""Selects the LLM provider from configuration.

Switching provider is a configuration change only, e.g. LLM_PROVIDER=gemini.
"""

from __future__ import annotations

import os
from collections.abc import Mapping

from .base import LLMProvider, ProviderError

PROVIDERS = ("groq", "gemini", "ollama")
DEFAULT_PROVIDER = "groq"


def _truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes"}


def get_provider(name: str | None = None, env: Mapping[str, str] | None = None) -> LLMProvider:
    env = os.environ if env is None else env
    name = (name or env.get("LLM_PROVIDER") or DEFAULT_PROVIDER).strip().lower()

    if name == "groq":
        from .groq_provider import GroqProvider

        provider: LLMProvider = GroqProvider(
            model=env.get("GROQ_MODEL", "llama-3.1-8b-instant"),
            api_key=env.get("GROQ_API_KEY", ""),
        )
    elif name == "gemini":
        from .gemini_provider import GeminiProvider

        provider = GeminiProvider(
            model=env.get("GEMINI_MODEL", "gemini-flash-lite-latest"),
            api_key=env.get("GEMINI_API_KEY", ""),
        )
    elif name == "ollama":
        from .ollama_provider import OllamaProvider

        provider = OllamaProvider(
            model=env.get("OLLAMA_MODEL", "llama3.2"),
            base_url=env.get("OLLAMA_URL", "http://localhost:11434"),
        )
    else:
        raise ProviderError(f"Unknown LLM_PROVIDER '{name}'. Choose one of: {', '.join(PROVIDERS)}")

    # Privacy rule (NFR-008): real student prompts never go to a provider that
    # may train on them. Production refuses such a provider unless the
    # project is confirmed to be on a paid, no-training tier.
    if (
        provider.may_train_on_free_tier
        and env.get("APP_ENV", "development").lower() == "production"
        and not _truthy(env.get(f"{name.upper()}_PAID_TIER"))
    ):
        raise ProviderError(
            f"'{name}' free tier may use prompts for training and is not allowed in production. "
            f"Enable billing and set {name.upper()}_PAID_TIER=true, or use LLM_PROVIDER=groq."
        )
    return provider
