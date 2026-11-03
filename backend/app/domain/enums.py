from enum import StrEnum


class ContextCategory(StrEnum):
    """Categories detected by the context-aware tier (SPECIFICATION.md §3)."""

    MEDICAL = "MEDICAL"
    INSTITUTIONAL = "INSTITUTIONAL"


class ChatRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
