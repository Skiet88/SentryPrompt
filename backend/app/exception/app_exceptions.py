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


class AuthenticationError(SentryPromptError):
    """No valid login: missing, malformed, expired, forged or logged-out token."""

    status_code = 401
    error_code = "unauthenticated"

    def __init__(self, message: str = "Please log in.") -> None:
        super().__init__(message)


class ForbiddenError(SentryPromptError):
    """Logged in, but not allowed. error_code says why."""

    status_code = 403
    error_code = "forbidden"

    def __init__(self, message: str, error_code: str = "forbidden") -> None:
        super().__init__(message)
        self.error_code = error_code


class AuthUnavailableError(SentryPromptError):
    """The login could not be checked (Supabase unreachable). Fails closed:
    the request is refused, never let through."""

    status_code = 503
    error_code = "auth_unavailable"


class RateLimitExceededError(SentryPromptError):
    status_code = 429
    error_code = "rate_limited"

    def __init__(self, retry_after_seconds: int):
        super().__init__("Too many requests. Please wait a moment and try again.")
        self.retry_after_seconds = retry_after_seconds


class ProviderError(SentryPromptError):
    """The LLM provider could not be reached or returned an error.

    Carries only a safe summary: provider name, the provider's HTTP status and
    a machine-readable error code. Never the provider's message text, which can
    echo request content (e.g. a failed JSON generation includes model output).
    """

    status_code = 502
    error_code = "llm_provider_error"

    def __init__(
        self,
        message: str,
        *,
        provider: str | None = None,
        provider_status: int | None = None,
        provider_error_code: str | None = None,
    ):
        super().__init__(message)
        self.provider = provider
        self.provider_status = provider_status
        self.provider_error_code = provider_error_code
