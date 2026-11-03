from dataclasses import dataclass

from .enums import DetectorSource


@dataclass(frozen=True, slots=True)
class FlaggedSpan:
    """Position of flagged text within a prompt. Stores indices, never the
    text itself. Create via flagged_span_factory."""

    span_id: str
    result_id: str
    start_index: int
    end_index: int
    detector_source: DetectorSource
    category_id: str
