from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain import AdminAuditLog


class AdminAuditLogRepository(ABC):
    """Read-only: entries are only written together with the status change
    they record (UserRepository.change_status), and never updated or deleted
    (FR-022; the database also rejects UPDATE, DELETE and TRUNCATE)."""

    @abstractmethod
    async def list_recent(self, limit: int, offset: int = 0) -> list[AdminAuditLog]:
        """Newest first."""
