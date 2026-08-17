# Finding ledger — parallel wave 2: RR-EMIT · N-3BSTRATA · R9-SEATPROV (2026-07-31)

> Orchestration: three parallel lanes (two isolated-worktree builds + one research agent), serial
> landings (single fixture-recorder law — only N-3BSTRATA re-records). Owner decisions this wave:
> all-3-lane scope (N-logit explicitly EXCLUDED — its facing-band re-anchor cost glues it to W4-b) ·
> N-3BSTRATA schema = optional role tag (untagged = both strata, backward compatible) · split
> authored for maniac + lag only · lag 4-bet nudge included · wave-wide fixture re-record
> authorization.

## R9-SEATPROV (research, DONE — doc only, local)

`docs/ai-dlc/research/rfi-seat-provenance.md`. Status PARTIAL: solver-chart provenance ESTABLISHED
for 9-max full-ring at coarse seat granularity (strongest triple: 9-max full-ring cash 100bb,
solver-derived simplified charts, Preflop Wizard 2026 — UTG ~11 / MP ~13 / HJ ~17 / CO ~24 /
BTN ~40 / SB ~30); measured-POPULATION provenance NOT established. UTG1/UTG2/LJ individually
unsourced anywhere. Verdicts: W5-b3 cliff 2.84 UNRESOLVED (pool baselines 3.64–4.23); band
3.2–5.25 = baseline bracket, NOT archetype gate; ~6.5 derivation RETIRED. Standing law: seat-axis
gating stays SHAPE-only; first safe instrument = ordinal cross-persona cliff comparison (maniac
excluded). DO-NOT: 6-max ladders, the retired 6.5.

## RR-EMIT (PR #148)

Build-time `unopened` range emitter (`backend/tools/rr_emit.py`) + nit curve spec
(`content/personas/ladders/nit.unopened.json`, runtime-invisible) + proving gate: emitted output
semantically identical to the shipped W5-b3 nit ladder, per seat/mix (parse-level), gate passed
FIRST-RUN with zero content/engine edits (token spelling even byte-identical, unasserted).

Reviews: refuter PASS-with-issues (3) · Codex PASS-WITH-ISSUES (2 MED + 2 LOW). Convergent MED.

| ID | Sev | Finding | Adjudication |
|---|---|---|---|
| R-1+C-1 | MED | `_validate` admitted specs breaking the "unrepresentable defect classes" claim — negative slope width rolled the row cursor backwards and re-claimed core-owned classes into a second mix (both reviewers reproduced); tier kinds/weights/shape unchecked | **FIXED** — validator hardened: kind whitelist, weights vocabulary+range+sum, non-negative int widths, duplicate tail ownership, ValueError not KeyError; 7 negative-control tests |
| C-2 | MED | unopened-only boundary documentation-only (a `vs_rfi` spec with `call` weights sailed through); CLI output unvalidated | **FIXED** — `facing`+action-vocabulary fence in `_validate`; every emitted node round-trips the real `PersonaNode` model |
| C-3 | LOW | spec's `emits` target = dead metadata (test hardcoded nit.json) | **FIXED** — proving-gate pack path now derived from `emits`; repointing it fails the gate |
| R-2 | LOW-MED | tier declaration order unvalidated ("tail before core emits weak mix first — silently backwards") | **NOT-A-DEFECT** — the shipped nit pack itself lists its limp tail mix FIRST (lint-clean); core-first enforcement would break the proving target. Mix-order pathologies in committed emitted packs are caught by the repo lint belt |
| C-4 | LOW | byte-identical token spelling true today but ungated | **ACCEPTED** — semantic identity is the contract; spelling is RR-NORM scope |

Builder-filed followups (routed): multi-slope `slopes` override readability (future station spec) ·
wildcard `positions: null` packs structurally inexpressible (scope fence, revisit only if
station/fish ladders are ever wanted) · `_raise_width_pct` local combo-weighting could drift vs
R10-COUNT's. Landing: rebased onto post-#147 main, full suite 1289 passed / 2 skipped, ruff clean.

## N-3BSTRATA (built; triple review in flight)

Builder result: role tag (opener|cold) as third first-match-wins criterion; `_preflop_opener`
(first preflop RAISE) plumbed via play.py AND mirrored in range_estimate.py (out-of-brief,
estimator-parity forced); maniac 1.2.0 + lag 1.2.0 opener nodes. Deterministic gates: maniac
opener fold-to-3bet 0.609→0.307 (~0.30 target), lag 0.829→0.499 (band 0.43–0.53), lag opener
4-bet 4.00% (3.0–5.5%), cold strata bit-unchanged, maniac gap 9.28 (20-reseed sweep
distributionally unmoved vs HEAD), frozen bands pass, lint inventory byte-identical. Expected
red: the three pre-authorized fixture re-records (landing items).

Reviews: refuter PASS (opener derivations proven equivalent incl. limp-reraise; ordering-law
direction correct; cold nodes byte-identical; red-first real) · theory PASS-WITH-ISSUES (1 HIGH
filed-forward + 1 MED + 2 LOW; maniac table archetype-faithful) · Codex FAIL (1 HIGH + 1 MED).
PR #149 (tip 6809f11).

| ID | Sev | Finding | Adjudication |
|---|---|---|---|
| C-H1 | HIGH | deterministic gate weighted the opener stratum by `unopened` nodes only; production opener = FIRST raiser incl. ISO raises over limpers (stronger range) — live lag blend measured 0.403, BELOW the 0.43–0.53 band the green gate claimed to prove | **FIXED** — new production-signal instrument (seeded 4000-hand play, opener = first preflop raise) is THE gate: maniac 0.2801 (n=821) ∈ [0.25,0.35], lag 0.4735 (n=490) mid-band; unopened figure demoted to authored-component pin (maniac 0.3073, lag 0.6034 ±0.02) |
| T-H1 | HIGH | CONTRACT-DEFECT (arrival-class, filed FORWARD): lag hit its band with 60.4% of 3-bet-flatting mass OFFSUIT, 22.8% on a dominated KTo/QTo/A9o… tier — inflated by lag's uniformly-too-wide opening ladder; no contract lever governs seat-ladder width vs induced vs_3bet composition | **PARTIALLY FIXED here + FILED** — the C-H1 re-fit trimmed exactly that tier (call 0.55→0.25 / 0.4→0.15 / trash→fold 1.0, strength-reordered per lint law); upstream opening-ladder width → roadmap follow-up `N-LAGLADDER` (re-check opener table when the lag ladder tightens) |
| M-1 | MED (all 3 reviewers convergent) | estimator role-routing untested (test_range_estimate never touches maniac/lag; live/replay parity ignored is_opener) | **FIXED** — full-playout parity now asserts `is_opener` per decision on EVERY street (exposed + fixed a stale `_Ctx` comment claiming False-postflop; live carries it postflop, sampler ignores it) + TT-discriminator posterior test (opener table 4-bets TT 0.15, cold never) + cold 3-bettor asserts False |
| L-1 | LOW (convergent) | "fail-loud" docstring overclaims — role-unaware caller silently degrades to an all-fold table | **FIXED** — reworded to fail-SAFE with the ⚠️ spelled out; both production callers pass a real boolean |
| L-2 | LOW | deterministic proxy uses uniform position weighting (disclosed simplification) | **ACCEPTED** — the proxy is now only a component pin; the gate lives on the production blend |
| T-L2 | LOW | coverage delta not yet reported at review time | **CLOSED at landing** — cumulative 331/1252 = 26.4%, −1.9pp (recovering), in-file |

Landing: fixtures re-recorded w/ provenance (coverage 1252/331; goldens all-six-rows move, maniac
AF 3.80→3.33 junk-continue composition; limper fires). Full suite 1300 passed / 2 skipped, ruff
clean, frozen bands held, zero lint-inventory exceptions.
