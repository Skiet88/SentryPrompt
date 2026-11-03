"""Domain layer: the entities in DOMAIN_MODEL.md, as immutable dataclasses.

Session, EmailVerificationToken and PasswordResetToken are managed by
Supabase Auth and therefore have no class here (DOMAIN_MODEL.md §6).
No I/O, no framework imports.
"""

from .admin_audit_log import AdminAuditLog
from .conversation import Conversation
from .detection_category import DetectionCategory
from .enums import (
    AccountStatus,
    AdminActionType,
    DetectionTier,
    DetectorSource,
    EvaluationOutcome,
    MessageRole,
    PromptStatus,
    SourceChannel,
    TestSetCategory,
    UserRole,
    Verdict,
)
from .evaluation_log_entry import EvaluationLogEntry
from .flagged_span import FlaggedSpan
from .message import Message
from .prompt import Prompt
from .rule_pattern import RulePattern
from .screening_result import ScreeningResult
from .test_set_entry import TestSetEntry
from .user import User

__all__ = [
    "AccountStatus", "AdminActionType", "AdminAuditLog", "Conversation", "DetectionCategory",
    "DetectionTier", "DetectorSource", "EvaluationLogEntry", "EvaluationOutcome", "FlaggedSpan",
    "Message", "MessageRole", "Prompt", "PromptStatus", "RulePattern", "ScreeningResult",
    "SourceChannel", "TestSetCategory", "TestSetEntry", "User", "UserRole", "Verdict",
]
