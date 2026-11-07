"""What the screening service returns to the API layer.

Deliberately contains no prompt text: the client already has it, and the
outcome carries only positions, categories and explanations (data minimisation).
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain import FlaggedSpan, ScreeningResult


@dataclass(frozen=True, slots=True)
class ExplainedSpan:
    span: FlaggedSpan  # positions refer to the student's original text
    category_name: str
    explanation: str


@dataclass(frozen=True, slots=True)
class ScreeningOutcome:
    prompt_id: str
    result: ScreeningResult
    spans: tuple[ExplainedSpan, ...]
    # Set when the context-aware check could not complete (NFR-015).
    notice: str | None = None

    @property
    def requires_student_decision(self) -> bool:
        return self.result.requires_student_decision
