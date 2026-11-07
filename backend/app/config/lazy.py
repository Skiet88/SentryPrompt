"""Builds a value on first use, then reuses it."""

from __future__ import annotations

from collections.abc import Callable
from typing import Generic, Protocol, TypeVar

T = TypeVar("T")
T_co = TypeVar("T_co", covariant=True)


class Provider(Protocol[T_co]):
    """Gives a value on request, so it is only built when actually needed."""

    def get(self) -> T_co: ...


class Lazy(Generic[T]):
    def __init__(self, factory: Callable[[], T]):
        self._factory = factory
        self._value: T | None = None

    def get(self) -> T:
        if self._value is None:
            self._value = self._factory()
        return self._value
