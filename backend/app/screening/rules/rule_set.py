"""The loaded, validated set of detection categories and rules."""

from __future__ import annotations

from dataclasses import dataclass

from app.domain import DetectionCategory, DetectionTier, RulePattern

from .match_validators import MatchValidator


@dataclass(frozen=True, slots=True)
class Rule:
    """One rule-based pattern with its category and optional match validator."""

    pattern: RulePattern
    category: DetectionCategory
    validator: MatchValidator | None = None


@dataclass(frozen=True, slots=True)
class RuleSet:
    # All categories, rule-based and context-aware, in priority order.
    categories: tuple[DetectionCategory, ...]
    # Rule-based rules, in category priority order.
    rules: tuple[Rule, ...]

    def priority_of(self, category_name: str) -> int:
        """Lower is higher priority; used to resolve overlapping matches."""
        for index, category in enumerate(self.categories):
            if category.name == category_name:
                return index
        raise KeyError(category_name)

    def category_named(self, name: str) -> DetectionCategory:
        for category in self.categories:
            if category.name == name:
                return category
        raise KeyError(name)

    def categories_in_tier(self, tier: DetectionTier) -> tuple[DetectionCategory, ...]:
        return tuple(c for c in self.categories if c.tier is tier)
