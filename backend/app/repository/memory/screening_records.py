"""In-memory screening results, flagged spans and record writer: used by
tests, and by development when no DATABASE_URL is configured."""

from __future__ import annotations

from collections import OrderedDict
from collections.abc import Sequence

from app.domain import EvaluationLogEntry, FlaggedSpan, ScreeningResult

from ..flagged_span_repository import FlaggedSpanRepository
from ..screening_record_writer import ScreeningRecordWriter
from ..screening_result_repository import ScreeningResultRepository
from .evaluation_log_entry_repository import DEFAULT_CAPACITY, InMemoryEvaluationLogEntryRepository


class InMemoryScreeningResultRepository(ScreeningResultRepository):
    def __init__(self, capacity: int = DEFAULT_CAPACITY):
        self._capacity = capacity
        self._items: OrderedDict[str, ScreeningResult] = OrderedDict()

    async def save(self, entity: ScreeningResult) -> ScreeningResult:
        self._items[entity.result_id] = entity
        while len(self._items) > self._capacity:
            self._items.popitem(last=False)
        return entity

    async def find_by_id(self, entity_id: str) -> ScreeningResult | None:
        return self._items.get(entity_id)

    async def find_all(self) -> list[ScreeningResult]:
        return list(self._items.values())

    async def find_by_prompt_id(self, prompt_id: str) -> list[ScreeningResult]:
        return [r for r in self._items.values() if r.prompt_id == prompt_id]


class InMemoryFlaggedSpanRepository(FlaggedSpanRepository):
    def __init__(self, capacity: int = DEFAULT_CAPACITY * 4):
        self._capacity = capacity
        self._items: OrderedDict[str, FlaggedSpan] = OrderedDict()

    async def save(self, entity: FlaggedSpan) -> FlaggedSpan:
        self._items[entity.span_id] = entity
        while len(self._items) > self._capacity:
            self._items.popitem(last=False)
        return entity

    async def find_by_id(self, entity_id: str) -> FlaggedSpan | None:
        return self._items.get(entity_id)

    async def find_all(self) -> list[FlaggedSpan]:
        return list(self._items.values())

    async def find_by_result_id(self, result_id: str) -> list[FlaggedSpan]:
        return [s for s in self._items.values() if s.result_id == result_id]


class InMemoryScreeningRecordWriter(ScreeningRecordWriter):
    def __init__(
        self,
        results: InMemoryScreeningResultRepository | None = None,
        spans: InMemoryFlaggedSpanRepository | None = None,
        log: InMemoryEvaluationLogEntryRepository | None = None,
    ):
        self.results = results or InMemoryScreeningResultRepository()
        self.spans = spans or InMemoryFlaggedSpanRepository()
        self.log = log or InMemoryEvaluationLogEntryRepository()

    async def record(
        self,
        result: ScreeningResult,
        spans: Sequence[FlaggedSpan],
        log_entry: EvaluationLogEntry,
    ) -> None:
        await self.results.save(result)
        for span in spans:
            await self.spans.save(span)
        await self.log.save(log_entry)
