"""What a detector returns, before the screening service turns it into the
persisted ScreeningResult and FlaggedSpan entities (step 3)."""

from dataclasses import dataclass
from enum import StrEnum

from app.domain import DetectorSource


class ContextCategory(StrEnum):
    """Category names the context-aware tier can return (SPECIFICATION.md §3)."""

    MEDICAL = "MEDICAL"
    INSTITUTIONAL = "INSTITUTIONAL"


@dataclass(frozen=True, slots=True)
class DetectedSpan:
    """A span one detector flagged. Create via detected_span_factory."""

    category: str
    start: int
    end: int
    detector_source: DetectorSource
    # Self-reported by the LLM; for qualitative discussion only, never a
    # threshold (MODEL_ARCHITECTURE.md §4).
    confidence: float | None = None


@dataclass(frozen=True, slots=True)
class ContextDetectionResult:
    """Outcome of one context-aware classification call."""

    provider: str
    model: str
    prompt_version: str
    spans: tuple[DetectedSpan, ...] = ()
    # True when the model's reply was not valid JSON: treated as "no flags"
    # but reported separately in the evaluation (MODEL_ARCHITECTURE.md §2).
    parse_failed: bool = False

    @property
    def is_flagged(self) -> bool:
        return bool(self.spans)
