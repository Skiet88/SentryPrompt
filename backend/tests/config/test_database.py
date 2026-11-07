from types import SimpleNamespace

import pytest
from pydantic import SecretStr
from sqlalchemy.pool import NullPool

from app.config.database import async_database_url, create_database_engine


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("postgresql://u:p@host:5432/db", "postgresql+asyncpg://u:p@host:5432/db"),
        ("postgres://u:p@host/db", "postgresql+asyncpg://u:p@host/db"),
        ("postgresql://u@host/db?sslmode=require", "postgresql+asyncpg://u@host/db"),
        (
            "postgresql://u@host/db?application_name=x&sslmode=require",
            "postgresql+asyncpg://u@host/db?application_name=x",
        ),
    ],
)
def test_async_database_url(raw, expected):
    assert async_database_url(raw) == expected


def config(url: str | None, ssl: str = "require"):
    return SimpleNamespace(database_url=SecretStr(url) if url else None, database_ssl=ssl)


def test_engine_requires_url():
    with pytest.raises(ValueError, match="DATABASE_URL"):
        create_database_engine(config(None))


def test_engine_hides_parameters_and_password():
    engine = create_database_engine(config("postgresql://user:hunter2@db.example/postgres"))
    assert engine.dialect.name == "postgresql" and engine.driver == "asyncpg"
    assert engine.sync_engine.hide_parameters is True
    assert "hunter2" not in repr(engine) and "hunter2" not in str(engine.url)


def test_unpooled_engine():
    engine = create_database_engine(config("postgresql://u@h/db", "disable"), pooled=False)
    assert isinstance(engine.pool, NullPool)
