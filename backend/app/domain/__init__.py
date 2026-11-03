"""Domain layer: immutable entities and value objects. No I/O, no framework imports."""

from .chat_message import ChatMessage
from .classification import ClassificationResult, ContextFlag
from .enums import ChatRole, ContextCategory

__all__ = ["ChatMessage", "ChatRole", "ClassificationResult", "ContextCategory", "ContextFlag"]
