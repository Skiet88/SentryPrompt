"""Application exceptions. Framework-free, so every layer can raise them."""

from .app_exceptions import (
    AuthenticationError,
    AuthUnavailableError,
    ConfigurationError,
    ForbiddenError,
    InvalidArgumentError,
    NotFoundError,
    ProviderError,
    RateLimitExceededError,
    SentryPromptError,
)

__all__ = [
    "AuthUnavailableError",
    "AuthenticationError",
    "ConfigurationError",
    "ForbiddenError",
    "InvalidArgumentError",
    "NotFoundError",
    "ProviderError",
    "RateLimitExceededError",
    "SentryPromptError",
]
