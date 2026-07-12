# Spec — Simulate villain range reveal (live, per-action, all streets)

> NEXT-item slice, roadmap `docs/ai-dlc/roadmap/simulate-table.md`. Gate-1 scope locked
> BY THE USER 2026-07-12: all streets from day one; postflop explicitly an ≈-labeled
> ESTIMATE. Built autonomously under the 2026-07-12 "proceed with everything"
> instruction; solo-inception — refuter pass mandatory before build.
> Runs AFTER the preflop-chart slice (shares `SimulateView.tsx`/`types.ts`/`app.css`).

## Goal (one line)
A per-villain reveal button that shows the current estimated hand-range of any live
(non-folded) villain as a weighted 13×13 chart that narrows as they act — exact
conditioning preflop, ≈-labeled approximate conditioning postflop — without ever peeking
at their actual cards.

## The load-bearing invariant — NO CARD PEEKING
The range is computed ONLY from public information: the villain's persona pack + the
action sequence they took + the revealed board. The conditioning code must never read
the villain's actual hole cards from `state_json` (which the server holds). This is both
an information-integrity rule (the chart is an honest "what could they have") and the
privacy structure S9 established. Test-enforced: the computed range for a hand must be
IDENTICAL across re-deals where only the villain's actual cards differ (same persona,
same public line).

## Mechanics (verified against code)
- **Preflop = exact.** `personas.py` bots decide by sampling explicit combo ranges
  (`parse_range`) per node with per-action frequencies. Posterior after a sequence of
  actions = prior combos intersected/weighted by each action's probability for that
  combo at that node (weight = product of action probs; combos the persona never plays
  that way drop to 0). Deterministic math over pack data — no estimate.
- **Postflop = approximate, ≈-labeled.** `personas_postflop.py` decides via the 7-rung
  merit ladder over the villain's ACTUAL cards + board. The reveal instead conditions
  per candidate combo: what WOULD this persona have done holding that combo on this
  board (rung + lever probabilities) — then reweights by the observed action. Category-
  level approximation is acceptable (rung probabilities, not exact lever RNG); the UI
  labels every postflop chart "estimated".
- **Dead cards:** combos containing the hero's cards or revealed board cards are
  excluded (hero knows those); OTHER villains' cards are NOT excluded (hero can't know).
- **Folded villains have no button** (user decision); the panel closes if its villain
  folds.
- **Pacing lockstep:** during S11 staged playback the chart may only reflect actions the
  staged index has narrated — driven by the same staged index, never the raw batch.

## Files / interfaces to touch
**Backend**
- NEW `backend/app/domain/table/range_estimate.py` (pure domain, purity-allowlisted):
  `estimate_range(persona_pack, public_actions, board, dead_cards) -> dict[combo, weight]`
  + preflop-exact and postflop-approx internals. NO import of hole-card state.
- `backend/app/services/sim_session.py` — read-only helper: session + seat → public
  action history (from persisted hand events) → estimate.
- `backend/app/api/v1/simulate.py` — `GET /simulate/{id}/villain-range/{seat}` →
  `{seat, persona_label, street, weights: {combo_class: float}, exact: bool}`;
  404-style `available=false` for hero/folded seats.
- `backend/app/schemas/simulate.py` — `VillainRangeView`.
**Frontend**
- `frontend/src/api/types.ts` — mirror.
- NEW `frontend/src/components/simulate/SimVillainRange.tsx` — weighted 13×13 heat chart
  (cell opacity ∝ weight — NOT RangeGrid's action segments; new sim-owned cell renderer,
  reusing only the outer panel idiom); "estimated" tag when `exact=false`; per-villain
  open/close.
- `frontend/src/components/simulate/SimTable.tsx` — small reveal affordance on live
  villain pods (button, ≥24px target, visible focus).
- `frontend/src/components/SimulateView.tsx` — panel state; staged-index gating; refetch
  on each narrated villain action while open.
- `frontend/src/styles/app.css` — `.sim-vrange-*` section (tokens-only).

## Out of scope
Hero range display (the preflop-chart slice) · equity-vs-range math · persisting
estimates · multiway exploit notes · any change to persona play itself · turn/river
grading interplay · hidden-persona mode (future gate for this button — noted, not built).

## Constraints (invariants)
Domain purity (no web/DB imports; no `state_json` access from domain) · NO-PEEK
invariant above (test-enforced) · ≈ labeling on postflop charts · tokens-only CSS, AA
both themes, focus visible · perf: estimate computed on request + on narrated action
while open, never per-frame; if a postflop estimate exceeds ~150ms server-side, coarsen
to category buckets (measure first).

## Verify-by (end-to-end)
- Preflop exactness: BTN open → wide chart; same persona 4-bet line → strict subset,
  matches hand-computed pack posterior (fixture).
- No-peek: two seeded deals, same persona + same public line, different actual villain
  cards ⇒ byte-identical weights (test).
- Postflop: chart narrows after a barrel; carries "estimated" tag; combos blocked by
  board/hero cards are zero-weight.
- Folded villain: no button; open panel closes on fold. Staged playback: chart lags the
  log, never leads (lockstep test with S11 pacing).
- `./scripts/verify.sh` + ruff + FE typecheck/build green; refuter pass BEFORE build;
  `design-reviewer` acceptable both themes.
