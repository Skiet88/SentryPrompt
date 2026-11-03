from dataclasses import dataclass

from .enums import ContextCategory


@dataclass(frozen=True, slots=True)
class ContextFlag:
    """A span the context-aware detector flagged. Create via context_flag_factory."""

    category: ContextCategory
    span: str
    start: int
    end: int
    confidence: float | None = None


@dataclass(frozen=True, slots=True)
class ClassificationResult:
    """Outcome of one context-aware classification call."""

    provider: str
    model: str
    prompt_version: str
    flags: tuple[ContextFlag, ...] = ()
    # True when the model's reply was not valid JSON. Treated as "no flags"
    # but reported separately in the evaluation (MODEL_ARCHITECTURE.md §2).
    parse_failed: bool = False

    @property
    def is_flagged(self) -> bool:
        return bool(self.flags)
