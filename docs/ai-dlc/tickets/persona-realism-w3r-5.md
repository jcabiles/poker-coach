# W3R-5 tickets — defense-side texture/scare fold brake (#8), NEW MECHANIC

Spec: `docs/ai-dlc/specs/persona-realism-w3r-5.md`. Single owner/worker — the engine edit, the context thread and the
estimator thread share ONE fit + ONE fixture re-record and cannot be parallelised (the estimator parity test gates on
the fitted engine). Behavior change is INTENDED (texture legs fire for every caller immediately — they key on `board`,
which every caller already passes) ⇒ seeded fixtures re-record (P1/P2a precedent). All four magnitudes are **FIT
SEEDS** — measured to target, never dropped in. NO new persona lever, NO new bucket, NO taxonomy edit, grader frozen.

**A1 GUARDRAIL (read first):** this is a multiplicative **BOOST** to fold merit before normalization. Nothing in this
slice may clamp, `max()`, or lower-bound a fold merit or a fold FREQUENCY. Every test is a relative inequality or a
bounded-range check. **A test of the form `assert fold_rate >= X` FAILS the slice.**

Owned files: `backend/app/domain/personas_postflop.py` (new helpers after `:381`, call site `:727`, signature `:593`),
`backend/app/domain/table/postflop_context.py` (one new helper), `backend/app/domain/table/play.py` (`:140–159`,
`:218–232`), `backend/app/domain/table/range_estimate.py` (`:86–98`, `:131–201`, `:278–289`),
`backend/tests/{test_personas_postflop,test_postflop_context,test_range_estimate,test_arrival_range_ftc}.py`, the
re-recorded fixture data files.

## T1 — the fold-side brake (engine)
Add the three legs next to the bet-side ones (after `_wetness_bet_mult`, `:371–381`), REUSING `_overcard_count`
(`:345`), `texture.classify` and `_VULNERABLE_ONE_PAIR` (`:342`) — no second taxonomy:
`_OVERCARD_FOLD_BOOST` (0→1.00, 1→~1.15, 2+→~1.30) · `_scare_texture_fold_boost(board)` (first-match chain mirroring
`_wetness_bet_mult`: monotone ~1.30, paired/trips ~1.18, connected ~1.12, else 1.00; `len(board)<3` → 1.0) ·
`_AGGRESSION_FOLD_TIGHTEN ** min(max(street_aggressions-1, 0), _AGGRESSION_FOLD_CAP=2)` (~1.25) · combined product
capped at `_SCARE_FOLD_CAP` (~2.0). Add kwarg `street_aggressions: int = 1` (`:593–607`). Apply at **`:727` only** —
`fold_merit *= ...` after the `_MW_CATCH_TIGHTEN` block (`:725–726`), before the FOLD append — scoped to
`_VULNERABLE_ONE_PAIR` + `ACE_HIGH` (the ACE_HIGH leg is what closes the H117 facing-a-raise float the `_FOLD_BASE`
comment at `:242–251` re-routed here; the GLOBAL base cut that was measured-and-dropped there must NOT be
re-attempted). Tests (capture-weights, no sampling): monotone > dry, paired > dry, 2-overcard > dry at identical
bucket/price/opponents; `street_aggressions` 1<2<3, flat 3→4; combined multiplier ∈ [1.0, `_SCARE_FOLD_CAP`];
dry-rainbow-zero-overcard + `street_aggressions=1` **byte-identical**; and a **fold-side-only regression** test that
the unopened BET merit for a one-pair hand on a monotone board is UNCHANGED (W3-d scoping at `:769–771` untouched).
- **Done-condition:** all of the above pass; existing overcard/wetness BET tests green **unmodified**.
- **Owned:** `personas_postflop.py` (helpers after `:381`, `:593` signature, `:727` call site), the new unit tests.
- **HARD-STOP:** if closing #8 appears to need a change on the BET side or a `_FOLD_BASE` table edit, STOP — both are
  explicit no-gos.

## T2 — `street_aggressions` context + live thread
Add `street_aggression_count(action_history, street) -> int` to `postflop_context.py` (sibling of `bet_prev_street`,
`:88–105`): the number of BET/RAISE actions by ANY seat on `street`, the actor's own included — so a lone faced c-bet
reads **1** (identity) and hero-bet→villain-raise reads **2** (the raise-war signal). Derive it in `play.py` beside
`derive_postflop_context` (`:218`) and thread it through `bot_decision` → `_postflop_decision` (`:140–159`,
`:229–232`). Unit-test the counter: unopened street 0, single c-bet 1, bet+raise 2, bet+raise+re-raise 3, and that it
RESETS across streets.
- **Done-condition:** counter tests pass; the live bot passes the derived value; `street_aggressions=1` paths
  byte-identical.
- **Owned:** `postflop_context.py` (one new function), `play.py` (`:140–159`, `:218–232`), `test_postflop_context.py`.
- **Depends-on:** T1 (the kwarg).
- **HARD-STOP:** do NOT add this as a `PostflopContext` field. Building a `PostflopContext` in the estimator (T3)
  would default `in_position=False` and silently activate the W3-b OOP damp (`_position_agg_mult`, `:586–590`) on
  every unopened node for position-sensitive personas. Scalar kwarg, default 1.

## T3 — estimator thread + parity test (estimator-parity law)
`range_estimate.py`: add `street_aggressions` to `_Ctx` (`:86–98`), count it in `_replay_contexts` (reset with the
street at `:131–136`, increment on the BET/RAISE branch at `:191–201`), and pass it at the sampler call (`:278–289`).
The texture legs need no threading — the estimator already passes the real `board`. New parity test modelled on
`test_range_estimate.py:405`: scripted monotone-board **bet-then-raise** node, `_postflop_action_dist(...)` equals a
`_CaptureFirstChoices` capture of the live `sample_postflop_decision(..., street_aggressions=k)` for the replayed k,
AND the k=1 distribution differs (discriminating).
- **Done-condition:** parity test passes and is discriminating; the existing estimator fixture/equivalence tests stay
  green (re-recorded only where the intended texture change legitimately moves them).
- **Owned:** `range_estimate.py` (`:86–98`, `:131–201`, `:278–289`), `test_range_estimate.py`.
- **Depends-on:** T1, T2.

## T4 — FIT the magnitudes + directional target + fixture re-record
Fit all four constants inside their ranges — overcard 1: 1.08–1.25, 2+: 1.15–1.45 · monotone 1.15–1.45, paired
1.08–1.30, connected 1.05–1.20 · `_AGGRESSION_FOLD_TIGHTEN` 1.10–1.45 · `_SCARE_FOLD_CAP` 1.7–2.5 — against BOTH
targets at once. Add the seeded directional check to `test_arrival_range_ftc.py`: partition each persona's flop
arrival spots by `classify(board)` into SCARY (monotone or paired) vs DRY (rainbow + unpaired) and assert fold-to-bet
at a fixed size is strictly HIGHER on SCARY for `calling_station`, `nit`, `passive_fish` (relative, baseline-free —
never an absolute floor). Re-record the seeded fixtures the change moves (golden / coverage_baseline / limper belt).
- **Done-condition:** the scary-vs-dry assertion passes for all three personas; **every** persona's AF/WTSD/ftc band
  IN its existing frozen band (NO re-anchor); the four LIVE T4 `FLOP_BANDS` still pass (station 0.33 ≤ 0.15 / 1.5 ≤
  0.40, fish 0.33 ≤ 0.38 / 1.5 ≤ 0.80 — these upper edges are the α-ceiling proxy and BIND here);
  `./scripts/verify.sh` green; `ruff check .` clean; `content/` JSON validates. Report the fitted constants,
  per-persona re-measured AF/WTSD/ftc, the scary-vs-dry deltas, T4 curve movement, fixtures moved, and the cumulative
  graded-coverage delta vs the immutable snapshot.
- **Owned:** the four constants in `personas_postflop.py`, `test_arrival_range_ftc.py`, the fixture data files.
- **Depends-on:** T1, T2, T3.
- **HARD-STOP:** if no in-range magnitude set satisfies the directional target AND keeps every band + T4 edge green,
  STOP and report the sweep. A band re-anchor is an owner decision (§7; the W3R-2 exception was fish+station WTSD
  only). Any leg fitted below ~1.10 is COSMETIC under the softmax law — report it as a failed fit, not a pass.

## Sequencing
T1 (engine + kwarg) → T2 (context + live thread) → T3 (estimator + parity) → T4 (fit + directional + re-record).
Strictly serial, single owner/worker: T4's fit invalidates T3's parity fixture if run out of order, and every task
touches the one `personas_postflop.py` facing-branch hotspot. No hotspot contention with W3R-6/W3R-7 provided this
slice lands first (it edits `:727`; W3R-7 is taxonomy/`_made_bucket`).
