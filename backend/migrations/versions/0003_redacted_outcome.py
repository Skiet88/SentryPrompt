"""Allow the "redacted" evaluation outcome.

Students can now choose "hide flagged details and send": every flagged detail
is replaced before the prompt reaches the AI. The evaluation log records that
choice as its own outcome, so the research can tell it apart from "send
anyway" (override). Only the list of allowed values changes; existing rows
are untouched and the log stays append-only.

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-04
"""

from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

TABLE = "evaluation.evaluation_log_entries"
CONSTRAINT = "evaluation_log_entries_outcome_check"


def upgrade() -> None:
    op.execute(f"ALTER TABLE {TABLE} DROP CONSTRAINT {CONSTRAINT}")
    op.execute(
        f"ALTER TABLE {TABLE} ADD CONSTRAINT {CONSTRAINT} "
        "CHECK (outcome IN ('flagged', 'unflagged', 'override', 'unavailable', 'redacted'))"
    )


def downgrade() -> None:
    # Fails if 'redacted' rows exist: the append-only log can't be rewritten,
    # so such a database can't go back to a version that doesn't know them.
    op.execute(f"ALTER TABLE {TABLE} DROP CONSTRAINT {CONSTRAINT}")
    op.execute(
        f"ALTER TABLE {TABLE} ADD CONSTRAINT {CONSTRAINT} "
        "CHECK (outcome IN ('flagged', 'unflagged', 'override', 'unavailable'))"
    )
