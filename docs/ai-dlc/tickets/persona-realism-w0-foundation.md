# Tickets — Persona-Realism W0 Foundation

> Spec: `docs/ai-dlc/specs/persona-realism-w0-foundation.md`. Three per-slice PRs, three branches off fresh `main`.
> Owner-decided: build sequentially (one implementer), stop after all three PRs are open (no merge). Each PR gets
> `refuter` + `persona-realism-theory-reviewer` + Codex Sol at fan-in.

## Slice W0-a — denominator  → branch `feat/persona-realism-w0a-denominator`
Owned files: `backend/app/domain/table/sizing.py`, `backend/tests/test_sizing.py` (or new `test_pot_before_aggression.py`).

- [ ] **T-a1.** Add `PreAggressionPot(NamedTuple)` + `pot_before_current_aggression(action_history, street)` to
      `sizing.py`, reconstructing pot-before + latest-aggressor-increment via street-scoped per-`ActionType` chip replay
      (model on `range_estimate._replay_contexts.pay()`). Domain-pure (only `app.domain.spot` types).
      *Done:* function importable, `ruff` clean, `test_domain_purity` green.
- [ ] **T-a2.** Unit tests: self-re-raise, fresh single raise, checked-through, multi-street scoping.
      *Done:* new tests green; the self-re-raise case demonstrates the value the inline `personas_postflop.py:492`
      formula gets wrong.
- [ ] **T-a3.** Full verify + PR. *Done:* `./scripts/verify.sh` green, existing suites byte-identical, PR open.

## Slice W0-b — six harness metrics + DoD  → branch `feat/persona-realism-w0b-metrics`
Owned files: `backend/tests/test_personas_postflop.py`.

- [ ] **T-b1.** Convert per-decision `log` to `PostflopDecision(NamedTuple)` (seat, street, action, is_aggressor,
      in_position, amount_bb); update all existing consumers (`:1563, 1575, 1581-1585`) to named access; add a preflop
      log path. *Done:* AF/FtC/WTSD values **byte-identical** to pre-refactor (existing band tests green, unchanged).
- [ ] **T-b2.** Compute the six metrics (CBet-flop%, W$SD, VPIP/PFR/gap, size-bucketed FtC, IP/OOP c-bet split,
      turn-barrel%) with the ≥30-floor→None convention; derive `in_position` harness-side (excl FOLDED/ALLIN, BB-IP-vs-SB).
      *Done:* each metric returns a numeric value (or documented None) per persona on the fixture.
- [ ] **T-b3.** Smoke test asserting all six compute (no NaN/exception, shapes correct) + document the metric-DoD rule
      (D7) in this wave's spec/roadmap. *Done:* smoke test green; #5/#6 documented as ~flat-until-W3.
- [ ] **T-b4.** Full verify + PR. *Done:* `./scripts/verify.sh` green, `ruff` clean, PR open.

## Slice W0-c — node-trace pack + fit-loop doc  → branch `feat/persona-realism-w0c-node-trace`
Owned files: `backend/tests/node_trace.py` (new), `backend/tests/test_node_trace.py` (new),
`docs/ai-dlc/contracts/persona-realism-fit-loop.md` (new).

- [ ] **T-c1.** `node_trace.py`: fixed seeded spot set (per persona × {IP flop, OOP flop, made-pair+overcards, turn
      barrel, busted-draw river, multiway flop, low-SPR high-commitment}); a capture-rng runner (model on
      `range_estimate._CaptureRng`) logging {persona, spot_id, bucket, draw_class, merits, chosen_action,
      intended_prescription}. No domain edit, no `range_estimate`/`_play_hand` dependency.
      *Done:* pack runs, returns trace rows for the full seed set.
- [ ] **T-c2.** `test_node_trace.py`: assert structure — every row has the required fields, merits non-empty & sum>0.
      *Done:* test green.
- [ ] **T-c3.** `persona-realism-fit-loop.md`: measure→adjust-seed→re-measure loop + single-end-of-cluster re-anchor
      rule, pointing at `test_personas_postflop.py:1337-1480` + the metric-DoD rule; link from the roadmap.
      *Done:* doc exists and is linked.
- [ ] **T-c4.** Full verify + PR. *Done:* `./scripts/verify.sh` green, `ruff` clean, PR open.

## Dependencies / parallelism
- The three slices are **file-disjoint** → independently PR-able; each branches off clean `main`.
- No cross-slice code dependency (W0-c does **not** import W0-b's `_play_hand`; W0-a has no consumer yet).
- Estimator-parity work is **explicitly deferred to W1-b** (when the denominator is consumed) — noted in the spec.
