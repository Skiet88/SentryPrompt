"""Integration tests against a real PostgreSQL database.

Set TEST_DATABASE_URL to a server you can create databases on, e.g.
postgresql://postgres@127.0.0.1:54329/postgres (local) or the CI service.
Each test session creates a fresh database with stand-ins for what Supabase
provides (auth.users, the anon/authenticated roles), applies the migrations
with the real `alembic` command, and drops the database afterwards. Without
TEST_DATABASE_URL these tests are skipped.
"""

from __future__ import annotations

import asyncio
import os
import secrets
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlsplit, urlunsplit

import asyncpg
import pytest
from pydantic import SecretStr
from sqlalchemy.ext.asyncio import AsyncEngine

from app.config.database import create_database_engine
from app.repository.postgres.tables import ALL_TABLES

BACKEND_DIR = Path(__file__).resolve().parents[3]
ADMIN_URL = os.environ.get("TEST_DATABASE_URL")

SUPABASE_STANDINS = """
CREATE SCHEMA auth;
CREATE TABLE auth.users (id uuid PRIMARY KEY, email text);
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN CREATE ROLE anon; END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
        CREATE ROLE authenticated;
    END IF;
END
$$;
GRANT USAGE ON SCHEMA public TO anon, authenticated;
"""


def _with_database(url: str, name: str) -> str:
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, f"/{name}", parts.query, parts.fragment))


def run_alembic(database_url: str, *args: str) -> None:
    env = {**os.environ, "DATABASE_URL": database_url, "DATABASE_SSL": "disable"}
    # Safe: fixed command (this Python, the alembic module, test-defined args).
    subprocess.run(  # noqa: S603
        [sys.executable, "-m", "alembic", *args],
        cwd=BACKEND_DIR,
        env=env,
        check=True,
        capture_output=True,
    )


@pytest.fixture(scope="session")
def database_url() -> Iterator[str]:
    if not ADMIN_URL:
        pytest.skip("TEST_DATABASE_URL not set: PostgreSQL integration tests skipped")
    name = f"sentry_test_{secrets.token_hex(4)}"

    async def admin(sql: str) -> None:
        connection = await asyncpg.connect(ADMIN_URL)
        try:
            await connection.execute(sql)
        finally:
            await connection.close()

    async def setup() -> None:
        await admin(f'CREATE DATABASE "{name}"')
        connection = await asyncpg.connect(_with_database(ADMIN_URL, name))
        try:
            await connection.execute(SUPABASE_STANDINS)
        finally:
            await connection.close()

    asyncio.run(setup())
    url = _with_database(ADMIN_URL, name)
    run_alembic(url, "upgrade", "head")
    try:
        yield url
    finally:
        asyncio.run(admin(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)'))


@pytest.fixture
def engine(database_url: str) -> Iterator[AsyncEngine]:
    config = SimpleNamespace(database_url=SecretStr(database_url), database_ssl="disable")
    engine = create_database_engine(config, pooled=False)
    yield engine
    asyncio.run(_reset(engine))
    asyncio.run(engine.dispose())


async def _reset(engine: AsyncEngine) -> None:
    """Empty every table between tests. The append-only triggers reject
    TRUNCATE, so they are switched off for this transaction only; that needs
    superuser rights, which the app's database role on Supabase does not have."""
    tables = ", ".join(f"{t.schema}.{t.name}" for t in ALL_TABLES)
    async with engine.begin() as connection:
        await connection.exec_driver_sql("SET LOCAL session_replication_role = replica")
        await connection.exec_driver_sql(f"TRUNCATE {tables}, auth.users CASCADE")


def run(coroutine):
    return asyncio.run(coroutine)
