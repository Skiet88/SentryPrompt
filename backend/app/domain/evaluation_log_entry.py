from dataclasses import dataclass

from .enums import EvaluationOutcome


@dataclass(frozen=True, slots=True)
class EvaluationLogEntry:
    """Content-free record of one screening outcome (NFR-009). Has no field
    that could hold prompt text. Create via evaluation_log_entry_factory."""

    log_id: str
    result_id: str
    category_id: str | None  # None when the outcome is unflagged
    outcome: EvaluationOutcome
    timestamp_bucket: str  # hour bucket, e.g. "2026-11-03T14:00Z"
