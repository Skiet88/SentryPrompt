from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import delete, insert, select, update
from sqlalchemy.ext.asyncio import AsyncEngine

from app.domain import Conversation, Message
from app.factory.conversation_factory import build_conversation
from app.factory.message_factory import build_message

from ..conversation_repository import ConversationRepository, MessageRepository
from ..encryption.message_cipher import MessageCipher
from .mappers import Row, as_uuid
from .tables import conversations, messages


def _conversation_from_row(row: Row) -> Conversation:
    return build_conversation(
        user_id=str(row["user_id"]),
        channel=row["channel"],
        title=row["title"],
        conversation_id=str(row["id"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


class PostgresConversationRepository(ConversationRepository):
    def __init__(self, engine: AsyncEngine):
        self._engine = engine

    async def create(self, conversation: Conversation) -> Conversation:
        async with self._engine.begin() as connection:
            await connection.execute(
                insert(conversations),
                [
                    {
                        "id": as_uuid(conversation.conversation_id),
                        "user_id": as_uuid(conversation.user_id),
                        "title": conversation.title,
                        "channel": conversation.channel.value,
                        "created_at": conversation.created_at,
                        "updated_at": conversation.updated_at,
                    }
                ],
            )
        return conversation

    async def find_for_user(self, conversation_id: str, user_id: str) -> Conversation | None:
        async with self._engine.connect() as connection:
            row = (
                (
                    await connection.execute(
                        select(conversations).where(
                            conversations.c.id == as_uuid(conversation_id),
                            conversations.c.user_id == as_uuid(user_id),
                        )
                    )
                )
                .mappings()
                .first()
            )
        return _conversation_from_row(row) if row else None

    async def list_for_user(self, user_id: str) -> list[Conversation]:
        async with self._engine.connect() as connection:
            rows = (
                (
                    await connection.execute(
                        select(conversations)
                        .where(conversations.c.user_id == as_uuid(user_id))
                        .order_by(conversations.c.updated_at.desc())
                    )
                )
                .mappings()
                .all()
            )
        return [_conversation_from_row(r) for r in rows]

    async def delete_for_user(self, conversation_id: str, user_id: str) -> bool:
        async with self._engine.begin() as connection:
            result = await connection.execute(
                delete(conversations).where(
                    conversations.c.id == as_uuid(conversation_id),
                    conversations.c.user_id == as_uuid(user_id),
                )
            )
        return bool(result.rowcount)


class PostgresMessageRepository(MessageRepository):
    def __init__(self, engine: AsyncEngine, cipher: MessageCipher):
        self._engine = engine
        self._cipher = cipher

    async def append(
        self, conversation: Conversation, new_messages: Sequence[Message], updated_at: datetime
    ) -> None:
        rows = [
            {
                "id": as_uuid(m.message_id),
                "conversation_id": as_uuid(conversation.conversation_id),
                "role": m.role.value,
                "content_ciphertext": self._cipher.encrypt(
                    m.content, message_id=m.message_id, conversation_id=conversation.conversation_id
                ),
                "created_at": m.created_at,
            }
            for m in new_messages
        ]
        async with self._engine.begin() as connection:
            if rows:
                await connection.execute(insert(messages), rows)
            await connection.execute(
                update(conversations)
                .where(
                    conversations.c.id == as_uuid(conversation.conversation_id),
                    conversations.c.user_id == as_uuid(conversation.user_id),
                )
                .values(updated_at=updated_at)
            )

    async def list_for_conversation(
        self, conversation: Conversation, limit: int | None = None
    ) -> list[Message]:
        query = (
            select(messages)
            .join(conversations, conversations.c.id == messages.c.conversation_id)
            .where(
                messages.c.conversation_id == as_uuid(conversation.conversation_id),
                conversations.c.user_id == as_uuid(conversation.user_id),
            )
            .order_by(messages.c.created_at.desc(), messages.c.id.desc())
        )
        if limit:
            query = query.limit(limit)
        async with self._engine.connect() as connection:
            rows = (await connection.execute(query)).mappings().all()
        return [
            build_message(
                conversation_id=conversation.conversation_id,
                role=r["role"],
                content=self._cipher.decrypt(
                    r["content_ciphertext"],
                    message_id=str(r["id"]),
                    conversation_id=conversation.conversation_id,
                ),
                message_id=str(r["id"]),
                created_at=r["created_at"],
            )
            for r in reversed(rows)
        ]
