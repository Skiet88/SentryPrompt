import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.domain import AccountStatus, AdminActionType, UserRole
from app.factory.admin_audit_log_factory import build_admin_audit_log
from app.repository.postgres.user_repository import PostgresAdminAuditLogRepository, PostgresUserRepository
from tests.repository.postgres.conftest import run


async def add_auth_user(engine, user_id: uuid.UUID, email: str) -> None:
    async with engine.begin() as connection:
        await connection.execute(
            text("INSERT INTO auth.users (id, email) VALUES (:id, :e)"), {"id": user_id, "e": email}
        )


def test_profile_created_by_sign_up_trigger_is_returned(engine):
    user_id = uuid.uuid4()
    run(add_auth_user(engine, user_id, "a@b.co"))
    user = run(
        PostgresUserRepository(engine).find_or_create(str(user_id), email="a@b.co", email_verified=True)
    )
    assert (user.user_id, user.role, user.status, user.email_verified) == (
        str(user_id),
        UserRole.STUDENT,
        AccountStatus.ACTIVE,
        True,
    )


def test_missing_profile_is_created_with_safe_defaults(engine):
    user_id = uuid.uuid4()
    run(add_auth_user(engine, user_id, "a@b.co"))

    async def remove_profile():
        async with engine.begin() as connection:
            await connection.execute(text("DELETE FROM public.profiles WHERE id = :id"), {"id": user_id})

    run(remove_profile())
    user = run(
        PostgresUserRepository(engine).find_or_create(str(user_id), email="a@b.co", email_verified=False)
    )
    assert (user.role, user.status) == (UserRole.STUDENT, AccountStatus.ACTIVE)


def test_role_and_status_come_from_the_database(engine):
    user_id = uuid.uuid4()
    run(add_auth_user(engine, user_id, "admin@b.co"))

    async def promote_and_suspend():
        async with engine.begin() as connection:
            await connection.execute(
                text("UPDATE public.profiles SET role = 'admin', status = 'suspended' WHERE id = :id"),
                {"id": user_id},
            )

    run(promote_and_suspend())
    user = run(
        PostgresUserRepository(engine).find_or_create(str(user_id), email="admin@b.co", email_verified=True)
    )
    assert (user.role, user.status) == (UserRole.ADMIN, AccountStatus.SUSPENDED)


def test_update_display_name(engine):
    user_id = uuid.uuid4()
    run(add_auth_user(engine, user_id, "a@b.co"))
    repo = PostgresUserRepository(engine)
    run(repo.update_display_name(str(user_id), "Thabo"))
    assert run(repo.find_or_create(str(user_id), email="a@b.co", email_verified=True)).display_name == "Thabo"


# --- Admin: status changes and the audit log (FR-021, FR-022) ---


def _entry(admin_id, target_id, action=AdminActionType.SUSPEND, **kwargs):
    return build_admin_audit_log(str(admin_id), str(target_id), action, **kwargs)


def test_find_profiles_returns_only_existing_profiles(engine):
    first, second = uuid.uuid4(), uuid.uuid4()
    run(add_auth_user(engine, first, "a@b.co"))
    run(add_auth_user(engine, second, "c@d.co"))
    found = run(PostgresUserRepository(engine).find_profiles([str(first), str(second), str(uuid.uuid4())]))
    assert set(found) == {str(first), str(second)}
    assert found[str(first)].role is UserRole.STUDENT and found[str(first)].status is AccountStatus.ACTIVE
    assert run(PostgresUserRepository(engine).find_profiles([])) == {}


def test_change_status_writes_the_audit_entry_in_the_same_transaction(engine):
    admin_id, target_id = uuid.uuid4(), uuid.uuid4()
    run(add_auth_user(engine, target_id, "a@b.co"))
    repo, audit = PostgresUserRepository(engine), PostgresAdminAuditLogRepository(engine)
    entry = _entry(admin_id, target_id, details="Misuse")

    assert run(repo.change_status(str(target_id), AccountStatus.SUSPENDED, entry)) is True
    assert run(repo.find_profiles([str(target_id)]))[str(target_id)].status is AccountStatus.SUSPENDED
    assert run(audit.list_recent(10)) == [entry]


def test_failed_audit_insert_rolls_back_the_status_change(engine):
    admin_id, target_id = uuid.uuid4(), uuid.uuid4()
    run(add_auth_user(engine, target_id, "a@b.co"))
    repo = PostgresUserRepository(engine)
    entry = _entry(admin_id, target_id)
    run(repo.change_status(str(target_id), AccountStatus.SUSPENDED, entry))

    # Same log ID again: the audit insert fails, so the reinstatement must not stick.
    duplicate = _entry(admin_id, target_id, AdminActionType.REINSTATE, log_id=entry.log_id)
    with pytest.raises(IntegrityError):
        run(repo.change_status(str(target_id), AccountStatus.ACTIVE, duplicate))
    assert run(repo.find_profiles([str(target_id)]))[str(target_id)].status is AccountStatus.SUSPENDED
    assert len(run(PostgresAdminAuditLogRepository(engine).list_recent(10))) == 1


def test_change_status_of_unknown_account_writes_nothing(engine):
    repo = PostgresUserRepository(engine)
    entry = _entry(uuid.uuid4(), uuid.uuid4())
    assert run(repo.change_status(entry.target_user_id, AccountStatus.SUSPENDED, entry)) is False
    assert run(PostgresAdminAuditLogRepository(engine).list_recent(10)) == []


def test_audit_log_is_newest_first_and_paginated(engine):
    admin_id, target_id = uuid.uuid4(), uuid.uuid4()
    run(add_auth_user(engine, target_id, "a@b.co"))
    repo = PostgresUserRepository(engine)
    base = datetime(2026, 11, 1, tzinfo=UTC)
    entries = [
        _entry(admin_id, target_id, action, timestamp=base + timedelta(minutes=i))
        for i, action in enumerate(
            [AdminActionType.SUSPEND, AdminActionType.REINSTATE, AdminActionType.SUSPEND]
        )
    ]
    for entry, status in zip(
        entries, [AccountStatus.SUSPENDED, AccountStatus.ACTIVE, AccountStatus.SUSPENDED], strict=True
    ):
        run(repo.change_status(str(target_id), status, entry))
    audit = PostgresAdminAuditLogRepository(engine)
    assert run(audit.list_recent(10)) == list(reversed(entries))
    assert run(audit.list_recent(1, offset=1)) == [entries[1]]


def test_audit_entries_survive_account_deletion(engine):
    admin_id, target_id = uuid.uuid4(), uuid.uuid4()
    run(add_auth_user(engine, target_id, "a@b.co"))
    entry = _entry(admin_id, target_id)
    run(PostgresUserRepository(engine).change_status(str(target_id), AccountStatus.SUSPENDED, entry))

    async def delete_account():
        async with engine.begin() as connection:
            await connection.execute(text("DELETE FROM auth.users WHERE id = :id"), {"id": target_id})

    run(delete_account())
    assert run(PostgresAdminAuditLogRepository(engine).list_recent(10)) == [entry]
