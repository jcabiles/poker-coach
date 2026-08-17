# Finding ledger — R9-SIGNAL (opponent-line signal plumbing)

Slice: byte-identical line-signal derivation (design-pass-amended; parallel-wave partner of
W5-b4). Branch `feat/persona-realism-r9-signal` (worker-built in isolated worktree), commits
`a2a7e2d` (build, pre-rebase `5fab603`) + `d6013e7` (review folds), rebased onto `6aabf41`
(#140 tip). Reviewers (git-READ-ONLY): `refuter`, Codex `gpt-5.6-sol`.

## Done-condition

`aggressor_barrel_run(history, street, aggressor_position)` in
`app/domain/table/postflop_context.py` — consecutive POSTFLOP-ONLY barrel run (flop ≡ 0 by
construction; a preflop raise never counts — the W3R-5 trap; `_PREV_STREET`/`bet_prev_street`
untouched as the separate own-initiative signal); `aggressor_bet_prev_street: bool = False`
flat kwarg on `sample_postflop_decision` (NOT a PostflopContext field — estimator-parity
reason), threaded in `bot_decision` from the current street's last aggressor; READ BY NOBODY.
Byte-identity gate: zero pack/fixture/band changes (refuter verified the full suite delta vs a
pristine parent is exactly +the new tests). 10 unit tests + estimator-parity (True/False legs
identical) + post-fold capture test. `BACKEND VERIFY OK` 1150 pass / 1 skip post-rebase.

## Findings

| # | Source | Sev | Finding | Adjudication |
|---|--------|-----|---------|--------------|
| R-1 | refuter | MED | CONSECUTIVE pin's docstring example off by one (bet-flop/check-turn/bet-river "scores 1" — code correctly returns 0 per design pin 2); the R9-DEFENCE consumer would read exactly that sentence when picking g(run) | **ACCEPTED — FIXED** `d6013e7`: both examples restated exactly (0 for broken run; 1 for the true delayed stab check-flop/bet-turn) |
| C-1/R-2 | Codex+refuter (convergent) | MED/LOW | Call-site derivation in `bot_decision` had NO test — the kwarg is deliberately dead, so deleting the wiring, hardcoding False, or using the whole-hand aggressor would pass the suite | **ACCEPTED — FIXED**: monkeypatch capture test over 120 organic hands — per-decision parity vs independent recomputation, unopened-street False, non-vacuous both directions |
| R-3 | refuter | LOW | Flag derived on matched-with-option shapes (CHECK+RAISE legal) where no faced wager exists — inert now, foot-gun for the consumer | **ACCEPTED — FIXED**: consumer note at the call site (R9-DEFENCE must gate on facing-chips nodes) |
| R-4 | refuter | LOW | New per-decision allocation in play.py | **NO ACTION**: measured 3.78µs ≈ 1-2% of hand cost, in line with the four existing history scans |
| W-1 | builder | — | Brief self-contradiction on the delayed-stab number; builder chose the design report's rule | **CONFIRMED CORRECT** by both reviewers against r9-defence-design.md §Q1 pin 2 |

Verdicts: refuter **PASS** (all three pins verified incl. the flop-trap contrast with
`bet_prev_street`; byte-identity proven vs pristine parent) · Codex **FAIL→resolved**.

## Notes

- Built and reviewed in parallel with W5-b4 (disjoint files; this slice touches no packs or
  fixtures, so no lane contention — the wave's premise held).
- The R9-DEFENCE consumer remains BLOCKED on owner adjudication of the full defence design
  (`docs/ai-dlc/reports/r9-defence-design.md`); this slice commits to nothing about it.
