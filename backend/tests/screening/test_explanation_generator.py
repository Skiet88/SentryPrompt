from app.screening.explanation_generator import UNAVAILABLE_NOTICE, ExplanationGenerator
from app.screening.rules.rule_source import JsonRuleSource

explainer = ExplanationGenerator(JsonRuleSource().load())


def test_explains_rule_and_context_categories_in_plain_language():
    assert explainer.explain("SA_ID").startswith("This looks like a South African ID number")
    assert "health" in explainer.explain("MEDICAL")
    assert "university" in explainer.explain("INSTITUTIONAL")


def test_unavailable_notice():
    assert explainer.unavailable_notice() == UNAVAILABLE_NOTICE
    assert "couldn't fully check" in UNAVAILABLE_NOTICE
