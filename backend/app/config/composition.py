"""Composition root: builds the screening service from settings.

The one place that chooses concrete classes (rules file, LLM provider,
prompt version). Everything else depends on interfaces.
"""

from __future__ import annotations

from typing import Protocol

from app.llm import LLMConfig, LLMProviderFactory
from app.repository.evaluation_log_entry_repository import EvaluationLogEntryRepository
from app.repository.memory.evaluation_log_entry_repository import InMemoryEvaluationLogEntryRepository
from app.screening.classification_parser import ClassificationParser
from app.screening.context_aware_detector import ContextAwareDetector
from app.screening.explanation_generator import ExplanationGenerator
from app.screening.prompt_template import CONTEXT_DETECTOR_PROMPT_VERSION, PromptTemplate
from app.screening.rules.rule_based_detector import RuleBasedDetector
from app.screening.rules.rule_source import JsonRuleSource, RuleSource
from app.service.screening.screening_service import ScreeningService


class ScreeningConfig(LLMConfig, Protocol):
    """Settings the screening pipeline needs (the app's Settings satisfies this)."""

    @property
    def context_detector_timeout_seconds(self) -> float: ...


def build_screening_service(
    config: ScreeningConfig,
    rule_source: RuleSource | None = None,
    provider_factory: LLMProviderFactory | None = None,
    evaluation_log: EvaluationLogEntryRepository | None = None,
) -> ScreeningService:
    rule_set = (rule_source or JsonRuleSource()).load()
    provider = (provider_factory or LLMProviderFactory()).create(config)
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
        evaluation_log=evaluation_log or InMemoryEvaluationLogEntryRepository(),
    )
