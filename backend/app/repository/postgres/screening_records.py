"""PostgreSQL repositories for the evaluation schema (content-free, NFR-009)."""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncEngine

from app.domain import EvaluationLogEntry, FlaggedSpan, ScreeningResult

from ..evaluation_log_entry_repository import EvaluationLogEntryRepository
from ..flagged_span_repository import FlaggedSpanRepository
from ..screening_record_writer import ScreeningRecordWriter
from ..screening_result_repository import ScreeningResultRepository
from . import mappers
from .tables import evaluation_log_entries, flagged_spans, screening_results


class PostgresScreeningResultRepository(ScreeningResultRepository):
    def __init__(self, engine: AsyncEngine):
        self._engine = engine

    async def save(self, entity: ScreeningResult) -> ScreeningResult:
        async with self._engine.begin() as connection:
            await connection.execute(insert(screening_results), [mappers.screening_result_to_row(entity)])
        return entity

    async def find_by_id(self, entity_id: str) -> ScreeningResult | None:
        async with self._engine.connect() as connection:
            row = (
                (
                    await connection.execute(
                        select(screening_results).where(screening_results.c.id == mappers.as_uuid(entity_id))
                    )
                )
                .mappings()
                .first()
            )
        return mappers.screening_result_from_row(row) if row else None

    async def find_all(self) -> list[ScreeningResult]:
        async with self._engine.connect() as connection:
            rows = (await connection.execute(select(screening_results))).mappings().all()
        return [mappers.screening_result_from_row(r) for r in rows]

    async def find_by_prompt_id(self, prompt_id: str) -> list[ScreeningResult]:
        async with self._engine.connect() as connection:
            rows = (
                (
                    await connection.execute(
                        select(screening_results).where(
                            screening_results.c.prompt_id == mappers.as_uuid(prompt_id)
                        )
                    )
                )
                .mappings()
                .all()
            )
        return [mappers.screening_result_from_row(r) for r in rows]


class PostgresFlaggedSpanRepository(FlaggedSpanRepository):
    def __init__(self, engine: AsyncEngine):
        self._engine = engine

    async def save(self, entity: FlaggedSpan) -> FlaggedSpan:
        async with self._engine.begin() as connection:
            await connection.execute(insert(flagged_spans), [mappers.flagged_span_to_row(entity)])
        return entity

    async def find_by_id(self, entity_id: str) -> FlaggedSpan | None:
        async with self._engine.connect() as connection:
            row = (
                (
                    await connection.execute(
                        select(flagged_spans).where(flagged_spans.c.id == mappers.as_uuid(entity_id))
                    )
                )
                .mappings()
                .first()
            )
        return mappers.flagged_span_from_row(row) if row else None

    async def find_all(self) -> list[FlaggedSpan]:
        async with self._engine.connect() as connection:
            rows = (await connection.execute(select(flagged_spans))).mappings().all()
        return [mappers.flagged_span_from_row(r) for r in rows]

    async def find_by_result_id(self, result_id: str) -> list[FlaggedSpan]:
        async with self._engine.connect() as connection:
            rows = (
                (
                    await connection.execute(
                        select(flagged_spans)
                        .where(flagged_spans.c.result_id == mappers.as_uuid(result_id))
                        .order_by(flagged_spans.c.start_index)
                    )
                )
                .mappings()
                .all()
            )
        return [mappers.flagged_span_from_row(r) for r in rows]


class PostgresEvaluationLogEntryRepository(EvaluationLogEntryRepository):
    """Append-only: the database rejects UPDATE and DELETE (migration 0001)."""

    def __init__(self, engine: AsyncEngine):
        self._engine = engine

    async def save(self, entity: EvaluationLogEntry) -> EvaluationLogEntry:
        async with self._engine.begin() as connection:
            await connection.execute(
                insert(evaluation_log_entries), [mappers.evaluation_log_entry_to_row(entity)]
            )
        return entity

    async def find_by_id(self, entity_id: str) -> EvaluationLogEntry | None:
        async with self._engine.connect() as connection:
            row = (
                (
                    await connection.execute(
                        select(evaluation_log_entries).where(
                            evaluation_log_entries.c.id == mappers.as_uuid(entity_id)
                        )
                    )
                )
                .mappings()
                .first()
            )
        return mappers.evaluation_log_entry_from_row(row) if row else None

    async def find_all(self) -> list[EvaluationLogEntry]:
        async with self._engine.connect() as connection:
            rows = (await connection.execute(select(evaluation_log_entries))).mappings().all()
        return [mappers.evaluation_log_entry_from_row(r) for r in rows]

    async def find_by_result_id(self, result_id: str) -> list[EvaluationLogEntry]:
        async with self._engine.connect() as connection:
            rows = (
                (
                    await connection.execute(
                        select(evaluation_log_entries).where(
                            evaluation_log_entries.c.result_id == mappers.as_uuid(result_id)
                        )
                    )
                )
                .mappings()
                .all()
            )
        return [mappers.evaluation_log_entry_from_row(r) for r in rows]


class PostgresScreeningRecordWriter(ScreeningRecordWriter):
    """Writes result, spans and log entry in one transaction."""

    def __init__(self, engine: AsyncEngine):
        self._engine = engine

    async def record(
        self,
        result: ScreeningResult,
        spans: Sequence[FlaggedSpan],
        log_entry: EvaluationLogEntry,
    ) -> None:
        async with self._engine.begin() as connection:
            await connection.execute(insert(screening_results), [mappers.screening_result_to_row(result)])
            if spans:
                await connection.execute(
                    insert(flagged_spans), [mappers.flagged_span_to_row(s) for s in spans]
                )
            await connection.execute(
                insert(evaluation_log_entries), [mappers.evaluation_log_entry_to_row(log_entry)]
            )
