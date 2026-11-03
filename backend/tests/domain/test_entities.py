import dataclasses

import pytest

from app.domain import ScreeningResult, Verdict
from app.factory.prompt_factory import build_prompt
from app.factory.rule_pattern_factory import build_rule_pattern
from app.factory.screening_result_factory import build_screening_result
from app.factory.user_factory import build_user


def test_entities_are_immutable():
    prompt = build_prompt("text", "webapp")
    with pytest.raises(dataclasses.FrozenInstanceError):
        prompt.raw_text = "changed"


def test_screening_result_aggregate_and_is_flagged():
    assert ScreeningResult.aggregate(Verdict.NO_FLAG, Verdict.FLAG) is Verdict.FLAG
    assert build_screening_result("p", "FLAG", "NO_FLAG").is_flagged
    assert not build_screening_result("p", "NO_FLAG", "NO_FLAG").is_flagged


def test_rule_pattern_matches():
    pattern = build_rule_pattern("cat", r"\b\d{13}\b", "SA ID")
    assert pattern.matches("My ID is 9203105800089")
    assert not pattern.matches("No numbers here")


@pytest.mark.parametrize("verified, status, allowed", [
    (True, "active", True),
    (False, "active", False),
    (True, "suspended", False),
])
def test_user_can_submit_prompts_only_when_verified_and_active(verified, status, allowed):
    user = build_user("uid", "a@b.co", email_verified=verified, status=status)
    assert user.can_submit_prompts is allowed


def test_user_is_admin():
    assert build_user("uid", "a@b.co", role="admin").is_admin
    assert not build_user("uid", "a@b.co").is_admin
