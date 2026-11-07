"""Checks a DATABASE_URL without ever repeating it.

Errors from URL parsing can contain the URL itself, including the password
(observed in practice: a password left in [square brackets] was echoed in a
traceback). Every check here raises a fixed message instead.
"""

from __future__ import annotations

from urllib.parse import SplitResult, urlsplit

HELP = (
    "Use the Session pooler connection string from Supabase (Connect -> Connection string), "
    "replace [YOUR-PASSWORD] including the square brackets, and URL-encode any special "
    "characters in the password (or use letters and numbers only)."
)


class InvalidDatabaseUrl(ValueError):
    pass


def parse_database_url(raw_url: str) -> SplitResult:
    """Parse and sanity-check a PostgreSQL URL. Messages never include the URL."""
    url = raw_url.strip()
    if "[" in url or "]" in url:
        raise InvalidDatabaseUrl(f"DATABASE_URL contains square brackets. {HELP}")
    if "#" in url:
        raise InvalidDatabaseUrl(f"DATABASE_URL contains '#'. {HELP}")
    try:
        parts = urlsplit(url)
        host, _port = parts.hostname, parts.port  # .port raises on a bad port
    except ValueError:
        raise InvalidDatabaseUrl(f"DATABASE_URL is not a valid connection string. {HELP}") from None
    if parts.scheme not in ("postgresql", "postgres", "postgresql+asyncpg"):
        raise InvalidDatabaseUrl("DATABASE_URL must be a postgresql:// connection string")
    if parts.netloc.count("@") > 1:
        raise InvalidDatabaseUrl(f"DATABASE_URL has more than one '@'. {HELP}")
    if not host:
        raise InvalidDatabaseUrl(f"DATABASE_URL has no server address. {HELP}")
    return parts
