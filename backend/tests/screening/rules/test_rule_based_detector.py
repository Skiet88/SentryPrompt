import asyncio

import pytest

from app.domain import DetectorSource, Verdict


def found(detector, text: str) -> list[tuple[str, str]]:
    return [(s.category, text[s.start : s.end]) for s in detector.detect_now(text).spans]


@pytest.mark.parametrize(
    "text, expected",
    [
        ("My ID is 9203105800089, is it valid?", [("SA_ID", "9203105800089")]),
        ("My student number is 8402215", [("STUDENT_NUMBER", "8402215")]),
        ("Call me on 082 555 1234", [("PHONE", "082 555 1234")]),
        ("Call me on +27 82 555 1234", [("PHONE", "+27 82 555 1234")]),
        ("Email t.mokoena84@gmail.com please", [("EMAIL", "t.mokoena84@gmail.com")]),
        ("My card is 4539 1488 0343 6467", [("BANK_CARD", "4539 1488 0343 6467")]),
        (
            "loan account number is 62881193021",
            [("BANK_ACCOUNT", "account number is 62881193021")],
        ),
        ("I live at 14 Rosebank Ave.", [("ADDRESS", "14 Rosebank Ave")]),
    ],
)
def test_detects_each_rule_category(detector, text, expected):
    assert found(detector, text) == expected


def test_sa_id_is_not_also_reported_as_card(detector):
    assert [c for c, _ in found(detector, "ID 9203105800089")] == ["SA_ID"]


def test_number_failing_luhn_is_not_a_card(detector):
    assert found(detector, "Order ref 4111 1111 1111 1112") == []


@pytest.mark.parametrize(
    "text",
    [
        "Explain recursion with a worked example.",
        "How does compound interest work for student loans generally?",
        "My banking app shows a reference number of TX-88213-ZA",
        "Write a regex that matches South African ID numbers, format only.",
    ],
)
def test_clean_prompts_are_not_flagged(detector, text):
    result = detector.detect_now(text)
    assert result.spans == () and result.verdict is Verdict.NO_FLAG


def test_multiple_categories_returned_in_text_order(detector):
    text = "Email a@b.co or call 082 555 1234"
    assert [c for c, _ in found(detector, text)] == ["EMAIL", "PHONE"]


def test_async_detect_matches_sync_and_marks_source(detector):
    text = "My ID is 9203105800089"
    result = asyncio.run(detector.detect(text))
    assert result == detector.detect_now(text)
    assert result.verdict is Verdict.FLAG
    assert all(s.detector_source is DetectorSource.RULE for s in result.spans)
    assert detector.source is DetectorSource.RULE
