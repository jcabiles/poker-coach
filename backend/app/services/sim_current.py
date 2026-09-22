"""Which Simulate session is the owner playing right now (P4)?

The phone and the Mac both ask the server this on boot instead of trusting
browser storage, so both land on the same table. Kept out of `sim_session.py`
(already ~2000 lines) because it only picks a row and hands the id to that
module's `restore_session()`; everything about hands, grading and privacy stays
there.

Spec: docs/ai-dlc/specs/phone-p4-live-session.md, item 5.
"""

from __future__ import annotations

from sqlalchemy import func
from sqlmodel import Session, col, select

from app.db.models import SimHand, SimSession
from app.schemas.simulate import SessionView
from app.services.sim_session import restore_session


def current_session(db: Session, owner_id: str = "") -> SessionView | None:
    """The owner's active session played most recently, or None (=> 404).

    Ordered by the newest hand of each session rather than by the session's own
    `created_at`: a pre-P4 table whose browser key was lost is still `active`
    forever (only Leave ends a session), and creation order would let such an
    orphan outrank the table actually being played. Sessions with no hands at
    all sort last — SQLite puts NULL last under `DESC`. The session's own
    `created_at` breaks ties; the id is a uuid and cannot.
    """
    # `col()` is SQLModel's own escape hatch: the model attributes read as their
    # Python values (a `datetime` has no `.desc()`), which is the same mismatch
    # the type-check baselines in pyproject.toml record for other modules.
    last_hand_at = (
        select(func.max(SimHand.created_at))
        .where(col(SimHand.session_id) == SimSession.id)
        .correlate(SimSession)
        .scalar_subquery()
    )
    session = db.exec(
        select(SimSession)
        .where(col(SimSession.owner_id) == owner_id)
        .where(col(SimSession.status) == "active")
        .order_by(last_hand_at.desc(), col(SimSession.created_at).desc())
    ).first()
    if session is None:
        return None
    # None when the chosen session has no readable current hand — the route
    # turns that into the same 404, which lands the client on the sit-down
    # screen rather than the generic error panel.
    return restore_session(db, session.id, owner_id=owner_id)
