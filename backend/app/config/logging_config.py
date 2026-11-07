"""Logging setup with a filter that masks secrets (SECURITY_RULES.md §3).

The filter is a safety net: code must still never log passwords, tokens,
keys, prompt text or message content in the first place.
"""

from __future__ import annotations

import logging
import re

_SECRET_PATTERNS = [
    re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]+"),  # Authorization headers
    re.compile(r"\beyJ[A-Za-z0-9_-]{5,}\.[A-Za-z0-9_-]{5,}\.[A-Za-z0-9_-]*"),  # JWTs
    re.compile(r"\bgsk_[A-Za-z0-9]{10,}"),  # Groq API keys
    re.compile(r"\bAIza[0-9A-Za-z_-]{20,}"),  # Google API keys
    re.compile(r"\bsb_secret_[A-Za-z0-9_-]{10,}"),  # Supabase secret keys
]
REDACTED = "[REDACTED_SECRET]"


def mask_secrets(text: str) -> str:
    for pattern in _SECRET_PATTERNS:
        text = pattern.sub(REDACTED, text)
    return text


class SecretMaskingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = mask_secrets(record.getMessage())
        record.args = None
        return True


def configure_logging(level: str = "INFO") -> None:
    root = logging.getLogger()
    if not root.handlers:
        logging.basicConfig(format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    root.setLevel(level)
    for handler in root.handlers:
        if not any(isinstance(f, SecretMaskingFilter) for f in handler.filters):
            handler.addFilter(SecretMaskingFilter())
