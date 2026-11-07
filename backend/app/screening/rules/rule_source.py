"""Where detection categories and rules come from (NFR-005).

RuleSource is an interface so the config file can later be replaced by the
database (admin-managed rules, UC10) without changing the detector.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from app.domain import DetectionCategory, DetectionTier
from app.exception import ConfigurationError, InvalidArgumentError
from app.factory.detection_category_factory import build_detection_category
from app.factory.rule_pattern_factory import build_rule_pattern

from .match_validators import ValidatorRegistry, validator_registry
from .rule_set import Rule, RuleSet

DEFAULT_RULES_FILE = Path(__file__).parent / "detection_categories.json"
SUPPORTED_VERSION = 1


class RuleSource(ABC):
    @abstractmethod
    def load(self) -> RuleSet: ...


class JsonRuleSource(RuleSource):
    def __init__(self, path: Path = DEFAULT_RULES_FILE, validators: ValidatorRegistry = validator_registry):
        self._path = path
        self._validators = validators

    def load(self) -> RuleSet:
        data = self._read()
        categories: list[DetectionCategory] = []
        rules: list[Rule] = []
        seen_names: set[str] = set()
        seen_ids: set[str] = set()

        for entry in self._list(data, "categories", "file"):
            category = self._build_category(entry)
            self._check_unique(category.name, seen_names, "category name")
            self._check_unique(category.category_id, seen_ids, "id")
            patterns = self._list(entry, "patterns", f"category {category.name}")
            if category.tier is DetectionTier.RULE_BASED and not patterns:
                raise ConfigurationError(f"Rule-based category {category.name} has no patterns")
            if category.tier is DetectionTier.CONTEXT_AWARE and patterns:
                raise ConfigurationError(f"Context-aware category {category.name} cannot have patterns")
            categories.append(category)
            for pattern_entry in patterns:
                rule = self._build_rule(pattern_entry, category)
                self._check_unique(rule.pattern.pattern_id, seen_ids, "id")
                rules.append(rule)

        return RuleSet(categories=tuple(categories), rules=tuple(rules))

    def _read(self) -> dict[str, Any]:
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ConfigurationError(f"Cannot read rules file {self._path.name}: {exc}") from exc
        if not isinstance(data, dict) or data.get("version") != SUPPORTED_VERSION:
            raise ConfigurationError(f"Rules file must be a version {SUPPORTED_VERSION} object")
        return data

    @staticmethod
    def _list(container: dict[str, Any], key: str, where: str) -> list[dict[str, Any]]:
        value = container.get(key)
        if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
            raise ConfigurationError(f"'{key}' in {where} must be a list of objects")
        return value

    @staticmethod
    def _check_unique(value: str, seen: set[str], label: str) -> None:
        if value in seen:
            raise ConfigurationError(f"Duplicate {label} in rules file: {value}")
        seen.add(value)

    @staticmethod
    def _build_category(entry: dict[str, Any]) -> DetectionCategory:
        try:
            return build_detection_category(
                name=entry.get("name", ""),
                description=entry.get("description", ""),
                tier=entry.get("tier", ""),
                category_id=entry.get("id"),
            )
        except InvalidArgumentError as exc:
            raise ConfigurationError(f"Invalid category {entry.get('name')!r}: {exc}") from exc

    def _build_rule(self, entry: dict[str, Any], category: DetectionCategory) -> Rule:
        try:
            pattern = build_rule_pattern(
                category_id=category.category_id,
                regex_pattern=entry.get("regex", ""),
                description=entry.get("description", ""),
                pattern_id=entry.get("id"),
            )
        except InvalidArgumentError as exc:
            raise ConfigurationError(f"Invalid pattern in {category.name}: {exc}") from exc
        validator_name = entry.get("validator")
        validator = self._validators.get(validator_name) if validator_name is not None else None
        return Rule(pattern=pattern, category=category, validator=validator)
