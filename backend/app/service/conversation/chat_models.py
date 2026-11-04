from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.domain import Conversation, Message
from app.service.screening.screening_outcome import ScreeningOutcome


class SendStatus(StrEnum):
    SENT = "sent"
    # Flagged or not fully checked: the student must edit, send anyway or
    # cancel (FR-007). Nothing was sent to the AI or saved (FR-008).
    NEEDS_DECISION = "needs_decision"


@dataclass(frozen=True, slots=True)
class SendOutcome:
    status: SendStatus
    screening: ScreeningOutcome
    user_message: Message | None = None
    assistant_message: Message | None = None


@dataclass(frozen=True, slots=True)
class ConversationWithMessages:
    conversation: Conversation
    messages: tuple[Message, ...]
