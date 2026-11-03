"""LLM layer: provider interface (Strategy), self-registering providers,
and the factory that creates the configured one."""

from . import providers  # noqa: F401  (registers the concrete providers)
from .chat_message import ChatMessage
from .config import LLMConfig
from .provider import LLMProvider
from .provider_factory import LLMProviderFactory
from .registry import ProviderRegistry, provider_registry
from .training_data_policy import TrainingDataPolicy

__all__ = [
    "ChatMessage",
    "LLMConfig",
    "LLMProvider",
    "LLMProviderFactory",
    "ProviderRegistry",
    "TrainingDataPolicy",
    "provider_registry",
]
