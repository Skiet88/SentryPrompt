from __future__ import annotations

from datetime import datetime

from app.domain import AccountStatus, User, UserRole
from app.factory.user_factory import build_user
from app.util.clock import utc_now

from ..user_repository import UserRepository


class InMemoryUserRepository(UserRepository):
    def __init__(self) -> None:
        self._profiles: dict[str, dict[str, str | datetime]] = {}

    def set_profile(
        self,
        user_id: str,
        *,
        role: UserRole | str = UserRole.STUDENT,
        status: AccountStatus | str = AccountStatus.ACTIVE,
        display_name: str = "",
    ) -> None:
        """Test helper: set role/status the way an admin or the database would."""
        self._profiles[user_id] = {
            "display_name": display_name,
            "role": str(role),
            "status": str(status),
            "created_at": utc_now(),
        }

    async def find_or_create(self, user_id: str, *, email: str, email_verified: bool) -> User:
        if user_id not in self._profiles:
            self.set_profile(user_id)
        profile = self._profiles[user_id]
        return build_user(
            user_id,
            email,
            display_name=str(profile["display_name"]),
            role=str(profile["role"]),
            email_verified=email_verified,
            status=str(profile["status"]),
            created_at=profile["created_at"],  # type: ignore[arg-type]
        )

    async def update_display_name(self, user_id: str, display_name: str) -> None:
        self._profiles[user_id]["display_name"] = display_name
