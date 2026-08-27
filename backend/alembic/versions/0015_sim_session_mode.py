"""sim_session mode + blind_check_json columns (two-mode-simulate T1)

Revision ID: 0015
Revises: 0014

Adds two nullable columns to sim_session: `mode` (the Training/Challenge
choice, server_default 'training' so every pre-existing session reads back as
Training) and `blind_check_json` (the stored hand-200 blind-check result,
JSON-serialized text; NULL means no check has been stored yet). Both are
additive-nullable — no backfill, no re-grade.

Downgrade: SQLite can't DROP COLUMN in place, so both columns come off via
batch_alter_table (0012/0013/0014 precedent).
"""
from alembic import op
import sqlalchemy as sa

revision = "0015"
down_revision = "0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Additive nullable — existing sessions read back mode='training'.
    op.add_column(
        "sim_session",
        sa.Column("mode", sa.String(), nullable=True, server_default="training"),
    )
    op.add_column(
        "sim_session", sa.Column("blind_check_json", sa.String(), nullable=True)
    )


def downgrade() -> None:
    with op.batch_alter_table("sim_session") as batch:
        batch.drop_column("blind_check_json")
        batch.drop_column("mode")
