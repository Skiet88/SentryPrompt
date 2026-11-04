from __future__ import annotations

from abc import abstractmethod

from app.domain import FlaggedSpan

from .base import ReadRepository, WriteRepository


class FlaggedSpanRepository(ReadRepository[FlaggedSpan, str], WriteRepository[FlaggedSpan]):
    @abstractmethod
    async def find_by_result_id(self, result_id: str) -> list[FlaggedSpan]: ...
