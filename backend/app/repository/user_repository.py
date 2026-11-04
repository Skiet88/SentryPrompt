"""Profiles (the User fields we own: display name, role, status).

Identity (email, verification, password) belongs to Supabase Auth, so it is
passed in from the verified login rather than stored here.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain import User


class UserRepository(ABC):
    @abstractmethod
    async def find_or_create(self, user_id: str, *, email: str, email_verified: bool) -> User:
        """The user's profile, created with defaults (student, active) if the
        sign-up trigger has not created it yet."""

    @abstractmethod
    async def update_display_name(self, user_id: str, display_name: str) -> None: ...
