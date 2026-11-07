from __future__ import annotations

from app.domain import DetectionCategory, DetectionTier

from . import _require


def build_detection_category(
    name: str,
    description: str,
    tier: DetectionTier | str,
    *,
    category_id: str | None = None,
) -> DetectionCategory:
    return DetectionCategory(
        category_id=_require.new_or_given_id(category_id, "category_id"),
        name=_require.text(name, "Category name", 100),
        description=_require.text(description, "Category description"),
        tier=_require.enum_value(DetectionTier, tier, "tier"),
    )
