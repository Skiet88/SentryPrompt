from __future__ import annotations

import logging
from collections import OrderedDict

from app.domain import EvaluationLogEntry

from ..evaluation_log_entry_repository import EvaluationLogEntryRepository

logger = logging.getLogger(__name__)

DEFAULT_CAPACITY = 10_000


class InMemoryEvaluationLogEntryRepository(EvaluationLogEntryRepository):
    """Bounded so a long-running process can't grow without limit; once full,
    the oldest entries are dropped (with a warning). Interim until step 5."""

    def __init__(self, capacity: int = DEFAULT_CAPACITY):
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        self._capacity = capacity
        self._entries: OrderedDict[str, EvaluationLogEntry] = OrderedDict()

    async def save(self, entity: EvaluationLogEntry) -> EvaluationLogEntry:
        if entity.log_id in self._entries:
            raise ValueError("Evaluation log entries are append-only")
        self._entries[entity.log_id] = entity
        if len(self._entries) > self._capacity:
            self._entries.popitem(last=False)
            logger.warning("In-memory evaluation log full; oldest entry dropped")
        return entity

    async def find_by_id(self, entity_id: str) -> EvaluationLogEntry | None:
        return self._entries.get(entity_id)

    async def find_all(self) -> list[EvaluationLogEntry]:
        return list(self._entries.values())

    async def find_by_result_id(self, result_id: str) -> list[EvaluationLogEntry]:
        return [e for e in self._entries.values() if e.result_id == result_id]
