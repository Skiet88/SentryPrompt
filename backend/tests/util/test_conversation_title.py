import pytest

from app.util.conversation_title import MAX_GENERATED_TITLE_LENGTH, title_from_prompt

FALLBACK = "New conversation"


def test_short_prompt_is_used_on_one_line():
    assert title_from_prompt("  Explain\n\nrecursion   simply ", FALLBACK) == "Explain recursion simply"


def test_long_prompt_is_cut_at_a_word_with_an_ellipsis():
    title = title_from_prompt(
        "Can you help me write an email to my lecturer asking for an extension please", FALLBACK
    )
    assert title.endswith("…")
    assert len(title) <= MAX_GENERATED_TITLE_LENGTH
    assert title == "Can you help me write an email to my lecturer asking for an…"


def test_a_cut_never_splits_a_placeholder():
    text = "Please help me with this question about my account " + "[REDACTED_BANK_ACCOUNT] and more words"
    title = title_from_prompt(text, FALLBACK)
    assert "[REDACTED_" not in title or "[REDACTED_BANK_ACCOUNT]" in title
    assert title.endswith("…")


@pytest.mark.parametrize("text", ["", "   \n\t "])
def test_empty_text_uses_the_fallback(text):
    assert title_from_prompt(text, FALLBACK) == FALLBACK


def test_one_very_long_word_is_cut():
    title = title_from_prompt("x" * 200, FALLBACK)
    assert title == "x" * (MAX_GENERATED_TITLE_LENGTH - 1) + "…"
