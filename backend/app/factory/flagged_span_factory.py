from __future__ import annotations

from app.domain import DetectorSource, FlaggedSpan
from app.exception import InvalidArgumentError

from . import _require


def build_flagged_span(
    result_id: str,
    start_index: int,
    end_index: int,
    detector_source: DetectorSource | str,
    category_id: str,
    *,
    span_id: str | None = None,
) -> FlaggedSpan:
    if not isinstance(start_index, int) or not isinstance(end_index, int):
        raise InvalidArgumentError("Span indices must be integers")
    if start_index < 0 or end_index <= start_index:
        raise InvalidArgumentError("Span must satisfy 0 <= start_index < end_index")
    return FlaggedSpan(
        span_id=_require.new_or_given_id(span_id, "span_id"),
        result_id=_require.identifier(result_id, "result_id"),
        start_index=start_index,
        end_index=end_index,
        detector_source=_require.enum_value(DetectorSource, detector_source, "detector_source"),
        category_id=_require.identifier(category_id, "category_id"),
    )
