import pytest

from app.exception import InvalidArgumentError
from app.factory.rule_pattern_factory import build_rule_pattern


def test_builds_pattern():
    pattern = build_rule_pattern("cat-1", r"\b\d{13}\b", "13-digit SA ID")
    assert pattern.regex_pattern == r"\b\d{13}\b"


@pytest.mark.parametrize("regex", ["", "   ", "([unclosed", "*"])
def test_rejects_invalid_regex(regex):
    with pytest.raises(InvalidArgumentError, match="regex_pattern"):
        build_rule_pattern("cat-1", regex, "desc")


def test_requires_description_and_category():
    with pytest.raises(InvalidArgumentError, match="description"):
        build_rule_pattern("cat-1", r"\d", "")
    with pytest.raises(InvalidArgumentError, match="category_id"):
        build_rule_pattern("", r"\d", "desc")
