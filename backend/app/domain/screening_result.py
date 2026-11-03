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
        """Flag if either detector flagged (parallel detection, FR-004)."""
        if Verdict.FLAG in (rule_based, context_aware):
            return Verdict.FLAG
        return Verdict.NO_FLAG

    @property
    def is_flagged(self) -> bool:
        return self.aggregated_verdict is Verdict.FLAG
