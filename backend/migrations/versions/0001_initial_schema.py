"""Initial schema: application and evaluation tables, RLS, profile trigger.

Implements ERD.md §1A. Runs on Supabase, where the auth schema (auth.users)
and the anon/authenticated roles already exist.

Security (SECURITY_RULES.md §3):
- Row Level Security is enabled on every table with no policies, and table
  access is revoked from Supabase's public roles, so the browser's
  publishable key can never read or write this data. Only the backend
  (connecting as the database owner) can.
- The evaluation schema has no column that can hold prompt text and no link
  to any user (NFR-009).
- The evaluation log and the admin audit log are append-only at the
  database level: UPDATE, DELETE and TRUNCATE are rejected (FR-022, NFR-009).
  This protects against application bugs and SQL injection; it does not stop
  someone with owner access to the database, who could drop the triggers.
- Deleting an account in Supabase Auth deletes the profile, conversations
  and messages through ON DELETE CASCADE (NFR-014); the audit log has no
  foreign keys, so it is kept.

Revision ID: 0001
Revises:
Create Date: 2026-11-04
"""

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

APP_TABLES = (
    "public.profiles",
    "public.conversations",
    "public.messages",
    "public.admin_audit_log",
    # Alembic's own bookkeeping table also lives in the exposed public schema.
    "public.alembic_version",
)
EVALUATION_TABLES = (
    "evaluation.screening_results",
    "evaluation.flagged_spans",
    "evaluation.evaluation_log_entries",
)

UPGRADE = r"""
DO $$
BEGIN
    IF to_regclass('auth.users') IS NULL THEN
        RAISE EXCEPTION 'auth.users not found: run this migration against the Supabase database';
    END IF;
END
$$;

CREATE SCHEMA IF NOT EXISTS evaluation;

-- ---- public: application data ----------------------------------------------

CREATE TABLE public.profiles (
    id           uuid PRIMARY KEY REFERENCES auth.users (id) ON DELETE CASCADE,
    display_name text NOT NULL DEFAULT '' CHECK (char_length(display_name) <= 100),
    role         text NOT NULL DEFAULT 'student' CHECK (role IN ('student', 'admin')),
    status       text NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'suspended')),
    created_at   timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE public.conversations (
    id         uuid PRIMARY KEY,
    user_id    uuid NOT NULL REFERENCES auth.users (id) ON DELETE CASCADE,
    title      text NOT NULL CHECK (char_length(title) BETWEEN 1 AND 200),
    channel    text NOT NULL CHECK (channel IN ('webapp', 'extension')),
    created_at timestamptz NOT NULL,
    updated_at timestamptz NOT NULL,
    CHECK (updated_at >= created_at)
);
CREATE INDEX conversations_user_id_idx ON public.conversations (user_id);

CREATE TABLE public.messages (
    id                 uuid PRIMARY KEY,
    conversation_id    uuid NOT NULL REFERENCES public.conversations (id) ON DELETE CASCADE,
    role               text NOT NULL CHECK (role IN ('user', 'assistant')),
    -- Encrypted by the backend before it is written (NFR-011).
    content_ciphertext bytea NOT NULL,
    created_at         timestamptz NOT NULL
);
CREATE INDEX messages_conversation_id_idx ON public.messages (conversation_id);

CREATE TABLE public.admin_audit_log (
    id             uuid PRIMARY KEY,
    -- No foreign keys: the audit trail survives account deletion (FR-022).
    admin_user_id  uuid NOT NULL,
    target_user_id uuid NOT NULL,
    action_type    text NOT NULL CHECK (action_type IN ('suspend', 'reinstate')),
    "timestamp"    timestamptz NOT NULL,
    details        text NOT NULL DEFAULT '',
    CHECK (admin_user_id <> target_user_id)
);

-- ---- evaluation: content-free research data (NFR-009) ------------------------

CREATE TABLE evaluation.screening_results (
    id                    uuid PRIMARY KEY,
    -- The prompt itself is never stored; this ID only links records together.
    prompt_id             uuid NOT NULL,
    rule_based_verdict    text NOT NULL CHECK (rule_based_verdict IN ('FLAG', 'NO_FLAG')),
    context_aware_verdict text NOT NULL CHECK (context_aware_verdict IN ('FLAG', 'NO_FLAG', 'UNAVAILABLE')),
    aggregated_verdict    text NOT NULL CHECK (aggregated_verdict IN ('FLAG', 'NO_FLAG', 'UNAVAILABLE')),
    decided_at            timestamptz NOT NULL
);

CREATE TABLE evaluation.flagged_spans (
    id              uuid PRIMARY KEY,
    result_id       uuid NOT NULL REFERENCES evaluation.screening_results (id) ON DELETE CASCADE,
    -- Positions only, never the flagged text.
    start_index     integer NOT NULL CHECK (start_index >= 0),
    end_index       integer NOT NULL,
    detector_source text NOT NULL CHECK (detector_source IN ('rule', 'context')),
    -- Category IDs come from backend/app/screening/rules/detection_categories.json
    -- (the single source of truth for categories), so there is no foreign key.
    category_id     uuid NOT NULL,
    CHECK (end_index > start_index)
);
CREATE INDEX flagged_spans_result_id_idx ON evaluation.flagged_spans (result_id);

CREATE TABLE evaluation.evaluation_log_entries (
    id               uuid PRIMARY KEY,
    result_id        uuid NOT NULL REFERENCES evaluation.screening_results (id),
    category_id      uuid,
    outcome          text NOT NULL CHECK (outcome IN ('flagged', 'unflagged', 'override', 'unavailable')),
    timestamp_bucket text NOT NULL CHECK (timestamp_bucket ~ '^\d{4}-\d{2}-\d{2}T\d{2}:00Z$'),
    CHECK ((outcome IN ('unflagged', 'unavailable')) = (category_id IS NULL))
);
CREATE INDEX evaluation_log_entries_result_id_idx ON evaluation.evaluation_log_entries (result_id);

-- ---- append-only tables ------------------------------------------------------

CREATE FUNCTION evaluation.reject_modification() RETURNS trigger
LANGUAGE plpgsql SET search_path = '' AS $$
BEGIN
    RAISE EXCEPTION '% is append-only', TG_TABLE_NAME;
END
$$;

CREATE TRIGGER evaluation_log_entries_append_only
    BEFORE UPDATE OR DELETE ON evaluation.evaluation_log_entries
    FOR EACH ROW EXECUTE FUNCTION evaluation.reject_modification();

CREATE TRIGGER admin_audit_log_append_only
    BEFORE UPDATE OR DELETE ON public.admin_audit_log
    FOR EACH ROW EXECUTE FUNCTION evaluation.reject_modification();

-- TRUNCATE would bypass the row-level triggers, so block it as well.
CREATE TRIGGER evaluation_log_entries_no_truncate
    BEFORE TRUNCATE ON evaluation.evaluation_log_entries
    FOR EACH STATEMENT EXECUTE FUNCTION evaluation.reject_modification();

CREATE TRIGGER admin_audit_log_no_truncate
    BEFORE TRUNCATE ON public.admin_audit_log
    FOR EACH STATEMENT EXECUTE FUNCTION evaluation.reject_modification();

-- ---- a profile for every new account ----------------------------------------

CREATE FUNCTION public.handle_new_user() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path = '' AS $$
BEGIN
    INSERT INTO public.profiles (id) VALUES (NEW.id);
    RETURN NEW;
END
$$;
REVOKE ALL ON FUNCTION public.handle_new_user() FROM PUBLIC;

CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();
"""

DOWNGRADE = """
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
DROP FUNCTION IF EXISTS public.handle_new_user();
DROP TABLE IF EXISTS evaluation.evaluation_log_entries;
DROP TABLE IF EXISTS evaluation.flagged_spans;
DROP TABLE IF EXISTS evaluation.screening_results;
DROP FUNCTION IF EXISTS evaluation.reject_modification() CASCADE;
DROP TABLE IF EXISTS public.admin_audit_log;
DROP TABLE IF EXISTS public.messages;
DROP TABLE IF EXISTS public.conversations;
DROP TABLE IF EXISTS public.profiles;
DROP SCHEMA IF EXISTS evaluation;
"""


def _lock_down() -> str:
    """Enable RLS everywhere and revoke access from Supabase's public roles."""
    statements = [
        f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;" for table in APP_TABLES + EVALUATION_TABLES
    ]
    tables = ", ".join(APP_TABLES + EVALUATION_TABLES)
    # Safe: table and role names are constants defined in this file, never input.
    statements.append(
        f"""
DO $$
DECLARE r text;
BEGIN
    FOREACH r IN ARRAY ARRAY['anon', 'authenticated'] LOOP
        IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = r) THEN
            EXECUTE format('REVOKE ALL ON {tables} FROM %I', r);
            EXECUTE format('REVOKE ALL ON SCHEMA evaluation FROM %I', r);
        END IF;
    END LOOP;
END
$$;"""
    )
    statements.append("REVOKE ALL ON SCHEMA evaluation FROM PUBLIC;")
    return "\n".join(statements)


def _execute_script(sql: str) -> None:
    """Run a fixed, multi-statement SQL script directly on the driver.

    The scripts in this file are constants with no user input. Passing them to
    the driver as-is avoids SQLAlchemy treating text such as ':00Z' as a bind
    parameter, and allows several statements in one call.
    """
    driver_connection = op.get_bind().connection.dbapi_connection
    if driver_connection is None:
        raise RuntimeError("No database connection available for the migration")
    driver_connection.run_async(lambda connection: connection.execute(sql))


def upgrade() -> None:
    _execute_script(UPGRADE)
    _execute_script(_lock_down())


def downgrade() -> None:
    _execute_script(DOWNGRADE)
