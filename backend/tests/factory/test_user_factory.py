import pytest

from app.domain import AccountStatus, UserRole
from app.exception import InvalidArgumentError
from app.factory.user_factory import MAX_DISPLAY_NAME_LENGTH, build_user


def test_builds_student_with_defaults():
    user = build_user("uid-1", " Thabo@Example.com ")
    assert user.email == "thabo@example.com"
    assert (user.role, user.status, user.email_verified) == (UserRole.STUDENT, AccountStatus.ACTIVE, False)
    assert user.display_name == ""


def test_trims_display_name():
    assert build_user("uid-1", "a@b.co", display_name="  Thabo  ").display_name == "Thabo"


@pytest.mark.parametrize(
    "kwargs, message",
    [
        ({"user_id": ""}, "user_id"),
        ({"email": "not-an-email"}, "email"),
        ({"role": "superuser"}, "role"),
        ({"status": "deleted"}, "status"),
        ({"email_verified": "yes"}, "email_verified"),
        ({"display_name": "x" * (MAX_DISPLAY_NAME_LENGTH + 1)}, "display_name"),
    ],
)
def test_rejects_invalid_input(kwargs, message):
    args = {"user_id": "uid-1", "email": "a@b.co", **kwargs}
    with pytest.raises(InvalidArgumentError, match=message):
        build_user(**args)
