from dataclasses import dataclass

from .enums import DetectionTier


@dataclass(frozen=True, slots=True)
class DetectionCategory:
    """A sensitive-information category (SPECIFICATION.md §3).
    Create via detection_category_factory."""

    category_id: str
    name: str
    description: str
    tier: DetectionTier
