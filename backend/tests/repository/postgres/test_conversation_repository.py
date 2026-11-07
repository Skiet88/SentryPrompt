"""Conversations and messages in PostgreSQL: encryption at rest (NFR-011),
owner scoping (IDOR) and deletion."""

import os
import uuid

import pytest
from sqlalchemy import text

from app.factory.conversation_factory import DEFAULT_TITLE, build_conversation
from app.factory.message_factory import build_message
from app.repository.encryption.message_cipher import AesGcmMessageCipher, DecryptionError
from app.repository.encryption.title_cipher import AesGcmTitleCipher
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


def setup(engine, key: bytes | None = None):
    key = key or os.urandom(32)
    cipher = AesGcmMessageCipher(key)
    conversations = PostgresConversationRepository(engine, AesGcmTitleCipher(key))
    return conversations, PostgresMessageRepository(engine, cipher), cipher


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


# --- Titles: made from the first prompt, so encrypted like messages ---

TITLE = "I take sertraline and need an extension"


async def raw_titles(engine):
    async with engine.connect() as connection:
        rows = await connection.execute(text("SELECT id, title_ciphertext FROM public.conversations"))
        return {str(r.id): r.title_ciphertext for r in rows}


def test_title_round_trips_and_is_stored_only_as_ciphertext(engine):
    conversations, *_ = setup(engine)
    owner = run(add_user(engine))
    conversation = run(conversations.create(build_conversation(owner, "webapp")))
    assert run(conversations.set_title(conversation.conversation_id, owner, TITLE)) is True

    found = run(conversations.find_for_user(conversation.conversation_id, owner))
    assert found is not None and found.title == TITLE
    stored = run(raw_titles(engine))[conversation.conversation_id]
    assert stored is not None and b"sertraline" not in stored


def test_default_title_is_stored_as_null(engine):
    conversations, *_ = setup(engine)
    owner = run(add_user(engine))
    conversation = run(conversations.create(build_conversation(owner, "webapp")))
    assert run(raw_titles(engine))[conversation.conversation_id] is None
    assert run(conversations.list_for_user(owner))[0].title == DEFAULT_TITLE


def test_set_title_is_owner_scoped(engine):
    conversations, *_ = setup(engine)
    owner, other = run(add_user(engine)), run(add_user(engine))
    conversation = run(conversations.create(build_conversation(owner, "webapp")))
    assert run(conversations.set_title(conversation.conversation_id, other, "hijacked")) is False
    assert run(conversations.list_for_user(owner))[0].title == DEFAULT_TITLE


def test_title_moved_to_another_conversation_falls_back_to_default(engine):
    conversations, *_ = setup(engine)
    owner = run(add_user(engine))
    first = run(conversations.create(build_conversation(owner, "webapp", title=TITLE)))
    second = run(conversations.create(build_conversation(owner, "webapp")))

    async def copy_title():
        async with engine.begin() as connection:
            await connection.execute(
                text(
                    "UPDATE public.conversations SET title_ciphertext = "
                    "(SELECT title_ciphertext FROM public.conversations WHERE id = :src) WHERE id = :dst"
                ),
                {"src": uuid.UUID(first.conversation_id), "dst": uuid.UUID(second.conversation_id)},
            )

    run(copy_title())
    moved = run(conversations.find_for_user(second.conversation_id, owner))
    assert moved is not None and moved.title == DEFAULT_TITLE


def test_wrong_key_cannot_read_titles(engine):
    conversations, *_ = setup(engine)
    owner = run(add_user(engine))
    run(conversations.create(build_conversation(owner, "webapp", title=TITLE)))
    other_key, *_ = setup(engine, os.urandom(32))
    assert run(other_key.list_for_user(owner))[0].title == DEFAULT_TITLE
