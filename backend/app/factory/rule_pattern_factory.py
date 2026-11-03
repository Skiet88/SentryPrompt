from __future__ import annotations

from app.domain import RulePattern
from app.exception import InvalidArgumentError
from app.util.validation import is_valid_regex

from . import _require


def build_rule_pattern(
    category_id: str,
    regex_pattern: str,
    description: str,
    *,
    pattern_id: str | None = None,
) -> RulePattern:
    if not is_valid_regex(regex_pattern):
        raise InvalidArgumentError("regex_pattern must be a valid, non-empty regular expression")
    return RulePattern(
        pattern_id=_require.new_or_given_id(pattern_id, "pattern_id"),
        category_id=_require.identifier(category_id, "category_id"),
        regex_pattern=regex_pattern,
        description=_require.text(description, "Pattern description"),
    )
