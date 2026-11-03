"""Allowed values for the String-typed attributes in DOMAIN_MODEL.md."""

from enum import StrEnum


class SourceChannel(StrEnum):
    """Prompt.sourceChannel and Conversation.channel."""

    WEBAPP = "webapp"
    EXTENSION = "extension"


class PromptStatus(StrEnum):
    """Prompt.status: the states in STATE_DIAGRAMS.md §1."""

    DRAFT = "draft"
    VALIDATING = "validating"
    REJECTED = "rejected"
    SCREENING = "screening"
    CLEAN = "clean"
    FLAGGED = "flagged"
    EDIT_REQUESTED = "edit_requested"
    OVERRIDDEN = "overridden"
    CANCELLED = "cancelled"
    FORWARDED = "forwarded"
    RESPONSE_RECEIVED = "response_received"
    DISCARDED = "discarded"


class Verdict(StrEnum):
    """ScreeningResult verdicts (SERVICE_LAYER.md §3).

    UNAVAILABLE means the context-aware check could not complete (provider
    error, timeout, or an unreadable reply). Screening fails closed: an
    unavailable check is never treated as clean (NFR-015)."""

    FLAG = "FLAG"
    NO_FLAG = "NO_FLAG"
    UNAVAILABLE = "UNAVAILABLE"


class DetectorSource(StrEnum):
    """FlaggedSpan.detectorSource."""

    RULE = "rule"
    CONTEXT = "context"


class DetectionTier(StrEnum):
    """DetectionCategory.tier (SPECIFICATION.md §3)."""

    RULE_BASED = "rule-based"
    CONTEXT_AWARE = "context-aware"


class EvaluationOutcome(StrEnum):
    """EvaluationLogEntry.outcome."""

    FLAGGED = "flagged"
    UNFLAGGED = "unflagged"
    OVERRIDE = "override"


class TestSetCategory(StrEnum):
    """TestSetEntry.groundTruthCategory (TEST_SET.csv)."""

    __test__ = False  # not a pytest test class

    ID_NUMBER = "ID_NUMBER"
    FINANCIAL = "FINANCIAL"
    CONTACT_LOCATION = "CONTACT_LOCATION"
    MEDICAL = "MEDICAL"
    INSTITUTIONAL = "INSTITUTIONAL"
    CLEAN = "CLEAN"


class UserRole(StrEnum):
    STUDENT = "student"
    ADMIN = "admin"


class AccountStatus(StrEnum):
    ACTIVE = "active"
    SUSPENDED = "suspended"


class MessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"


class AdminActionType(StrEnum):
    SUSPEND = "suspend"
    REINSTATE = "reinstate"
