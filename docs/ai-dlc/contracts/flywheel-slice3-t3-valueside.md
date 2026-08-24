# Contract map — S3-T3 value-side stack-to-pot lever (improvement slice 3, ticket 3)

S3-T3 is ticket 3 of improvement slice 3 (the calldown-focused slice tracked in `docs/ai-
dlc/tickets/flywheel-slice3-calldown.md`). It adds a stack-to-pot ratio (SPR — remaining stack ÷ pot
size) multiplier to the made-hand aggression path in the villain-bot postflop policy.

**Bottom line.** The insertion point exists and both inputs it needs — `stack_bb` and `pot_bb` — are
already parameters of `sample_postflop_decision`
(`backend/app/domain/personas_postflop.py:1311-1327`) and already flow from `play.py`'s
`bot_decision` (`backend/app/domain/table/play.py:219-286`) with no new threading; the lever is free
on estimator parity because `range_estimate.py`'s `_Ctx` already carries both fields
(`backend/app/domain/table/range_estimate.py:97-138`). But acceptance criterion 1 ("pooled capped-
node composition moves toward the uncapped norm") has **no existing instrument to measure it
against** — no fixture, test, or tool in this repo records the capped-versus-uncapped bluff-share
split; the only reference implementation lived in a design dossier's ad-hoc probe, never committed.
The design seed (Option 1 in `local/session-2026-08-19/dossier-valueside.md`, a machine-local
research file) matches the code: the made-value block at `:1674-1711` has no size or stack term
today, confirming the dossier's central measurement. The top trap is scope: Option 1's text places
the multiplier in the "made-value damp stage... before position and multiway," but the pipeline
already applies position (`pos_mult`) and the multiway damp (`_MW_VALUE_DAMP`) inside that same
block, before the SPR-commit check at `:1731` — the worker must pick an explicit position in the
existing sequence, not assume a separate stage.

## 1. The made-value aggression path

**Signature and call chain.** `bot_decision(state, seat, pack, rng)`
(`backend/app/domain/table/play.py:219`) computes `pot_bb = sum(s.invested_total_bb for s in
state.seats)` (`:243`) and passes `seat_state.stack_bb` (`:286`) through `_postflop_decision`
(`:163-201`) to `sample_postflop_decision(pack, hole, board, legal, pot_bb, stack_bb, opponents,
rng, ...)` (`:182-193`), whose own signature (`personas_postflop.py:1311-1327`) takes `pot_bb:
float` and `stack_bb: float` as its 5th/6th positional parameters — **both are already in scope at
the decision site; nothing must be threaded in.** `advance_to_hero` (`play.py:300`) drives the bot
loop to the hero's turn and delegates to `bot_decision`; it is not a second call site.

**The made-value branch, by street shape.** The function branches on whether the seat faces chips
(`ActionType.FOLD in by_kind`, `:1427`) or is unopened/matched-with-option (`:1657`, the `else`
branch). S3-T3's target is the unopened/matched-with-option BET candidate's non-bluff arm,
`personas_postflop.py:1674-1711`: `agg_merit = (_AGG_BASE[bucket] +
_DRAW_AGG_BONUS[draw]*street_mult) * agg_scale` (`:1677-1679`), then `check_merit =
_CHECK_BASE[bucket]` (`:1680`), then in order: the multiway value damp for `bucket in
_MW_VALUE_BUCKETS = (TOP_PAIR, MIDDLE_PAIR)` (`:868`, applied `:1684-1685`), the overcard+wetness
damp for `bucket in _VULNERABLE_ONE_PAIR` (`:701`, applied `:1690-1692`), the river floors
(`_RIVER_RAISE_FLOOR`/`_RIVER_BET_FLOOR`, `:1697-1708`), and finally `agg_merit *= pos_mult` — the
position multiplier, applied LAST on this arm (`:1711`).

`_AGG_BASE` (`:235-241`, five rungs, MONSTER 0.85 down to a bluff-cell floor) is indexed by
`StrengthBucket` alone — no size term, no stack term, matching the dossier's §2.1 finding that made-
value bet frequency is "exactly flat in stack-to-pot ratio for every bucket below an overpair." This
block covers MONSTER, TWO_PAIR_PLUS, OVERPAIR_TPTK, TOP_PAIR, MIDDLE_PAIR (AIR/ACE_HIGH take the
`bluff_cell` branch at `:1665-1673`, never reaching `_AGG_BASE`). The facing-a-bet RAISE arm mirrors
this at `:1643-1651` (`raise_base = _RAISE_BASE[bucket]`), also with no stack term — in scope only
if "made-value aggression" includes raises; dossier Option 1 scopes to BET only, matching precedent
(`_MW_VALUE_DAMP`, `pos_mult`), and flags BET-vs-RAISE as an explicit worker decision (dossier §5,
Option 1(a)).

**The commitment block — the only existing stack response.** Immediately after, `:1731`: `if
stack_bb / pot_bb <= pf.spr_commit:` — the same two variables, already computed. When true and the
hand is made value (`_RUNG[bucket] >= _RUNG[OVERPAIR_TPTK]`, `:1732`), `_commit_transform`
(`:1175-1186`) multiplies BET/RAISE by the flat `_COMMIT_AGG_BOOST = 3.0` (`:460`) and zeroes FOLD.
`pf.spr_commit` is a per-persona pack field (`content/models.py:392`, 1.2–3.3 across packs, e.g.
`content/personas/lag.json:240` = 3.0) — a single step function, not a continuous response (dossier
§2.2: "one flat step on the two strongest buckets").

## 2. Capped nodes and the measurement gap for acceptance criterion 1

**Where the stack caps the bet.** `engine.legal_actions` clamps the BET/RAISE bracket's `max_bb` to
the seat's remaining stack (per `test_range_estimate.py:1288-1295`'s short-stack fixture: a seat
with 4bb behind gets `BET(min=1.0, max=4.0)`, raise bracket collapses to a jam, `min==max==4.0`,
when a full min-raise is unreachable). A "capped node" is a decision where the drawn wager exceeds
this bracket max and clamps down — downstream of the merit computation in §1 (the merit vector
decides the ACTION; a later size draw, gated after the action `rng.choices` per the RNG draw-order
contract at `personas_postflop.py:1362-1370`, enforced by
`test_nlogit_g6_one_action_draw_then_one_sizing_draw`, `test_personas_postflop.py:9111`, decides the
SIZE).

**No existing instrument measures capped-versus-uncapped composition.** Searched
`backend/tests/test_personas_postflop.py` (~9,000+ lines), `backend/tools/derobo_gate.py`,
`backend/tools/export_analytics.py`, and every other `grep -rn "capped"` hit under `backend/tests/`
and `backend/tools/`: matches are unrelated ("capped at the 4-way tier,"
`test_personas_postflop.py:1763`; MDF discussion, `test_postflop.py:949`; the parity test's short-
stack fixture, `test_range_estimate.py:1326-1380`, one hand at one node, not a pooled statistic).
Dossier §2.3's "PR #199's instrument" (a shim recording the wager actually made, 40,000 hands across
seeds) is reproduced only inside the dossier — its provenance section (§8) states "No repository
file was modified." **A real gap: as scoped, S3-T3's own acceptance criterion 1 has nothing to run
against on day one.** The worker must either build the pooled composition harness as part of this
ticket (dossier §7: capped-node share of the roster's own bluff-share calibration, pooled across ≥3
seeds at 40,000 hands — single-seed standard error is ±0.037, dossier §2.3), or get an explicit
scope narrowing from the ticket owner before claiming criterion 1 met.
`tools/export_analytics.py:61` (imports only `strength_bucket`) and `tools/derobo_gate.py`'s pooled
export path already run multi-seed pooled hands through `sample_postflop_decision`, so extending one
is more tractable than a from-scratch harness — but neither does this today.

## 3. Byte-identity surface

**Where the stack does not bind.** `:1674-1711` is a no-op-by-construction target whenever `stack_bb
/ pot_bb` is deep relative to `spr_commit` — dossier Option 1 (§5) proposes a ramp returning exactly
1.0 above `spr_commit`, tapering only below it, mirroring the existing below-threshold draw damp's
ramp at `:1744` (`c = min(max((spr_commit - stack_bb/pot_bb) /spr_commit, 0.0), 1.0)`). A targeted
test at a deep stack (`stack_bb/pot_bb` above the persona's `spr_commit`, values 1.2–3.3 in
`content/personas/*.json`) should show the multiplier at exactly 1.0, byte-identical merit — the
ticket's own required test ("a multiplier firing at a shallow stack and not firing at a deep one,"
S3-T3 done-condition).

**Fixtures that might move, and why.**

- `_GOLDEN_STATS_N200` (`test_personas_postflop.py:3794`, exact triples at n=200 on a shared RNG
  stream): stream-position-sensitive, not situation-sensitive, so it moves if the multiplier changes
  ANY made-value merit anywhere on the stream's first 200 hands below `spr_commit`. Precedent:
  `docs/ai-dlc/contracts/flywheel-slice3-calldown.md` §5 already documents it as a tripwire
  re-recorded on prior engine changes.
- `_PRE_M3_FIRES` (`backend/tests/test_limper_coverage_belt.py:236`): sibling pin on the same
  stream, historically re-pinned together with the golden.
- Coverage baseline (`backend/tests/test_coverage_baseline.py`, immutable snapshot
  `coverage_baseline.persona-realism-start.json`, theory contract §7): moves if the lever changes how
  far a hand goes (a damped bet becomes a check) — the theory contract names this exact route.
- Export digests (`backend/tools/export_analytics.py`) and the five-seed de-robotization gate's
  separation stat (`backend/tools/derobo_gate.py`, floor 0.70× the frozen baseline pairwise distance,
  artifact id `EXPECTED_BASELINE_ARTIFACT_ID = "a5baseline-98abd160f03a501b"`, `derobo_gate.py:105`):
  both read pooled stats through the same merit path.
- The parity test (`test_no_aggressive_bracket_field_is_read_before_the_action_draw`,
  `test_range_estimate.py:1317`): content should not move (it exercises only AIR) but must be
  re-run — see §4.

**What should NOT move.** Everything on the bluff-cell path (`bluff_cell` branch `:1665-1673`;
`_BLUFF_RAISE_FACTOR`, `_bluff_size_factor`, `bluff_mass`) — the lever scopes to
`_AGG_BASE`/`_RAISE_BASE` only. Dossier §7: "Confirmation that `HEAD_VECTORS` did NOT move — if it
does, the lever is reaching the bluff path and the scope is wrong" (`HEAD_VECTORS` lives in
`backend/tests/test_price_tail.py`, unaffected — its probes run at SPR 10.0 on AIR/ACE_HIGH
fixtures, dossier §5 Option 1(d)).

## 4. Guards that could trip

- **PR #199 parity guard** (`test_no_aggressive_bracket_field_is_read_before_the_action_draw`,
    `test_range_estimate.py:1317-1369`). Keys on: no BET/RAISE bracket field (`min_bb`/`max_bb`) may
    be read inside the merit computation — the estimator's `_legal_from_ctx` leaves those `None`
    (`test_range_estimate.py:1291-1293`, `estimator_bracket[aggressive] == (None, None)`). Confirms
    why the SPR lever is parity-free: `stack_bb`/ `pot_bb` are the estimator's reconstructed chip-
    walk values, already asserted equal to live `HandState` (`range_estimate.py:1-30`, `_Ctx` at
    `:97-138`), not a bracket field. Trips only if new code reads `la.max_bb`/`la.min_bb` off a
    `LegalAction` instead — an avoidable but real mistake given the instinct to reach for "the cap."
- **α fold-ceiling test** (`test_personas_postflop.py`,
    `test_fold_to_bet_respects_alpha_ceiling` at `:713-830`). *(Corrected 2026-08-24: this
    entry also named an "ACE_HIGH mirror" at `:833-978`. That test enforced the per-bucket α
    ruling the owner withdrew on 2026-08-24 and was deleted with it — theory contract
    amendment A9. **No ace-high α assertion remains anywhere in the file**; the α ceiling is
    asserted over `_CATCHER_BUCKETS` only. Those line numbers are now occupied by a
    different test — `test_fold_to_bet_persona_ordering_at_fixed_size` begins at `:833` —
    so locate anchors in that file by name, not by number.)* Out of
    scope directly — gates FOLD merit on the CALL/FOLD facing branch, not the made-value BET path.
    Indirect risk only if the lever changes how many hands reach a later facing node, via the
    coverage-baseline mechanism in §3.
- **LAG went-to-showdown ceiling, 0.59** (`test_personas_postflop.py:2880`, `BANDS["lag"]` WTSD
    tuple `(0.26, 0.59)`). Named as the risk by acceptance criterion 2 and dossier §5 Option 1(d):
    damping value bets at committed nodes converts bets into checks and sends more hands to showdown
    — LAG already measures 0.5775 against this ceiling, ~1.2 standard deviations of headroom. The
    single most exposed band in the slice.
- **HARD aggression-factor / ordering legs.** No separate cross-persona AF ordering test exists — AF
    is gated per-persona in `BANDS[persona]` (`test_personas_postflop.py:2865-2895`,
    `test_persona_postflop_bands`). The three PERMANENT cross-persona legs are WTSD-based, in
    `test_persona_wtsd_ordering_invariants` (`:6848+`): station > tag, station > lag, maniac <
    station (theory contract §7 A4.2 item 4). A value damp that pushes hands to showdown risks
    these, not an AF ordering — read the ticket phrase as "the per-persona WTSD/AF bands plus the
    three WTSD ordering legs."
- **Per-seat sizing ecology (slice 1).** Not touched — S3-T3 reads only `stack_bb`/`pot_bb`, never a
    sizing-bracket or `sizing_dist` field.

## 5. Theory contract §3 as written today, and what the amendment must state

**Current §3 text** (`docs/ai-dlc/contracts/persona-realism-theory-contract.md:35-53`, "Semi-bluff
EV identities"), the load-bearing paragraph:

> "**Bettor bluff-share formula** (RECONCILE RP5-S5 — lead OVERRULED Sol /
> audit §10.1-P5c): the bettor's optimal bluff share of a value bet is `s /
> (1 + 2s)` (where `s` = bet-as-fraction-of-pot). This gives ½=25%, ⅔=28.6%,
> pot=33%, 2×=40%. ... The only wording correction: the engine's
> `_BUCKET_BLUFF_SHARE` is 4 coarse representatives (SMALL=.20, MED=.27,
> LARGE=.32, OVERBET=.375), 'directionally consistent with `s/(1+2s)`,
> coarsened to 4 representatives' — NOT 'exact match at every size.' No
> engine table change."

Also relevant, §7's stacked-multiplier order (`:426`): "base merit → made-value damps (P2,
`_AGG_BASE` only, floor ≥0.25) → street mult (P4, bluff side only) → position mult (P1, whole
candidate) → multiway (P9, geometric)." **No size or stack term** — confirming, from the contract
side, the same absence the dossier measured from the code. (The contract's stated order and the
code's actual order at `:1674-1711` also disagree — code applies multiway `:1684-1685` before
overcard/wetness `:1690-1692` and position last `:1711`, not §7's made-
value→street→position→multiway. Not S3-T3's to fix, but the amendment must not copy §7's order as
the code's.)

**What the "limits" amendment must state**, per the ticket ("document the bluff-share identity's
limits") and dossier §3:

1. **The value-hand side has no lever today** — nothing in `_AGG_BASE`/ `_RAISE_BASE` responds to
   bet size or stack depth (dossier §2.1, §3.1: "the value side is not reachable from the merit
   layer at capped nodes").
2. **SPR dependence is the one exception, and it is a single step** — the commitment block at
   `:1731-1743` boosts OVERPAIR_TPTK+ by a flat 3.0× at or below `spr_commit`, nothing between deep-
   stack and committed regimes (dossier §2.2).
3. **The bluff-side repricing PR #199 withdrew cannot be offset from the value side at capped
   nodes** — dossier §3.1 (~25% required value-side cut against ~10% total available motion,
   including deleting the commitment boost outright) is the load-bearing number to carry forward, so
   a future author does not re-attempt the repricing believing S3-T3's lever unblocks it (dossier
   §6: "What Option 1 does not do, and must not be described as doing").
4. **The identity is a range property, not a per-node property** — a merit-layer lever moves a
   POOLED statistic toward calibration, never satisfies the identity at one decision (dossier §3.2)
   — why criterion 1 needs the pooled multi-seed instrument from §2, not a per-node assertion.

The amendment likely reads as a new row in §4's table (a `P#` per mechanic, P1–P9 at `:74-91`; the
dossier calls this one `P10`, §5 Option 1(c)) plus the limits paragraph after §3's bluff-share text
— exact placement is the worker's drafting choice, not prescribed here.
