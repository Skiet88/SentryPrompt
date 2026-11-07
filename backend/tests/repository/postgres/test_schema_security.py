"""The database schema enforces the security rules, not just the code."""

import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, IntegrityError

from tests.repository.postgres.conftest import run, run_alembic

EXPOSED_SCHEMAS = ("public", "evaluation")


async def scalar_rows(engine, sql: str, **params):
    async with engine.connect() as connection:
        return (await connection.execute(text(sql), params)).all()


async def execute(engine, sql: str, **params):
    async with engine.begin() as connection:
        await connection.execute(text(sql), params)


def test_every_table_has_row_level_security(engine):
    """SECURITY_RULES.md §3: RLS on every table, checked automatically."""
    rows = run(
        scalar_rows(
            engine,
            """SELECT n.nspname || '.' || c.relname, c.relrowsecurity
               FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
               WHERE c.relkind = 'r' AND n.nspname = ANY(:schemas)""",
            schemas=list(EXPOSED_SCHEMAS),
        )
    )
    assert len(rows) >= 8
    without_rls = [name for name, rls in rows if not rls]
    assert without_rls == []


def test_public_roles_have_no_table_access(engine):
    rows = run(
        scalar_rows(
            engine,
            """SELECT grantee, table_schema || '.' || table_name, privilege_type
               FROM information_schema.role_table_grants
               WHERE grantee IN ('anon', 'authenticated') AND table_schema = ANY(:schemas)""",
            schemas=list(EXPOSED_SCHEMAS),
        )
    )
    assert rows == []


def test_evaluation_tables_cannot_hold_prompt_text(engine):
    """NFR-009: no text column except fixed, checked codes."""
    rows = run(
        scalar_rows(
            engine,
            """SELECT table_name || '.' || column_name
               FROM information_schema.columns
               WHERE table_schema = 'evaluation'
                 AND data_type IN ('text', 'character varying', 'bytea', 'json', 'jsonb')
               ORDER BY 1""",
        )
    )
    assert [r[0] for r in rows] == [
        "evaluation_log_entries.outcome",
        "evaluation_log_entries.timestamp_bucket",
        "flagged_spans.detector_source",
        "screening_results.aggregated_verdict",
        "screening_results.context_aware_verdict",
        "screening_results.rule_based_verdict",
    ]


def test_coded_text_columns_reject_free_text(engine):
    with pytest.raises(IntegrityError):
        run(
            execute(
                engine,
                """INSERT INTO evaluation.screening_results
                   VALUES (:id, :pid, 'My ID is 9203105800089', 'NO_FLAG', 'NO_FLAG', now())""",
                id=uuid.uuid4(),
                pid=uuid.uuid4(),
            )
        )


def _insert_result_and_log(engine) -> None:
    result_id = uuid.uuid4()
    run(
        execute(
            engine,
            "INSERT INTO evaluation.screening_results "
            "VALUES (:id, :pid, 'NO_FLAG', 'NO_FLAG', 'NO_FLAG', now())",
            id=result_id,
            pid=uuid.uuid4(),
        )
    )
    run(
        execute(
            engine,
            "INSERT INTO evaluation.evaluation_log_entries "
            "VALUES (:log, :id, NULL, 'unflagged', '2026-11-04T09:00Z')",
            log=uuid.uuid4(),
            id=result_id,
        )
    )


@pytest.mark.parametrize(
    "statement",
    [
        "UPDATE evaluation.evaluation_log_entries SET outcome = 'flagged'",
        "DELETE FROM evaluation.evaluation_log_entries",
        "TRUNCATE evaluation.evaluation_log_entries",
    ],
)
def test_evaluation_log_is_append_only(engine, statement):
    _insert_result_and_log(engine)
    with pytest.raises(DBAPIError, match="append-only"):
        run(execute(engine, statement))


@pytest.mark.parametrize(
    "statement",
    [
        "UPDATE public.admin_audit_log SET details = 'changed'",
        "DELETE FROM public.admin_audit_log",
        "TRUNCATE public.admin_audit_log",
    ],
)
def test_admin_audit_log_is_append_only(engine, statement):
    run(
        execute(
            engine,
            "INSERT INTO public.admin_audit_log VALUES (:id, :a, :t, 'suspend', now(), 'x')",
            id=uuid.uuid4(),
            a=uuid.uuid4(),
            t=uuid.uuid4(),
        )
    )
    with pytest.raises(DBAPIError, match="append-only"):
        run(execute(engine, statement))


def test_new_account_gets_a_student_profile(engine):
    user_id = uuid.uuid4()
    run(execute(engine, "INSERT INTO auth.users (id, email) VALUES (:id, 'a@b.co')", id=user_id))
    rows = run(
        scalar_rows(
            engine, "SELECT role, status, display_name FROM public.profiles WHERE id = :id", id=user_id
        )
    )
    assert rows == [("student", "active", "")]


def test_account_deletion_cascades_but_keeps_audit_log(engine):
    """NFR-014 (erasure) with FR-022 precedence (audit log kept)."""
    user_id, admin_id, conversation_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    run(execute(engine, "INSERT INTO auth.users (id, email) VALUES (:id, 'student@b.co')", id=user_id))
    run(
        execute(
            engine,
            "INSERT INTO public.conversations (id, user_id, channel, created_at, updated_at) "
            "VALUES (:c, :u, 'webapp', now(), now())",
            c=conversation_id,
            u=user_id,
        )
    )
    run(
        execute(
            engine,
            "INSERT INTO public.messages VALUES (:m, :c, 'user', :content, now())",
            m=uuid.uuid4(),
            c=conversation_id,
            content=b"ciphertext",
        )
    )
    run(
        execute(
            engine,
            "INSERT INTO public.admin_audit_log VALUES (:id, :a, :u, 'suspend', now(), '')",
            id=uuid.uuid4(),
            a=admin_id,
            u=user_id,
        )
    )

    run(execute(engine, "DELETE FROM auth.users WHERE id = :id", id=user_id))

    for table in ("public.profiles", "public.conversations", "public.messages"):
        # Safe: table names come from the fixed tuple above.
        assert run(scalar_rows(engine, f"SELECT count(*) FROM {table}")) == [(0,)], table  # noqa: S608
    assert run(scalar_rows(engine, "SELECT count(*) FROM public.admin_audit_log")) == [(1,)]


def test_admin_cannot_target_own_account(engine):
    same = uuid.uuid4()
    with pytest.raises(IntegrityError):
        run(
            execute(
                engine,
                "INSERT INTO public.admin_audit_log VALUES (:id, :a, :a, 'suspend', now(), '')",
                id=uuid.uuid4(),
                a=same,
            )
        )


def test_migration_downgrades_and_upgrades_cleanly(database_url):
    run_alembic(database_url, "downgrade", "base")
    run_alembic(database_url, "upgrade", "head")
