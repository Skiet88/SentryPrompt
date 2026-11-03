"""Creates the configured LLM provider and applies the training-data policy."""

from __future__ import annotations

from .config import LLMConfig
from .provider import LLMProvider
from .registry import ProviderRegistry, provider_registry
from .training_data_policy import TrainingDataPolicy


class LLMProviderFactory:
    def __init__(
        self,
        registry: ProviderRegistry = provider_registry,
        policy: TrainingDataPolicy | None = None,
    ):
        self._registry = registry
        self._policy = policy or TrainingDataPolicy()

    def create(self, config: LLMConfig, name: str | None = None) -> LLMProvider:
        provider = self._registry.create(name or config.llm_provider, config)
        self._policy.enforce(provider, config)
        return provider
