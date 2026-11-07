"""Applies SentryPrompt's account rules on top of Supabase Auth.

Supabase confirms who the caller is; role and status come only from our
profiles table, never from the request (SECURITY_RULES.md §2).
"""

from __future__ import annotations

import logging

from app.domain import AccountStatus, User
from app.exception import AuthenticationError, ForbiddenError
from app.factory.user_factory import build_user
from app.repository.user_repository import UserRepository

from .i_auth_service import IAuthService
from .identity_provider import IdentityProvider

logger = logging.getLogger(__name__)

# Supabase access tokens are a few hundred bytes to ~2 KB; anything far larger
# is rejected before it is forwarded anywhere.
MAX_TOKEN_LENGTH = 8192


class AuthService(IAuthService):
    def __init__(self, identity_provider: IdentityProvider, users: UserRepository):
        self._identity = identity_provider
        self._users = users

    async def authenticate(self, access_token: str) -> User:
        token = access_token.strip()
        if not token or len(token) > MAX_TOKEN_LENGTH or any(c.isspace() for c in token):
            raise AuthenticationError()
        identity = await self._identity.verify_token(token)
        return await self._users.find_or_create(
            identity.user_id, email=identity.email, email_verified=identity.email_verified
        )

    def require_active(self, user: User) -> User:
        if not user.email_verified:
            raise ForbiddenError("Verify your email address first.", "email_not_verified")
        if user.status is AccountStatus.SUSPENDED:
            raise ForbiddenError("This account is suspended. Contact an administrator.", "account_suspended")
        return user

    def require_admin(self, user: User) -> User:
        active = self.require_active(user)
        if not active.is_admin:
            raise ForbiddenError("This action is for administrators only.", "admin_only")
        return active

    async def update_display_name(self, user: User, display_name: str) -> User:
        self.require_active(user)
        # Validate through the factory (trimmed, at most 100 characters).
        updated = build_user(
            user.user_id,
            user.email,
            display_name=display_name,
            role=user.role,
            email_verified=user.email_verified,
            status=user.status,
            created_at=user.created_at,
        )
        await self._users.update_display_name(user.user_id, updated.display_name)
        return updated

    async def delete_account(self, user: User) -> None:
        """Allowed even while suspended or unverified: erasure is not
        conditional on account state (POPIA, NFR-014, STATE_DIAGRAMS.md §2)."""
        await self._identity.delete_user(user.user_id)
        logger.info("Account deleted: %s", user.user_id)
