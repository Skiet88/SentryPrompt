"""Builds ProviderErrors that are safe to log (SECURITY_RULES.md §3).

Only the HTTP status and an error code that looks like a code (e.g.
"model_not_found") are kept. Anything else from the provider's response is
dropped, because error bodies can contain model output or request content.
"""

from __future__ import annotations

import re

from app.exception import ProviderError

_SAFE_CODE = re.compile(r"[a-z0-9_.-]{1,64}")


def safe_error_code(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    code = value.strip().lower()
    return code if _SAFE_CODE.fullmatch(code) else None


def http_error(provider: str, status: int | None, code: object = None) -> ProviderError:
    safe_code = safe_error_code(code)
    detail = " ".join(part for part in (f"HTTP {status}" if status else None, safe_code) if part)
    return ProviderError(
        f"{provider} request failed: {detail or 'unknown error'}",
        provider=provider,
        provider_status=status,
        provider_error_code=safe_code,
    )


def network_error(provider: str, kind: str) -> ProviderError:
    """kind: "timeout", "connection_error" or "unreadable_response"."""
    return ProviderError(f"{provider} request failed: {kind}", provider=provider, provider_error_code=kind)


def unexpected_error(provider: str, exc: BaseException) -> ProviderError:
    return ProviderError(
        f"{provider} request failed: {type(exc).__name__}",
        provider=provider,
        provider_error_code="unexpected_error",
    )
