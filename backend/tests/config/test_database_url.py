"""DATABASE_URL mistakes give a helpful error that never repeats the URL."""

import pytest
from pydantic import ValidationError

from app.config.database_url import InvalidDatabaseUrl, parse_database_url
from app.config.settings import Settings

PASSWORD = "CorrectHorse42"  # noqa: S105 - made-up value for the test
POOLER = "aws-0-eu-central-1.pooler.supabase.com"


@pytest.mark.parametrize(
    "url, hint",
    [
        (f"postgresql://postgres.abc:[{PASSWORD}]@{POOLER}:5432/postgres", "square brackets"),
        (f"postgresql://postgres.abc:{PASSWORD}#x@{POOLER}:5432/postgres", "'#'"),
        (f"postgresql://postgres.abc:{PASSWORD}@x@{POOLER}:5432/postgres", "more than one '@'"),
        (f"postgresql://postgres.abc:{PASSWORD}@{POOLER}:notaport/postgres", "not a valid connection string"),
        (f"postgresql://postgres.abc:{PASSWORD}@:5432/postgres", "no server address"),
        (f"mysql://postgres.abc:{PASSWORD}@{POOLER}/db", "postgresql://"),
    ],
    ids=["brackets", "hash", "two_ats", "bad_port", "no_host", "wrong_scheme"],
)
def test_mistakes_are_explained_without_repeating_the_url(url, hint):
    with pytest.raises(InvalidDatabaseUrl) as caught:
        parse_database_url(url)
    message = str(caught.value)
    assert hint in message
    assert PASSWORD not in message and POOLER not in message
    assert caught.value.__cause__ is None


def test_settings_error_does_not_leak_the_password():
    with pytest.raises(ValidationError) as caught:
        Settings(
            _env_file=None, database_url=f"postgresql://postgres.abc:[{PASSWORD}]@{POOLER}:5432/postgres"
        )
    assert "square brackets" in str(caught.value)
    assert PASSWORD not in str(caught.value)


def test_valid_pooler_url_is_accepted():
    parts = parse_database_url(f"postgresql://postgres.abc:{PASSWORD}@{POOLER}:5432/postgres")
    assert (parts.hostname, parts.port, parts.username) == (POOLER, 5432, "postgres.abc")


def test_url_encoded_special_characters_are_accepted():
    assert parse_database_url(f"postgresql://postgres.abc:p%40ss%23word@{POOLER}:5432/postgres").port == 5432
