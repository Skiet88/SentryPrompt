from app.screening.classification_parser import ClassificationParser
from app.screening.context_aware_detector import ContextAwareDetector
from app.screening.prompt_template import PromptTemplate
from tests.conftest import FakeProvider

PROMPT = PromptTemplate(version="test_v1", text="SYSTEM PROMPT")


def test_sends_prompt_and_text_and_parses_reply():
    provider = FakeProvider(reply='{"flags": [{"category": "MEDICAL", "span": "sertraline"}]}')
    detector = ContextAwareDetector(provider, PROMPT, ClassificationParser())

    text = "I take sertraline"
    result = detector.detect(text)

    assert provider.received == [("SYSTEM PROMPT", text)]
    assert [text[s.start:s.end] for s in result.spans] == ["sertraline"]
    assert (result.provider, result.model, result.prompt_version) == ("fake", "fake-model", "test_v1")
