from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

from app.domain import AccountStatus, AdminAuditLog, User, UserRole
from app.factory.user_factory import build_user
from app.util.clock import utc_now

from ..admin_audit_log_repository import AdminAuditLogRepository
from ..user_repository import ProfileRecord, UserRepository


class InMemoryUserRepository(UserRepository, AdminAuditLogRepository):
    """Profiles and the admin audit log (tests and development without a database)."""

    def __init__(self) -> None:
        self._profiles: dict[str, dict[str, str | datetime]] = {}
        self._audit: list[AdminAuditLog] = []

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

    async def find_profiles(self, user_ids: Sequence[str]) -> dict[str, ProfileRecord]:
        return {
            uid: ProfileRecord(
                user_id=uid,
                display_name=str(p["display_name"]),
                role=UserRole(str(p["role"])),
                status=AccountStatus(str(p["status"])),
                created_at=p["created_at"],  # type: ignore[arg-type]
            )
            for uid in user_ids
            if (p := self._profiles.get(uid)) is not None
        }

    async def change_status(self, user_id: str, status: AccountStatus, audit_entry: AdminAuditLog) -> bool:
        if user_id not in self._profiles:
            return False
        self._profiles[user_id]["status"] = status.value
        self._audit.append(audit_entry)
        return True

    async def list_recent(self, limit: int, offset: int = 0) -> list[AdminAuditLog]:
        newest_first = sorted(self._audit, key=lambda e: e.timestamp, reverse=True)
        return newest_first[offset : offset + limit]
