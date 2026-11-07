"""Profiles (the User fields we own: display name, role, status).

Identity (email, verification, password) belongs to Supabase Auth, so it is
passed in from the verified login rather than stored here.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

from app.domain import AccountStatus, AdminAuditLog, User, UserRole


@dataclass(frozen=True, slots=True)
class ProfileRecord:
    user_id: str
    display_name: str
    role: UserRole
    status: AccountStatus
    created_at: datetime


class UserRepository(ABC):
    @abstractmethod
    async def find_or_create(self, user_id: str, *, email: str, email_verified: bool) -> User:
        """The user's profile, created with defaults (student, active) if the
        sign-up trigger has not created it yet."""

    @abstractmethod
    async def update_display_name(self, user_id: str, display_name: str) -> None: ...

    @abstractmethod
    async def find_profiles(self, user_ids: Sequence[str]) -> dict[str, ProfileRecord]: ...

    @abstractmethod
    async def change_status(self, user_id: str, status: AccountStatus, audit_entry: AdminAuditLog) -> bool:
        """Set the account status and write the audit entry in ONE transaction
        (FR-022: no unaudited admin action). False if there is no such profile."""
