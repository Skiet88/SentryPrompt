import dataclasses

import pytest

from app.domain import AdminActionType
from app.exception import InvalidArgumentError
from app.factory.admin_audit_log_factory import build_admin_audit_log


def test_builds_log():
    log = build_admin_audit_log("admin-1", "user-1", "suspend", details="Repeated misuse")
    assert log.action_type is AdminActionType.SUSPEND
    assert log.details == "Repeated misuse"


def test_admin_cannot_act_on_own_account():
    with pytest.raises(InvalidArgumentError, match="own account"):
        build_admin_audit_log("admin-1", "admin-1", "suspend")


def test_rejects_unknown_action():
    with pytest.raises(InvalidArgumentError, match="action_type"):
        build_admin_audit_log("admin-1", "user-1", "delete_messages")


def test_has_no_field_referencing_conversation_content():
    """NFR-013: account-level only."""
    fields = {f.name for f in dataclasses.fields(build_admin_audit_log("a", "b", "reinstate"))}
    assert not fields & {"message_id", "conversation_id", "content"}
