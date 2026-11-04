import uuid

from sqlalchemy import text

from app.domain import AccountStatus, UserRole
from app.repository.postgres.user_repository import PostgresUserRepository
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
