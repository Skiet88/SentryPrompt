"""Masks rule-detected spans before a prompt is sent to an external LLM.

The rule-based detector runs locally first. Anything it finds (ID numbers,
card and account numbers, phone numbers, emails, addresses) is replaced with
a placeholder such as [REDACTED_SA_ID], so those values never leave the
server as part of SentryPrompt's own screening (NFR-008).
"""

from __future__ import annotations

from collections.abc import Iterable


def redact(text: str, spans: Iterable[tuple[int, int, str]]) -> str:
    """Return text with each (start, end, category) span replaced by a placeholder.

    Overlapping spans are merged, keeping the first span's category.
    """
    merged: list[list] = []
    for start, end, category in sorted(spans):
        if not 0 <= start < end <= len(text):
            raise ValueError(f"span ({start}, {end}) is outside the text")
        if merged and start < merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end, category])

    out, pos = [], 0
    for start, end, category in merged:
        out.append(text[pos:start])
        out.append(f"[REDACTED_{category.upper()}]")
        pos = end
    out.append(text[pos:])
    return "".join(out)
