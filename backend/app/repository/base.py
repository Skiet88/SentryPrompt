"""Small repository interfaces (REPOSITORY_DESIGN.md §2), split by capability
so each repository exposes only what its entity allows (interface segregation):
an append-only log simply doesn't inherit DeleteRepository."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")
ID = TypeVar("ID")


class ReadRepository(ABC, Generic[T, ID]):
    @abstractmethod
    async def find_by_id(self, entity_id: ID) -> T | None: ...

    @abstractmethod
    async def find_all(self) -> list[T]: ...


class WriteRepository(ABC, Generic[T]):
    @abstractmethod
    async def save(self, entity: T) -> T: ...


class DeleteRepository(ABC, Generic[ID]):
    @abstractmethod
    async def delete(self, entity_id: ID) -> None: ...
