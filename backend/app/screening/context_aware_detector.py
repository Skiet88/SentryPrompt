"""Context-aware detector: classifies (already redacted) text with the LLM."""

from __future__ import annotations

from app.llm import LLMProvider

from .classification_parser import ClassificationParser
from .detection import ContextDetectionResult
from .prompt_template import PromptTemplate


class ContextAwareDetector:
    def __init__(self, provider: LLMProvider, prompt: PromptTemplate, parser: ClassificationParser):
        self._provider = provider
        self._prompt = prompt
        self._parser = parser

    def detect(self, text: str) -> ContextDetectionResult:
        raw_reply = self._provider.complete_json(self._prompt.text, text)
        return self._parser.parse(
            raw_reply,
            text,
            provider=self._provider.name,
            model=self._provider.model,
            prompt_version=self._prompt.version,
        )
