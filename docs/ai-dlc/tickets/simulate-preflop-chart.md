# Tickets — Simulate preflop range chart

> Spec: `specs/simulate-preflop-chart.md`. Runs AFTER the S10/S11 waves merge
> (file contention: `SimulateView.tsx`, `types.ts`, `app.css`). Refuter pass on the
> spec REQUIRED before C1 starts. Sequential — one owner.

## C1 — Backend: chart endpoint (implementer)
Read-only helper in `sim_session.py` (decision point → mapped Spot → `range_grid(lookup)`
grid + exploit-note lookup by live villain persona) + `GET /simulate/{id}/preflop-chart`
+ `PreflopChartView` schema. No DB writes, no migration.
- Accept: mappable RFI spot returns grid identical to Practice's drill grid for the same
  Spot (fixture test); unmappable/multiway/postflop/not-hero-turn → `available=false`;
  missing exploit pair → `exploit_note=null`, grid still present.
- Done: new endpoint tests green; `verify.sh` + ruff green.
- Owns: `services/sim_session.py`, `api/v1/simulate.py`, `schemas/simulate.py`,
  new backend test file.

## C2 — Frontend: SimRangeChart panel (ux-ui, needs C1)
`SimRangeChart.tsx` (RangeGrid markup copy, sim-owned, collapsed default + own
localStorage key, fetch on first expand, exploit note line, no-chart message), mount in
`SimulateView.tsx` under the action bar (preflop hero turns only), `types.ts` mirror,
`.sim-chart-*` CSS (tokens-only).
- Accept: expand shows grid + note; collapse persists; zero fetch while collapsed;
  postflop hidden; AA + focus both themes; typecheck/build green.
- Done: `design-reviewer` acceptable; Practice RangeGrid visually unchanged.
- Owns: `SimRangeChart.tsx`, `SimulateView.tsx`, `frontend/src/api/types.ts`,
  `app.css` (`.sim-chart-*`).

Parallelizable: none (C2 needs C1's wire shape live).
