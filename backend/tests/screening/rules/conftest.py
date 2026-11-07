import pytest

from app.screening.rules.rule_based_detector import RuleBasedDetector
from app.screening.rules.rule_set import RuleSet
from app.screening.rules.rule_source import JsonRuleSource


@pytest.fixture(scope="session")
def rule_set() -> RuleSet:
    return JsonRuleSource().load()


@pytest.fixture(scope="session")
def detector(rule_set) -> RuleBasedDetector:
    return RuleBasedDetector(rule_set)
