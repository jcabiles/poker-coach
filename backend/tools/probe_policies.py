"""Rule-breaking action policy for the phase-3 judge-bias probe.

Engine-LEGAL but strategically illogical (amendment draft §A): the policy never
folds, calls any bet with any holding, bets/raises every chance it gets, and
always uses the same nonsense sizing regardless of pot, board, or holding. No
human plays this way for 30 consecutive hands; every action is still legal per
`engine.legal_actions`, so the renderer's terminal-state validation passes.

Lives in tools/ (NOT app/domain/): experiment code stays out of the product
domain core (dual-review ruling, ledger phase3-probe #1).
"""

from __future__ import annotations

import random

from app.domain.action import Decision
from app.domain.spot import ActionType
from app.domain.table.engine import HandState, legal_actions

# The fixed nonsense sizing (in big blinds). Deliberately weird and identical
# in every spot — "always 7.77" is the kind of mechanical tell the probe exists
# to verify a judge can see.
RULE_BREAKER_BET_BB = 7.77


def rule_breaker_decision(
    state: HandState, seat: int, pack: object = None, rng: random.Random | None = None
) -> Decision:
    """Same call shape as `bot_decision(state, seat, pack, rng)`; pack/rng unused —
    the policy is deterministic and holding-blind by design."""
    del seat, pack, rng
    legal = list(legal_actions(state))
    kinds = {la.action: la for la in legal}

    # Aggression up to (and only up to) the nonsense number: bet 7.77 when the
    # street is unopened, raise TO 7.77 when the bet is still below it, and
    # flat-call absolutely everything above it. Nine of these at a table would
    # otherwise min-raise each other forever — capping the aggression at the
    # fixed size keeps hands terminating while staying maximally mechanical.
    if ActionType.BET in kinds:
        la = kinds[ActionType.BET]
        return Decision(
            action=ActionType.BET,
            size_bb=min(max(RULE_BREAKER_BET_BB, la.min_bb), la.max_bb),
        )
    if ActionType.RAISE in kinds and state.current_bet_bb < RULE_BREAKER_BET_BB:
        la = kinds[ActionType.RAISE]
        return Decision(
            action=ActionType.RAISE,
            size_bb=min(max(RULE_BREAKER_BET_BB, la.min_bb), la.max_bb),
        )
    # Never fold: call any action, any holding, any size.
    if ActionType.CALL in kinds:
        return Decision(action=ActionType.CALL)
    return Decision(action=ActionType.CHECK)
