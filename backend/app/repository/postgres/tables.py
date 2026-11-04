"""Table definitions used by the PostgreSQL repositories.

The schema itself is created and changed only by Alembic migrations
(migrations/versions/); these definitions must match them, which the
integration tests check by reading and writing every table.
"""

from sqlalchemy import Column, DateTime, Integer, LargeBinary, MetaData, Table, Text, Uuid

metadata = MetaData()

# ---- evaluation schema (content-free research data, NFR-009) ---------------

screening_results = Table(
    "screening_results",
    metadata,
    Column("id", Uuid, primary_key=True),
    Column("prompt_id", Uuid, nullable=False),
    Column("rule_based_verdict", Text, nullable=False),
    Column("context_aware_verdict", Text, nullable=False),
    Column("aggregated_verdict", Text, nullable=False),
    Column("decided_at", DateTime(timezone=True), nullable=False),
    schema="evaluation",
)

flagged_spans = Table(
    "flagged_spans",
    metadata,
    Column("id", Uuid, primary_key=True),
    Column("result_id", Uuid, nullable=False),
    Column("start_index", Integer, nullable=False),
    Column("end_index", Integer, nullable=False),
    Column("detector_source", Text, nullable=False),
    Column("category_id", Uuid, nullable=False),
    schema="evaluation",
)

evaluation_log_entries = Table(
    "evaluation_log_entries",
    metadata,
    Column("id", Uuid, primary_key=True),
    Column("result_id", Uuid, nullable=False),
    Column("category_id", Uuid, nullable=True),
    Column("outcome", Text, nullable=False),
    Column("timestamp_bucket", Text, nullable=False),
    schema="evaluation",
)

# ---- public schema (application data) -----------------------------------------

profiles = Table(
    "profiles",
    metadata,
    Column("id", Uuid, primary_key=True),
    Column("display_name", Text, nullable=False),
    Column("role", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    schema="public",
)

conversations = Table(
    "conversations",
    metadata,
    Column("id", Uuid, primary_key=True),
    Column("user_id", Uuid, nullable=False),
    # Encrypted (TitleCipher); NULL means the default title.
    Column("title_ciphertext", LargeBinary, nullable=True),
    Column("channel", Text, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    schema="public",
)

messages = Table(
    "messages",
    metadata,
    Column("id", Uuid, primary_key=True),
    Column("conversation_id", Uuid, nullable=False),
    Column("role", Text, nullable=False),
    Column("content_ciphertext", LargeBinary, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    schema="public",
)

admin_audit_log = Table(
    "admin_audit_log",
    metadata,
    Column("id", Uuid, primary_key=True),
    Column("admin_user_id", Uuid, nullable=False),
    Column("target_user_id", Uuid, nullable=False),
    Column("action_type", Text, nullable=False),
    Column("timestamp", DateTime(timezone=True), nullable=False),
    Column("details", Text, nullable=False),
    schema="public",
)

ALL_TABLES = (
    screening_results,
    flagged_spans,
    evaluation_log_entries,
    profiles,
    conversations,
    messages,
    admin_audit_log,
)
