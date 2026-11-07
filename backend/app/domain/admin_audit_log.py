from dataclasses import dataclass
from datetime import datetime

from .enums import AdminActionType


@dataclass(frozen=True, slots=True)
class AdminAuditLog:
    """Record of one admin action (FR-022). Account-level only: never
    references conversation content (NFR-013). Create via admin_audit_log_factory."""

    log_id: str
    admin_user_id: str
    target_user_id: str
    action_type: AdminActionType
    timestamp: datetime
    details: str
