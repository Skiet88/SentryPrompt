"""What a detector returns, before the screening service turns it into the
persisted ScreeningResult and FlaggedSpan entities (step 3)."""

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from app.domain import DetectorSource, Verdict


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


class DetectionResult(Protocol):
    """What every detector returns (Liskov: the screening service treats all
    detectors' results the same way)."""

    @property
    def spans(self) -> tuple[DetectedSpan, ...]: ...

    @property
    def verdict(self) -> Verdict: ...

    @property
    def completed(self) -> bool:
        """False when the detector could not finish (verdict UNAVAILABLE)."""
        ...


@dataclass(frozen=True, slots=True)
class RuleDetectionResult:
    """Outcome of the rule-based detector. It runs locally and always
    completes, so its verdict is never UNAVAILABLE."""

    spans: tuple[DetectedSpan, ...] = ()

    @property
    def completed(self) -> bool:
        return True

    @property
    def verdict(self) -> Verdict:
        return Verdict.FLAG if self.spans else Verdict.NO_FLAG


@dataclass(frozen=True, slots=True)
class ContextDetectionResult:
    """Outcome of one context-aware classification call."""

    provider: str
    model: str
    prompt_version: str
    spans: tuple[DetectedSpan, ...] = ()
    # True when the model's reply was not valid JSON. Reported separately in
    # the evaluation (MODEL_ARCHITECTURE.md §2).
    parse_failed: bool = False
    # Set when the check could not complete: provider error, timeout, or an
    # unreadable reply. Never treated as clean (fail closed, NFR-015).
    failure_reason: str | None = None

    @property
    def is_flagged(self) -> bool:
        return bool(self.spans)

    @property
    def completed(self) -> bool:
        return self.failure_reason is None

    @property
    def verdict(self) -> Verdict:
        if not self.completed:
            return Verdict.UNAVAILABLE
        return Verdict.FLAG if self.spans else Verdict.NO_FLAG
