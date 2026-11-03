"""Screening pipeline (Facade over the detectors, redaction and explanations).

1. Validate the prompt (FR-001).
2. Rule-based detector on the original text (local, always completes).
3. Redact everything it found (NFR-008).
4. Context-aware detector on the redacted text (fails closed, NFR-015).
5. Aggregate both verdicts into a ScreeningResult (FR-004).
6. Map every span to the original text and explain it (FR-005, FR-006).

Both detectors run on every prompt and neither result is ever skipped
(FR-004). The context-aware detector waits for the rule-based one (~1 ms)
because it must only ever see redacted text.
"""

from __future__ import annotations

from app.domain import DetectorSource, PromptStatus, SourceChannel
from app.factory.flagged_span_factory import build_flagged_span
from app.factory.prompt_factory import build_prompt
from app.factory.screening_result_factory import build_screening_result
from app.screening.detection import DetectedSpan
from app.screening.detector import Detector
from app.screening.explanation_generator import CategoryCatalog, ExplanationGenerator
from app.screening.redaction import RedactedText, redact_with_map

from .i_screening_service import IScreeningService
from .screening_outcome import ExplainedSpan, ScreeningOutcome


class ScreeningService(IScreeningService):
    def __init__(
        self,
        rule_detector: Detector,
        context_detector: Detector,
        catalog: CategoryCatalog,
        explainer: ExplanationGenerator,
    ):
        if rule_detector.source is not DetectorSource.RULE:
            raise ValueError("rule_detector must be a rule-based detector")
        if context_detector.source is not DetectorSource.CONTEXT:
            raise ValueError("context_detector must be a context-aware detector")
        self._rule_detector = rule_detector
        self._context_detector = context_detector
        self._catalog = catalog
        self._explainer = explainer

    async def screen(self, raw_text: str, channel: SourceChannel | str) -> ScreeningOutcome:
        prompt = build_prompt(raw_text, channel, status=PromptStatus.SCREENING)

        rule_result = await self._rule_detector.detect(prompt.raw_text)
        redacted = redact_with_map(prompt.raw_text, [(s.start, s.end, s.category) for s in rule_result.spans])
        context_result = await self._context_detector.detect(redacted.text)

        result = build_screening_result(prompt.prompt_id, rule_result.verdict, context_result.verdict)
        spans = (
            *self._explain(result.result_id, rule_result.spans, None),
            *self._explain(result.result_id, context_result.spans, redacted),
        )
        return ScreeningOutcome(
            prompt_id=prompt.prompt_id,
            result=result,
            spans=tuple(sorted(spans, key=lambda e: (e.span.start_index, e.span.end_index))),
            notice=None if context_result.completed else self._explainer.unavailable_notice(),
        )

    def _explain(
        self,
        result_id: str,
        spans: tuple[DetectedSpan, ...],
        redacted: RedactedText | None,
    ) -> list[ExplainedSpan]:
        explained = []
        for span in spans:
            start, end = (
                (span.start, span.end) if redacted is None else redacted.to_original(span.start, span.end)
            )
            category = self._catalog.category_named(span.category)
            explained.append(
                ExplainedSpan(
                    span=build_flagged_span(
                        result_id, start, end, span.detector_source, category.category_id
                    ),
                    category_name=category.name,
                    explanation=self._explainer.explain(category.name),
                )
            )
        return explained
