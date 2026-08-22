# Tickets — improvement slice 3: calldown

**status: approved**

**Bottom line.** Four tickets, strictly serial (each depends on the one before
it landing), all touching the same two files: the villain-bot postflop policy
module and its test file. S3-T1 (S3 = slice 3; T1 = ticket 1) makes the
strong-draw calling floor tunable; S3-T2 does the bulk of the went-to-showdown
reduction by retuning per-persona calling dials; S3-T3 adds a stack-to-pot
value-side lever; S3-T4 extends an α fold-ceiling guard and conditionally
re-derives one damp constant. Full context, evidence table, and constraints:
`docs/ai-dlc/specs/flywheel-slice3-calldown.md`. Contract map for this
surface: `docs/ai-dlc/contracts/flywheel-slice3-calldown.md`.

**Shared done-condition, run at every ticket's tip:**

```
./scripts/verify.sh
cd backend && ruff check .
cd backend && PYTHONPATH=. .venv/bin/python -m tools.derobo_gate --check --all-seeds
cd backend && PYTHONPATH=. .venv/bin/python -m pytest -k "persona_postflop_bands or wtsd_ordering"
```

**Single-owner hotspots.** `backend/app/domain/personas_postflop.py` (the
villain-bot postflop policy — computes call/fold/raise merit for the six
persona archetypes) and `backend/tests/test_personas_postflop.py` (its
~9,000-line test file) are single-owner for the duration of this slice: only
one ticket's branch may be in flight against them at a time, per the serial
chain below. Do not open S3-T2 until S3-T1 has merged, and so on.

## Dependency order

```
S3-T1 (tunable strong-draw floor) ──> S3-T2 (per-persona dial retune)
   ──> S3-T3 (value-side stack/pot lever) ──> S3-T4 (α-guard extension + conditional damp re-derivation)
```

Strictly serial. S3-T4's damp re-derivation half is conditional on S3-T2
having bought enough headroom (station and lag WTSD down toward their
grounded bands) — if not, S3-T4 ships the guard extension alone and files the
re-derivation as a follow-up with the measured shortfall.

---

## S3-T1 — Make the strong-draw calling weight tunable

**Goal:** replace the strong-draw call-bonus floor so it responds to a
persona's calling dial instead of pinning at dial=1.0 for every tight
persona.

**Do:** `personas_postflop.py:1228-1250` currently reads (paraphrased): when
the draw category is STRONG and `looseness < 1.0`, floor the strong-draw
bonus term at `max(looseness, 1.0)` — so any persona with a dial under 1.0
gets the bonus computed as if its dial were exactly 1.0, making the dial
inert for that term. Replace the floor with a form that still moves with the
dial while preserving a floor on the equity-justified share (design freedom
to the builder). `calling_station` (dial 4.0) must remain byte-identical —
the floor's predicate already excludes dial ≥ 1.0, so this should fall out of
correct implementation rather than need a special case. The `rscale`
CALL:RAISE coupling at `:1643-1646` (the rebalancing term that keeps the
CALL:RAISE ratio stable when the floor used to fire) must be re-derived
against the new form, not assumed to still hold. `_call_merit_at_ref`
(`:1246`) stays the base engine's unfloored merit — do not change what it
computes.

**Acceptance criteria:**
1. A dial sweep (varying `call_looseness` across its range and reading off
   strong-draw call frequency) shows monotonic movement with the dial for
   the five affected personas (nit, tag, lag, maniac, passive_fish).
2. `calling_station` stays byte-identical on the existing guard test
   (`test_nd_t4_calling_station_byte_identical_on_strong_draw` or its
   successor).
3. `rscale` CALL:RAISE coupling re-derived and demonstrated correct at the
   new form, not just left unchanged.
4. Five-seed de-robotization gate green, binding pair (LAG–TAG) reported by
   name with its measured separation.
5. Interim-regime bands green (`test_persona_postflop_bands`).
6. No new `rng.choices` call introduced anywhere in the changed path.

**Done-condition:** the shared done-condition above, plus a targeted test for
the monotonic dial sweep that fails before this ticket's change and passes
after.

**Owns:** `backend/app/domain/personas_postflop.py` (the strong-draw floor at
`:1228-1250` and the `rscale` coupling at `:1643-1646`), `backend/tests/
test_personas_postflop.py`. Single-owner hotspot — see above.

**Dependencies:** none (first in the chain). S3-T2 may not start until this
merges.

**Review tier:** persona-realism theory reviewer + refuter + Codex Sol
(OpenAI cross-family reviewer, high reasoning effort), briefed to derive the
new floor's correctness rather than react to the diff.

---

## S3-T2 — Tune the calling dials toward grounded went-to-showdown, per persona

**status: BUILT (fix round, 2026-08-22) — awaiting review.** The first attempt
was BLOCKED and shipped documents only (pull request #213). The fix round
repaired the two guards that were measuring the calling dial rather than their
own claim, retuned the nit (0.45 → 0.32) and the TAG (0.6 → 0.38), and withdrew
the LAG's floor on owner ruling 11 of 2026-08-22, leaving the LAG at 0.55: its
dial does move it, but through cross-persona coupling, so the effect depends on
the companions' dials — filed for an owner decision on whether to tune it in a
follow-up. Registered floors MET on the band harness: nit −1.80
percentage points against a floor of 1.0, TAG −6.15 against 3.5. Report:
`../research/slice3-calldown/t2-fix-round-report.md`.

**Goal:** move nit, tag, and lag's went-to-showdown rate down toward their
research-grounded bands by retuning `call_looseness` pack values, without
breaching any HARD ordering constraint between personas.

**Do:** adjust `call_looseness` values in `content/personas/*.json` (pack
values only — no new constants in code), largest gaps first: nit, tag, lag.
Each persona must move DOWN toward its grounded band. HARD ordering legs
(statements that one persona's statistic must exceed another's) that may
never be breached: station's went-to-showdown rate exceeds tag's, station's
exceeds lag's, maniac's stays below station's. Two transition-scoped legs —
fish's rate stays below tag's, and station's rate exceeds fish's by more than
0.10 — may each be moved ONCE, with the movement's measurement, direction,
and the grounded pair it moves toward all recorded in the pull request. After
the ticket, the interim regime's ceiling ratchet (ceilings move down by
measurement + 3 standard deviations, rounded outward, never above the
incumbent) must be reapplied and the arithmetic recorded.

**The reduction target is pre-registered after S3-T1's dial-sweep data
exists, not before** — pre-registering an exact number at spec time, before
the sweep shows how much headroom S3-T1 bought, would be fake precision. The
ticket's author registers the target in the pull request description before
building against it.

**Acceptance criteria:**
1. Band-harness went-to-showdown for nit, tag, and lag reduced by the
   pre-registered amount (see above).
2. No persona's aggression-factor or fold-to-continuation-bet leg leaves its
   band as a side effect.
3. Five-seed de-robotization gate green, LAG–TAG pair reported explicitly.
4. Pooled export went-to-showdown (the 50,000-hand diagnostic instrument,
   not the gating instrument) reported before/after as diagnostic context.
5. Any HARD ordering leg breach is a stop-and-report, not a tuning target to
   work around.

**Done-condition:** the shared done-condition above. Expect this ticket to
produce the largest golden re-record of the slice (pinned statistical
fixtures — `_GOLDEN_STATS_N200`, `_PRE_M3_FIRES`, coverage baseline, export
digests — moving because the dials moved); each re-record needs provenance
and a revert-to-prove-attribution check.

**Owns:** `content/personas/*.json` (calling dial values only),
`backend/tests/test_personas_postflop.py` (band assertions and any new
targeted test). Single-owner on the test file — see hotspot note above.

**Dependencies:** S3-T1 must be merged first (it is the prerequisite that
makes the strong-draw weight tunable at all).

**Review tier:** persona-realism theory reviewer + refuter + Codex Sol
(high reasoning effort).

---

## S3-T3 — Value-side lever: stack-to-pot multiplier on made-value aggression

**status: BUILT (2026-08-22) — awaiting review.** All five acceptance criteria
pass. The lever ships as `_value_spr_mult`, no persona pack changed, and the
theory contract gained amendment A8 in the same branch. **Read the report's
headline before the criteria table:** the composition defect the ticket aimed at
is 5.45 percentage points wide and this lever moves 0.10 of it, because the gap
is mostly ARRIVAL — capped decisions are reached by stronger ranges — which no
merit-layer lever can touch. That finding, and the reason the withdrawn
bluff-side repricing still cannot be offset from the value side, are what
amendment A8 exists to carry forward. The instrument criterion 1 needed did not
exist and was built here: `backend/tools/capped_composition_probe.py`. Report:
`../research/slice3-calldown/t3-report.md`; the directions registered before the
multiplier was written: `../research/slice3-calldown/t3-preregistration.md`.

**Goal:** add the one approved new lever from the slice-2 reviews — a
minimal stack-to-pot ratio multiplier on made-value aggression — closing the
missing value-hand side of the theory contract's bluff-share identity (the
formula tying a bettor's bluff frequency to bet size, which currently has no
lever on the value-hand side).

**Do:** implement the multiplier reading only stack and pot size (no bracket
fields — see the parity note below). Spec seed for the exact form:
`local/session-2026-08-19/dossier-valueside.md`, Option 1 (a machine-local
research dossier, not committed to this repo). Amend
`docs/ai-dlc/contracts/persona-realism-theory-contract.md` §3 in the same
pull request to document the bluff-share identity's limits — this is the
sibling amendment named in the owner-ratified went-to-showdown amendment
draft's Part V.

**Parity-free by construction:** because the lever reads only stack and pot
(no bracket fields — the sizing-bracket data the villain-range estimator
also reads), PR #199's parity guard (the test keeping the estimator's math
in sync with the live bot's) cannot trip.

**Acceptance criteria:**
1. Pooled capped-node composition (the mix of actions at decisions where the
   stack size caps the bet) moves toward the uncapped norm, in the
   pre-registered direction, measured pooled-across-seeds or paired
   before/after — never on a single seed.
2. LAG went-to-showdown ceiling watched explicitly (0.59 incumbent at spec
   time; may be lower by this ticket's tip if S3-T2's ratchet moved it).
3. Five-seed de-robotization gate green.
4. Byte-identity preserved wherever the stack does not bind (i.e., wherever
   this lever is a no-op by construction).
5. Contract §3 amendment lands in the same pull request, not deferred.

**Done-condition:** the shared done-condition above, plus a targeted test
showing the multiplier firing at a shallow stack and not firing at a deep
one.

**Owns:** `backend/app/domain/personas_postflop.py` (made-value aggression
path), `backend/tests/test_personas_postflop.py`,
`docs/ai-dlc/contracts/persona-realism-theory-contract.md` (§3 amendment
only). Single-owner on the postflop module and its test file — see hotspot
note above.

**Dependencies:** S3-T2 must be merged first (serial chain).

**Review tier:** persona-realism theory reviewer + refuter + Codex Sol
(high reasoning effort).

---

## S3-T4 — α-guard extension over ACE_HIGH, plus conditional damp re-derivation

**Goal:** extend the existing α fold-ceiling guard (a poker-theoretic upper
bound on how often a hand class should fold) to cover the ACE_HIGH bucket
(naked ace-high, no pair or draw) on the river call leg, honoring the
2026-08-19 owner ruling that α already bounds that bucket. Then, only if
S3-T2 bought enough headroom, re-derive the `_ACE_HIGH_RIVER_CALL_DAMP`
constant.

**Do:** extend the guard's scope — currently limited to the test-only
`_CATCHER_BUCKETS` constant, which excludes ACE_HIGH — to include the
ACE_HIGH river call leg. Confirm the guard is non-vacuous: it must fail under
a deliberate damp inflation (a test that artificially raises the damp beyond
what α allows and confirms the guard catches it), not merely pass by
construction.

**Then, conditionally:** if S3-T2's measured result shows station and lag
went-to-showdown moved down toward their grounded bands (headroom bought),
re-derive `_ACE_HIGH_RIVER_CALL_DAMP` against the then-current river price
distribution, per the owner-ratified amendment draft's section III.2
conditions: re-measured minimum-defence obligation (the game-theoretic floor
on how often a bluff-catcher must call to prevent profitable bluffing), the
resulting river continue rate, and the interim ceiling ratchet reapplied. If
headroom does not exist, ship the guard extension alone and file the
re-derivation as a follow-up with the measured shortfall recorded — do not
force the re-derivation through without headroom.

**Acceptance criteria:**
1. Guard is non-vacuous (fails under deliberate damp inflation, as above).
2. Guard extension covers the ACE_HIGH river call leg with no change to
   AIR's existing zero.
3. If the conditional re-derivation fires: new damp value derived from the
   re-measured price distribution, minimum-defence math shown, ratchet
   reapplied and recorded.
4. If the conditional does not fire: pull request states the measured
   shortfall and files the re-derivation as a follow-up.
5. Five-seed de-robotization gate green; interim-regime bands green.

**Done-condition:** the shared done-condition above.

**Owns:** `backend/app/domain/personas_postflop.py` (the ACE_HIGH river call
leg and, conditionally, `_ACE_HIGH_RIVER_CALL_DAMP`),
`backend/tests/test_personas_postflop.py` (`_CATCHER_BUCKETS` extension and
the non-vacuity test). Single-owner on both files — see hotspot note above.

**Dependencies:** S3-T3 must be merged first (serial chain); the damp
re-derivation half further depends on S3-T2's measured headroom.

**Review tier:** persona-realism theory reviewer + refuter minimum; add
Codex Sol (high reasoning effort) if the damp re-derivation fires.

---

## Slice close

Per the spec's verify-by: pooled and per-persona went-to-showdown from both
instruments (band harness and 50,000-hand export), before/after across the
full chain, plus the owner's blind play session — which outranks the gate
numbers under the standing 2026-08-17 ruling that blind play is the primary
acceptance evidence for a slice, not a passing gate alone.
