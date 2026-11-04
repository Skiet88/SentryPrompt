from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import insert as plain_insert
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncEngine

from app.domain import AccountStatus, AdminAuditLog, User, UserRole
from app.factory.admin_audit_log_factory import build_admin_audit_log
from app.factory.user_factory import build_user

from ..admin_audit_log_repository import AdminAuditLogRepository
from ..user_repository import ProfileRecord, UserRepository
from .mappers import as_uuid
from .tables import admin_audit_log, profiles


class PostgresUserRepository(UserRepository):
    def __init__(self, engine: AsyncEngine):
        self._engine = engine

    async def find_or_create(self, user_id: str, *, email: str, email_verified: bool) -> User:
        uid = as_uuid(user_id)
        async with self._engine.begin() as connection:
            # Normally created by the sign-up trigger; this covers accounts
            # created before the tables existed. Defaults: student, active.
            await connection.execute(insert(profiles).values(id=uid).on_conflict_do_nothing())
            row = (await connection.execute(select(profiles).where(profiles.c.id == uid))).mappings().one()
        return build_user(
            user_id,
            email,
            display_name=row["display_name"],
            role=row["role"],
            email_verified=email_verified,
            status=row["status"],
            created_at=row["created_at"],
        )

    async def update_display_name(self, user_id: str, display_name: str) -> None:
        async with self._engine.begin() as connection:
            await connection.execute(
                update(profiles).where(profiles.c.id == as_uuid(user_id)).values(display_name=display_name)
            )

    async def find_profiles(self, user_ids: Sequence[str]) -> dict[str, ProfileRecord]:
        if not user_ids:
            return {}
        async with self._engine.connect() as connection:
            rows = (
                (
                    await connection.execute(
                        select(profiles).where(profiles.c.id.in_([as_uuid(u) for u in user_ids]))
                    )
                )
                .mappings()
                .all()
            )
        return {
            str(r["id"]): ProfileRecord(
                user_id=str(r["id"]),
                display_name=r["display_name"],
                role=UserRole(r["role"]),
                status=AccountStatus(r["status"]),
                created_at=r["created_at"],
            )
            for r in rows
        }

    async def change_status(self, user_id: str, status: AccountStatus, audit_entry: AdminAuditLog) -> bool:
        async with self._engine.begin() as connection:
            result = await connection.execute(
                update(profiles).where(profiles.c.id == as_uuid(user_id)).values(status=status.value)
            )
            if not result.rowcount:
                return False
            await connection.execute(
                plain_insert(admin_audit_log),
                [
                    {
                        "id": as_uuid(audit_entry.log_id),
                        "admin_user_id": as_uuid(audit_entry.admin_user_id),
                        "target_user_id": as_uuid(audit_entry.target_user_id),
                        "action_type": audit_entry.action_type.value,
                        "timestamp": audit_entry.timestamp,
                        "details": audit_entry.details,
                    }
                ],
            )
        return True


class PostgresAdminAuditLogRepository(AdminAuditLogRepository):
    def __init__(self, engine: AsyncEngine):
        self._engine = engine

    async def list_recent(self, limit: int, offset: int = 0) -> list[AdminAuditLog]:
        async with self._engine.connect() as connection:
            rows = (
                (
                    await connection.execute(
                        select(admin_audit_log)
                        .order_by(admin_audit_log.c.timestamp.desc(), admin_audit_log.c.id)
                        .limit(limit)
                        .offset(offset)
                    )
                )
                .mappings()
                .all()
            )
        return [
            build_admin_audit_log(
                admin_user_id=str(r["admin_user_id"]),
                target_user_id=str(r["target_user_id"]),
                action_type=r["action_type"],
                details=r["details"],
                log_id=str(r["id"]),
                timestamp=r["timestamp"],
            )
            for r in rows
        ]
