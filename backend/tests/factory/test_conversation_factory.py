from datetime import timedelta

import pytest

from app.domain import SourceChannel
from app.exception import InvalidArgumentError
from app.factory.conversation_factory import DEFAULT_TITLE, build_conversation


def test_builds_conversation_with_defaults():
    conversation = build_conversation("uid-1", "webapp")
    assert conversation.title == DEFAULT_TITLE
    assert conversation.channel is SourceChannel.WEBAPP
    assert conversation.updated_at == conversation.created_at


def test_rejects_update_before_creation(aware_time):
    with pytest.raises(InvalidArgumentError, match="updated_at"):
        build_conversation("uid-1", "webapp", created_at=aware_time,
                           updated_at=aware_time - timedelta(seconds=1))


@pytest.mark.parametrize("kwargs, message", [
    ({"user_id": ""}, "user_id"),
    ({"channel": "sms"}, "channel"),
    ({"title": ""}, "title"),
    ({"title": "x" * 201}, "title"),
])
def test_rejects_invalid_input(kwargs, message):
    args = {"user_id": "uid-1", "channel": "webapp", **kwargs}
    with pytest.raises(InvalidArgumentError, match=message):
        build_conversation(**args)
