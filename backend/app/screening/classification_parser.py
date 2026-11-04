"""Turns the context-aware model's raw JSON reply into a ContextDetectionResult."""

from __future__ import annotations

import json
import logging

from app.exception import InvalidArgumentError
from app.factory.detected_span_factory import build_context_spans

from .detection import ContextDetectionResult, DetectedSpan

logger = logging.getLogger(__name__)


class ClassificationParser:
    def parse(
        self,
        raw_reply: str,
        source_text: str,
        *,
        provider: str,
        model: str,
        prompt_version: str,
    ) -> ContextDetectionResult:
        items = self._extract_items(raw_reply)
        if items is None:
            logger.warning("Context detector reply was not valid JSON (%s/%s)", provider, model)
            return ContextDetectionResult(
                provider, model, prompt_version, parse_failed=True, failure_reason="unreadable_reply"
            )

        # Every occurrence of every flagged phrase, without duplicates (the
        # model may name the same phrase twice).
        unique: dict[tuple[str, int, int], DetectedSpan] = {}
        for item in items:
            for span in self._to_spans(item, source_text):
                unique.setdefault((span.category, span.start, span.end), span)
        spans = tuple(sorted(unique.values(), key=lambda s: (s.start, s.end)))
        return ContextDetectionResult(provider, model, prompt_version, spans=spans)

    @staticmethod
    def _extract_items(raw_reply: str) -> list[object] | None:
        try:
            items = json.loads(raw_reply)["flags"]
        except (json.JSONDecodeError, KeyError, TypeError):
            return None
        return items if isinstance(items, list) else None

    @staticmethod
    def _to_spans(item: object, source_text: str) -> tuple[DetectedSpan, ...]:
        if not isinstance(item, dict):
            return ()
        try:
            return build_context_spans(
                category=item.get("category", ""),
                span_text=item.get("span", ""),
                source_text=source_text,
                confidence=item.get("confidence"),
            )
        except InvalidArgumentError as exc:
            # Unusable flags (unknown category, span not in the text, bad
            # confidence) are dropped; they could not be shown to the student.
            logger.info("Dropped context flag: %s", exc)
            return ()
