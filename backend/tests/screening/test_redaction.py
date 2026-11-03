import pytest

from app.screening.redaction import redact


def test_redacts_spans():
    text = "My ID is 9203105800089, email t.m@gmail.com"
    spans = [(9, 22, "sa_id"), (30, 43, "email")]
    assert redact(text, spans) == "My ID is [REDACTED_SA_ID], email [REDACTED_EMAIL]"


def test_redact_merges_overlaps_and_keeps_clean_text():
    assert redact("abc 123456 xyz", [(4, 8, "a"), (6, 10, "b")]) == "abc [REDACTED_A] xyz"
    assert redact("nothing here", []) == "nothing here"


def test_redact_rejects_bad_span():
    with pytest.raises(ValueError):
        redact("short", [(2, 99, "x")])
