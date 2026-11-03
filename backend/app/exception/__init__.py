"""Application exceptions. Framework-free, so every layer can raise them."""

from .app_exceptions import (
    ConfigurationError,
    InvalidArgumentError,
    NotFoundError,
    ProviderError,
    RateLimitExceededError,
    SentryPromptError,
)

__all__ = [
    "ConfigurationError",
    "InvalidArgumentError",
    "NotFoundError",
    "ProviderError",
    "RateLimitExceededError",
    "SentryPromptError",
]
