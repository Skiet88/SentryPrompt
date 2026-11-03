from dataclasses import dataclass
from datetime import datetime

from .enums import AccountStatus, UserRole


@dataclass(frozen=True, slots=True)
class User:
    """An account. Identity and password are managed by Supabase Auth, so
    there is no passwordHash here (AUTH_DESIGN.md §0). Create via user_factory."""

    user_id: str
    email: str
    display_name: str
    role: UserRole
    email_verified: bool
    status: AccountStatus
    created_at: datetime

    @property
    def is_admin(self) -> bool:
        return self.role is UserRole.ADMIN

    @property
    def can_submit_prompts(self) -> bool:
        """FR-014 and FR-021: verified and not suspended."""
        return self.email_verified and self.status is AccountStatus.ACTIVE
