"""Convert between domain entities and database rows. Rows are turned back
into entities through the factories, so stored data is validated on read."""

from __future__ import annotations

import uuid
from collections.abc import Mapping
from typing import Any

from app.domain import EvaluationLogEntry, FlaggedSpan, ScreeningResult
from app.factory.evaluation_log_entry_factory import rebuild_evaluation_log_entry
from app.factory.flagged_span_factory import build_flagged_span
from app.factory.screening_result_factory import build_screening_result

Row = Mapping[Any, Any]


def as_uuid(value: str) -> uuid.UUID:
    return uuid.UUID(value)


def screening_result_to_row(result: ScreeningResult) -> dict[str, Any]:
    return {
        "id": as_uuid(result.result_id),
        "prompt_id": as_uuid(result.prompt_id),
        "rule_based_verdict": result.rule_based_verdict.value,
        "context_aware_verdict": result.context_aware_verdict.value,
        "aggregated_verdict": result.aggregated_verdict.value,
        "decided_at": result.decided_at,
    }


def screening_result_from_row(row: Row) -> ScreeningResult:
    return build_screening_result(
        prompt_id=str(row["prompt_id"]),
        rule_based_verdict=row["rule_based_verdict"],
        context_aware_verdict=row["context_aware_verdict"],
        result_id=str(row["id"]),
        decided_at=row["decided_at"],
    )


def flagged_span_to_row(span: FlaggedSpan) -> dict[str, Any]:
    return {
        "id": as_uuid(span.span_id),
        "result_id": as_uuid(span.result_id),
        "start_index": span.start_index,
        "end_index": span.end_index,
        "detector_source": span.detector_source.value,
        "category_id": as_uuid(span.category_id),
    }


def flagged_span_from_row(row: Row) -> FlaggedSpan:
    return build_flagged_span(
        result_id=str(row["result_id"]),
        start_index=row["start_index"],
        end_index=row["end_index"],
        detector_source=row["detector_source"],
        category_id=str(row["category_id"]),
        span_id=str(row["id"]),
    )


def evaluation_log_entry_to_row(entry: EvaluationLogEntry) -> dict[str, Any]:
    return {
        "id": as_uuid(entry.log_id),
        "result_id": as_uuid(entry.result_id),
        "category_id": as_uuid(entry.category_id) if entry.category_id else None,
        "outcome": entry.outcome.value,
        "timestamp_bucket": entry.timestamp_bucket,
    }


def evaluation_log_entry_from_row(row: Row) -> EvaluationLogEntry:
    return rebuild_evaluation_log_entry(
        log_id=str(row["id"]),
        result_id=str(row["result_id"]),
        outcome=row["outcome"],
        category_id=str(row["category_id"]) if row["category_id"] is not None else None,
        timestamp_bucket=row["timestamp_bucket"],
    )
