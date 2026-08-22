# Spec — S3-T5: the checked-down path (improvement slice 3, ticket 5)

**status: draft rev 2 — owner authorized spec + conditional build 2026-08-22; rev 1 FAILED blind review (refuter + Codex Sol, 2026-08-22) on four converging findings, all folded in below; confirmation pass PASS-WITH-FIXES (Sonnet refuter), fixes applied — READY, pending slice-3 spec amendment at build time**

**Bottom line.** Between 42% and 48% of the nit, TAG and LAG personas' showdown
hands never face a wager at all — every street is checked through. The calling
dial that slice 3's earlier tickets tune cannot reach those hands, which is why
S3-T2 (the calling-dial retune, ticket 2 of this slice) fell short of its
went-to-showdown target. This ticket adds **one bounded, pack-read lever** that
makes a bot more willing to bet at an unopened turn or river node, so fewer
hands drift to showdown with no money going in. The motivating human behaviour
is the stab a player makes when checked to — but the engine cannot tell a
stab from a lead (nothing in the decision's inputs records whether anyone acted
earlier on the street), so the lever is honestly named for what it moves:
**unopened late-street bet frequency**, leads included. The lever is off by default (an absent pack
field leaves every persona byte-identical), it lives entirely inside the one
function both the live bot and the villain-range estimator already share, it
adds no random draw, and it is gated on went-to-showdown (a HARD-today
statistic) and **diagnosed** with a new harness counter, "share of showdown
hands that never faced a wager", which this ticket builds first — the theory
contract requires a metric to be live before anything is measured against it.

Owner authorization (2026-08-22): spec now; build only if the slice-3 chain
(S3-T2 → S3-T3 → S3-T4) lands with budget to spare. Boundary: **pack values plus
one bounded engine lever, default = today's behaviour.** Anything wider returns
to the owner. **Scope amendment required:** the approved slice-3 spec
(`flywheel-slice3-calldown.md` §"Constraints", "engine work is limited to the
two levers named here") admits only S3-T1's split and S3-T3's multiplier. The
build PR amends that spec with a dated owner-ruling note admitting this
conditional fifth ticket; until that amendment lands, this document is a
proposal, not an approved ticket.

## 1. Problem, measured

| persona | showdown hands that never faced a wager (band harness, pinned 4,000-hand sample) | went-to-showdown vs grounded band |
|---|---|---|
| nit | 47.7% | 0.635, about 35 points above its band |
| tag | 44.1% | 0.614 |
| lag | 41.6% | 0.566 |

Source: `../research/slice3-calldown/t2-preregistration.md` §1 and
`../research/slice3-calldown/t2-findings.md` §5.3. The hands that DO face a
wager meet about one wager each, so the calling dial's whole reach is a single
decision per hand; the checked-through hands are the larger population and are
untouched by every lever this slice has so far.

Why this is a realism defect and not only a statistic: a human who is checked
to on the turn with position, or on the river after two check-arounds, bets a
meaningful fraction of the time — with value to protect or with air to take the
pot. A table where three of six seats let the hand drift to showdown is what a
judge reads as passive-robotic, and showdowns are also what makes every other
tell visible (roadmap, slice 3 entry).

## 2. Where the decision lives (from the contract map)

Contract map: `../contracts/flywheel-slice3-t5-checkdown.md`. The only branch
that can produce a CHECK is the unopened / matched-with-option arm of
`sample_postflop_decision` (`backend/app/domain/personas_postflop.py:1657-1713`),
where `check_merit = _CHECK_BASE[bucket]` competes with one aggressive
candidate built from `_AGG_BASE`, the draw bonus, `agg_scale` (pack
`aggression`) and, on the BET leg only, `pos_mult` (pack
`position_sensitivity`). The street is read there only to decay the
semi-bluff bonus and to floor thin river value. No field distinguishes "first
to act after a check-around" from "continuing my own bet"; no stab, probe or
delayed-c-bet lever exists.

## 3. The lever

**Name:** `late_street_bet` — a pack field on `PersonaPostflop`, `float` in
`[0, 1]`, `Optional`, default `None` (→ multiplier 1.0, byte-identical).

**Where it applies:** the unopened node (`legal` offers CHECK + BET) on the
**turn and river only**, BET leg only — never the matched-with-option RAISE
leg, never the flop (the flop c-bet is already governed by `position_sensitivity`
and `aggression`, and the theory contract's c-bet band is `[UNVERIFIED]`).

**What it does:** on the NON-BLUFF path only, with the full guard written out —
`not bluff_cell and agg_action is ActionType.BET and street in (TURN, RIVER)
and late_street_bet is not None` (mirroring the `pos_mult` guard at `:1664`,
which already forces 1.0 on the RAISE leg) — as the
statement immediately before the final `agg_merit *= pos_mult`
(`personas_postflop.py:1709-1711`, the "exactly once on each path" position
multiply), multiply the aggressive candidate's merit by

    1 + late_street_bet * _LATE_STREET_GAIN[street]     # {TURN: g_t, RIVER: g_r}

The bluff cell (`:1665-1673`, its own path with multiway damping baked into
`bluff_mass` at `:1391`) is untouched, so pure air rises only through its own
mass. Note for the record: the code applies position LAST on the non-bluff
path, after the multiway and texture damps, which already deviates from the
theory contract §7's written multiplier order (`:427`); this ticket inserts
next to the existing position multiply and does not reorder anything — the
pre-existing §7 mismatch is filed as a contract note, not fixed here.

with `g_t`, `g_r` module constants chosen by the build from a sweep so that at
`late_street_bet = 1.0` the nit's never-faced-a-wager share falls by at least
the registered floor (§5) without any persona's aggression factor leaving its
HARD band. Constants are recorded with their sweep in the pre-registration.
The multiplier is bounded, monotone in the dial, and applied to the merit
feeding the EXISTING single `rng.choices` action draw — no new random draw,
no reordering of draws, no read of any sizing-bracket field (so PR #199's
estimator-parity guard cannot trip and the estimator inherits the lever
automatically because it calls the same function).

**Why a multiplier on the aggressive candidate rather than a damp on
`check_merit`:** the aggressive candidate already carries every hand-strength
and draw term; scaling it keeps the bet a *strength-weighted* stab (value and
semi-bluff rise together, pure air rises only through the bluff cell's own
mass), which is the theory contract's stacked-multiplier order (§7). Damping
`check_merit` would raise bets uniformly across buckets, including hopeless
air, and would move aggression factor faster than went-to-showdown.

**Pack values:** set `late_street_bet` on nit, tag and lag only (the three
personas the measurement names), values from the sweep, registered before
tuning. Maniac, calling station and passive fish stay unauthored (off) — the
station and fish are meant to check down; the maniac already bets.

**Known tell risk (Codex Sol, 2026-08-22):** the same odds boost applies across
histories, blockers and range advantage, and top-pair/overpair thin value is
boosted alongside strong hands (only middle pair is river-floored at
`:1693-1708`). The build reports per-bucket turn/river bet frequency before
and after as a diagnostic table so a reviewer can see whether the spread
narrowed into a uniform stab rate; a visibly flattened spread is a
stop-and-report.

## 3a. The instrument comes first (build phase A)

No committed harness computes "share of showdown hands that never faced a
wager" — `_persona_stats` (`backend/tests/test_personas_postflop.py:2937-3012`)
returns only aggression factor, fold-to-c-bet and went-to-showdown; the 47.7 /
44.1 / 41.6% figures are prose in a research note. Phase A of the build adds a
`never_faced_wager` counter to `_persona_stats` (showdown hands with zero
faced wagers across all postflop streets ÷ showdown hands), records its value
for all six personas at the pinned seed with the packs unedited, and lands
that as the first commit of the PR. It is a DIRECTIONAL diagnostic under the
theory contract (`:394-409`), never a HARD gate; went-to-showdown is the gate.

## 4. Constraints carried in (violating any is a defect)

- HARD went-to-showdown ordering legs: `station > tag`, `station > lag`,
  `maniac < station` never weaken. Transition-scoped legs `fish < tag` and
  `station − fish > 0.10`: each may move once under ruling 2, recorded.
- Aggression-factor and fold-to-c-bet bands stay HARD and green for all six.
- Interim ceiling ratchet re-applied after tuning (measurement + 3 SD, rounded
  outward, never above the incumbent); no persona ships above its ceiling.
- Five-seed de-robotization gate green; LAG–TAG pair reported. If the
  separation floor binds: stop and report, never tune to the gate (ruling 3).
- No new RNG draw; action draw stays the first `rng.choices` call.
- α fold-ceilings untouched; no fold floors added anywhere.
- Re-records (`_GOLDEN_STATS_N200`, `_PRE_M3_FIRES`, coverage baseline, export
  digests) only with provenance + revert-to-prove-attribution; tolerances
  never widen (ruling 4).
- Hero grading (`backend/app/domain/postflop.py`) is out of scope.
- Schema: add to `content/schema/persona.schema.json` `postflop.properties`,
  not `required`; Pydantic field `Optional[float] = Field(default=None, ge=0, le=1)`.
- Byte-identity test: with all six packs unedited, a 4,000-hand harness run
  reproduces the pre-ticket fingerprints exactly.

## 5. Pre-registration (written in the PR before any pack value moves)

1. The sweep, **one persona at a time with the other five packs unedited**
   (the harness is mixed-persona — `:2958-2973` — so a roster-wide sweep would
   let the TAG's extra bets lower the nit's faced-wager share and earn the
   nit's result for it): `late_street_bet ∈ {0.25, 0.5, 0.75, 1.0}` × candidate
   `(g_t, g_r)` pairs, on the band harness at its pinned seed, reporting for
   the swept persona: never-faced-a-wager share, went-to-showdown, aggression
   factor, fold-to-c-bet, per-bucket turn/river bet frequency. Then one
   combined run at the chosen values for the roster check.
2. Registered floors, derived from the sweep's reach (not invented): a
   reduction in the never-faced-a-wager share for nit and TAG of at least the
   amount the deepest AF-admissible dial delivers minus one binomial standard
   error; went-to-showdown direction DOWN for all three; the LAG gets a
   direction only (its lever is not yet known — `t2-findings.md` §5.3).
3. If the admissible dials cannot clear the floors, ship the admissible values
   and record the shortfall (owner answer 2026-08-22 on shortfalls).

## 6. Acceptance criteria

1. Went-to-showdown falls for nit, TAG and LAG (paired before/after on the
   harness's pinned sample) — the gate. Never-faced-a-wager share for nit and
   TAG falls by at least the registered floor in the single-persona sweeps —
   the diagnostic, reported, not gated.
2. All HARD bands green (AF, fold-to-c-bet, went-to-showdown) for all six
   personas; ordering legs as in §4; ceiling ratchet re-applied and recorded.
3. Byte-identity test passes with packs unedited; targeted tests — named
   `test_late_street_bet_fires_on_unopened_turn_river_bet_leg`,
   `test_late_street_bet_is_identity_when_absent_or_off_scope`, and
   `test_late_street_bet_estimator_parity_unopened` — show the
   multiplier firing at an unopened turn/river BET leg on the non-bluff path
   and NOT firing on the flop, on the RAISE leg, on the bluff cell, or when
   the field is absent.
4. Five-seed gate green, LAG–TAG pair reported.
5. Estimator parity: `test_estimator_prices_the_faced_bet` and the parity
   guard from PR #199 pass unchanged, plus a NEW unopened turn/river
   estimator-vs-sampler parity test (the existing test covers faced nodes
   only).
6. 50,000-hand export went-to-showdown before/after reported as diagnostic
   context.
7. The slice-3 spec amendment admitting this ticket lands in the same PR.

## 7. Verify-by (runnable, at the ticket's tip)

```
./scripts/verify.sh
cd backend && ruff check .
cd backend && PYTHONPATH=. .venv/bin/python -m tools.derobo_gate --check --all-seeds
cd backend && PYTHONPATH=. .venv/bin/python -m pytest -k "persona_postflop_bands or wtsd_ordering or late_street"
```

## 8. Out of scope

A flop bet-frequency lever · any change to `check_merit` · a true
"checked-to-me" signal (the roadmap's `prev_street_checked_through` item,
persona-realism.md B12-b) — a later ticket may add it and re-scope this lever
onto real stabs · sizing changes (sizes
stay seat-conditional per slice 1) · the LAG's showdown lever · the commit-gated
pots mechanism (`W4-a`, deferred past the finale by owner ruling).

## 9. Review tier

persona-realism theory reviewer + refuter + Codex Sol (high), same as S3-T2/T3.
Spec itself: one blind refuter + one blind Codex Sol pass before the build.
