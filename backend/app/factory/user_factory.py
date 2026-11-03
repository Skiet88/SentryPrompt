from __future__ import annotations

from datetime import datetime

from app.domain import AccountStatus, User, UserRole
from app.exception import InvalidArgumentError
from app.util.validation import is_blank, is_valid_email

from . import _require

MAX_DISPLAY_NAME_LENGTH = 100


def build_user(
    user_id: str,
    email: str,
    *,
    display_name: str = "",
    role: UserRole | str = UserRole.STUDENT,
    email_verified: bool = False,
    status: AccountStatus | str = AccountStatus.ACTIVE,
    created_at: datetime | None = None,
) -> User:
    """user_id is required: it is the ID Supabase Auth assigned to the account."""
    email = email.strip().lower() if isinstance(email, str) else email
    if not is_valid_email(email):
        raise InvalidArgumentError("email must be a valid email address")
    if not isinstance(email_verified, bool):
        raise InvalidArgumentError("email_verified must be true or false")
    name = "" if is_blank(display_name) else _require.text(
        display_name.strip(), "display_name", MAX_DISPLAY_NAME_LENGTH
    )
    return User(
        user_id=_require.identifier(user_id, "user_id"),
        email=email,
        display_name=name,
        role=_require.enum_value(UserRole, role, "role"),
        email_verified=email_verified,
        status=_require.enum_value(AccountStatus, status, "status"),
        created_at=_require.timestamp(created_at, "created_at"),
    )
