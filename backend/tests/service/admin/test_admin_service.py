"""AdminService (FR-021, FR-022, NFR-013)."""

import ast
import asyncio
import inspect
from pathlib import Path

import pytest

from app.domain import AccountStatus, AdminActionType
from app.exception import ForbiddenError, InvalidArgumentError, NotFoundError
from app.service.admin import admin_service as admin_service_module
from app.service.admin.admin_service import MAX_PAGE_SIZE, MAX_REASON_LENGTH, AdminService
from tests.conftest import ADMIN_ID, STUDENT_ID, SUSPENDED_ID, UNVERIFIED_ID, make_auth_service

OTHER_ADMIN_ID = "00000000-0000-4000-8000-000000000009"


def run(coroutine):
    return asyncio.run(coroutine)


def setup():
    auth, provider, users = make_auth_service()
    users.set_profile(STUDENT_ID)
    users.set_profile(UNVERIFIED_ID)
    service = AdminService(provider, users, users)
    admin = run(auth.authenticate("admin-token"))
    return service, provider, users, admin, auth


async def status_of(users, user_id):
    return (await users.find_profiles([user_id]))[user_id].status


def test_suspend_changes_status_writes_audit_entry_and_bans_login():
    service, provider, users, admin, _ = setup()
    result = run(service.suspend(admin, STUDENT_ID, "  Repeated misuse  "))

    assert result.status is AccountStatus.SUSPENDED
    assert result.login_block_updated is True
    assert result.audit_entry is not None
    assert result.audit_entry.action_type is AdminActionType.SUSPEND
    assert (result.audit_entry.admin_user_id, result.audit_entry.target_user_id) == (ADMIN_ID, STUDENT_ID)
    assert result.audit_entry.details == "Repeated misuse"
    assert run(status_of(users, STUDENT_ID)) is AccountStatus.SUSPENDED
    assert run(users.list_recent(10)) == [result.audit_entry]
    assert provider.banned == {STUDENT_ID: True}


def test_reinstate_unbans_and_audits():
    service, provider, users, admin, _ = setup()
    result = run(service.reinstate(admin, SUSPENDED_ID))
    assert result.status is AccountStatus.ACTIVE
    assert result.audit_entry is not None
    assert result.audit_entry.action_type is AdminActionType.REINSTATE
    assert run(status_of(users, SUSPENDED_ID)) is AccountStatus.ACTIVE
    assert provider.banned == {SUSPENDED_ID: False}


def test_suspended_user_is_blocked_by_backend_right_after_suspension():
    service, _, _, admin, auth = setup()
    run(service.suspend(admin, STUDENT_ID))
    student = run(auth.authenticate("student-token"))
    with pytest.raises(ForbiddenError) as caught:
        auth.require_active(student)
    assert caught.value.error_code == "account_suspended"


def test_repeating_an_action_retries_the_ban_without_a_second_audit_entry():
    service, provider, users, admin, _ = setup()
    provider.ban_unavailable = True
    first = run(service.suspend(admin, STUDENT_ID))
    assert first.login_block_updated is False
    assert first.audit_entry is not None
    # Still blocked by our backend even though Supabase was not updated.
    assert run(status_of(users, STUDENT_ID)) is AccountStatus.SUSPENDED

    provider.ban_unavailable = False
    second = run(service.suspend(admin, STUDENT_ID))
    assert second.login_block_updated is True
    assert second.audit_entry is None
    assert len(run(users.list_recent(10))) == 1
    assert provider.banned == {STUDENT_ID: True}


def test_admin_cannot_act_on_own_account():
    service, provider, users, admin, _ = setup()
    with pytest.raises(InvalidArgumentError):
        run(service.suspend(admin, ADMIN_ID))
    assert run(users.list_recent(10)) == []
    assert provider.banned == {}


def test_admin_cannot_suspend_another_admin():
    service, provider, users, admin, _ = setup()
    users.set_profile(OTHER_ADMIN_ID, role="admin")
    with pytest.raises(ForbiddenError) as caught:
        run(service.suspend(admin, OTHER_ADMIN_ID))
    assert caught.value.error_code == "target_is_admin"
    assert run(status_of(users, OTHER_ADMIN_ID)) is AccountStatus.ACTIVE
    assert provider.banned == {}


def test_unknown_account_is_not_found_and_nothing_is_written():
    service, provider, users, admin, _ = setup()
    with pytest.raises(NotFoundError):
        run(service.suspend(admin, "00000000-0000-4000-8000-0000000000ff"))
    assert run(users.list_recent(10)) == []
    assert provider.banned == {}


def test_overlong_reason_rejected():
    service, _, users, admin, _ = setup()
    with pytest.raises(InvalidArgumentError):
        run(service.suspend(admin, STUDENT_ID, "x" * (MAX_REASON_LENGTH + 1)))
    assert run(status_of(users, STUDENT_ID)) is AccountStatus.ACTIVE


@pytest.mark.parametrize("token", ["student-token", "unverified-token", "suspended-token"])
def test_non_admins_are_refused_by_every_method(token):
    service, provider, users, _, auth = setup()
    user = run(auth.authenticate(token))
    calls = [
        service.list_users(user, 1, 10),
        service.suspend(user, STUDENT_ID),
        service.reinstate(user, SUSPENDED_ID),
        service.audit_log(user, 10),
    ]
    for call in calls:
        with pytest.raises(ForbiddenError):
            run(call)
    assert provider.banned == {}
    assert run(users.list_recent(10)) == []


def test_suspended_admin_is_refused():
    service, _, users, _, auth = setup()
    users.set_profile(ADMIN_ID, role="admin", status="suspended")
    admin = run(auth.authenticate("admin-token"))
    with pytest.raises(ForbiddenError):
        run(service.list_users(admin, 1, 10))


def test_list_users_merges_accounts_with_profiles():
    service, _, _, admin, _ = setup()
    views = {v.user_id: v for v in run(service.list_users(admin, 1, 50))}
    assert views[ADMIN_ID].role.value == "admin"
    assert views[SUSPENDED_ID].status is AccountStatus.SUSPENDED
    assert views[UNVERIFIED_ID].email_verified is False
    assert views[STUDENT_ID].email == "student@uni.ac.za"


@pytest.mark.parametrize("page, per_page", [(0, 10), (1, 0), (1, MAX_PAGE_SIZE + 1)])
def test_list_users_rejects_bad_pagination(page, per_page):
    service, _, _, admin, _ = setup()
    with pytest.raises(InvalidArgumentError):
        run(service.list_users(admin, page, per_page))


@pytest.mark.parametrize("limit, offset", [(0, 0), (MAX_PAGE_SIZE + 1, 0), (10, -1)])
def test_audit_log_rejects_bad_pagination(limit, offset):
    service, _, _, admin, _ = setup()
    with pytest.raises(InvalidArgumentError):
        run(service.audit_log(admin, limit, offset))


def test_audit_log_newest_first():
    service, _, _, admin, _ = setup()
    first = run(service.suspend(admin, STUDENT_ID)).audit_entry
    second = run(service.reinstate(admin, STUDENT_ID)).audit_entry
    assert run(service.audit_log(admin, 10)) == [second, first]


def test_admin_package_has_no_access_to_conversations_or_messages():
    """NFR-013, checked structurally: the service is built only from an
    identity provider and account repositories, and no module in the admin
    package imports anything about conversations, messages or chat."""
    parameters = list(inspect.signature(AdminService.__init__).parameters)
    assert parameters == ["self", "identity", "users", "audit"]
    package_dir = Path(admin_service_module.__file__).parent
    for module in package_dir.glob("*.py"):
        for node in ast.walk(ast.parse(module.read_text())):
            names = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""] + [alias.name for alias in node.names]
            for name in names:
                lowered = name.lower()
                assert not any(word in lowered for word in ("conversation", "message", "chat", "cipher")), (
                    f"{module.name} imports {name}"
                )
