"""Migration 0015 (two-mode-simulate T1): sim_session.mode + blind_check_json.

Proves the additive-nullable pattern is safe on a database that already has
an ACTIVE session with real hand state — the upgrade must not disturb it.
"""

from __future__ import annotations

from sqlalchemy import create_engine, text

from alembic import command
from app.db.migrate import make_alembic_config


def test_migration_0015_upgrade_preserves_active_session(tmp_path):
    url = f"sqlite:///{tmp_path / 'mig15.db'}"
    cfg = make_alembic_config(url)

    # Land on 0014 (predecessor), insert an ACTIVE session the old schema's
    # way (no mode / blind_check_json columns yet), plus a related hand row.
    command.upgrade(cfg, "0014")
    engine = create_engine(url, connect_args={"check_same_thread": False})
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO sim_session (id, owner_id, button_seat, hand_no, "
                "status, created_at) "
                "VALUES ('m15', '', 3, 7, 'active', '2026-01-01 00:00:00')"
            )
        )
        conn.execute(
            text(
                "INSERT INTO sim_hand (session_id, hand_no, button_seat, rng_seed, "
                "status, state_json, created_at) "
                "VALUES ('m15', 7, 3, '1', 'in_progress', '{}', '2026-01-01 00:00:00')"
            )
        )
    engine.dispose()

    # Up to head: additive nullable columns. Existing row reads mode='training'
    # and blind_check_json NULL; hand state (hand_no/button_seat/status)
    # is unchanged.
    command.upgrade(cfg, "head")
    engine = create_engine(url, connect_args={"check_same_thread": False})
    with engine.begin() as conn:
        row = conn.execute(
            text(
                "SELECT mode, blind_check_json, hand_no, button_seat, status "
                "FROM sim_session WHERE id='m15'"
            )
        ).fetchone()
        assert row == ("training", None, 7, 3, "active")
        cols = {r[1] for r in conn.execute(text("PRAGMA table_info(sim_session)")).fetchall()}
        assert "mode" in cols and "blind_check_json" in cols
    engine.dispose()
