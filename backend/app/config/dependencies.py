"""Dependency providers for FastAPI's Depends(). Tests replace these with
app.dependency_overrides instead of patching modules."""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.domain import User
from app.exception import AuthenticationError, RateLimitExceededError
from app.service.auth.i_auth_service import IAuthService
from app.service.conversation.i_chat_service import IChatService
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


bearer_scheme = HTTPBearer(
    auto_error=False,
    description="Supabase access token. In development, get one with scripts/dev_login.py.",
)


def _client_key(request: Request) -> str:
    """The direct peer address. Behind a reverse proxy, the server must be
    configured to trust that proxy's forwarded-for header (deployment step);
    the header is never trusted from arbitrary clients, since it is trivially
    spoofed."""
    return request.client.host if request.client else UNKNOWN_CLIENT


def _limit(decision_allowed: bool, retry_after: int) -> None:
    if not decision_allowed:
        raise RateLimitExceededError(retry_after)


def get_chat_service(request: Request) -> Provider[IChatService]:
    provider: Provider[IChatService] = request.app.state.chat_service
    return provider


def get_auth_service(request: Request) -> Provider[IAuthService]:
    provider: Provider[IAuthService] = request.app.state.auth_service
    return provider


async def get_current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    auth: Annotated[Provider[IAuthService], Depends(get_auth_service)],
) -> User:
    """Deny by default (SECURITY_RULES.md §2): every protected endpoint
    depends on this. Attempts are limited per client address before the
    token is sent to Supabase."""
    decision = request.app.state.auth_rate_limiter.hit(_client_key(request))
    _limit(decision.allowed, decision.retry_after_seconds)
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AuthenticationError()
    return await auth.get().authenticate(credentials.credentials)


async def get_active_user(
    user: Annotated[User, Depends(get_current_user)],
    auth: Annotated[Provider[IAuthService], Depends(get_auth_service)],
) -> User:
    """Verified and not suspended (FR-014, FR-021)."""
    return auth.get().require_active(user)


async def get_admin_user(
    user: Annotated[User, Depends(get_current_user)],
    auth: Annotated[Provider[IAuthService], Depends(get_auth_service)],
) -> User:
    return auth.get().require_admin(user)


def enforce_screening_rate_limit(request: Request, user: Annotated[User, Depends(get_active_user)]) -> None:
    """Per user, plus a global limit protecting the LLM quota."""
    decision = request.app.state.screening_rate_limits.check(user.user_id)
    _limit(decision.allowed, decision.retry_after_seconds)


def enforce_profile_rate_limit(request: Request, user: Annotated[User, Depends(get_current_user)]) -> None:
    decision = request.app.state.profile_rate_limiter.hit(user.user_id)
    _limit(decision.allowed, decision.retry_after_seconds)
