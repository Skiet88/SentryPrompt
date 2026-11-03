import pytest

from app.domain import MessageRole
from app.exception import InvalidArgumentError
from app.factory.message_factory import build_message


def test_builds_message():
    message = build_message("conv-1", "assistant", "Here is your outline")
    assert message.role is MessageRole.ASSISTANT


@pytest.mark.parametrize("conversation_id, role, content", [
    ("", "user", "hi"),
    ("conv-1", "system", "hi"),
    ("conv-1", "user", "  "),
])
def test_rejects_invalid_input(conversation_id, role, content):
    with pytest.raises(InvalidArgumentError):
        build_message(conversation_id, role, content)
