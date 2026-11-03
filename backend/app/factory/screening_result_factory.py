from __future__ import annotations

from datetime import datetime

from app.domain import ScreeningResult, Verdict

from . import _require


def build_screening_result(
    prompt_id: str,
    rule_based_verdict: Verdict | str,
    context_aware_verdict: Verdict | str,
    *,
    result_id: str | None = None,
    decided_at: datetime | None = None,
) -> ScreeningResult:
    """The aggregated verdict is always computed here (ScreeningResult.aggregate),
    never accepted from the caller, so it can't disagree with the two detectors."""
    rule = _require.enum_value(Verdict, rule_based_verdict, "rule_based_verdict")
    context = _require.enum_value(Verdict, context_aware_verdict, "context_aware_verdict")
    return ScreeningResult(
        result_id=_require.new_or_given_id(result_id, "result_id"),
        prompt_id=_require.identifier(prompt_id, "prompt_id"),
        rule_based_verdict=rule,
        context_aware_verdict=context,
        aggregated_verdict=ScreeningResult.aggregate(rule, context),
        decided_at=_require.timestamp(decided_at, "decided_at"),
    )
