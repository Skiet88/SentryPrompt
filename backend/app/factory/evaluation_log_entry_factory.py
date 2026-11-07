from __future__ import annotations

import re
from datetime import UTC, datetime

from app.domain import EvaluationLogEntry, EvaluationOutcome
from app.exception import InvalidArgumentError

from . import _require


def to_hour_bucket(moment: datetime) -> str:
    """Truncate to the hour (UTC) so log entries can't be matched to an
    individual request by exact time (NFR-009)."""
    return moment.astimezone(UTC).strftime("%Y-%m-%dT%H:00Z")


def build_evaluation_log_entry(
    result_id: str,
    outcome: EvaluationOutcome | str,
    category_id: str | None = None,
    *,
    log_id: str | None = None,
    occurred_at: datetime | None = None,
) -> EvaluationLogEntry:
    parsed_outcome = _require.enum_value(EvaluationOutcome, outcome, "outcome")
    if parsed_outcome in (EvaluationOutcome.UNFLAGGED, EvaluationOutcome.UNAVAILABLE):
        if category_id is not None:
            raise InvalidArgumentError(f"An {parsed_outcome.value} outcome has no category")
    else:
        category_id = _require.identifier(category_id, "category_id")
    return EvaluationLogEntry(
        log_id=_require.new_or_given_id(log_id, "log_id"),
        result_id=_require.identifier(result_id, "result_id"),
        category_id=category_id,
        outcome=parsed_outcome,
        timestamp_bucket=to_hour_bucket(_require.timestamp(occurred_at, "occurred_at")),
    )


_HOUR_BUCKET = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:00Z")


def rebuild_evaluation_log_entry(
    log_id: str,
    result_id: str,
    outcome: EvaluationOutcome | str,
    category_id: str | None,
    timestamp_bucket: str,
) -> EvaluationLogEntry:
    """Rebuild a stored entry (e.g. from the database), validating every field."""
    if not isinstance(timestamp_bucket, str) or not _HOUR_BUCKET.fullmatch(timestamp_bucket):
        raise InvalidArgumentError("timestamp_bucket must look like 2026-11-03T14:00Z")
    entry = build_evaluation_log_entry(result_id, outcome, category_id, log_id=log_id)
    return EvaluationLogEntry(
        log_id=entry.log_id,
        result_id=entry.result_id,
        category_id=entry.category_id,
        outcome=entry.outcome,
        timestamp_bucket=timestamp_bucket,
    )
