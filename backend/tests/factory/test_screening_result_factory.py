import pytest

from app.domain import Verdict
from app.exception import InvalidArgumentError
from app.factory.screening_result_factory import build_screening_result


@pytest.mark.parametrize("rule, context, expected", [
    ("FLAG", "FLAG", Verdict.FLAG),
    ("FLAG", "NO_FLAG", Verdict.FLAG),
    ("NO_FLAG", "FLAG", Verdict.FLAG),
    ("NO_FLAG", "NO_FLAG", Verdict.NO_FLAG),
])
def test_aggregated_verdict_is_computed(rule, context, expected):
    result = build_screening_result("prompt-1", rule, context)
    assert result.aggregated_verdict is expected
    assert result.rule_based_verdict is Verdict(rule)
    assert result.context_aware_verdict is Verdict(context)


def test_rejects_unknown_verdict():
    with pytest.raises(InvalidArgumentError, match="rule_based_verdict"):
        build_screening_result("prompt-1", "MAYBE", "FLAG")


def test_requires_prompt_id():
    with pytest.raises(InvalidArgumentError, match="prompt_id"):
        build_screening_result("", "FLAG", "FLAG")
