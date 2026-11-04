import asyncio
import json

import pytest

from app.domain import EvaluationOutcome, MessageRole, Verdict
from app.exception import NotFoundError, ProviderError
from app.llm.provider_errors import http_error
from app.repository.memory.conversation_repository import InMemoryConversationStore
from app.repository.memory.screening_records import InMemoryScreeningRecordWriter
from app.service.conversation.chat_models import SendStatus
from app.service.conversation.chat_service import ChatService
from app.service.screening.screening_service import ScreeningService
from tests.conftest import FakeProvider
from tests.service.screening.test_screening_service import RULES, make_service

ID_AND_MEDICATION = "My ID is 9203105800089 and I take sertraline"
MEDICAL_REPLY = json.dumps({"flags": [{"category": "MEDICAL", "span": "sertraline"}]})


def run(coroutine):
    return asyncio.run(coroutine)


class Setup:
    def __init__(self, detector_reply='{"flags": []}', detector_error=None, history_limit=20, timeout=5.0):
        self.records = InMemoryScreeningRecordWriter()
        self.detector = FakeProvider(reply=detector_reply, error=detector_error)
        screening: ScreeningService = make_service(self.detector, log=self.records)
        self.llm = FakeProvider()
        self.store = InMemoryConversationStore()
        self.chat = ChatService(
            self.store,
            self.store,
            screening,
            self.llm,
            history_limit=history_limit,
            reply_timeout_seconds=timeout,
        )


def user(user_id="00000000-0000-4000-8000-0000000000aa"):
    from app.factory.user_factory import build_user

    return build_user(user_id, "s@uni.ac.za", email_verified=True)


STUDENT, OTHER = user(), user("00000000-0000-4000-8000-0000000000bb")


def test_clean_prompt_is_sent_and_both_messages_saved():
    s = Setup()
    conversation = run(s.chat.create_conversation(STUDENT, "webapp"))
    outcome = run(s.chat.send(STUDENT, conversation.conversation_id, "Explain recursion."))
    assert outcome.status is SendStatus.SENT
    assert outcome.assistant_message.content == s.llm.chat_reply
    detail = run(s.chat.get_conversation(STUDENT, conversation.conversation_id))
    assert [(m.role, m.content) for m in detail.messages] == [
        (MessageRole.USER, "Explain recursion."),
        (MessageRole.ASSISTANT, s.llm.chat_reply),
    ]


def test_flagged_prompt_needs_decision_and_nothing_is_sent_or_saved():
    s = Setup()
    conversation = run(s.chat.create_conversation(STUDENT, "webapp"))
    outcome = run(s.chat.send(STUDENT, conversation.conversation_id, ID_AND_MEDICATION))
    assert outcome.status is SendStatus.NEEDS_DECISION
    assert outcome.screening.result.aggregated_verdict is Verdict.FLAG
    assert s.llm.chat_received == []
    assert run(s.chat.get_conversation(STUDENT, conversation.conversation_id)).messages == ()


def test_send_anyway_always_redacts_rule_values_for_ai_and_storage():
    s = Setup(detector_reply=MEDICAL_REPLY)
    conversation = run(s.chat.create_conversation(STUDENT, "webapp"))
    outcome = run(s.chat.send(STUDENT, conversation.conversation_id, ID_AND_MEDICATION, send_anyway=True))
    assert outcome.status is SendStatus.SENT
    [sent] = s.llm.chat_received
    assert sent[-1].content == "My ID is [REDACTED_SA_ID] and I take sertraline"
    assert "9203105800089" not in outcome.user_message.content
    stored = run(s.chat.get_conversation(STUDENT, conversation.conversation_id)).messages[0]
    assert stored.content == "My ID is [REDACTED_SA_ID] and I take sertraline"
    [entry] = run(s.records.log.find_all())
    assert entry.outcome is EvaluationOutcome.OVERRIDE


def test_unchecked_prompt_needs_decision_then_can_be_sent_anyway():
    s = Setup(detector_error=http_error("groq", 503, "service_unavailable"))
    conversation = run(s.chat.create_conversation(STUDENT, "webapp"))
    first = run(s.chat.send(STUDENT, conversation.conversation_id, "Plan my study week."))
    assert first.status is SendStatus.NEEDS_DECISION and first.screening.notice
    second = run(s.chat.send(STUDENT, conversation.conversation_id, "Plan my study week.", send_anyway=True))
    assert second.status is SendStatus.SENT


def test_previous_messages_are_sent_as_context_up_to_the_limit():
    s = Setup(history_limit=2)
    conversation = run(s.chat.create_conversation(STUDENT, "webapp"))
    for text in ("first", "second", "third"):
        run(s.chat.send(STUDENT, conversation.conversation_id, text))
    last_call = s.llm.chat_received[-1]
    assert [m.content for m in last_call] == ["second", s.llm.chat_reply, "third"]


@pytest.mark.parametrize("action", ["get", "send", "delete"])
def test_other_students_conversation_is_not_found(action):
    s = Setup()
    conversation = run(s.chat.create_conversation(OTHER, "webapp"))
    calls = {
        "get": lambda: s.chat.get_conversation(STUDENT, conversation.conversation_id),
        "send": lambda: s.chat.send(STUDENT, conversation.conversation_id, "hi"),
        "delete": lambda: s.chat.delete_conversation(STUDENT, conversation.conversation_id),
    }
    with pytest.raises(NotFoundError):
        run(calls[action]())
    assert run(s.chat.get_conversation(OTHER, conversation.conversation_id)).conversation == conversation


def test_list_shows_only_own_conversations_newest_first():
    s = Setup()
    older = run(s.chat.create_conversation(STUDENT, "webapp", "Older"))
    newer = run(s.chat.create_conversation(STUDENT, "extension", "Newer"))
    run(s.chat.create_conversation(OTHER, "webapp"))
    run(s.chat.send(STUDENT, newer.conversation_id, "hi"))
    assert [c.conversation_id for c in run(s.chat.list_conversations(STUDENT))] == [
        newer.conversation_id,
        older.conversation_id,
    ]


def test_delete_conversation():
    s = Setup()
    conversation = run(s.chat.create_conversation(STUDENT, "webapp"))
    run(s.chat.delete_conversation(STUDENT, conversation.conversation_id))
    with pytest.raises(NotFoundError):
        run(s.chat.get_conversation(STUDENT, conversation.conversation_id))


@pytest.mark.parametrize("problem", ["error", "timeout", "empty"])
def test_ai_failure_saves_nothing(problem):
    s = Setup(timeout=0.05)
    if problem == "error":
        s.llm.chat_error = http_error("groq", 503, "service_unavailable")
    elif problem == "timeout":
        s.llm.chat_delay_seconds = 0.5
    else:
        s.llm.chat_reply = "   "
    conversation = run(s.chat.create_conversation(STUDENT, "webapp"))
    with pytest.raises(ProviderError):
        run(s.chat.send(STUDENT, conversation.conversation_id, "Explain recursion."))
    assert run(s.chat.get_conversation(STUDENT, conversation.conversation_id)).messages == ()


def test_rule_set_has_the_categories_used_for_placeholders():
    assert RULES.category_named("SA_ID").name == "SA_ID"


# --- Titles from the first prompt ---


def test_first_sent_prompt_titles_the_chat_after_redaction():
    s = Setup(detector_reply=MEDICAL_REPLY)
    conversation = run(s.chat.create_conversation(STUDENT, "webapp"))
    outcome = run(s.chat.send(STUDENT, conversation.conversation_id, ID_AND_MEDICATION, send_anyway=True))
    assert outcome.conversation_title == "My ID is [REDACTED_SA_ID] and I take sertraline"
    assert "9203105800089" not in outcome.conversation_title
    [listed] = run(s.chat.list_conversations(STUDENT))
    assert listed.title == outcome.conversation_title


def test_title_is_not_changed_by_later_prompts():
    s = Setup()
    conversation = run(s.chat.create_conversation(STUDENT, "webapp"))
    run(s.chat.send(STUDENT, conversation.conversation_id, "Explain recursion."))
    later = run(s.chat.send(STUDENT, conversation.conversation_id, "Now explain loops."))
    assert later.conversation_title == "Explain recursion."
    assert run(s.chat.list_conversations(STUDENT))[0].title == "Explain recursion."


def test_a_chosen_title_is_kept():
    s = Setup()
    conversation = run(s.chat.create_conversation(STUDENT, "webapp", title="Essay help"))
    run(s.chat.send(STUDENT, conversation.conversation_id, "Explain recursion."))
    assert run(s.chat.list_conversations(STUDENT))[0].title == "Essay help"


def test_no_title_from_a_prompt_that_was_not_sent():
    s = Setup(detector_reply=MEDICAL_REPLY)
    conversation = run(s.chat.create_conversation(STUDENT, "webapp"))
    outcome = run(s.chat.send(STUDENT, conversation.conversation_id, ID_AND_MEDICATION))
    assert outcome.status is SendStatus.NEEDS_DECISION
    assert outcome.conversation_title is None
    assert run(s.chat.list_conversations(STUDENT))[0].title == "New conversation"
