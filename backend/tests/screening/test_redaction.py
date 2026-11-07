import pytest

from app.screening.redaction import redact, redact_with_map


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


# ---- position map (FR-005: highlight the original text) ----------------------

ORIGINAL = "My ID is 9203105800089 and I take sertraline"
ID_SPAN = (9, 22, "SA_ID")


def test_redacted_text_and_map():
    redacted = redact_with_map(ORIGINAL, [ID_SPAN])
    assert redacted.text == "My ID is [REDACTED_SA_ID] and I take sertraline"
    assert redacted.original_length == len(ORIGINAL)


def test_maps_span_after_placeholder_back_to_original():
    redacted = redact_with_map(ORIGINAL, [ID_SPAN])
    start = redacted.text.index("sertraline")
    original = redacted.to_original(start, start + len("sertraline"))
    assert ORIGINAL[original[0] : original[1]] == "sertraline"


def test_maps_span_before_placeholder_unchanged():
    redacted = redact_with_map(ORIGINAL, [ID_SPAN])
    assert redacted.to_original(0, 5) == (0, 5)


def test_span_touching_placeholder_covers_hidden_value():
    redacted = redact_with_map(ORIGINAL, [ID_SPAN])
    start = redacted.text.index("ID is [REDACTED")
    end = redacted.text.index("]") + 1
    original = redacted.to_original(start, end)
    assert ORIGINAL[original[0] : original[1]] == "ID is 9203105800089"


def test_map_with_no_redactions_is_identity():
    redacted = redact_with_map("plain text", [])
    assert redacted.text == "plain text" and redacted.to_original(2, 6) == (2, 6)


def test_map_rejects_out_of_range_span():
    with pytest.raises(ValueError):
        redact_with_map("abc", []).to_original(1, 9)
