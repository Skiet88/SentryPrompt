import pytest

from app.exception import ConfigurationError
from app.screening.rules.match_validators import (
    LuhnValidator,
    MatchValidator,
    ValidatorRegistry,
    validator_registry,
)


@pytest.mark.parametrize(
    "number, valid",
    [
        ("4539 1488 0343 6467", True),
        ("4111111111111111", True),
        ("4111-1111-1111-1112", False),
        ("9203105800089", False),
        ("", False),
    ],
)
def test_luhn(number, valid):
    assert LuhnValidator().is_valid(number) is valid


def test_luhn_is_registered():
    assert isinstance(validator_registry.get("luhn"), LuhnValidator)


def test_unknown_validator_rejected():
    with pytest.raises(ConfigurationError, match="Unknown match validator"):
        validator_registry.get("checksum42")


def test_new_validator_added_without_editing_registry():
    registry = ValidatorRegistry()

    @registry.register
    class AlwaysValid(MatchValidator):
        name = "always"

        def is_valid(self, match_text: str) -> bool:
            return True

    assert registry.get("always").is_valid("x")
    with pytest.raises(ConfigurationError, match="already registered"):
        registry.register(AlwaysValid)
