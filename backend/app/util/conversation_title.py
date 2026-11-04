"""Short chat titles made from a (redacted) prompt."""

from __future__ import annotations

import re

MAX_GENERATED_TITLE_LENGTH = 60
_PLACEHOLDER = re.compile(r"\[REDACTED_[A-Z_]{1,40}\]")


def title_from_prompt(redacted_text: str, fallback: str, max_length: int = MAX_GENERATED_TITLE_LENGTH) -> str:
    """The prompt on one line, cut at a word boundary with "…" if long.

    Only ever called with redacted text, so placeholders such as
    [REDACTED_SA_ID] stand where detected values were; a cut never splits one.
    """
    text = " ".join(redacted_text.split())
    if not text:
        return fallback
    if len(text) <= max_length:
        return text
    cut = max_length - 1
    for match in _PLACEHOLDER.finditer(text):
        if match.start() < cut < match.end():
            cut = match.start()
            break
    head = text[:cut]
    # Drop a partly cut last word (only if the cut fell inside it).
    if text[cut] != " " and " " in head.strip():
        head = head[: head.rstrip().rfind(" ")]
    head = head.rstrip(" ,.;:-")
    return f"{head}…" if head else fallback
