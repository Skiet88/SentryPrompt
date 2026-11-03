"""Exception hierarchy. Each exception carries the HTTP status and error code
the API layer should use, so handlers never need per-exception logic."""


class SentryPromptError(Exception):
    status_code: int = 500
    error_code: str = "internal_error"


class InvalidArgumentError(SentryPromptError):
    status_code = 400
    error_code = "invalid_argument"


class NotFoundError(SentryPromptError):
    status_code = 404
    error_code = "not_found"


class ConfigurationError(SentryPromptError):
    status_code = 500
    error_code = "configuration_error"


class ProviderError(SentryPromptError):
    """The LLM provider could not be reached or returned an error."""

    status_code = 502
    error_code = "llm_provider_error"
