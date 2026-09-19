"""sim_session table_size column (simulate-6max S1 T1)

Revision ID: 0016
Revises: 0015

Adds one nullable column to sim_session: `table_size` (6 or 9, the seat count
chosen on the sit-down screen), server_default "9" so every pre-existing
session reads back as 9-max. Additive-nullable — no backfill, no re-grade.

Downgrade: SQLite can't DROP COLUMN in place, so the column comes off via
batch_alter_table (0012/0013/0014/0015 precedent).
"""

from alembic import op
import sqlalchemy as sa

revision = "0016"
down_revision = "0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Additive nullable — existing sessions read back table_size=9.
    op.add_column(
        "sim_session",
        sa.Column("table_size", sa.Integer(), nullable=True, server_default="9"),
    )


def downgrade() -> None:
    with op.batch_alter_table("sim_session") as batch:
        batch.drop_column("table_size")
