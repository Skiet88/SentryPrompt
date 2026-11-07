"""Enforces NFR-008: real student prompts never go to a provider that may train on them."""

from __future__ import annotations

from app.exception import ConfigurationError

from .config import LLMConfig
from .provider import LLMProvider

PRODUCTION = "production"


class TrainingDataPolicy:
    def enforce(self, provider: LLMProvider, config: LLMConfig) -> None:
        """Raise if a training-on-free-tier provider is used in production
        without its paid tier confirmed (e.g. GEMINI_PAID_TIER=true)."""
        if not provider.may_train_on_free_tier:
            return
        if config.app_env.lower() != PRODUCTION:
            return
        if getattr(config, f"{provider.name}_paid_tier", False):
            return
        raise ConfigurationError(
            f"'{provider.name}' free tier may use prompts for training and is not allowed in "
            f"production. Enable billing and set {provider.name.upper()}_PAID_TIER=true, "
            "or use LLM_PROVIDER=groq."
        )
