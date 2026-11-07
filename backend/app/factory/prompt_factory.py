from __future__ import annotations

from datetime import datetime

from app.domain import Prompt, PromptStatus, SourceChannel

from . import _require

# FR-001 requires "a defined max length". 4,000 characters is well above
# NFR-010's typical prompt (~200 words) while bounding screening cost.
MAX_PROMPT_LENGTH = 4000


def build_prompt(
    raw_text: str,
    source_channel: SourceChannel | str,
    *,
    prompt_id: str | None = None,
    submitted_at: datetime | None = None,
    status: PromptStatus | str = PromptStatus.VALIDATING,
) -> Prompt:
    """Covers Prompt.validate(): empty or over-long text is rejected (FR-001)."""
    return Prompt(
        prompt_id=_require.new_or_given_id(prompt_id, "prompt_id"),
        raw_text=_require.text(raw_text, "Prompt text", MAX_PROMPT_LENGTH),
        source_channel=_require.enum_value(SourceChannel, source_channel, "source_channel"),
        submitted_at=_require.timestamp(submitted_at, "submitted_at"),
        status=_require.enum_value(PromptStatus, status, "status"),
    )
