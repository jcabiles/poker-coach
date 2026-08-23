# Contract map — the checked-down path (S3-T5 pre-work)

**Bottom line.** The decision that produces a checked-down showdown lives in
one place: the `else` branch of `sample_postflop_decision` (unopened /
matched-with-option node) in
`backend/app/domain/personas_postflop.py:1657-1713`, where `check_merit =
_CHECK_BASE[bucket]` competes against one aggressive candidate (`BET` or
`RAISE`) built from `_AGG_BASE`, the draw bonus, `agg_scale`
(persona `aggression`), and — on the BET leg only — `pos_mult`
(`position_sensitivity`, already street-blind). A checked-through hand is
just this branch firing CHECK on flop, turn and river in sequence, advanced
by the plain while-loop in `backend/app/domain/table/play.py:300-341`, which
applies whatever `bot_decision` returns with no showdown-aware branching of
its own. **Three candidate insertion points for one bounded lever exist:
(1) a new street-and-history-aware multiplier on `check_merit` itself,
(2) a new term in `_AGG_BASE`/`agg_merit` conditioned on "checked to me
already this hand," or (3) a `_position_agg_mult`-style multiplier keyed on
street (a stab/probe/delayed-cbet dial) — none of these fields exist today.**
The biggest trap is not the merit arithmetic — it is that
`sample_postflop_decision` is also called, byte-for-byte, by
`backend/app/domain/table/range_estimate.py` (the villain-range estimator),
so any new lever that reads hand history or reorders `rng.choices` calls
risks breaking `test_estimator_prices_the_faced_bet` (PR #199) or the
"no new RNG draw" spec constraint, and every WTSD (went-to-showdown) band
this lever would move is a HARD CI gate today.

## 1. Where a bot can CHECK when nobody has bet

**The single decision point.** `sample_postflop_decision`
(`backend/app/domain/personas_postflop.py:1311`) branches on the `legal`
action shapes it is handed (docstring at :1358-1360): unopened (CHECK+BET)
or matched-with-option (CHECK+RAISE) both fall into the `else` arm at
`:1657-1713`. This is the ONLY branch that can produce a CHECK — the facing
node (`:1591-1656`, FOLD+CALL[+RAISE]) never offers CHECK as an action. The
same branch runs on flop, turn and river alike; `street` is read inside it
only to decay a draw's semi-bluff bonus (`_draw_agg_street_mult`,
`:687-703`) and to floor thin value on the river (`_RIVER_BET_FLOOR`,
`_RIVER_RAISE_FLOOR`) — there is no separate "should I stab/probe/barrel"
gate keyed on prior-street history.

**Merit terms that compete, and the pack fields feeding them:**

| Term | Feeds from | Line |
|---|---|---|
| `check_merit = _CHECK_BASE[bucket]` | strength-bucket table only, no pack field | `:1680`, table `:244-252` |
| `agg_merit` (bluff cell) | `bluff_mass` (derived from `pf.bluff_freq`), `pos_mult` | `:1665-1673` |
| `agg_merit` (non-bluff) | `_AGG_BASE[bucket]` + `_DRAW_AGG_BONUS[draw] * _draw_agg_street_mult` , then `* agg_scale` (persona `aggression`) | `:1677-1679`, `:1392` |
| `pos_mult` | `pf.position_sensitivity` (`_position_agg_mult`, `:1200-1204`) — BET leg only, `agg_action is ActionType.BET` gate at `:1664` | `:1200-1204` |
| multiway value damp | `_MW_VALUE_DAMP` per opponent, BET only, `_MW_VALUE_BUCKETS` | `:1684-1685` |
| vulnerable-one-pair slowdown | `_overcard_bet_damp` × `_wetness_bet_mult`, BET + `_VULNERABLE_ONE_PAIR` only | `:1690-1692` |
| river value floors | `_RIVER_RAISE_FLOOR` / `_RIVER_BET_FLOOR`, archetype-uniform (no pack field) | `:1693-1708` |

**No stab/probe/delayed-c-bet field exists.** `PersonaPack.PersonaPostflop`
(`backend/app/domain/content/models.py:300-393`) has exactly one
position-aware aggressor-side lever, `position_sensitivity`
(`:373`, `[0,1]`, applies only to the whole aggressive candidate on the BET
leg, "None → 0.0, keeping un-opted packs identical"). It does not
distinguish "first to act after a check" from "continuing a bet from last
street" — there is no `aggressor_bet_prev_street`-equivalent read on the
aggressive side at all; that signal (`aggressor_bet_prev_street`, derived by
`table/postflop_context.py`'s `aggressor_barrel_run`) is currently consumed
ONLY on the facing-chips side, by the line damp (`_line_scaled`,
`:1207-1230`, `_LINE_SCOPE_BUCKETS` at `:1278-1285`). A checked-down lever
that wants "bet more on the turn/river after checking flop" or "lead more
into a passive field" has no existing pack field to extend — it would need a
new one (see §5).

**`_DRAW_FREE_RIVER_PROB = 0.30`** (`:439`) is unrelated to the bet/check
choice itself — it prices a strong draw's realized equity
(`_strong_draw_realized_equity`, `:1013-1043`) for the CALL side, not the
CHECK/BET side, and per the caller's framing this is to be left as-is
(owner ruling 6), with any follow-up filed against the theory-contract row
that governs it rather than touched by S3-T5.

## 2. The engine loop, and what measures the checked-down path today

**Street advance on check-around.** `advance_to_hero`
(`backend/app/domain/table/play.py:300-341`) is a flat `while` loop: it calls
`bot_decision`, applies whatever `Decision` comes back via `apply()`, and
loops until `state.hand_over`, `to_act_seat is None`, or the hero is up.
There is no branch anywhere in this loop that treats "everyone checked" as a
special case — street advancement to showdown or the next street is entirely
a property of the `HandState`/`apply()` engine underneath (not shown in this
excerpt; out of scope for this map since it is shared table-engine code, not
persona logic). This means a checked-down lever installed in
`personas_postflop.py` needs no engine-loop change — the loop already
advances correctly on any CHECK sequence.

**What would move if bots bet more on checked-down paths:**

- `backend/tests/test_personas_postflop.py::test_persona_postflop_bands`
  (~`:6454`, gate references at `:4046-4063`) — asserts AF (aggression
  factor), fold-to-c-bet, and WTSD against `BANDS` (`:2864-2905`). **All
  three are HARD-today gates** (theory contract, cited below) and all three
  would move: more bets on checked-down streets raises AF directly, and
  fewer checked-through hands lowers WTSD.
- `test_persona_wtsd_ordering_invariants` (`:6848`) — the five HARD/
  TRANSITION-scoped cross-persona WTSD ordering legs (§4 below); a lever
  applied unevenly across personas risks flipping one.
- `_GOLDEN_STATS_N200` (`:3794`) and `_PRE_M3_FIRES` — pinned per-persona
  (AF, FtC, WTSD) fingerprints at a fixed 200-hand sample and seed; ANY
  change to bet frequency on an unopened node re-records these (expected,
  per the slice-3 spec's "expected re-records per behavior ticket" list).
- Coverage baseline and export digests, produced by
  `backend/tools/export_analytics.py` — `went_to_showdown`
  (`:277`, `:286`, keyed off `settlement.showdown_seats`) is written per
  decision row; a lever that reduces checked-through hands changes this
  column's distribution and any digest hashed over it.
- `backend/tools/derobo_gate.py` (the five-seed de-robotization gate) — runs
  a candidate self-play batch through poker-analytics' two §a.5 constraint
  rules: the **separation floor** (nearest-centroid label preservation 6/6,
  min pairwise distance ≥ 0.70× the frozen pre-fix roster's) and the
  **determinism guard** (modal action share < 0.98 in ≥ 80% of decision
  contexts observed ≥ 50 times, `:8-16`). The slice-3 spec explicitly warns
  WTSD is "a large share of pooled distance" and this slice is "the likeliest
  on the roadmap to press the separation floor" (`docs/ai-dlc/specs/
  flywheel-slice3-calldown.md:90-95`) — a checked-down lever is exactly a
  WTSD-moving change and inherits that warning directly.
- `t2-preregistration.md` §1's own instrument — "share of showdown hands
  that never faced a wager," measured at 47.7% (nit) / 44.1% (TAG) / 41.6%
  (LAG) on the band harness's pinned 4,000-hand sample
  (`docs/ai-dlc/research/slice3-calldown/t2-preregistration.md:32-36`) — is
  the one purpose-built statistic for this exact path; a new lever's
  acceptance criterion should almost certainly be stated against it.

## 3. Theory contract and slice-3 spec/contract boundaries

**Theory contract** (`docs/ai-dlc/contracts/persona-realism-theory-contract.md`):

- **Only three stats are HARD-gatable today: AF, Fold-to-C-bet aggregate,
  WTSD** (`:162`). Everything else — including any per-street
  stab/probe/delayed-c-bet split — is DIRECTIONAL-only or HARD-pending; a new
  lever cannot be gated harder than DIRECTIONAL unless it is one of these
  three aggregates.
- **P1 position (IP/OOP) row** (`:76`): applies to "the WHOLE aggressive
  candidate," aggressor-side c-bet/barrel only, OOP continue-realization
  explicitly deferred — this is `position_sensitivity`'s contract row, and
  the only existing row that touches "how often does a bot bet when checked
  to."
- **C-bet band verdict** (`:359-368`): the c-bet band itself is
  `[UNVERIFIED]` on level and **may never become a HARD gate** while
  unverified — a new checked-down lever must not be justified or gated
  against an absolute c-bet-frequency target, only against AF/FtC/WTSD or
  DIRECTIONAL comparisons.
- **WTSD row** (`:202`, `:217-234`): HARD-today, currently under an interim
  regime (grounded floors installed 2026-08-21, ceilings ratcheted per
  ticket) rather than the original engine-anchored bands; §5's note (C6) was
  corrected at slice-3 approval to say the checked-down path — not P3/P8 —
  is where the remaining WTSD movement is expected to come from
  (`docs/ai-dlc/contracts/flywheel-slice3-calldown.md:56-60`, echoing
  theory-contract `:234`).
- No theory-contract row exists for "stab," "probe," or "delayed c-bet" by
  name — the closest analogue is P1 position, street-blind, aggressor-side
  only.

**Slice-3 spec/contract boundary statements**
(`docs/ai-dlc/specs/flywheel-slice3-calldown.md`,
`docs/ai-dlc/contracts/flywheel-slice3-calldown.md`):

- **Hero-grading is a hard, out-of-scope boundary**: `_calibrate_catcher_fold`
  and everything in `backend/app/domain/postflop.py` grade the human
  player's decisions, not villain bots, and are "category error to touch"
  (spec `:103-105`, contract `:9-11`). A checked-down lever must stay inside
  `personas_postflop.py` / `PersonaPack`.
- **No new RNG draw anywhere** — "the action draw stays the FIRST
  `rng.choices` call, sizing second," guarded by `test_nlogit_g6...` capture
  RNGs and the range estimator's key on that draw order (spec `:97-100`).
  This directly constrains how a new lever may be implemented: it must
  reshape existing merits feeding the existing single `rng.choices` call, not
  add a second random draw to decide "bet or check."
- **α fold-ceilings are ceilings only** — no ticket may add a lower-bound
  fold assertion (spec `:101-102`). Irrelevant to CHECK/BET merits directly
  (α governs the facing-chips FOLD side) but signals the general asymmetry:
  this program adds ceilings, not floors, on defensive-side behavior.
  A checked-down lever sits on the aggressive side and is not itself bound
  by α, but should not be defended by an argument that would, by symmetry,
  imply a new fold floor.
- **Separation floor watch**: WTSD is a large share of pooled distance in
  the de-robotization gate; LAG–TAG is the tightest axis post-PR #205 (seed
  604 at 1.23× the required floor) (spec `:90-95`). If a checked-down lever
  binds the separation floor, that is "a stop-and-report, not a tuning
  target."
- **Expected re-records, tolerances never widened**: `_GOLDEN_STATS_N200`,
  `_PRE_M3_FIRES`, coverage baseline, export digests are expected to
  re-record per behavior ticket; exact pins stay exact (spec `:107-111`).

## 4. Hard constraints

- **HARD went-to-showdown ordering legs** (`test_persona_wtsd_ordering_invariants`,
  `backend/tests/test_personas_postflop.py:6848-6920`, docstring), three
  PERMANENT legs that no slice under the interim regime may weaken:
  `station > tag`, `station > lag`, `maniac < station`. Two more legs are
  TRANSITION-SCOPED (pinned against the engine rather than derived from
  grounded targets, and contradict the grounded targets): `fish < tag`, and
  `station - fish > 0.10`. A checked-down lever that changes bet frequency
  unevenly across personas is the most direct way to trip any of these five.
- **The α fold-ceiling test**, `test_fold_to_bet_respects_alpha_ceiling`
  (`backend/tests/test_personas_postflop.py:713`), asserted over
  `_CATCHER_BUCKETS` (excludes ACE_HIGH) via `catcher_fold_by_size`; ceilings
  only, per the spec constraint above. A checked-down lever does not touch
  the FOLD side and should not interact with this test directly, but any
  reshaping of `check_merit` normalization could shift downstream facing-node
  frequencies indirectly if the same node population is later faced with a
  bet more or less often — worth re-running as a smoke check even though it
  is not the primary target.
- **Estimator parity guard from PR #199** — `test_estimator_prices_the_faced_bet`
  (`backend/tests/test_range_estimate.py:661-691`) keys on: (a) the
  estimator's reconstructed price arithmetic matching theory contract §3/§7
  exactly (`f = to_call / pot-before-the-aggression`), and (b)
  **exact parity between `_postflop_action_dist` (the estimator,
  `backend/app/domain/table/range_estimate.py`) and the live sampler
  (`sample_postflop_decision`) at each price**, because both call the same
  function. A new lever avoids tripping this guard by (i) living entirely
  inside `sample_postflop_decision` so both callers inherit it automatically
  — never adding a parallel code path in `range_estimate.py` — and (ii) not
  changing anything on the FACING-CHIPS branch this test exercises (it only
  tests CALL/FOLD merit at three faced prices on TAG, not the unopened
  CHECK/BET branch a checked-down lever would touch). A checked-down lever
  that stays inside the unopened/matched-with-option branch (`:1657-1713`)
  is structurally outside this test's asserted nodes, but should still be
  spot-checked against the estimator, per the contract map's warning that
  "estimator parity is structural, not merely tested"
  (`docs/ai-dlc/contracts/flywheel-slice3-calldown.md:1-13`).
- **Per-seat sizing ecology (slice 1)** — bet SIZES must stay seat-conditional,
  not i.i.d. (`_sizing_dist`, `:878-924`, `sizing_by_node`), orthogonal to a
  checked-down lever (which changes WHETHER a bet happens, not its size) —
  but preserve it if the lever also touches sizing plumbing.

## 5. Where a new pack field would be validated, and default safety

A new lever (e.g. a "stab/probe/delayed-c-bet frequency" field) follows the
exact pattern `position_sensitivity` and `line_sensitivity` already
established:

- **Pydantic model**: add an `Optional[float] | None = Field(default=None,
  ...)` field to `PersonaPostflop`
  (`backend/app/domain/content/models.py:300-393`), following the
  "field ABSENCE is the legacy opt-out" convention already used for
  `continue_ref` (`:421-429`) and `position_sensitivity`/`line_sensitivity`
  (comment at `:370-371`: "None → 0.0, keeping un-opted packs identical").
- **JSON schema**: `content/schema/persona.schema.json` defines a
  `postflop` object with `additionalProperties: false` at its own object
  level (schema block containing `position_sensitivity`, `:144`, and
  `line_sensitivity`, `:124`) — a new field must be added to this schema's
  `properties` block or every pack fails validation, but MUST NOT be added
  to that block's `required` array (`:76`), so existing packs
  (`content/personas/{nit,tag,lag,maniac,passive_fish,calling_station}.json`)
  remain valid without authoring the new key.
- **Byte-identical default**: the engine-side read must guard on the field
  being `None`/absent (mirroring `_position_agg_mult`'s `if not s or context
  is None: return 1.0` at `:1202-1203`) so an unauthored field is a true
  identity no-op — the same "default-off contract" the spec's boundary
  section names for every existing split lever. None of the six shipped
  packs would need to change for this lever to be off; landing the ticket
  and leaving all six packs unedited is the byte-identical baseline the
  slice-3 contract requires before any pack value is tuned.
