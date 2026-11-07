import asyncio

import pytest

from app.exception import AuthenticationError, ForbiddenError, InvalidArgumentError
from app.service.auth.auth_service import MAX_TOKEN_LENGTH
from tests.conftest import ADMIN_ID, STUDENT_ID, SUSPENDED_ID, make_auth_service


def run(coroutine):
    return asyncio.run(coroutine)


def test_authenticate_returns_user_with_role_from_profile_not_token():
    service, _, _ = make_auth_service()
    student = run(service.authenticate("student-token"))
    admin = run(service.authenticate("admin-token"))
    assert (student.user_id, student.role.value) == (STUDENT_ID, "student")
    assert (admin.user_id, admin.role.value) == (ADMIN_ID, "admin")


@pytest.mark.parametrize("token", ["", "   ", "has space", "a" * (MAX_TOKEN_LENGTH + 1)])
def test_malformed_tokens_rejected_without_contacting_supabase(token):
    service, provider, _ = make_auth_service()
    with pytest.raises(AuthenticationError):
        run(service.authenticate(token))
    assert provider.received_tokens == []


def test_unknown_token_rejected():
    service, _, _ = make_auth_service()
    with pytest.raises(AuthenticationError):
        run(service.authenticate("forged-token"))


@pytest.mark.parametrize(
    "token, code",
    [("unverified-token", "email_not_verified"), ("suspended-token", "account_suspended")],
)
def test_require_active(token, code):
    service, _, _ = make_auth_service()
    user = run(service.authenticate(token))
    with pytest.raises(ForbiddenError) as caught:
        service.require_active(user)
    assert caught.value.error_code == code


def test_require_admin():
    service, _, _ = make_auth_service()
    assert service.require_admin(run(service.authenticate("admin-token"))).is_admin
    with pytest.raises(ForbiddenError) as caught:
        service.require_admin(run(service.authenticate("student-token")))
    assert caught.value.error_code == "admin_only"


def test_update_display_name_validates_and_persists():
    service, _, _ = make_auth_service()
    user = run(service.authenticate("student-token"))
    assert run(service.update_display_name(user, "  Thabo  ")).display_name == "Thabo"
    assert run(service.authenticate("student-token")).display_name == "Thabo"
    with pytest.raises(InvalidArgumentError):
        run(service.update_display_name(user, "x" * 101))


def test_suspended_user_cannot_edit_but_can_delete():
    service, provider, _ = make_auth_service()
    suspended = run(service.authenticate("suspended-token"))
    with pytest.raises(ForbiddenError):
        run(service.update_display_name(suspended, "New name"))
    run(service.delete_account(suspended))
    assert provider.deleted == [SUSPENDED_ID]
