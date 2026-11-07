"""Provider registry. Providers register themselves with @provider_registry.register,
so adding a provider means adding a module, not editing this file (open/closed)."""

from __future__ import annotations

from app.exception import ConfigurationError

from .config import LLMConfig
from .provider import LLMProvider


class ProviderRegistry:
    def __init__(self) -> None:
        self._providers: dict[str, type[LLMProvider]] = {}

    def register(self, provider_cls: type[LLMProvider]) -> type[LLMProvider]:
        name = provider_cls.name
        if name in self._providers:
            raise ConfigurationError(f"LLM provider '{name}' is already registered")
        self._providers[name] = provider_cls
        return provider_cls

    def names(self) -> list[str]:
        return sorted(self._providers)

    def create(self, name: str, config: LLMConfig) -> LLMProvider:
        key = name.strip().lower()
        if key not in self._providers:
            raise ConfigurationError(
                f"Unknown LLM provider '{name}'. Choose one of: {', '.join(self.names())}"
            )
        return self._providers[key].from_config(config)


provider_registry = ProviderRegistry()
