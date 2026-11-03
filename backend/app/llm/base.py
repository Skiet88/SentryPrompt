"""Provider-neutral interface for the LLM used by SentryPrompt.

The context-aware detector and the chat response both go through an
LLMProvider, so the backend can switch between Groq, Gemini and Ollama with
one setting (LLM_PROVIDER) and no other code changes.
"""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

PROMPT_VERSION = "context_detector_v1"
SYSTEM_PROMPT = (Path(__file__).parent / "prompts" / f"{PROMPT_VERSION}.txt").read_text(encoding="utf-8")

CONTEXT_CATEGORIES = {"MEDICAL", "INSTITUTIONAL"}


class ProviderError(RuntimeError):
    """The provider could not be reached or returned an error."""


@dataclass
class ContextFlag:
    category: str
    span: str
    start: int
    end: int
    confidence: float | None = None


@dataclass
class ClassificationResult:
    provider: str
    model: str
    prompt_version: str = PROMPT_VERSION
    flags: list[ContextFlag] = field(default_factory=list)
    # True when the model's reply was not valid JSON. Treated as "no flags"
    # but counted separately in the evaluation (MODEL_ARCHITECTURE.md §2).
    parse_failed: bool = False


@dataclass
class ChatMessage:
    role: str  # "user" or "assistant"
    content: str


class LLMProvider(ABC):
    name: str = ""
    # True for providers whose free tier may use prompts for training.
    may_train_on_free_tier: bool = False

    def __init__(self, model: str):
        self.model = model

    @abstractmethod
    def _complete_json(self, system: str, text: str) -> str:
        """Send one classification request and return the raw reply text."""

    @abstractmethod
    def chat(self, messages: list[ChatMessage]) -> str:
        """Return the model's reply to an approved conversation."""

    def classify(self, text: str) -> ClassificationResult:
        raw = self._complete_json(SYSTEM_PROMPT, text)
        return parse_classification(raw, text, self.name, self.model)


def parse_classification(raw: str, text: str, provider: str, model: str) -> ClassificationResult:
    result = ClassificationResult(provider=provider, model=model)
    try:
        data = json.loads(raw)
        items = data["flags"]
        if not isinstance(items, list):
            raise TypeError("flags is not a list")
    except (json.JSONDecodeError, KeyError, TypeError):
        logger.warning("Context detector reply was not valid JSON (%s/%s)", provider, model)
        result.parse_failed = True
        return result

    for item in items:
        if not isinstance(item, dict):
            continue
        category = str(item.get("category", "")).upper()
        span = item.get("span")
        if category not in CONTEXT_CATEGORIES or not isinstance(span, str) or not span:
            continue
        start = text.find(span)
        if start == -1:
            # The model quoted text that isn't in the prompt; it can't be
            # highlighted (FR-005), so it isn't reported as a flag.
            logger.info("Dropped %s flag: span not found in prompt", category)
            continue
        confidence = item.get("confidence")
        result.flags.append(ContextFlag(
            category=category,
            span=span,
            start=start,
            end=start + len(span),
            confidence=float(confidence) if isinstance(confidence, (int, float)) else None,
        ))
    return result
