"""Turns the context-aware model's raw JSON reply into a ClassificationResult."""

from __future__ import annotations

import json
import logging

from app.domain import ClassificationResult, ContextFlag
from app.exception import InvalidArgumentError
from app.factory.context_flag_factory import build_context_flag

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
    ) -> ClassificationResult:
        items = self._extract_items(raw_reply)
        if items is None:
            logger.warning("Context detector reply was not valid JSON (%s/%s)", provider, model)
            return ClassificationResult(provider, model, prompt_version, parse_failed=True)

        flags = tuple(f for f in (self._to_flag(i, source_text) for i in items) if f is not None)
        return ClassificationResult(provider, model, prompt_version, flags=flags)

    @staticmethod
    def _extract_items(raw_reply: str) -> list | None:
        try:
            items = json.loads(raw_reply)["flags"]
        except (json.JSONDecodeError, KeyError, TypeError):
            return None
        return items if isinstance(items, list) else None

    @staticmethod
    def _to_flag(item: object, source_text: str) -> ContextFlag | None:
        if not isinstance(item, dict):
            return None
        try:
            return build_context_flag(
                category=item.get("category", ""),
                span=item.get("span", ""),
                source_text=source_text,
                confidence=item.get("confidence"),
            )
        except InvalidArgumentError as exc:
            # Unusable flags (unknown category, span not in the text, bad
            # confidence) are dropped; they could not be shown to the student.
            logger.info("Dropped context flag: %s", exc)
            return None
