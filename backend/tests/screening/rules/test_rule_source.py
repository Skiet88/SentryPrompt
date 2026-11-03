import json
from pathlib import Path

import pytest

from app.domain import DetectionTier
from app.exception import ConfigurationError
from app.screening.rules.rule_source import DEFAULT_RULES_FILE, JsonRuleSource

RULE_BASED = ["SA_ID", "BANK_CARD", "BANK_ACCOUNT", "PHONE", "EMAIL", "ADDRESS", "STUDENT_NUMBER"]


def test_loads_taxonomy_in_priority_order(rule_set):
    assert [c.name for c in rule_set.categories] == [*RULE_BASED, "MEDICAL", "INSTITUTIONAL"]
    assert [c.name for c in rule_set.categories_in_tier(DetectionTier.CONTEXT_AWARE)] == [
        "MEDICAL",
        "INSTITUTIONAL",
    ]
    assert [r.category.name for r in rule_set.rules] == RULE_BASED


def test_every_category_has_a_plain_language_description(rule_set):
    for category in rule_set.categories:
        assert len(category.description) > 40, category.name


def test_card_rule_uses_luhn_validator(rule_set):
    [card_rule] = [r for r in rule_set.rules if r.category.name == "BANK_CARD"]
    assert card_rule.validator is not None and card_rule.validator.name == "luhn"


def test_ids_are_stable_uuids(rule_set):
    first = rule_set.category_named("SA_ID").category_id
    assert first == JsonRuleSource().load().category_named("SA_ID").category_id
    assert len(first) == 36


# ---- invalid files -----------------------------------------------------------


def write(tmp_path: Path, data) -> Path:
    path = tmp_path / "rules.json"
    path.write_text(data if isinstance(data, str) else json.dumps(data), encoding="utf-8")
    return path


def valid_data() -> dict:
    return json.loads(DEFAULT_RULES_FILE.read_text(encoding="utf-8"))


def load(tmp_path, data):
    return JsonRuleSource(write(tmp_path, data)).load()


def test_missing_file(tmp_path):
    with pytest.raises(ConfigurationError, match="Cannot read"):
        JsonRuleSource(tmp_path / "missing.json").load()


@pytest.mark.parametrize("content", ["not json", "[]", '{"version": 2, "categories": []}'])
def test_rejects_malformed_file(tmp_path, content):
    with pytest.raises(ConfigurationError):
        load(tmp_path, content)


def test_rejects_invalid_regex(tmp_path):
    data = valid_data()
    data["categories"][0]["patterns"][0]["regex"] = "([unclosed"
    with pytest.raises(ConfigurationError, match="Invalid pattern in SA_ID"):
        load(tmp_path, data)


def test_rejects_unknown_validator(tmp_path):
    data = valid_data()
    data["categories"][0]["patterns"][0]["validator"] = "made_up"
    with pytest.raises(ConfigurationError, match="Unknown match validator"):
        load(tmp_path, data)


def test_rejects_duplicate_category_name(tmp_path):
    data = valid_data()
    duplicate = dict(data["categories"][0], id="00000000-0000-0000-0000-000000000001")
    duplicate["patterns"] = [dict(duplicate["patterns"][0], id="00000000-0000-0000-0000-000000000002")]
    data["categories"].append(duplicate)
    with pytest.raises(ConfigurationError, match="Duplicate category name"):
        load(tmp_path, data)


def test_rejects_duplicate_id(tmp_path):
    data = valid_data()
    data["categories"][1]["id"] = data["categories"][0]["id"]
    with pytest.raises(ConfigurationError, match="Duplicate id"):
        load(tmp_path, data)


def test_rule_based_category_needs_patterns(tmp_path):
    data = valid_data()
    data["categories"][0]["patterns"] = []
    with pytest.raises(ConfigurationError, match="has no patterns"):
        load(tmp_path, data)


def test_context_category_cannot_have_patterns(tmp_path):
    data = valid_data()
    data["categories"][-1]["patterns"] = [{"regex": r"\d", "description": "x"}]
    with pytest.raises(ConfigurationError, match="cannot have patterns"):
        load(tmp_path, data)


def test_rejects_unknown_tier(tmp_path):
    data = valid_data()
    data["categories"][0]["tier"] = "semantic"
    with pytest.raises(ConfigurationError, match="Invalid category"):
        load(tmp_path, data)
