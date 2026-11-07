from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.domain import AccountStatus, AdminAuditLog, UserRole


@dataclass(frozen=True, slots=True)
class AdminUserView:
    """What an admin may see about an account: never any content."""

    user_id: str
    email: str
    email_verified: bool
    display_name: str
    role: UserRole
    status: AccountStatus
    created_at: datetime | None


@dataclass(frozen=True, slots=True)
class StatusChangeResult:
    user_id: str
    status: AccountStatus
    # Set when the status actually changed (an audit entry was written).
    audit_entry: AdminAuditLog | None
    # False when the Supabase login block could not be updated; the account
    # is still blocked/unblocked in our backend, and repeating the action retries.
    login_block_updated: bool
