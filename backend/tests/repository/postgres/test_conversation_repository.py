"""Conversations and messages in PostgreSQL: encryption at rest (NFR-011),
owner scoping (IDOR) and deletion."""

import os
import uuid

import pytest
from sqlalchemy import text

from app.factory.conversation_factory import build_conversation
from app.factory.message_factory import build_message
from app.repository.encryption.message_cipher import AesGcmMessageCipher, DecryptionError
from app.repository.postgres.conversation_repository import (
    PostgresConversationRepository,
    PostgresMessageRepository,
)
from app.util.clock import utc_now
from tests.repository.postgres.conftest import run

SENSITIVE_TEXT = "I take sertraline for anxiety"


async def add_user(engine) -> str:
    user_id = uuid.uuid4()
    async with engine.begin() as connection:
        await connection.execute(
            text("INSERT INTO auth.users (id, email) VALUES (:id, 'x@y.co')"), {"id": user_id}
        )
    return str(user_id)


def setup(engine):
    cipher = AesGcmMessageCipher(os.urandom(32))
    return PostgresConversationRepository(engine), PostgresMessageRepository(engine, cipher), cipher


def conversation_with_messages(engine):
    conversations, messages, cipher = setup(engine)
    owner = run(add_user(engine))
    conversation = run(conversations.create(build_conversation(owner, "webapp", title="Help")))
    user_msg = build_message(conversation.conversation_id, "user", SENSITIVE_TEXT)
    reply = build_message(conversation.conversation_id, "assistant", "Here are some study tips.")
    run(messages.append(conversation, [user_msg, reply], utc_now()))
    return conversations, messages, cipher, conversation, owner


def test_messages_round_trip_in_order(engine):
    _, messages, _, conversation, _ = conversation_with_messages(engine)
    stored = run(messages.list_for_conversation(conversation))
    assert [m.content for m in stored] == [SENSITIVE_TEXT, "Here are some study tips."]
    assert [m.content for m in run(messages.list_for_conversation(conversation, limit=1))] == [
        "Here are some study tips."
    ]


def test_database_holds_only_ciphertext(engine):
    conversation_with_messages(engine)

    async def raw():
        async with engine.connect() as connection:
            return (
                (await connection.execute(text("SELECT content_ciphertext FROM public.messages")))
                .scalars()
                .all()
            )

    blobs = run(raw())
    assert len(blobs) == 2
    assert all(b"sertraline" not in bytes(b) and b"study" not in bytes(b) for b in blobs)


def test_ciphertext_moved_to_another_conversation_cannot_be_read(engine):
    conversations, messages, _, conversation, owner = conversation_with_messages(engine)
    other = run(conversations.create(build_conversation(owner, "webapp")))

    async def move():
        async with engine.begin() as connection:
            await connection.execute(
                text("UPDATE public.messages SET conversation_id = :to WHERE conversation_id = :from"),
                {"to": uuid.UUID(other.conversation_id), "from": uuid.UUID(conversation.conversation_id)},
            )

    run(move())
    with pytest.raises(DecryptionError):
        run(messages.list_for_conversation(other))


def test_wrong_key_cannot_read(engine):
    _, _, _, conversation, _ = conversation_with_messages(engine)
    with pytest.raises(DecryptionError):
        run(
            PostgresMessageRepository(engine, AesGcmMessageCipher(os.urandom(32))).list_for_conversation(
                conversation
            )
        )


def test_conversations_are_owner_scoped(engine):
    conversations, _, _, conversation, owner = conversation_with_messages(engine)
    stranger = run(add_user(engine))
    assert run(conversations.find_for_user(conversation.conversation_id, stranger)) is None
    assert run(conversations.list_for_user(stranger)) == []
    assert run(conversations.delete_for_user(conversation.conversation_id, stranger)) is False
    assert run(conversations.find_for_user(conversation.conversation_id, owner)) is not None


def test_message_query_also_enforces_the_owner(engine):
    """Defence in depth: even a forged Conversation object with another
    user's ID reads nothing, because the query joins on the owner."""
    from dataclasses import replace

    _, messages, _, conversation, _ = conversation_with_messages(engine)
    stranger = run(add_user(engine))
    assert run(messages.list_for_conversation(replace(conversation, user_id=stranger))) == []


def test_delete_removes_messages(engine):
    conversations, _, _, conversation, owner = conversation_with_messages(engine)
    assert run(conversations.delete_for_user(conversation.conversation_id, owner)) is True

    async def count():
        async with engine.connect() as connection:
            return (await connection.execute(text("SELECT count(*) FROM public.messages"))).scalar_one()

    assert run(count()) == 0


def test_list_is_newest_first(engine):
    conversations, messages, _, first, owner = conversation_with_messages(engine)
    second = run(conversations.create(build_conversation(owner, "extension", title="Later")))
    run(messages.append(second, [build_message(second.conversation_id, "user", "hi")], utc_now()))
    assert [c.conversation_id for c in run(conversations.list_for_user(owner))] == [
        second.conversation_id,
        first.conversation_id,
    ]
