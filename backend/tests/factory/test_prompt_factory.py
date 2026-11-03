from datetime import datetime

import pytest

from app.domain import PromptStatus, SourceChannel
from app.exception import InvalidArgumentError
from app.factory.prompt_factory import MAX_PROMPT_LENGTH, build_prompt


def test_builds_prompt_with_defaults():
    prompt = build_prompt("Help me with my essay", "webapp")
    assert prompt.source_channel is SourceChannel.WEBAPP
    assert prompt.status is PromptStatus.VALIDATING
    assert prompt.prompt_id and prompt.submitted_at.tzinfo is not None


def test_accepts_max_length():
    assert len(build_prompt("a" * MAX_PROMPT_LENGTH, "extension").raw_text) == MAX_PROMPT_LENGTH


@pytest.mark.parametrize(
    "text, message",
    [
        ("", "cannot be empty"),
        ("   ", "cannot be empty"),
        ("a" * (MAX_PROMPT_LENGTH + 1), "cannot be longer"),
    ],
)
def test_rejects_empty_or_too_long_text(text, message):
    with pytest.raises(InvalidArgumentError, match=message):
        build_prompt(text, "webapp")


def test_rejects_unknown_channel():
    with pytest.raises(InvalidArgumentError, match="source_channel must be one of"):
        build_prompt("text", "email")


def test_rejects_naive_timestamp():
    with pytest.raises(InvalidArgumentError, match="timezone-aware"):
        build_prompt("text", "webapp", submitted_at=datetime(2026, 1, 1))


def test_rejects_blank_given_id():
    with pytest.raises(InvalidArgumentError, match="prompt_id"):
        build_prompt("text", "webapp", prompt_id=" ")
