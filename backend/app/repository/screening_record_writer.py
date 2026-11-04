"""Unit of Work for the screening write path: a screening's result, its
flagged spans and its evaluation log entry are saved together or not at all,
so research data is never left half-written."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from app.domain import EvaluationLogEntry, FlaggedSpan, ScreeningResult


class ScreeningRecordWriter(ABC):
    @abstractmethod
    async def record(
        self,
        result: ScreeningResult,
        spans: Sequence[FlaggedSpan],
        log_entry: EvaluationLogEntry,
    ) -> None: ...
