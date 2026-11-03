import dataclasses

import pytest

from app.domain import ContextCategory
from app.exception import InvalidArgumentError
from app.factory.context_flag_factory import build_context_flag

TEXT = "I've been on sertraline for two months"


def test_builds_flag_with_position():
    flag = build_context_flag("medical", "sertraline", TEXT, 0.9)
    assert flag.category is ContextCategory.MEDICAL
    assert TEXT[flag.start:flag.end] == "sertraline"
    assert flag.confidence == 0.9


def test_confidence_is_optional():
    assert build_context_flag("INSTITUTIONAL", "two months", TEXT).confidence is None


def test_flag_is_immutable():
    flag = build_context_flag("MEDICAL", "sertraline", TEXT)
    with pytest.raises(dataclasses.FrozenInstanceError):
        flag.span = "changed"


@pytest.mark.parametrize("category, span, confidence, message", [
    ("FINANCIAL", "sertraline", None, "Unknown context category"),
    ("MEDICAL", "", None, "cannot be empty"),
    ("MEDICAL", "   ", None, "cannot be empty"),
    ("MEDICAL", "depression", None, "does not occur"),
    ("MEDICAL", "sertraline", 1.5, "between 0 and 1"),
])
def test_rejects_invalid_input(category, span, confidence, message):
    with pytest.raises(InvalidArgumentError, match=message):
        build_context_flag(category, span, TEXT, confidence)
