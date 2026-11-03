from __future__ import annotations

from datetime import datetime

from app.domain import AdminActionType, AdminAuditLog
from app.exception import InvalidArgumentError

from . import _require


def build_admin_audit_log(
    admin_user_id: str,
    target_user_id: str,
    action_type: AdminActionType | str,
    *,
    details: str = "",
    log_id: str | None = None,
    timestamp: datetime | None = None,
) -> AdminAuditLog:
    admin = _require.identifier(admin_user_id, "admin_user_id")
    target = _require.identifier(target_user_id, "target_user_id")
    if admin == target:
        raise InvalidArgumentError("An admin cannot perform account actions on their own account")
    return AdminAuditLog(
        log_id=_require.new_or_given_id(log_id, "log_id"),
        admin_user_id=admin,
        target_user_id=target,
        action_type=_require.enum_value(AdminActionType, action_type, "action_type"),
        timestamp=_require.timestamp(timestamp, "timestamp"),
        details=details or "",
    )
