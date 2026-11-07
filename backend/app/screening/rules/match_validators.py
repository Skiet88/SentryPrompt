"""Extra checks a regex match must pass before it counts as a flag.

Validators register themselves by name, so the config file can refer to them
("validator": "luhn") and a new validator is added without editing this
registry (open/closed).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar

from app.exception import ConfigurationError


class MatchValidator(ABC):
    name: ClassVar[str]

    @abstractmethod
    def is_valid(self, match_text: str) -> bool: ...


class ValidatorRegistry:
    def __init__(self) -> None:
        self._validators: dict[str, MatchValidator] = {}

    def register(self, validator_cls: type[MatchValidator]) -> type[MatchValidator]:
        if validator_cls.name in self._validators:
            raise ConfigurationError(f"Match validator '{validator_cls.name}' is already registered")
        self._validators[validator_cls.name] = validator_cls()
        return validator_cls

    def get(self, name: str) -> MatchValidator:
        if name not in self._validators:
            raise ConfigurationError(
                f"Unknown match validator '{name}'. Available: {', '.join(sorted(self._validators))}"
            )
        return self._validators[name]


validator_registry = ValidatorRegistry()


@validator_registry.register
class LuhnValidator(MatchValidator):
    """Every real card number passes the Luhn checksum, so random long digit
    runs are not reported as cards."""

    name = "luhn"

    def is_valid(self, match_text: str) -> bool:
        digits = [int(c) for c in match_text if c.isdigit()]
        if not digits:
            return False
        total = 0
        for position, digit in enumerate(reversed(digits)):
            if position % 2 == 1:
                digit *= 2
                if digit > 9:
                    digit -= 9
            total += digit
        return total % 10 == 0
