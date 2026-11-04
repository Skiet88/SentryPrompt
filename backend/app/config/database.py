"""Database engine for Supabase PostgreSQL (async SQLAlchemy + asyncpg)."""

from __future__ import annotations

from typing import Literal, Protocol
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pydantic import SecretStr
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.pool import NullPool

# libpq-style parameters that asyncpg does not accept in the URL; TLS is set
# explicitly through DATABASE_SSL instead.
_UNSUPPORTED_QUERY_PARAMS = {"sslmode", "sslrootcert", "sslcert", "sslkey"}


class DatabaseConfig(Protocol):
    @property
    def database_url(self) -> SecretStr | None: ...
    @property
    def database_ssl(self) -> Literal["require", "disable"]: ...


def async_database_url(raw_url: str) -> str:
    """Normalise a Supabase/PostgreSQL URL for the asyncpg driver."""
    parts = urlsplit(raw_url.strip())
    query = [(k, v) for k, v in parse_qsl(parts.query) if k not in _UNSUPPORTED_QUERY_PARAMS]
    return urlunsplit(("postgresql+asyncpg", parts.netloc, parts.path, urlencode(query), parts.fragment))


def create_database_engine(config: DatabaseConfig, *, pooled: bool = True) -> AsyncEngine:
    """pooled=False opens a fresh connection per use (tests and one-off scripts)."""
    if config.database_url is None:
        raise ValueError("DATABASE_URL is not set")
    extra: dict[str, object] = {} if pooled else {"poolclass": NullPool}
    return create_async_engine(
        async_database_url(config.database_url.get_secret_value()),
        pool_pre_ping=True,
        # Never log SQL parameters (they could include personal data).
        echo=False,
        hide_parameters=True,
        connect_args={
            # "require" encrypts the connection (TLS) to Supabase.
            "ssl": config.database_ssl,
            # Supabase's connection pooler does not support prepared-statement
            # caching; disabling it keeps both pooler modes working.
            "statement_cache_size": 0,
        },
        **extra,
    )
