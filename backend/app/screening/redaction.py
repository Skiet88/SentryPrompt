"""Masks rule-detected spans before a prompt is sent to an external LLM.

The rule-based detector runs locally first. Anything it finds (ID numbers,
card and account numbers, phone numbers, emails, addresses) is replaced with
a placeholder such as [REDACTED_SA_ID], so those values never leave the
server as part of SentryPrompt's own screening (NFR-008).

Because placeholders differ in length from what they replace, positions in
the redacted text differ from positions in the original. RedactedText keeps
a map so spans the LLM flags in the redacted text can be highlighted in the
student's original text (FR-005).
"""

from __future__ import annotations

from bisect import bisect_right
from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class _Segment:
    redacted_start: int
    redacted_end: int
    original_start: int
    original_end: int
    is_placeholder: bool


@dataclass(frozen=True, slots=True)
class RedactedText:
    text: str
    original_length: int
    _segments: tuple[_Segment, ...]

    def to_original(self, start: int, end: int) -> tuple[int, int]:
        """Map a span in the redacted text to the original text. A span that
        touches a placeholder grows to cover everything the placeholder hid."""
        if not 0 <= start < end <= len(self.text):
            raise ValueError(f"span ({start}, {end}) is outside the redacted text")
        first = self._segment_at(start)
        last = self._segment_at(end - 1)
        original_start = (
            first.original_start
            if first.is_placeholder
            else first.original_start + (start - first.redacted_start)
        )
        original_end = (
            last.original_end if last.is_placeholder else last.original_start + (end - last.redacted_start)
        )
        return original_start, original_end

    def _segment_at(self, position: int) -> _Segment:
        starts = [segment.redacted_start for segment in self._segments]
        return self._segments[bisect_right(starts, position) - 1]


def redact_with_map(text: str, spans: Iterable[tuple[int, int, str]]) -> RedactedText:
    """Replace each (start, end, category) span with a placeholder.

    Overlapping spans are merged, keeping the first span's category.
    """
    merged: list[tuple[int, int, str]] = []
    for start, end, category in sorted(spans):
        if not 0 <= start < end <= len(text):
            raise ValueError(f"span ({start}, {end}) is outside the text")
        if merged and start < merged[-1][1]:
            prev_start, prev_end, prev_category = merged[-1]
            merged[-1] = (prev_start, max(prev_end, end), prev_category)
        else:
            merged.append((start, end, category))

    parts: list[str] = []
    segments: list[_Segment] = []
    original_pos = 0
    redacted_pos = 0

    def add(piece: str, original_start: int, original_end: int, is_placeholder: bool) -> None:
        nonlocal redacted_pos
        if not piece:
            return
        parts.append(piece)
        segments.append(
            _Segment(redacted_pos, redacted_pos + len(piece), original_start, original_end, is_placeholder)
        )
        redacted_pos += len(piece)

    for start, end, category in merged:
        add(text[original_pos:start], original_pos, start, is_placeholder=False)
        add(f"[REDACTED_{category.upper()}]", start, end, is_placeholder=True)
        original_pos = end
    add(text[original_pos:], original_pos, len(text), is_placeholder=False)

    return RedactedText(text="".join(parts), original_length=len(text), _segments=tuple(segments))


def redact(text: str, spans: Iterable[tuple[int, int, str]]) -> str:
    """Return only the redacted text (see redact_with_map)."""
    return redact_with_map(text, spans).text
