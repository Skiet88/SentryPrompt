"""Rule-based detector: finds structured personal data with regex rules.

Runs locally and always completes. Overlapping matches are resolved by
category priority (the order in the rules file), so each span gets exactly
one category: a 13-digit SA ID is not also reported as a card.
"""

from __future__ import annotations

from app.domain import DetectorSource

from ..detection import DetectedSpan, RuleDetectionResult
from ..detector import Detector
from .rule_set import RuleSet


class RuleBasedDetector(Detector):
    source = DetectorSource.RULE

    def __init__(self, rule_set: RuleSet):
        self._rule_set = rule_set

    async def detect(self, text: str) -> RuleDetectionResult:
        return self.detect_now(text)

    def detect_now(self, text: str) -> RuleDetectionResult:
        """Synchronous version, for the offline evaluation harness."""
        candidates = [
            DetectedSpan(
                category=rule.category.name,
                start=match.start(),
                end=match.end(),
                detector_source=DetectorSource.RULE,
            )
            for rule in self._rule_set.rules
            for match in rule.pattern.finditer(text)
            if rule.validator is None or rule.validator.is_valid(match.group(0))
        ]
        return RuleDetectionResult(spans=self._resolve_overlaps(candidates))

    def _resolve_overlaps(self, candidates: list[DetectedSpan]) -> tuple[DetectedSpan, ...]:
        by_priority = sorted(candidates, key=lambda s: (self._rule_set.priority_of(s.category), s.start))
        kept: list[DetectedSpan] = []
        for span in by_priority:
            if all(span.end <= other.start or span.start >= other.end for other in kept):
                kept.append(span)
        return tuple(sorted(kept, key=lambda s: s.start))
