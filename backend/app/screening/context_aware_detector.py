"""Context-aware detector: classifies (already redacted) text with the LLM.

Fails closed (NFR-015): if the provider errors or exceeds the time limit,
the result is marked unavailable rather than clean.
"""

from __future__ import annotations

import asyncio
import logging

from app.domain import DetectorSource
from app.exception import ProviderError
from app.llm import LLMProvider

from .classification_parser import ClassificationParser
from .detection import ContextDetectionResult
from .detector import Detector
from .prompt_template import PromptTemplate

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT_SECONDS = 1.5  # leaves room within NFR-010's 2-second budget


class ContextAwareDetector(Detector):
    source = DetectorSource.CONTEXT

    def __init__(
        self,
        provider: LLMProvider,
        prompt: PromptTemplate,
        parser: ClassificationParser,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    ):
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        self._provider = provider
        self._prompt = prompt
        self._parser = parser
        self._timeout = timeout_seconds

    async def detect(self, text: str) -> ContextDetectionResult:
        try:
            raw_reply = await asyncio.wait_for(
                self._provider.complete_json(self._prompt.text, text), timeout=self._timeout
            )
        except TimeoutError:
            logger.warning("Context detector timed out after %.1fs (%s)", self._timeout, self._provider.name)
            return self._unavailable("timeout")
        except ProviderError as exc:
            # Log the error type only: provider messages could echo request data.
            logger.warning(
                "Context detector provider error (%s): %s", self._provider.name, type(exc).__name__
            )
            return self._unavailable("provider_error")

        return self._parser.parse(
            raw_reply,
            text,
            provider=self._provider.name,
            model=self._provider.model,
            prompt_version=self._prompt.version,
        )

    def _unavailable(self, reason: str) -> ContextDetectionResult:
        return ContextDetectionResult(
            provider=self._provider.name,
            model=self._provider.model,
            prompt_version=self._prompt.version,
            failure_reason=reason,
        )
