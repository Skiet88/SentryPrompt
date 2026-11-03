import asyncio

import pytest

from app.domain import Verdict
from app.exception import ProviderError
from app.screening.classification_parser import ClassificationParser
from app.screening.context_aware_detector import ContextAwareDetector
from app.screening.prompt_template import PromptTemplate
from tests.conftest import FakeProvider

PROMPT = PromptTemplate(version="test_v1", text="SYSTEM PROMPT")


def detect(provider: FakeProvider, text: str, timeout: float = 1.0):
    detector = ContextAwareDetector(provider, PROMPT, ClassificationParser(), timeout_seconds=timeout)
    return asyncio.run(detector.detect(text))


def test_sends_prompt_and_text_and_parses_reply():
    provider = FakeProvider(reply='{"flags": [{"category": "MEDICAL", "span": "sertraline"}]}')
    text = "I take sertraline"

    result = detect(provider, text)

    assert provider.received == [("SYSTEM PROMPT", text)]
    assert [text[s.start : s.end] for s in result.spans] == ["sertraline"]
    assert result.verdict is Verdict.FLAG
    assert (result.provider, result.model, result.prompt_version) == ("fake", "fake-model", "test_v1")


def test_clean_reply_gives_no_flag():
    assert detect(FakeProvider(), "Explain recursion").verdict is Verdict.NO_FLAG


def test_timeout_fails_closed():
    result = detect(FakeProvider(delay_seconds=0.5), "text", timeout=0.05)
    assert result.verdict is Verdict.UNAVAILABLE
    assert result.failure_reason == "timeout"


def test_provider_error_fails_closed():
    result = detect(FakeProvider(error=ProviderError("rate limited")), "text")
    assert result.verdict is Verdict.UNAVAILABLE
    assert result.failure_reason == "provider_error"


def test_unreadable_reply_fails_closed():
    result = detect(FakeProvider(reply="not json"), "text")
    assert result.verdict is Verdict.UNAVAILABLE
    assert result.parse_failed


def test_rejects_non_positive_timeout():
    with pytest.raises(ValueError):
        ContextAwareDetector(FakeProvider(), PROMPT, ClassificationParser(), timeout_seconds=0)
