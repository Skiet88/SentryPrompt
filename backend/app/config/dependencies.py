"""Dependency providers for FastAPI's Depends(). Tests replace these with
app.dependency_overrides instead of patching modules."""

from __future__ import annotations

from functools import lru_cache

from fastapi import Request

from app.exception import RateLimitExceededError
from app.service.screening.i_screening_service import IScreeningService

from .lazy import Provider
from .settings import Settings

UNKNOWN_CLIENT = "unknown"


@lru_cache
def get_settings() -> Settings:
    return Settings()


def get_screening_service(request: Request) -> Provider[IScreeningService]:
    """Returns a provider, not the service: the endpoint asks for the service
    only after the request body has passed validation, so invalid input never
    triggers building it."""
    provider: Provider[IScreeningService] = request.app.state.screening_service
    return provider


def enforce_screening_rate_limit(request: Request) -> None:
    """Keyed by client address until login exists; step 6 keys it by user.

    The address is the direct peer. Behind a reverse proxy, the server must be
    configured to trust that proxy's forwarded-for header (deployment step);
    the header is never trusted from arbitrary clients, since it is trivially
    spoofed.
    """
    client = request.client.host if request.client else UNKNOWN_CLIENT
    decision = request.app.state.screening_rate_limits.check(client)
    if not decision.allowed:
        raise RateLimitExceededError(decision.retry_after_seconds)
