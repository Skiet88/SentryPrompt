"""Every migration can be undone and redone, on a database of its own."""

import asyncio
import secrets

import asyncpg
import pytest

from tests.repository.postgres.conftest import ADMIN_URL, SUPABASE_STANDINS, _with_database, run_alembic


async def _admin(sql: str) -> None:
    connection = await asyncpg.connect(ADMIN_URL)
    try:
        await connection.execute(sql)
    finally:
        await connection.close()


async def _columns(url: str) -> set[str]:
    connection = await asyncpg.connect(url)
    try:
        rows = await connection.fetch(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema = 'public' AND table_name = 'conversations'"
        )
    finally:
        await connection.close()
    return {r["column_name"] for r in rows}


@pytest.mark.skipif(not ADMIN_URL, reason="TEST_DATABASE_URL not set")
def test_title_migration_round_trip():
    name = f"sentry_migration_{secrets.token_hex(4)}"
    asyncio.run(_admin(f'CREATE DATABASE "{name}"'))
    url = _with_database(ADMIN_URL or "", name)
    try:

        async def standins() -> None:
            connection = await asyncpg.connect(url)
            try:
                await connection.execute(SUPABASE_STANDINS)
            finally:
                await connection.close()

        asyncio.run(standins())
        run_alembic(url, "upgrade", "head")
        assert "title_ciphertext" in asyncio.run(_columns(url))
        assert "title" not in asyncio.run(_columns(url))

        run_alembic(url, "downgrade", "0001")
        assert "title" in asyncio.run(_columns(url))
        assert "title_ciphertext" not in asyncio.run(_columns(url))

        run_alembic(url, "upgrade", "head")
        assert "title_ciphertext" in asyncio.run(_columns(url))
    finally:
        asyncio.run(_admin(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)'))
