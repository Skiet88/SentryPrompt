"""Chat with the AI, with every prompt screened first.

- Every prompt is screened on the server: the client can't skip screening
  or claim a prompt was clean (FR-008).
- Flagged or unchecked prompts are not sent unless the student chooses
  "send anyway" (FR-007); "edit" is simply sending a new text, which is
  screened again (UC4); "cancel" is not sending.
- Values found by the rule-based detector (ID, card and account numbers,
  phone numbers, emails, addresses) are ALWAYS replaced with placeholders
  before the prompt reaches the AI, even when sent anyway; the stored
  message is that redacted text too, so they are never kept.
- Conversations are only ever looked up together with their owner, and an
  unknown or someone else's conversation gives the same "not found"
  (no IDOR, and no hint that the conversation exists).
"""

from __future__ import annotations

import asyncio
import logging

from app.domain import Conversation, DetectorSource, MessageRole, SourceChannel, User
from app.exception import NotFoundError, ProviderError
from app.factory.conversation_factory import DEFAULT_TITLE, build_conversation
from app.factory.message_factory import build_message
from app.llm import ChatMessage, LLMProvider
from app.llm.provider_errors import network_error
from app.repository.conversation_repository import ConversationRepository, MessageRepository
from app.screening.redaction import redact_with_map
from app.service.screening.i_screening_service import IScreeningService
from app.util.clock import utc_now

from .chat_models import ConversationWithMessages, SendOutcome, SendStatus
from .i_chat_service import IChatService

logger = logging.getLogger(__name__)

DEFAULT_HISTORY_LIMIT = 20
DEFAULT_REPLY_TIMEOUT_SECONDS = 30.0
NOT_FOUND = "Conversation not found."


class ChatService(IChatService):
    def __init__(
        self,
        conversations: ConversationRepository,
        messages: MessageRepository,
        screening: IScreeningService,
        llm: LLMProvider,
        *,
        history_limit: int = DEFAULT_HISTORY_LIMIT,
        reply_timeout_seconds: float = DEFAULT_REPLY_TIMEOUT_SECONDS,
    ):
        if history_limit <= 0 or reply_timeout_seconds <= 0:
            raise ValueError("history_limit and reply_timeout_seconds must be positive")
        self._conversations = conversations
        self._messages = messages
        self._screening = screening
        self._llm = llm
        self._history_limit = history_limit
        self._reply_timeout = reply_timeout_seconds

    async def create_conversation(
        self, user: User, channel: SourceChannel | str, title: str | None = None
    ) -> Conversation:
        conversation = build_conversation(user.user_id, channel, title=title or DEFAULT_TITLE)
        return await self._conversations.create(conversation)

    async def list_conversations(self, user: User) -> list[Conversation]:
        return await self._conversations.list_for_user(user.user_id)

    async def get_conversation(self, user: User, conversation_id: str) -> ConversationWithMessages:
        conversation = await self._owned(user, conversation_id)
        messages = await self._messages.list_for_conversation(conversation)
        return ConversationWithMessages(conversation, tuple(messages))

    async def delete_conversation(self, user: User, conversation_id: str) -> None:
        if not await self._conversations.delete_for_user(conversation_id, user.user_id):
            raise NotFoundError(NOT_FOUND)

    async def send(
        self, user: User, conversation_id: str, text: str, *, send_anyway: bool = False
    ) -> SendOutcome:
        conversation = await self._owned(user, conversation_id)
        screening = await self._screening.screen(text, conversation.channel, send_anyway=send_anyway)
        if screening.requires_student_decision and not send_anyway:
            return SendOutcome(SendStatus.NEEDS_DECISION, screening)

        rule_spans = [
            (e.span.start_index, e.span.end_index, e.category_name)
            for e in screening.spans
            if e.span.detector_source is DetectorSource.RULE
        ]
        safe_text = redact_with_map(text, rule_spans).text
        history = await self._messages.list_for_conversation(conversation, limit=self._history_limit)
        reply = await self._ask_ai(
            [*(ChatMessage(m.role, m.content) for m in history), ChatMessage(MessageRole.USER, safe_text)]
        )

        user_message = build_message(conversation.conversation_id, MessageRole.USER, safe_text)
        assistant_message = build_message(conversation.conversation_id, MessageRole.ASSISTANT, reply)
        await self._messages.append(conversation, [user_message, assistant_message], utc_now())
        return SendOutcome(SendStatus.SENT, screening, user_message, assistant_message)

    async def _owned(self, user: User, conversation_id: str) -> Conversation:
        conversation = await self._conversations.find_for_user(conversation_id, user.user_id)
        if conversation is None:
            raise NotFoundError(NOT_FOUND)
        return conversation

    async def _ask_ai(self, messages: list[ChatMessage]) -> str:
        try:
            reply = await asyncio.wait_for(self._llm.chat(messages), timeout=self._reply_timeout)
        except TimeoutError:
            logger.warning("AI reply timed out after %.0fs (%s)", self._reply_timeout, self._llm.name)
            raise network_error(self._llm.name, "timeout") from None
        except ProviderError as exc:
            logger.warning("AI reply failed: %s", exc)
            raise
        if not reply.strip():
            raise network_error(self._llm.name, "unreadable_response")
        return reply
