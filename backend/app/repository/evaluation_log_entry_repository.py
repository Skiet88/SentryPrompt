from __future__ import annotations

from abc import abstractmethod

from app.domain import EvaluationLogEntry

from .base import ReadRepository, WriteRepository


class EvaluationLogEntryRepository(
    ReadRepository[EvaluationLogEntry, str], WriteRepository[EvaluationLogEntry]
):
    """Append-only (NFR-009): there is deliberately no delete or update."""

    @abstractmethod
    async def find_by_result_id(self, result_id: str) -> list[EvaluationLogEntry]: ...
