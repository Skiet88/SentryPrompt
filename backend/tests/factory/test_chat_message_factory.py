import pytest

from app.domain import ChatRole
from app.exception import InvalidArgumentError
from app.factory.chat_message_factory import build_chat_message


def test_builds_message():
    message = build_chat_message("user", "Hello")
    assert (message.role, message.content) == (ChatRole.USER, "Hello")


@pytest.mark.parametrize("role, content", [("system", "x"), ("user", ""), ("assistant", "  ")])
def test_rejects_invalid_input(role, content):
    with pytest.raises(InvalidArgumentError):
        build_chat_message(role, content)
