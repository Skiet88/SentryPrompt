from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain import AdminAuditLog, User

from .admin_models import AdminUserView, StatusChangeResult


class IAdminService(ABC):
    @abstractmethod
    async def list_users(self, admin: User, page: int, per_page: int) -> list[AdminUserView]: ...

    @abstractmethod
    async def suspend(self, admin: User, target_user_id: str, reason: str = "") -> StatusChangeResult: ...

    @abstractmethod
    async def reinstate(self, admin: User, target_user_id: str, reason: str = "") -> StatusChangeResult: ...

    @abstractmethod
    async def audit_log(self, admin: User, limit: int, offset: int = 0) -> list[AdminAuditLog]: ...
