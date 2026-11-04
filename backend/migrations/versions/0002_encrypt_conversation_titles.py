"""Store conversation titles encrypted.

Titles are now made from the (redacted) first prompt, which makes them
content: they are encrypted like messages (NFR-011, TitleCipher). The plain
`title` column is replaced by `title_ciphertext` (NULL = the default title).

Existing titles are not carried over: the migration has no access to the
encryption key, and copying them would keep plain text. Existing chats show
the default title.

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-04
"""

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE public.conversations ADD COLUMN title_ciphertext bytea")
    op.execute("ALTER TABLE public.conversations DROP COLUMN title")


def downgrade() -> None:
    op.execute(
        "ALTER TABLE public.conversations ADD COLUMN title text NOT NULL DEFAULT 'New conversation' "
        "CHECK (char_length(title) BETWEEN 1 AND 200)"
    )
    op.execute("ALTER TABLE public.conversations ALTER COLUMN title DROP DEFAULT")
    op.execute("ALTER TABLE public.conversations DROP COLUMN title_ciphertext")
