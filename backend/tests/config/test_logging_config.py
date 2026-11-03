import logging

import pytest

from app.config.logging_config import REDACTED, SecretMaskingFilter, mask_secrets


@pytest.mark.parametrize(
    "secret",
    [
        "Bearer abc.def-ghi_123",
        "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0In0.c2lnbmF0dXJl",
        "gsk_abcdefghijklmnop1234",
        "AIzaSyA1234567890abcdefghijkl",
        "sb_secret_abcdefghijklmno",
    ],
)
def test_masks_secrets(secret):
    assert mask_secrets(f"value={secret} end") == f"value={REDACTED} end"


def test_leaves_normal_text_alone():
    assert mask_secrets("Screening completed in 120 ms") == "Screening completed in 120 ms"


def test_filter_masks_formatted_arguments():
    record = logging.LogRecord("t", logging.INFO, __file__, 1, "auth header %s", ("Bearer abc123",), None)
    SecretMaskingFilter().filter(record)
    assert record.getMessage() == f"auth header {REDACTED}"
