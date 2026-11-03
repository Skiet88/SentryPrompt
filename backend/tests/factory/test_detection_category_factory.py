import pytest

from app.domain import DetectionTier
from app.exception import InvalidArgumentError
from app.factory.detection_category_factory import build_detection_category


def test_builds_category():
    category = build_detection_category("SA ID number", "South African ID numbers", "rule-based")
    assert category.tier is DetectionTier.RULE_BASED
    assert category.category_id


@pytest.mark.parametrize("name, description, tier", [
    ("", "desc", "rule-based"),
    ("name", "", "rule-based"),
    ("name", "desc", "semantic"),
    ("x" * 101, "desc", "rule-based"),
])
def test_rejects_invalid_input(name, description, tier):
    with pytest.raises(InvalidArgumentError):
        build_detection_category(name, description, tier)
