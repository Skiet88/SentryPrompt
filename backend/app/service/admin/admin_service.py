"""Suspend and reinstate accounts, with every action audited (FR-021, FR-022).

- The status change and its audit entry are written in one transaction, so
  there is never an unaudited action.
- Then the Supabase login block is updated. If that fails, the account is
  still blocked or unblocked by our backend (it checks status on every
  request), the result says so, and repeating the action retries the block
  without writing a second audit entry (AUTH_DESIGN.md §0.1).
- An admin cannot act on their own account or on another admin; admins are
  promoted only by hand in the database (no endpoint changes roles).
- This service has no access to conversations or messages (NFR-013).
"""

from __future__ import annotations

import logging

from app.domain import AccountStatus, AdminActionType, AdminAuditLog, User, UserRole
from app.exception import AuthUnavailableError, ForbiddenError, InvalidArgumentError, NotFoundError
from app.factory.admin_audit_log_factory import build_admin_audit_log
from app.repository.admin_audit_log_repository import AdminAuditLogRepository
from app.repository.user_repository import UserRepository
from app.service.auth.identity_provider import IdentityProvider

from .admin_models import AdminUserView, StatusChangeResult
from .i_admin_service import IAdminService

logger = logging.getLogger(__name__)

MAX_REASON_LENGTH = 500
MAX_PAGE_SIZE = 100


class AdminService(IAdminService):
    def __init__(self, identity: IdentityProvider, users: UserRepository, audit: AdminAuditLogRepository):
        self._identity = identity
        self._users = users
        self._audit = audit

    async def list_users(self, admin: User, page: int, per_page: int) -> list[AdminUserView]:
        self._require_admin(admin)
        if page < 1 or not 1 <= per_page <= MAX_PAGE_SIZE:
            raise InvalidArgumentError(f"page must be >= 1 and per_page between 1 and {MAX_PAGE_SIZE}")
        accounts = await self._identity.list_users(page, per_page)
        profiles = await self._users.find_profiles([a.user_id for a in accounts])
        views = []
        for account in accounts:
            profile = profiles.get(account.user_id)
            views.append(
                AdminUserView(
                    user_id=account.user_id,
                    email=account.email,
                    email_verified=account.email_verified,
                    display_name=profile.display_name if profile else "",
                    role=profile.role if profile else UserRole.STUDENT,
                    status=profile.status if profile else AccountStatus.ACTIVE,
                    created_at=profile.created_at if profile else None,
                )
            )
        return views

    async def suspend(self, admin: User, target_user_id: str, reason: str = "") -> StatusChangeResult:
        return await self._change(
            admin, target_user_id, AccountStatus.SUSPENDED, AdminActionType.SUSPEND, reason
        )

    async def reinstate(self, admin: User, target_user_id: str, reason: str = "") -> StatusChangeResult:
        return await self._change(
            admin, target_user_id, AccountStatus.ACTIVE, AdminActionType.REINSTATE, reason
        )

    async def audit_log(self, admin: User, limit: int, offset: int = 0) -> list[AdminAuditLog]:
        self._require_admin(admin)
        if not 1 <= limit <= MAX_PAGE_SIZE or offset < 0:
            raise InvalidArgumentError(f"limit must be between 1 and {MAX_PAGE_SIZE}, offset >= 0")
        return await self._audit.list_recent(limit, offset)

    async def _change(
        self, admin: User, target_user_id: str, status: AccountStatus, action: AdminActionType, reason: str
    ) -> StatusChangeResult:
        self._require_admin(admin)
        if target_user_id == admin.user_id:
            raise InvalidArgumentError("You cannot change the status of your own account.")
        if len(reason) > MAX_REASON_LENGTH:
            raise InvalidArgumentError(f"reason cannot be longer than {MAX_REASON_LENGTH} characters")

        profile = (await self._users.find_profiles([target_user_id])).get(target_user_id)
        if profile is None:
            raise NotFoundError("Account not found.")
        if profile.role is UserRole.ADMIN:
            raise ForbiddenError("Administrator accounts cannot be suspended here.", "target_is_admin")

        audit_entry: AdminAuditLog | None = None
        if profile.status is not status:
            audit_entry = build_admin_audit_log(admin.user_id, target_user_id, action, details=reason.strip())
            if not await self._users.change_status(target_user_id, status, audit_entry):
                raise NotFoundError("Account not found.")
            logger.info("Admin %s: %s %s", admin.user_id, action.value, target_user_id)

        try:
            await self._identity.set_banned(target_user_id, banned=status is AccountStatus.SUSPENDED)
            login_block_updated = True
        except AuthUnavailableError:
            logger.warning("Login block not updated for %s; repeat the action to retry", target_user_id)
            login_block_updated = False
        return StatusChangeResult(target_user_id, status, audit_entry, login_block_updated)

    @staticmethod
    def _require_admin(admin: User) -> None:
        # The API already requires an admin; checked again here so the
        # service is safe on its own (defence in depth).
        if not admin.is_admin or admin.status is not AccountStatus.ACTIVE or not admin.email_verified:
            raise ForbiddenError("This action is for administrators only.", "admin_only")
