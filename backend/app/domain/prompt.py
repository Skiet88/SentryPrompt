from dataclasses import dataclass
from datetime import datetime

from .enums import PromptStatus, SourceChannel


@dataclass(frozen=True, slots=True)
class Prompt:
    """A prompt being screened. Transient: never persisted, because rawText
    is personal content (NFR-009). Create via prompt_factory."""

    prompt_id: str
    raw_text: str
    source_channel: SourceChannel
    submitted_at: datetime
    status: PromptStatus
