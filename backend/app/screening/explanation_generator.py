"""Plain-language explanations shown to students (FR-006, NFR-001).

Explanations are the category descriptions from the rules file, so wording
is maintained as data alongside the categories rather than in code.
"""

from __future__ import annotations

from typing import Protocol

from app.domain import DetectionCategory

UNAVAILABLE_NOTICE = (
    "We couldn't fully check your prompt for sensitive information right now. Review it before sending."
)


class CategoryCatalog(Protocol):
    def category_named(self, name: str) -> DetectionCategory: ...


class ExplanationGenerator:
    def __init__(self, catalog: CategoryCatalog):
        self._catalog = catalog

    def explain(self, category_name: str) -> str:
        return self._catalog.category_named(category_name).description

    @staticmethod
    def unavailable_notice() -> str:
        """Shown when the context-aware check could not complete (NFR-015)."""
        return UNAVAILABLE_NOTICE
