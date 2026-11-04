from __future__ import annotations

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncEngine

from app.domain import User
from app.factory.user_factory import build_user

from ..user_repository import UserRepository
from .mappers import as_uuid
from .tables import profiles


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
