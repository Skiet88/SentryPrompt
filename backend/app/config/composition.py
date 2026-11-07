"""Composition root: builds the screening service from settings.

The one place that chooses concrete classes (rules file, LLM provider,
prompt version). Everything else depends on interfaces.
"""

from __future__ import annotations

from typing import Protocol

from app.llm import LLMConfig, LLMProvider, LLMProviderFactory
from app.repository.conversation_repository import ConversationRepository, MessageRepository
from app.repository.memory.screening_records import InMemoryScreeningRecordWriter
from app.repository.screening_record_writer import ScreeningRecordWriter
from app.screening.classification_parser import ClassificationParser
from app.screening.context_aware_detector import ContextAwareDetector
from app.screening.explanation_generator import ExplanationGenerator
from app.screening.prompt_template import CONTEXT_DETECTOR_PROMPT_VERSION, PromptTemplate
from app.screening.rules.rule_based_detector import RuleBasedDetector
from app.screening.rules.rule_source import JsonRuleSource, RuleSource
from app.service.conversation.chat_service import ChatService
from app.service.screening.screening_service import ScreeningService


class ScreeningConfig(LLMConfig, Protocol):
    """Settings the screening pipeline needs (the app's Settings satisfies this)."""

    @property
    def context_detector_timeout_seconds(self) -> float: ...


def build_screening_service(
    config: ScreeningConfig,
    rule_source: RuleSource | None = None,
    provider_factory: LLMProviderFactory | None = None,
    records: ScreeningRecordWriter | None = None,
    provider: LLMProvider | None = None,
) -> ScreeningService:
    rule_set = (rule_source or JsonRuleSource()).load()
    provider = provider or (provider_factory or LLMProviderFactory()).create(config)
    context_detector = ContextAwareDetector(
        provider,
        PromptTemplate.load(CONTEXT_DETECTOR_PROMPT_VERSION),
        ClassificationParser(),
        timeout_seconds=config.context_detector_timeout_seconds,
    )
    return ScreeningService(
        rule_detector=RuleBasedDetector(rule_set),
        context_detector=context_detector,
        catalog=rule_set,
        explainer=ExplanationGenerator(rule_set),
        records=records or InMemoryScreeningRecordWriter(),
    )


class ChatConfig(Protocol):
    @property
    def chat_history_limit(self) -> int: ...
    @property
    def chat_reply_timeout_seconds(self) -> float: ...


def build_chat_service(
    config: ChatConfig,
    conversations: ConversationRepository,
    messages: MessageRepository,
    screening: ScreeningService,
    provider: LLMProvider,
) -> ChatService:
    """The chat shares the screening service's LLM provider."""
    return ChatService(
        conversations,
        messages,
        screening,
        provider,
        history_limit=config.chat_history_limit,
        reply_timeout_seconds=config.chat_reply_timeout_seconds,
    )
