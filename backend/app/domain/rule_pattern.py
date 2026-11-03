import re
from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class RulePattern:
    """A regex belonging to a rule-based DetectionCategory (NFR-005).
    Create via rule_pattern_factory, which checks the regex compiles."""

    pattern_id: str
    category_id: str
    regex_pattern: str
    description: str
    _compiled: re.Pattern = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "_compiled", re.compile(self.regex_pattern))

    def matches(self, text: str) -> bool:
        return self._compiled.search(text) is not None
