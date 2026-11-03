import pytest

from app.util.validation import is_blank, is_probability


@pytest.mark.parametrize("value", [None, "", "   ", "\n"])
def test_blank_values(value):
    assert is_blank(value)


def test_non_blank_value():
    assert not is_blank("text")


@pytest.mark.parametrize("value", [0, 0.5, 1, 1.0])
def test_valid_probabilities(value):
    assert is_probability(value)


@pytest.mark.parametrize("value", [-0.1, 1.01, "0.5", True, None])
def test_invalid_probabilities(value):
    assert not is_probability(value)


@pytest.mark.parametrize("value, expected", [
    ("thabo@example.com", True), ("a@b.co", True),
    ("no-at-sign", False), ("a@b", False), ("a b@c.com", False), (None, False),
])
def test_is_valid_email(value, expected):
    from app.util.validation import is_valid_email

    assert is_valid_email(value) is expected


def test_is_timezone_aware():
    from datetime import datetime, timezone

    from app.util.validation import is_timezone_aware

    assert is_timezone_aware(datetime.now(timezone.utc))
    assert not is_timezone_aware(datetime(2026, 1, 1))


@pytest.mark.parametrize("value, expected", [(r"\d+", True), ("([", False), ("", False)])
def test_is_valid_regex(value, expected):
    from app.util.validation import is_valid_regex

    assert is_valid_regex(value) is expected
