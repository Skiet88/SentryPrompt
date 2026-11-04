"""Request/response models for /api/admin (FR-021, FR-022).

Account-level fields only: nothing here can carry conversation or message
content (NFR-013). The status-change request accepts only an optional reason;
the target comes from the URL and the admin from the login (no mass assignment).
"""

from __future__ import annotations

from datetime import datetime

from pydantic import Field

from app.domain import AccountStatus, AdminActionType, AdminAuditLog, UserRole
from app.service.admin.admin_models import AdminUserView, StatusChangeResult
from app.service.admin.admin_service import MAX_REASON_LENGTH

from .screening_schema import _CamelModel


class AdminUserResponse(_CamelModel):
    user_id: str
    email: str
    email_verified: bool
    display_name: str
    role: UserRole
    status: AccountStatus
    created_at: datetime | None

    @classmethod
    def from_view(cls, view: AdminUserView) -> AdminUserResponse:
        return cls(
            user_id=view.user_id,
            email=view.email,
            email_verified=view.email_verified,
            display_name=view.display_name,
            role=view.role,
            status=view.status,
            created_at=view.created_at,
        )


class StatusChangeRequest(_CamelModel):
    reason: str = Field(default="", max_length=MAX_REASON_LENGTH)


class StatusChangeResponse(_CamelModel):
    user_id: str
    status: AccountStatus
    # Null when the account already had this status (nothing new to audit).
    audit_log_id: str | None
    # False: blocked/unblocked in SentryPrompt, but the Supabase login block
    # could not be updated yet; repeat the action to retry.
    login_block_updated: bool

    @classmethod
    def from_result(cls, result: StatusChangeResult) -> StatusChangeResponse:
        return cls(
            user_id=result.user_id,
            status=result.status,
            audit_log_id=result.audit_entry.log_id if result.audit_entry else None,
            login_block_updated=result.login_block_updated,
        )


class AuditLogEntryResponse(_CamelModel):
    log_id: str
    admin_user_id: str
    target_user_id: str
    action_type: AdminActionType
    timestamp: datetime
    details: str

    @classmethod
    def from_entry(cls, entry: AdminAuditLog) -> AuditLogEntryResponse:
        return cls(
            log_id=entry.log_id,
            admin_user_id=entry.admin_user_id,
            target_user_id=entry.target_user_id,
            action_type=entry.action_type,
            timestamp=entry.timestamp,
            details=entry.details,
        )
