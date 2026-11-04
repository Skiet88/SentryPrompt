"""Alembic environment: runs migrations against DATABASE_URL from settings.

Usage (from backend/):  uv run alembic upgrade head
"""

from __future__ import annotations

import asyncio

from alembic import context
from sqlalchemy.engine import Connection

from app.config.database import create_database_engine
from app.config.settings import Settings


def _run(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=None, transaction_per_migration=True)
    with context.begin_transaction():
        context.run_migrations()


async def _run_online() -> None:
    engine = create_database_engine(Settings())
    try:
        async with engine.connect() as async_connection:
            await async_connection.run_sync(_run)
            await async_connection.commit()
    finally:
        await engine.dispose()


if context.is_offline_mode():
    raise SystemExit("Offline SQL generation is not supported; run against a database.")
asyncio.run(_run_online())
