"""Request/response models for /api/profile (FR-018, FR-020).

The update request accepts only displayName: role, status, email, userId and
emailVerified can never be set by a client (no mass assignment).
"""

from __future__ import annotations

from datetime import datetime

from pydantic import Field

from app.domain import AccountStatus, User, UserRole
from app.factory.user_factory import MAX_DISPLAY_NAME_LENGTH

from .screening_schema import _CamelModel


class ProfileResponse(_CamelModel):
    user_id: str
    email: str
    display_name: str
    role: UserRole
    status: AccountStatus
    email_verified: bool
    created_at: datetime

    @classmethod
    def from_user(cls, user: User) -> ProfileResponse:
        return cls(
            user_id=user.user_id,
            email=user.email,
            display_name=user.display_name,
            role=user.role,
            status=user.status,
            email_verified=user.email_verified,
            created_at=user.created_at,
        )


class UpdateProfileRequest(_CamelModel):
    display_name: str = Field(max_length=MAX_DISPLAY_NAME_LENGTH)
