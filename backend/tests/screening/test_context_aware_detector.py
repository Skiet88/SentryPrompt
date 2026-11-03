from app.screening.classification_parser import ClassificationParser
from app.screening.context_aware_detector import ContextAwareDetector
from app.screening.prompt_template import PromptTemplate
from tests.conftest import FakeProvider

PROMPT = PromptTemplate(version="test_v1", text="SYSTEM PROMPT")


def test_sends_prompt_and_text_and_parses_reply():
    provider = FakeProvider(reply='{"flags": [{"category": "MEDICAL", "span": "sertraline"}]}')
    detector = ContextAwareDetector(provider, PROMPT, ClassificationParser())

    result = detector.detect("I take sertraline")

    assert provider.received == [("SYSTEM PROMPT", "I take sertraline")]
    assert [f.span for f in result.flags] == ["sertraline"]
    assert (result.provider, result.model, result.prompt_version) == ("fake", "fake-model", "test_v1")
