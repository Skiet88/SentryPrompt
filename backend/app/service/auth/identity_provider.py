"""IdentityProvider interface: the service that owns accounts (Supabase Auth)."""

from __future__ import annotations

from abc import ABC, abstractmethod

from .identity import IdentityRecord, VerifiedIdentity


class IdentityProvider(ABC):
    @abstractmethod
    async def verify_token(self, access_token: str) -> VerifiedIdentity:
        """Confirm the token is genuine, unexpired and its session still live.

        Raises AuthenticationError if not, AuthUnavailableError if the
        provider cannot be reached (fail closed: never treated as valid).
        """

    @abstractmethod
    async def delete_user(self, user_id: str) -> None:
        """Permanently delete the account (the database cascade removes the
        user's profile, conversations and messages, NFR-014)."""

    @abstractmethod
    async def list_users(self, page: int, per_page: int) -> list[IdentityRecord]:
        """One page of accounts (admin only, FR-021)."""

    @abstractmethod
    async def set_banned(self, user_id: str, banned: bool) -> None:
        """Block (or unblock) logging in for this account (AUTH_DESIGN.md §0.1)."""
