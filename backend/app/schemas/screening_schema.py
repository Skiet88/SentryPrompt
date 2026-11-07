"""Request/response models for POST /api/prompts/screen (SERVICE_LAYER.md §3).

Strict: unknown fields are rejected (no mass assignment). Responses carry
positions, not the flagged text itself (data minimisation): the client
already has the prompt and highlights it using startIndex/endIndex.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from app.domain import DetectorSource, SourceChannel, Verdict
from app.factory.prompt_factory import MAX_PROMPT_LENGTH
from app.service.screening.screening_outcome import ScreeningOutcome


class _CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="forbid")


class ScreenPromptRequest(_CamelModel):
    text: str = Field(min_length=1, max_length=MAX_PROMPT_LENGTH)
    channel: SourceChannel = SourceChannel.WEBAPP


class FlagResponse(_CamelModel):
    category: str
    start_index: int
    end_index: int
    detector_source: DetectorSource
    explanation: str


class ScreenPromptResponse(_CamelModel):
    screening_result_id: str
    aggregated_verdict: Verdict
    rule_based_verdict: Verdict
    context_aware_verdict: Verdict
    requires_decision: bool
    notice: str | None
    flags: list[FlagResponse]

    @classmethod
    def from_outcome(cls, outcome: ScreeningOutcome) -> ScreenPromptResponse:
        result = outcome.result
        return cls(
            screening_result_id=result.result_id,
            aggregated_verdict=result.aggregated_verdict,
            rule_based_verdict=result.rule_based_verdict,
            context_aware_verdict=result.context_aware_verdict,
            requires_decision=outcome.requires_student_decision,
            notice=outcome.notice,
            flags=[
                FlagResponse(
                    category=e.category_name,
                    start_index=e.span.start_index,
                    end_index=e.span.end_index,
                    detector_source=e.span.detector_source,
                    explanation=e.explanation,
                )
                for e in outcome.spans
            ],
        )
