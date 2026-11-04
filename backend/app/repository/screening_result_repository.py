from __future__ import annotations

from abc import abstractmethod

from app.domain import ScreeningResult

from .base import ReadRepository, WriteRepository


class ScreeningResultRepository(ReadRepository[ScreeningResult, str], WriteRepository[ScreeningResult]):
    @abstractmethod
    async def find_by_prompt_id(self, prompt_id: str) -> list[ScreeningResult]: ...
