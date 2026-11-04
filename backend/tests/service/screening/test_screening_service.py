import asyncio
import json

import pytest

from app.domain import DetectorSource, EvaluationOutcome, Verdict
from app.exception import InvalidArgumentError, ProviderError
from app.repository.memory.screening_records import InMemoryScreeningRecordWriter
from app.screening.classification_parser import ClassificationParser
from app.screening.context_aware_detector import ContextAwareDetector
from app.screening.explanation_generator import UNAVAILABLE_NOTICE, ExplanationGenerator
from app.screening.prompt_template import PromptTemplate
from app.screening.rules.rule_based_detector import RuleBasedDetector
from app.screening.rules.rule_source import JsonRuleSource
from app.service.screening.screening_service import ScreeningService
from tests.conftest import FakeProvider

RULES = JsonRuleSource().load()
PROMPT = PromptTemplate(version="test_v1", text="SYSTEM PROMPT")


def llm_flags(*flags: tuple[str, str]) -> str:
    return json.dumps({"flags": [{"category": c, "span": s} for c, s in flags]})


def make_service(
    provider: FakeProvider, timeout: float = 1.0, log: InMemoryScreeningRecordWriter | None = None
) -> ScreeningService:
    return ScreeningService(
        rule_detector=RuleBasedDetector(RULES),
        context_detector=ContextAwareDetector(provider, PROMPT, ClassificationParser(), timeout),
        catalog=RULES,
        explainer=ExplanationGenerator(RULES),
        records=log or InMemoryScreeningRecordWriter(),
    )


def screen(provider: FakeProvider, text: str, timeout: float = 1.0, log=None):
    return asyncio.run(make_service(provider, timeout, log).screen(text, "webapp"))


def highlighted(text: str, outcome) -> list[tuple[str, str, DetectorSource]]:
    return [
        (e.category_name, text[e.span.start_index : e.span.end_index], e.span.detector_source)
        for e in outcome.spans
    ]


def test_clean_prompt():
    outcome = screen(FakeProvider(), "Explain recursion with an example.")
    assert outcome.result.aggregated_verdict is Verdict.NO_FLAG
    assert outcome.spans == () and outcome.notice is None
    assert not outcome.requires_student_decision


def test_rule_flag_only():
    text = "My ID is 9203105800089, is it valid?"
    outcome = screen(FakeProvider(), text)
    assert outcome.result.rule_based_verdict is Verdict.FLAG
    assert outcome.result.context_aware_verdict is Verdict.NO_FLAG
    assert outcome.result.aggregated_verdict is Verdict.FLAG
    assert highlighted(text, outcome) == [("SA_ID", "9203105800089", DetectorSource.RULE)]
    assert outcome.spans[0].explanation.startswith("This looks like a South African ID number")


def test_context_flag_only():
    text = "I was diagnosed with anxiety last year."
    outcome = screen(FakeProvider(reply=llm_flags(("MEDICAL", "diagnosed with anxiety"))), text)
    assert outcome.result.rule_based_verdict is Verdict.NO_FLAG
    assert outcome.result.context_aware_verdict is Verdict.FLAG
    assert highlighted(text, outcome) == [("MEDICAL", "diagnosed with anxiety", DetectorSource.CONTEXT)]


def test_both_detectors_flag_and_context_span_is_mapped_to_original_text():
    text = "My ID is 9203105800089 and I take sertraline"
    outcome = screen(FakeProvider(reply=llm_flags(("MEDICAL", "sertraline"))), text)
    assert highlighted(text, outcome) == [
        ("SA_ID", "9203105800089", DetectorSource.RULE),
        ("MEDICAL", "sertraline", DetectorSource.CONTEXT),
    ]


def test_llm_only_ever_sees_redacted_text():
    """NFR-008: rule-detected values never reach the LLM provider."""
    provider = FakeProvider()
    text = "ID 9203105800089, email t.mokoena84@gmail.com, card 4539 1488 0343 6467"
    screen(provider, text)
    [(_, sent)] = provider.received
    for secret in ("9203105800089", "t.mokoena84@gmail.com", "4539 1488 0343 6467"):
        assert secret not in sent
    assert "[REDACTED_SA_ID]" in sent and "[REDACTED_EMAIL]" in sent


def test_context_span_covering_a_placeholder_highlights_the_hidden_value():
    text = "My ID is 9203105800089 please"
    outcome = screen(FakeProvider(reply=llm_flags(("INSTITUTIONAL", "ID is [REDACTED_SA_ID]"))), text)
    context = [h for h in highlighted(text, outcome) if h[2] is DetectorSource.CONTEXT]
    assert context == [("INSTITUTIONAL", "ID is 9203105800089", DetectorSource.CONTEXT)]


@pytest.mark.parametrize(
    "provider, timeout",
    [
        (FakeProvider(delay_seconds=0.5), 0.05),
        (FakeProvider(error=ProviderError("rate limited")), 1.0),
        (FakeProvider(reply="not json"), 1.0),
    ],
    ids=["timeout", "provider_error", "unreadable_reply"],
)
def test_context_failure_fails_closed_with_notice(provider, timeout):
    outcome = screen(provider, "Help me plan my study week.", timeout)
    assert outcome.result.context_aware_verdict is Verdict.UNAVAILABLE
    assert outcome.result.aggregated_verdict is Verdict.UNAVAILABLE
    assert outcome.notice == UNAVAILABLE_NOTICE
    assert outcome.requires_student_decision


def test_rule_flag_still_reported_when_context_check_fails():
    text = "My ID is 9203105800089"
    outcome = screen(FakeProvider(error=ProviderError("down")), text)
    assert outcome.result.aggregated_verdict is Verdict.FLAG
    assert outcome.notice == UNAVAILABLE_NOTICE
    assert [h[0] for h in highlighted(text, outcome)] == ["SA_ID"]


def test_spans_link_to_result_and_catalog_categories():
    text = "Email a@b.co and I take sertraline"
    outcome = screen(FakeProvider(reply=llm_flags(("MEDICAL", "sertraline"))), text)
    for explained in outcome.spans:
        assert explained.span.result_id == outcome.result.result_id
        assert explained.span.category_id == RULES.category_named(explained.category_name).category_id
    assert outcome.result.prompt_id == outcome.prompt_id


@pytest.mark.parametrize("text", ["", "   ", "a" * 4001])
def test_invalid_prompt_rejected_before_any_detection(text):
    provider = FakeProvider()
    with pytest.raises(InvalidArgumentError):
        screen(provider, text)
    assert provider.received == []


def test_rejects_detectors_in_the_wrong_slots():
    rule = RuleBasedDetector(RULES)
    context = ContextAwareDetector(FakeProvider(), PROMPT, ClassificationParser())
    with pytest.raises(ValueError):
        ScreeningService(context, rule, RULES, ExplanationGenerator(RULES), InMemoryScreeningRecordWriter())


# ---- evaluation log (FR-011, NFR-009) ----------------------------------------


@pytest.mark.parametrize(
    "provider, text, expected_outcome, expected_category",
    [
        (FakeProvider(), "Explain recursion.", EvaluationOutcome.UNFLAGGED, None),
        (FakeProvider(), "My ID is 9203105800089", EvaluationOutcome.FLAGGED, "SA_ID"),
        (FakeProvider(error=ProviderError("down")), "Plan my week.", EvaluationOutcome.UNAVAILABLE, None),
    ],
    ids=["clean", "flagged", "unavailable"],
)
def test_records_content_free_evaluation_entry(provider, text, expected_outcome, expected_category):
    log = InMemoryScreeningRecordWriter()
    outcome = screen(provider, text, log=log)
    [entry] = asyncio.run(log.log.find_all())
    assert entry.result_id == outcome.result.result_id
    assert entry.outcome is expected_outcome
    expected_id = RULES.category_named(expected_category).category_id if expected_category else None
    assert entry.category_id == expected_id
    assert text not in repr(entry)


def test_logging_failure_does_not_block_screening():
    class BrokenLog(InMemoryScreeningRecordWriter):
        async def record(self, result, spans, log_entry):
            raise RuntimeError("database down")

    outcome = screen(FakeProvider(), "My ID is 9203105800089", log=BrokenLog())
    assert outcome.result.aggregated_verdict is Verdict.FLAG


def test_result_and_spans_are_saved_with_the_log_entry():
    records = InMemoryScreeningRecordWriter()
    text = "My ID is 9203105800089 and I take sertraline"
    outcome = screen(FakeProvider(reply=llm_flags(("MEDICAL", "sertraline"))), text, log=records)
    assert asyncio.run(records.results.find_by_id(outcome.result.result_id)) == outcome.result
    saved = asyncio.run(records.spans.find_by_result_id(outcome.result.result_id))
    assert sorted(s.span_id for s in saved) == sorted(e.span.span_id for e in outcome.spans)


def test_send_anyway_is_logged_as_override():
    records = InMemoryScreeningRecordWriter()
    asyncio.run(
        make_service(FakeProvider(), log=records).screen("My ID is 9203105800089", "webapp", send_anyway=True)
    )
    [entry] = asyncio.run(records.log.find_all())
    assert entry.outcome is EvaluationOutcome.OVERRIDE
