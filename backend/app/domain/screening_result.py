from dataclasses import dataclass
from datetime import datetime

from .enums import Verdict


@dataclass(frozen=True, slots=True)
class ScreeningResult:
    """Both detectors' verdicts for one prompt, kept separately (FR-004),
    plus the aggregated verdict. Create via screening_result_factory."""

    result_id: str
    prompt_id: str
    rule_based_verdict: Verdict
    context_aware_verdict: Verdict
    aggregated_verdict: Verdict
    decided_at: datetime

    @staticmethod
    def aggregate(rule_based: Verdict, context_aware: Verdict) -> Verdict:
        """FLAG if either detector flagged (FR-004). Otherwise UNAVAILABLE if
        the context-aware check could not complete (fail closed, NFR-015).
        NO_FLAG only when both checks completed and found nothing."""
        verdicts = (rule_based, context_aware)
        if Verdict.FLAG in verdicts:
            return Verdict.FLAG
        if Verdict.UNAVAILABLE in verdicts:
            return Verdict.UNAVAILABLE
        return Verdict.NO_FLAG

    @property
    def is_flagged(self) -> bool:
        return self.aggregated_verdict is Verdict.FLAG

    @property
    def requires_student_decision(self) -> bool:
        """True unless the prompt is confirmed clean: flagged or unchecked
        prompts both go through edit / send anyway / cancel (FR-007)."""
        return self.aggregated_verdict is not Verdict.NO_FLAG
