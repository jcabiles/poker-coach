"""sim_decision structured reasoning parts (feedback-prose-readability T3)

Revision ID: 0014
Revises: 0013

Adds one nullable TEXT column to sim_decision: the JSON-serialized
ReasoningParts {lead, points, sources} persisted at play time alongside the
flat verdict/reasoning prose (0013). Old rows read back NULL and every reader
falls back to the flat reasoning_text paragraph — no backfill, no re-grade.

Downgrade: SQLite can't DROP COLUMN in place, so the column comes off via
batch_alter_table (0012/0013 precedent).
"""
from alembic import op
import sqlalchemy as sa

revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Additive nullable — existing rows read back with NULL, no backfill.
    op.add_column(
        "sim_decision", sa.Column("reasoning_parts_json", sa.String(), nullable=True)
    )


def downgrade() -> None:
    with op.batch_alter_table("sim_decision") as batch:
        batch.drop_column("reasoning_parts_json")
