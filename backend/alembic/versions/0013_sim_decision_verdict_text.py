"""sim_decision verdict/reasoning text + sim_hand.created_at index (hand replayer)

Revision ID: 0013
Revises: 0012

Adds two nullable TEXT columns to sim_decision (the grader's tier verdict +
reasoning prose, persisted at play time so replay re-shows exactly what the hero
saw) and an index on sim_hand.created_at (the day-grouped history query).

Downgrade: SQLite can't DROP COLUMN in place, so the two sim_decision columns
come off via batch_alter_table (0012 precedent). The created_at index lives on a
DIFFERENT table (sim_hand), so the sim_decision column-drop batch will NOT remove
it — it must be dropped explicitly or a re-upgrade fails recreating a duplicate.
"""
from alembic import op
import sqlalchemy as sa

revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Additive nullable — existing rows read back with NULL, no backfill.
    op.add_column(
        "sim_decision", sa.Column("verdict_tier_text", sa.String(), nullable=True)
    )
    op.add_column(
        "sim_decision", sa.Column("reasoning_text", sa.String(), nullable=True)
    )
    op.create_index(
        "ix_sim_hand_created_at", "sim_hand", ["created_at"], unique=False
    )


def downgrade() -> None:
    # The created_at index is on sim_hand, NOT sim_decision — drop it explicitly;
    # the sim_decision column-drop batch below would leave it behind and break a
    # re-upgrade (duplicate index).
    op.drop_index("ix_sim_hand_created_at", table_name="sim_hand")
    with op.batch_alter_table("sim_decision") as batch:
        batch.drop_column("reasoning_text")
        batch.drop_column("verdict_tier_text")
