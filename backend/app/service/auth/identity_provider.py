"""IdentityProvider interface: the service that owns accounts (Supabase Auth)."""

from __future__ import annotations

from abc import ABC, abstractmethod

from .identity import VerifiedIdentity


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
