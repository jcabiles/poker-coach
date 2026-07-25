# Persona Realism — Roadmap (created 2026-07-23)

> Living, pass/fail, resumable. A fresh context reads this + the two source docs and knows exactly what's left.
> **Engine contract map (READ FIRST):** `docs/research/12-persona-engine-and-realism-fixes.md`
> — every lever, merit table, formula, line anchor, and INVARIANT. This roadmap is the *decomposition*.
> **The theory contract (READ FIRST — every "contract §N" citation below resolves here):**
> `docs/ai-dlc/contracts/persona-realism-theory-contract.md` — §2 fit-seed law, §4 P-invariants, §5 the
> keystone target table, §7 joint calibration, §9 the correction ledger, §10 reference pool, §11 the
> auto-FAIL checklist.
> **Grounded numbers (magnitudes):** `docs/ai-dlc/research/persona-realism-audit-2026-07-24.md` §10
> (prescriptions P1–P9) — a merit multiplier is a FIT SEED, never a drop-in constant (softmax law).
> **Full-scope backlog (superset, local/uncommitted):** `docs/ai-dlc/research/persona-realism-FULL-BUILDOUT.md`
> — every buildable item (Tracks A–H, Phases 0–9), findings-coverage map, owner forks. This roadmap is the
> *committed subset* of that backlog. Roadmap-structure debate + hardening gates:
> `docs/ai-dlc/research/persona-realism-artifacts/roadmap_debate/DEBATE.md`.
> Parent roadmap: `docs/ai-dlc/roadmap/simulate-table.md`.
>
> **Resume rule:** work waves in order; verify a slice's pass/fail ACTUALLY passes before `[x]`
> (agents falsely mark work done). Hand ONE slice at a time to `/ai-dlc`. Every slice gets a fresh
> `refuter` at fan-in (maker ≠ checker).

### F-namespace legend (READ BEFORE RESOLVING ANY `F#`) — added 2026-07-25

Three different F-numberings collide across the source docs. **Every `F#` in this roadmap is now tagged**;
an untagged `F#` in a ticket, spec or review comment is a defect — resolve it before acting.

| Tag | Namespace | Where defined |
|---|---|---|
| `audit-F#` | the **20 audit findings** F1–F20 | `persona-realism-FULL-BUILDOUT.md:451` (*"F1–F20 = the 20 audit findings"*) |
| `track-F#` | the **build-out Tracks** F1 seam intake · F2 concept cards · F3 GTO baseline (· F4 exploit-coaching · F5 persona sub-types) | `persona-realism-FULL-BUILDOUT.md:306-317` |
| `doc12-F#` | a **third** F-list — F1 elasticity, F6 aggression-scalar, F8 SPR-binary | `docs/research/12-persona-engine-and-realism-fixes.md` §5 |

**The committed theory contract resolves F-numbers against the `audit-` namespace ONLY.** Each mixed tag
costs a future slice one mis-resolved gate — so `track-F1` (seam intake) ≠ `audit-F1` (position ignored
postflop, fixed in W3-b), and `doc12-F6`/`doc12-F8` ≠ `audit-F6` (river bet floor, shipped W1-a) /
`audit-F8` (busted-draw river bluff, shipped W3-c).

---

## Decisions locked (2026-07-23 interview) — what this roadmap commits to

The narrow 2026-07-23 scope lock (stop before position / stack-depth / texture) is **RE-OPENED**. The grounded
research re-promotes those to core. This roadmap now holds the **full grounded program** as NOW/NEXT slices and
the **deferred/architecture tail** as typed Later bets. Specifically:

1. **Scope = full program, tail as Later.** Grounded prescriptions → NOW/NEXT; opener-position, villain-range
   rungs b/c, blockers, exploit-coaching, 5+way multiway → Later bets.
2. **Villain-range rung (a) is COMMITTED to NEXT** — a coarse static preflop-range-by-position *lookup* (data, not
   a solver; stays no-solver-compliant). It unlocks the barrel-more-on-scare-cards pilot and "facing a [type]"
   reads. Rungs (b) persona-conditional prior and (c) full equity-vs-range estimator stay Later.
3. **All four hardening gates adopted:** (D7) a new metric must show the expected direction before its slice can
   close; (D8) a seeded node-trace pack catches "right stat, wrong reasoning"; (D9) a human-realism playtest
   before the final band re-anchor; (`track-F1`) every mechanic slice files a coaching seam-row.
4. **Coaching seam-feeds the active teacher-rework** — concept-card candidates + a cleaner GTO grading baseline
   ride on landed mechanics (no new coaching roadmap, no collision). Full exploit-coaching is a Later ticket.

**Defaults applied (veto any at the approval gate):** opener-position-aware defense (needs schema+plumbing) →
Later · WTSD downward re-anchor → accepted, once, at W4 close · out-of-position realization damp → Later · commit-
factor spread → let the elasticity split carry separation first, widen the `D` exponent only if measured too weak ·
reference pool stays **online low-mid 9-max ~100bb**.

> **CORRECTION 2026-07-25 (C1).** The clause that used to follow the reference pool — *"the whole keystone is
> calibrated to it"* — was **FALSE**. The pool itself is unchanged, but the keystone was **not** calibrated to it:
> the §5 preflop VPIP/PFR rows carried **6-max** values and were corrected 2026-07-25 (theory contract §9 ledger
> #14). The **postflop** rows (c-bet, fold-to-c-bet, AF, WTSD, turn barrel) remain **UNVERIFIED for table size** —
> two of them are wired as HARD CI gates today. Auditing them is slice **W5-a2**; until it lands, treat every §5
> postflop row as DIRECTIONAL-only. (See also C14/C29 below and the whole **W5** wave.)

---

## North-star outcome — the WHY

- **Primary:** *the six villain bots make decisions that match their real-world archetype* — so the
  Simulate table teaches transferable reads instead of training the hero against unhinged, streetless bots.
  **Metric:** each persona's computed facing-a-bet distribution matches its archetype's documented shape —
  polarized rivers, archetype-correct fold-to-size elasticity, no off-archetype open-limps, no literal
  no-pair-no-draw calls, position/street/stack-aware lines.
  **Baseline (measured, doc 12):** maniac raised one pair on the river 38–54% and called busted air 23%;
  station called pure air 78%; fish & station differed only by a uniform stickiness shift (no shape
  difference); every response node was position/size/street-blind. → **Target:** river raises come only from
  `TWO_PAIR_PLUS+` / bluff-cell; air-call ≈0 without a draw; station fold-rate ≈flat across bet sizes while
  fish is fit-or-fold; **bots play differently from different SEATS** (blind-vs-middle-position defence,
  seat-appropriate continue frequencies, position-conditioned open widths); turn ≠ flop. All six personas.
  **Runnable metric — measured on the harness that EXISTS (R5, 2026-07-25):** the per-persona distributions
  computed by `_persona_stats_ext` / `ExtStats` (`backend/tests/test_personas_postflop.py:2147,2167`) plus the
  committed fixture suites — the uniform-range size-slope fixture `fold_by_size`
  (`backend/tests/test_personas_postflop.py:511`), the arrival-range FtC harness
  (`backend/tests/test_arrival_range_ftc.py`, W3R-0), and the `BANDS` population checks. Each slice adds its
  assertions **into those existing suites** with explicit thresholds + tolerances: river bucket→action
  distributions, size-response slopes (fold-rate vs bet size), per-seat preflop deltas, conditional barrel/give-up
  rates. That committed assertion set, not prose like "≈0 / roughly flat", is what "matches its archetype" means.
  **There is no separate "persona-distribution test module" and no slice creates one** — the earlier wording named
  an artifact nobody owned; the harness above is the artifact. Population VPIP/PFR/AF/WTSD stats stay a
  **secondary** regression check.
  **Metric owner (C2, 2026-07-25; RE-SCOPED 2026-07-25 per owner decision D1):** the metric used to require
  *"bots answer a UTG open differently from a BTN open"* — that is the **OPENER**-position axis, which genuinely
  needs a schema change + sampler plumbing (contract §9 #5) and is parked in LATER as **E1-b**. The success
  criterion therefore depended on unplanned work. It is now restated on the **ACTOR**-position axis (which seat
  the bot is sitting in), owned by **W5-b2** (+ W5-b3 for open widths). **Opener-awareness is EXPLICITLY OUT of
  the current success criterion** — a recorded reduction in ambition, not a quiet drop; it stays E1-b in LATER
  and returns to the north-star only if that bet is promoted. Promoting W5-b2 does **not** close the old
  opener-axis metric; it satisfies the re-scoped actor-axis one.

## Why this is one initiative, not six persona fixes

The **same root causes** drive every symptom (doc 12 §5, §9): the postflop engine is **context-blind** — one
shared merit table × 5 scalar levers, with no input for position, board texture, street, stack depth, or villain
range. So the fixes below repair **all six personas at once**; the aggressive three (maniac/LAG/TAG) are just
where the damage is loudest.

---

## Cross-cutting discipline — applies to EVERY opting-in slice

### Softmax law (anti-cosmetic-change) — NON-NEGOTIABLE
The engine normalizes merits into probabilities, so a merit multiplier is **NOT** the observed frequency change.
Every magnitude in §10 / the build-out is a **FIT SEED**: measure the observed stat → adjust the merit → re-measure.
Dropping in "×0.75 / ×0.50" or a fixed fold-reduction as-is ships a **cosmetic** change. No slice closes on
"the constant is in the code"; it closes on "the observed stat hit its target band."

### Metric Definition-of-Done gate (D7 — hardening gate)
A slice that needs a NEW harness metric to prove its effect **cannot close until that metric is live AND showing
the expected direction** (e.g. the IP-vs-OOP c-bet delta must exist and move before the position slice closes).
This converts "directional-until-built" from an open IOU into a per-slice exit criterion.

### Node-trace realism pack (D8 — hardening gate, anti-degeneracy)
A lightweight seeded-replay pack: fixed hands per persona across IP/OOP, overcards, turn barrel, busted draw,
multiway, high-commitment spots — logging bucket, draw class, merits, chosen action, intended prescription. Catches
"**right stat, WRONG node**" (a maniac hitting its aggression number by over-valuing made hands instead of
bluffing). Built in W0; each behavior slice adds its spots. Scope = seeded replay + merit log, NOT a new framework.

### Human-realism playtest checkpoint (D9 — hardening gate)
Blinded seeded replays + short free-play with 2–3 poker-literate reviewers. Acceptance = reviewers distinguish
archetypes above chance AND flag no recurring persona-breaking lines. Runs at **W3.5**, after the context
mechanics and BEFORE the final band re-anchor, so "feels human" feedback informs the fit. Stats-conformant ≠
line-coherent.
**Amended 2026-07-25 (C10) — acceptance must also be ABSOLUTE, not only relative.** "Above chance" is a *relative*
test, so **a roster uniformly shifted ~4 VPIP points tight passes it** — which is what happened. Every D9 run now
also asks, per persona: *"what format and stakes does this player's range suggest, and would you seat them at 9-max
full ring?"* (See W3.5, which also gains **W5-c3** as a prerequisite.)

### Coaching seam intake (`track-F1` — hardening gate)
> ⚠️ Code collision: this hardening-gate **`track-F1`** (seam intake) is NOT **`audit-F1`** (position ignored
> postflop, which this roadmap fixes in W3-b), and is NOT **`doc12-F1`** (elasticity). Same string, three unrelated
> referents — see the F-namespace legend at the top and disambiguate on hand-off.
Every mechanic slice files a structured seam-row (mechanic · concept-card candidate · baseline stat moved ·
example replay seed · source test · owner · status) into the `professional-teacher-rework` **Next** column as
accepted / deferred-with-reason. **A slice isn't done until its seam-row is filed.** Batch handoff at W4 close.

### Range-estimator parity — for any slice that makes the LIVE bot diverge (Codex-Sol HIGH)
`range_estimate.py:278` recovers the villain's action distribution by **replaying the persona policy** with a
capture-rng. "Keep `range_estimate` byte-identical" holds **only for un-opted-in direct callers**. The moment a
slice makes the live bot diverge from the streetless policy, the estimator MUST be threaded the **same** context
and re-tested for **parity with the live policy** — else the villain-range reveal feature silently lies. Each such
slice owns extending the estimator's replay context + a parity test. The action draw stays the FIRST `rng.choices`.

### Baseline & calibration discipline (anti-laundering)
Re-recording `coverage_baseline.json` every slice replaces the comparator, so small repeated losses can vanish.
Rule: an **immutable initiative-start snapshot** (`coverage_baseline.persona-realism-start.json`) exists; each
slice re-records the operational fixture for CI green **and** reports the CUMULATIVE graded-coverage delta vs the
immutable snapshot; any cumulative loss needs explicit adjudication. The **W4 pass** does the ONE authoritative
combined population-band re-anchor after the whole spine converges (don't chase bands across waves).

---

## NOW — the grounded program, as spec-ready vertical slices

### Wave plan (dependency order from the build-out §4)
**W0 foundation** (denominator + measurement + anti-degeneracy infra — unblocks honest gating for all of NOW)
→ **W1 low-risk wins** → **W2 identity + EV** → **W3 context** (plumbing → position/street/texture)
→ **W3R bot-review remediation** (2026-07-24 hand-history review — full 14-fix program; harness-first)
→ **W5-A / W5-C foundation** (target provenance + measurement repairs + engine correctness)
→ **remaining W3R tail** (W3R-4b, W3R-5, W3R-7) → **W5-B preflop range width**
→ **W3.5 human-realism checkpoint** (blinded, on remediated bots) → **W4 commitment brake LAST + single band re-anchor + seam batch**.
All postflop-mechanic slices own `personas_postflop.py` ⇒ they run **serially** on that spine. The commitment
brake is sequenced LAST (highest regression risk; it must layer on the stabilized price/fold equation, not force
re-tuning). Every slice: default-off byte-identity for un-opted-in direct callers until the live loop opts in.

**Wave-order correction (R3, 2026-07-25) — W5-A and W5-C PRECEDE the W3R tail.** The earlier order
(`W3R → W5`) was inverted against the actual dependency graph: **W3R-5 depends BACKWARDS into W5**
(`Depends-on: W5-a3-iii, W5-c2`) and **W3R-4b absorbs W5-c1**. The resume rule ("work waves in order") therefore
resolves to: finish the already-landed W3R head → **W5-A + W5-C** → **W3R-4b / W3R-5 / W3R-7** → **W5-B** →
W3.5 → W4. W5-B is independent of the W3R tail (JSON only) and may run alongside it.

**W5 concurrency (C13; AMENDED R1, 2026-07-25):** **W5-A** (docs/tests) and **W5-B**
(`content/personas/*.json`) touch **disjoint file sets and run in parallel**; within W5-B, serialize per pack (one
owner per JSON file). **W5-C is no longer a fully-disjoint group:** after W5-c1 was deleted into W3R-4b (it edited
`_made_bucket` in the `personas_postflop.py` serial spine), **W5-C's only genuinely disjoint slice is W5-c3**
(`backend/app/services/sim_session.py`). **W5-c2 is NOT disjoint** — it edits
`backend/app/domain/texture.py`, which is imported by `personas_postflop.py` (the spine), by
`backend/app/domain/postflop.py:39` (the **grader**) and by `backend/app/domain/srs.py:128` inside the **frozen**
`spot_signature()` — so it serializes against the spine and carries the frozen-invariant no-gos below.
The **W3R-5 re-spec** runs on the `personas_postflop.py` spine and stays **serial** with the rest of W3R.

**Contract-status record (C14) — do NOT edit the contract from this roadmap; that is W5-a2's deliverable.**
§5's **postflop** rows are **UNVERIFIED for table size** and therefore **DIRECTIONAL-only**; the two CI gates built
on them (**fold-to-c-bet**, **AF**) are demoted **HARD → no-regression** until sourced.

---

### ✅ DONE

- [x] **P1 — Correctness patch (fold-aces, open-limps, oversized 3bet, air-calls, dead-mix guard).** ✅ 2026-07-23
      Branch `feat/persona-realism-p1` (#83). Station no longer folds AA/KK/AKs unopened; maniac/LAG non-SB
      open-limps deleted; maniac `threebet_mult`→~3.3; maniac vs_4bet re-jams lighter/trappier than LAG;
      `_CALL_BASE[AIR]` 0.25→0.08 (street-neutral base drop); dead-mix validator + CI guard. Suite green,
      coverage 28.3→29.4%. (`tanh`-saturation `aggression` re-author deferred → NEXT.)

- [x] **P2a — Street-aware refactor + river polarization (keystone).** ✅ 2026-07-23
      Branch `feat/persona-realism-p2a` (#85). Added the `street` kwarg (default byte-identical); floored river
      RAISE for {MIDDLE_PAIR, TOP_PAIR, OVERPAIR_TPTK} + air-CALL to 0; `play.py` + `range_estimate.py` opt in
      (estimator-parity test green). Bands re-anchored (WTSD/AF). **Note the residue for W1:** P2a floored the
      river *raise*; the unopened river one-pair **BET** floor (MIDDLE_PAIR only) is still open → slice W1-a below.

---

### W0 — foundation (measurement + shared inputs + anti-degeneracy)

- [x] **W0-a — Shared pot-before-aggression denominator (A1).** ✅ 2026-07-24 (PR #91, `7435550`). *ICE 7·9·8 — small, shared.*
      **Problem:** the commitment gate (W2), the semi-bluff EV math (W2), and the faced_frac fix (W1) all need
      "the pot before the current bet/raise" + the latest aggressor's increment; a wrong denominator silently
      corrupts every EV threshold downstream.
      **Solution:** one domain-pure helper reconstructing pot-before + latest-aggressor increment from
      `state.action_history` (already at the `play.py` call site). No DB, no new state.
      **Pass/fail:** a self-re-raise unit test returns the correct pre-aggression pot; every existing suite stays
      byte-identical (pure add, no consumers yet). **No-gos:** domain purity; don't rewire the action draw.
      **Appetite:** ~1 small slice.

- [x] **W0-b — Harness metric scaffolding + Definition-of-Done gate (D1–D7).** ✅ 2026-07-24 (PR #92, `f1e1329`) — all six metrics compute (`ExtStats` / `_persona_stats_ext`, `backend/tests/test_personas_postflop.py:2147,2167`) but only **smoke-assert** today; promoting rows to HARD is W5-a3-iii's §6 refresh. *ICE 8·8·5 — infra, walking skeleton.*
      **Problem:** the harness measures only 3 stats today (AF, fold-to-cbet, WTSD). Six grounded mechanics can't
      be *honestly* gated without new metrics — so their acceptance would be prose, not a test.
      **Solution:** add the metric framework + six metrics: CBet-flop overall (D1), W$SD (D2), VPIP/PFR/gap joint
      (D3), size-bucket Fold-to-C-bet curve (D4 — the elasticity test), IP-vs-OOP C-bet split (D5), turn-barrel%
      (D6). Wire the **metric-DoD rule (D7)**: a downstream slice may not close until its metric is live + directional.
      **Pass/fail:** each metric computes on the existing fixture and emits a value; the DoD rule is documented in
      this file and referenced by the slices that depend on it. **No-gos:** measurement only, no behavior change;
      don't re-anchor any band here. **Appetite:** ~1 large slice (can sub-split per metric at `/ai-dlc`).

- [x] **W0-c — Node-trace realism pack (D8) + harness-fit loop doc (D11).** ✅ 2026-07-24 (PR #93, `5f4bd2b`). *ICE 7·8·6 — infra, anti-degeneracy.*
      **Problem:** stat-conformant bots can still play incoherent lines ("right stat, wrong node"); and the softmax
      law means every magnitude is a fit loop that must be repeatable.
      **Solution:** the seeded-replay + merit-log pack (D8) with an initial spot set; a short documented fit loop
      (measure → adjust seed → re-measure) + the single-end-of-cluster re-anchor rule (D11).
      **Pass/fail:** the pack runs and logs bucket/draw/merits/action/prescription for the seed set; the fit-loop
      doc exists and is linked from each mechanic slice. **No-gos:** lightweight (no new framework). **Appetite:** ~1 slice.

### W1 — low-risk wins (small, contained, some infra already present)

- [x] **W1-a — River one-pair BET floor, MIDDLE_PAIR only (B8, fixes `audit-F6`).** ✅ 2026-07-24 (feat/persona-realism-w1).
      `_RIVER_BET_FLOOR=(MIDDLE_PAIR,)`; the named byte-identity test split (theory H1); slice-authorized
      seeded-fixture re-records (golden AF/WTSD, coverage 30.4%, limper belt) — tolerance BANDS stay frozen to W4-b.
      *ICE 7·8·7 — small; re-anchors bands.*
      **Problem:** P2a floored the river *raise* but the unopened river **BET** for a middle pair (a bluff-catcher,
      never a value bet) is still not floored.
      **Solution:** `_RIVER_BET_FLOOR = (MIDDLE_PAIR,)` — floor the unopened river BET for MIDDLE_PAIR ONLY; strictly
      narrower than the existing raise-floor (which also covers top pair). Reframe as a conservative HU/balanced-villain
      DEFAULT (middle pair CAN value-bet vs capped/station ranges — a rank approximation, not a theorem).
      **Pass/fail:** middle-pair river unopened BET → 0 (committed unit assertion); top-pair/overpair BET untouched
      (assertion split). **The population WTSD/AF band re-anchor is DEFERRED to W4-b** (§10.4: P5 ships behind the
      unit-assertion split ONLY — re-anchoring here would re-fit bands that W2/W3 then move again). **No-gos:** don't
      touch the raise-floor P2a set; MIDDLE_PAIR only; no band edits pre-W4. **Appetite:** ~1 small slice.

- [x] **W1-b — faced_frac increment fix + backwards comment (B9, fixes `audit-F9`).** ✅ 2026-07-24 (feat/persona-realism-w1).
      ENGINE-ONLY (Codex #1: the estimator builds CALL min_bb=None → numerator 0 → the denominator fix is inert
      there, so NO `_Ctx`/estimator change was needed). play.py threads the W0-a increment; comment direction fixed
      (OVERSTATES); self-re-raise + back-raise + fresh-identity + wiring tests. **Follow-up spun out → Later:
      the estimator is faced-price-BLIND (numerator 0) — a pre-existing approximation; giving it a real to_call is a
      separate, higher-blast-radius slice.** *ICE 7·9·8 — small, genuinely low-risk.*
      **Problem:** on same-street re-raises the faced-price denominator uses the whole bet-to instead of the latest
      aggressor's increment → over-states price → over-folds; the in-code comment documents this backwards.
      **Solution:** use the A1 latest-aggressor increment as the same-street re-raise denominator; fix the comment.
      **Depends-on:** W0-a. **Pass/fail:** existing faced_frac tests 563/577 stay green (they cover fresh raisers
      only); a NEW self-re-raise test proves bots over-fold slightly less to 3-bet wars. **No-gos:** don't change
      fresh-raiser behavior. **Appetite:** ~1 small slice.

- [x] **W1-c — Multiway made-value tightening (B10, fixes `audit-F13`).** ✅ 2026-07-24 (feat/persona-realism-w1).
      `_MW_VALUE_DAMP=0.8` (unfit directional seed) on TOP_PAIR/MIDDLE_PAIR unopened BET only, capped at the 4-way
      tier; HU byte-identical; monotone+plateau test via exact captured weights. *ICE 6·7·8 — small, directional.*
      **Problem:** value-betting is opponent-count-blind — made hands barely tighten as more players see the flop.
      **Solution:** a geometric damp `~0.8**(opp−1)` (FIT SEED) on made-value aggression as opponent count rises;
      HU byte-identical; cap at a **labeled 4-way tier** (5+way magnitudes are unresearched — Later).
      **Pass/fail:** made-value aggression non-increasing in opponents (monotone test); HU byte-identical.
      **No-gos:** don't extend past the 4-way label; directional-only until a multiway metric exists. **Appetite:** ~1 small slice.

### W2 — persona identity + EV correctness

- [x] **W2-a — Elasticity split: `stickiness` → `call_looseness` + `size_elasticity` (C1, fixes `audit-F10`).** ✅ 2026-07-24 (PR #95, `abe2ea9`) — *ICE 8·7·5 — the keystone identity fix.* Two optional levers, default-off byte-identical; opt-in `size_elasticity` uses a DIRECT exponent (0 = size-blind, fixing the `0**-DAMP` crash + direction reversal a naive rename caused — fan-in catch). Station `size_elasticity 0.0` (flat fold-curve), fish `1.3` (steep). Fixtures re-recorded (shared-table); bands frozen.
      **Problem:** one dial controls **both** how loose a persona calls **and** how much bet size scares it, so you
      can't make the **station inelastic-but-loose** (calls any size) while the **fish is elastic-but-scared**
      (fit-or-fold) — the one axis that *defines* their difference is welded shut.
      **Solution:** two optional levers — `call_looseness` (the flat CALL multiplier) + `size_elasticity` (drives the
      price_factor exponent, decoupled from looseness); default = today's `stickiness`. Prefer a **continuous** faced-
      size function over the 4 abrupt α buckets. Station `size_elasticity ≈ 0` + high looseness; fish high elasticity +
      moderate looseness. Update the monotonicity pins to the new levers.
      **Depends-on:** W0-b (D4 size-bucket FtC curve — the elasticity test) must be live + directional before close.
      **Pass/fail:** station fold-rate roughly flat across SMALL→OVERBET; fish fold-rate rises steeply with size;
      `call_looseness↑` never lowers call freq; α-ceiling + monotonicity pins re-anchored deliberately (these are
      lever-identity assertions, NOT the population bands). **Population WTSD/AF band re-anchor DEFERRED to W4-b** —
      do not re-fit bands mid-spine. **No-gos:** keep default-off byte-identity for un-split packs; no band edits
      pre-W4. **Appetite:** ~1 large slice.

- [x] **W2-b — Semi-bluff draw-jam gate + weak-draw equity gate (B5 + B5b, fixes `audit-F5` + `audit-F7`).** ✅ 2026-07-24 (PR #95, `abe2ea9`) — *ICE 7·8·5 — coupled pair.* EV-gated commit shift: made hands value-jam byte-identical; a facing draw commits only when rule-of-4-and-2 equity clears the T1 threshold `f/(1+2f)` (STRONG folds to a 3×-pot overbet, jams pot-committed); naked WEAK draw stops stacking off (B5b damp). **Deviation (owner-approved, both reviewers):** the roadmap's "fold merit ≈ F\*" conflated the opponent's required-fold with the bot's own fold prob — replaced by a directional own-action policy (existing price-aware fold stands below T1). Rigorous F\* → Later. **maniac WTSD band assertion deferred to W4-b** (sits on the frozen 0.50 ceiling; throughput-n sampling noise, pre-existing).
      **Problem:** the SPR-commit path zeros fold merit and fires for naked air+draw (forced no-fold jam, `audit-F5`); and the
      `_DRAW_CALL_BONUS` (0.20, ~2.5× the air base) makes bots chase weak draws too far (`audit-F7`) — a fold-side brake alone
      can't overpower it.
      **Solution (one slice, two coupled levers):** (B5) zero fold ONLY inside the value-commit zone T1 (equity ≥
      B/(P+2B)); below T1 set fold merit so the *normalized* fold prob ≈ F* (the T2 required-fold identity), NOT a fixed
      multiplier; multiway preserves more fold mass. (B5b) a SEPARATE gate damping the draw call/raise BONUS by
      commitment/equity at high c. Sequence B5b→B5 finalize (B5's F* fold-merit is set LAST against the boosted denominator).
      **Depends-on:** W0-a. EV identities re-derivation-CONFIRMED (T1/T2; the 3×-pot threshold is **42.9%**, not 60%).
      **Pass/fail:** a flush draw pot-committed still jams; the same draw vs a 3×-pot overbet now folds; a naked weak
      draw stops stacking off at high commitment. **No-gos:** no equity SOLVE (heuristic rule-of-4-and-2 proxy; its
      calibration is Later/H7). **Appetite:** ~1 large slice.

### W3 — context (plumbing → position / street / texture)

- [x] **W3-a — Just-ahead plumbing: `in_position` + `bet_prev_street` + `busted_draw` (A2/A3/A4).** *ICE 7·8·6 — plumbing, walking-skeleton.* ✅ 2026-07-24 (PR #96, `4729346`) — new pure `table/postflop_context.py` (derivations + `PostflopContext`), threaded through `sample_postflop_decision` unread (defaults = today); 18 derivation unit tests; every golden/coverage/limper fixture byte-identical with NO re-record (walking skeleton = zero rng displacement). First of the 2-PR W3 packaging (plumbing seam).
      **Problem:** the postflop sampler receives almost no situational context; the position/street/busted mechanics
      below each need one boolean the sampler doesn't get.
      **Solution:** thread three derived inputs (default = today's behavior): **A2** `in_position` (true iff no
      not-folded, not-all-in opponent acts after me this street — exclude FOLDED + ALL-IN seats; **BB IS in position vs
      SB** postflop; 3+-handed = last live seat); **A3** `bet_prev_street` (per-street aggressor memory — fixes the
      whole-hand `is_aggressor` mislabel `audit-F17`, which ALSO corrupts sizing-node selection); **A4** `busted_draw` provenance
      (preserve "was a draw that missed" past the river).
      **Pass/fail:** derivation unit tests for multiway / BvB / all-in (A2), delayed-stab vs barrel + sizing-node
      selection (A3), busted-draw survives the river reset (A4); all existing suites byte-identical (no consumers yet).
      **No-gos:** thread just-ahead of consumers, not big-bang; domain purity. **Appetite:** ~1 slice.

- [x] **W3-b — Position mechanic IP/OOP (B1, fixes `audit-F1`).** *ICE 7·6·5 — GROUNDED direction, DIRECTIONAL magnitude.* ✅ 2026-07-24 (PR #97, `2d71baa`, PR 2 of the W3 seam) — `position_sensitivity` lever (tag/nit 1.0, lag 0.6; station/fish/maniac blind) × `_position_agg_mult` on the aggressor-side BET candidate; CBet_IP > CBet_OOP for disciplined types; un-opted callers byte-identical.
      **Problem:** bots play IP and OOP identically.
      **Solution:** an IP/OOP multiplier on the WHOLE aggressive candidate (bluff_mass + `_AGG_BASE` + draw-agg bonus,
      not just `_AGG_BASE`) + an optional per-persona `position_sensitivity` lever (station/fish ≈ 0 = stay
      position-blind as an intended leak; TAG/nit = full). FIT SEEDS, per-type LOW-confidence.
      **Depends-on:** W3-a (A2); W0-b D5 (IP/OOP c-bet split) live + directional before close (D7 gate). Coordinate the
      bet-band re-level with W3-c.
      **Pass/fail:** a CBet_IP > CBet_OOP gap appears for disciplined types (D5 metric); aggression-factor stays in band.
      **No-gos:** aggressor-side c-bet/barrel frequency ONLY (the OOP continue-realization damp is Later — don't smuggle
      it in). **Appetite:** ~1 large slice.

- [x] **W3-c — Street-conditional aggression schedule + busted-draw river bluff (B6 + B7, fixes `audit-F4`/`audit-F19`/`audit-F8`).** *ICE 7·7·4 — GROUNDED shape, turn LEVEL fit.* ✅ 2026-07-24 (PR #97, `2d71baa`, PR 2 of the W3 seam) — `_STREET_AGG_MULT` (flop 1.0 byte-identical → turn 0.6 → river 0.33) on bluff/semi-bluff ONLY; WEAK semi-bluff → 0 by river (`audit-F19`); busted-draw river bluff via `bet_prev_street`+`busted_draw` (STRAIGHT>FLUSH). Turn no longer byte-identical to flop; give-up line exists.
      **Problem:** aggression is street-neutral (turn == flop byte-identical); `bluff_mass` doesn't decay; busted draws
      lose their identity at the river and can't tell a coherent story.
      **Solution:** a `street_agg_mult` on the BLUFF/semi-bluff merit ONLY (value unchanged): flop 1.0 (byte-identical
      invariant) → turn ~0.5–0.7× → river ~0.33× at pot (FIT SEEDS); polarization tightens flop 2:1 → turn 1:1 → river
      1:2. Street-scale the weak-draw agg bonus (full flop → cut turn → ~0 river) to fix `audit-F19`. Add river bluff mass when
      the hand was a draw that bet the prior street (B7, via A4); prefer busted STRAIGHT draws over busted FLUSH draws
      (a provenance PROXY — validate via the LBR harness before treating as HARD). Optional `street_polarization` lever
      (maniac ≈ flat decline, nit steep).
      **Depends-on:** W3-a (A3/A4); W0-b D6 (turn-barrel%) live + directional before close (D7 gate).
      **Pass/fail:** the turn decision is no longer byte-identical to flop; `bluff_mass(river) < bluff_mass(flop)` for a
      fixed persona/bucket; a give-up line exists (checks back / folds air it would have barrelled); turn-barrel bands
      land in archetype ranges (D6). **No-gos:** heuristic only (no equity solve). **Appetite:** ~1 large slice.

- [x] **W3-d — Made-hand vulnerability + texture brakes (B2 + B3, fixes `audit-F3`-overcard-side + `audit-F20`).** *ICE 7·6·4 — GROUNDED direction, magnitudes fit.* ✅ 2026-07-24 (PR #97, `2d71baa`, PR 2 of the W3 seam) — `_overcard_bet_damp` (0→1.0/1→0.75/2+→0.5) + `_wetness_bet_mult` (dry 1.0 → two-tone 0.85 → connected 0.70 → monotone 0.55) on MIDDLE_PAIR/TOP_PAIR BET only; OVERPAIR_TPTK + sets untouched; composes multiplicatively with B1 + multiway.
      **Problem:** a vulnerable made hand doesn't slow down when overcards fall (`audit-F3`); board texture affects only SIZING,
      never whether-to-bet (`audit-F20`).
      **Solution:** (B2) on MIDDLE_PAIR / TOP_PAIR ONLY (NOT OVERPAIR_TPTK — it bundles overpairs), damp the bet merit by
      the count of overcards on board (0→×1.00, 1→×0.75, 2+→×0.50 FIT SEEDS; non-linear). (B3) multiply the whether-to-bet
      merit for one-pair by board wetness class (dry ×1.00 → high-two-tone ×0.85 → low-connected ×0.70 → monotone ×0.55
      FIT SEEDS; ordering asserted, magnitudes fit; a set still bets). Compose JOINTLY with B1 + multiway so multipliers
      don't stack into over-suppression. (The "barrel-MORE on scare cards" range side is DEFERRED to the villain-range
      pilot — NEXT.)
      **Depends-on:** W3-b (joint composition); D8 node-trace coverage.
      **Pass/fail:** made-pair bet-rate falls by overcard count for TAG/nit (by-overcard metric); one-pair bet-rate falls
      with wetness (ordering test); OVERPAIR_TPTK untouched. **No-gos:** gate strictly to the named buckets. **Appetite:** ~1 large slice.

### W3R — bot-review remediation (from the 2026-07-24 hand-history review — FULL 14-fix program)

> Source: `docs/ai-dlc/research/persona-realism-artifacts/bot-review-2026-07-24/` (findings digest, lever_matrix,
> lever_adjustment_plan, engine_sufficiency_verdict — all LOCAL/git-ignored). Owner played 123 hands (session
> 46f2884); 7 opus reviewers (1 theory/math + 6 per-persona) scrutinized every bot vs its archetype + the grounded
> research. **Engine-sufficiency verdict: PROCEED — zero must-add-now lever gaps; the 3 new-mechanic slices each
> build their own primitive inside their own ticket.** Owner scope decisions (2026-07-24): **full 14-fix program ·
> measurement harness FIRST / hard-prove every dial · blinded human playtest RETAINED** before the final re-anchor.
> All slices own `personas_postflop.py` / persona JSON ⇒ **SERIAL**; default-off byte-identity where a direct caller
> isn't opted in. Every slice: fresh `refuter` + `persona-realism-theory-reviewer` at fan-in; files a coaching
> seam-row (`track-F1`). Softmax law: every magnitude is a FIT SEED re-measured to its target stat, not a drop-in.
>
> **Concurrency:** most slices own `personas_postflop.py` and run **SERIAL** on that spine. Exceptions: **W3R-0**
> (measurement/test code only) and **W3R-1** (maniac.json config only) touch disjoint files and MAY run parallel
> with the spine and each other. All 14 adjustment-plan fixes are covered (14/14): W3R-1 #1/#13 · W3R-2 #2/#3/#6 ·
> W3R-3 #4/#5/#12 · W3R-4 #7/#11/#14 · W3R-5 #8 · W3R-6 #9 · W3R-7 #10.
>
> **Root causes fixed (owner's two flags):** (hyp-1 maniac junk) = the `vs_rfi "*"` any-two cold-call catch-all +
> ungated offsuit-ace opens (CONFIG, W3R-1) — NOT the opening raises, which are already suited>offsuit + position
> gated. (hyp-2 fish/station over-call) = station `size_elasticity 0.0` (size-blind by construction) + fish
> `call_looseness` never authored (inherits stickiness 1.4) (DIALS, W3R-2). Cross-cutting: defense is board-blind
> (texture damps are BET-only, W3R-5); marginal one-pair over-raises (W3R-6).

- [x] **W3R-0 — Arrival-range Fold-to-Cbet population harness (measurement-first; D4-keystone bands).** ✅ 2026-07-24 (PR #98, `2844e9c`). The
      reviewer confirmed only a UNIFORM-range slope fixture exists (`fold_by_size`,
      `backend/tests/test_personas_postflop.py:511`);
      the §5 ABSOLUTE bands (station overbet 18–40%, fish 60–80%) are NOT gated anywhere. Build a per-persona
      realistic-ARRIVAL-range FtC-by-size metric + wire the target bands as assertions consumed by W3R-2.
      **Pass/fail:** the metric computes per persona over arrival ranges and emits the size-bucket fold curve; the
      documented bands exist as assertions (xfail until W3R-2 fits the dials). **No-gos:** measurement only, no
      behavior change, no band re-anchor here. **Prereq for W3R-2 (owner chose hard-prove-first).** Appetite: ~1 large slice.
      > ⚠️ **RESTS-ON-BAD-DATA (C29, 2026-07-25) — applies to W3R-0 *and* W3R-2.** `FLOP_BANDS`
      > (`tests/test_arrival_range_ftc.py:354-372`) writes §5's size-slope numbers into **live assertions**
      > (station 3–15 → 18–40, fish 60–80). Two problems: **(i)** §5's postflop table was never table-size
      > re-checked, and contract §10's standing rule forbids writing an unverified 6-max-derived magnitude into a
      > test as a gate — §10's **recreational-archetype carve-out does NOT transfer here**, because it is argued
      > from *player adjustment* while the 9-max postflop shift comes from *pot composition* (multiway incidence),
      > which applies to the station and the fish exactly as much as to a TAG. **(ii) Denominator mismatch** — §5's
      > numbers are population aggregates over all headcounts; the harness measures **heads-up only**
      > (`opponents=1`, `test_arrival_range_ftc.py:223`). **Gate on W5-a2** before either band set is trusted.

- [x] **W3R-1 — Maniac (+lag) preflop range cleanup (#1, #13) — DONE (PR #100). ⚠️ ACCEPTED TARGET IS FAULTY — see the correction block below.** Replaced the `vs_rfi "*"`
      any-two catch-all with a real loose 3-tier flat range (3bet premiums / 3bet-or-flat playable / wide-marginal
      flat / fold trash); deleted maniac + lag SB open-limps; trimmed offsuit aces HJ `A7o+`, CO/BTN `A5o+`. **The
      root of hyp-1.** **Landed reality-corrected gates:** the "43–55 VPIP" target was WRONG — pre-edit maniac was
      ~36% (that 36% was LITERALLY the any-two junk); a legit range structurally caps ~33% in a 9-max lineup (the
      flat range barely fires; only widening OPENS could raise it, declined). Owner accepted ~33% legit maniac
      (VPIP 32.8%, 3bet% 12.59% back in band via tier-2 `3bet:0.45` restore, `vs_rfi-continue` re-anchored 46%).
      **No-gos honored:** EP opens byte-identical; no postflop lever. 974 pass/4 skip.
      > ⚠️ **CORRECTION BLOCK (C12, 2026-07-25) — W3R-1's landed code stands; its ACCEPTED TARGET is FAULTY.**
      > The record above is kept verbatim as the audit trail. What is now known to be wrong:
      > 1. **The accepted number is out of band.** Maniac VPIP **32.8%** sits **12.2 pts below** the contract band
      >    **45–58** — and ledger **#14** lists maniac VPIP as *deliberately unchanged*, because the researched
      >    9-max band already agreed with it. W3R-1 replaced a nearly-correct target with a wrong one.
      > 2. **The mechanism claim is refuted.** *"A legit range structurally caps ~33% in a 9-max lineup"* is false.
      >    Measured combo-weighted `unopened` RAISE width by seat — UTG 15.9 · UTG1 20.6 · UTG2 25.6 · LJ 34.3 ·
      >    HJ 42.4 · CO 49.1 · BTN 48.0 · SB 44.0 · BB 24.2, **mean 33.8%**. The observed VPIP 32.7% ≈ the
      >    arithmetic mean of the **authored** widths — a **JSON-authorship number, not a structural fact**.
      > 3. ***"Only widening OPENS could raise it"* is also wrong.** `vs_limpers` is `positions: null` at **31.1%
      >    raise**, in a lineup where `calling_station` limps **48.4%** and `passive_fish` **41.0%** of hands.
      > 4. **The 3-bet justification cites a band the contract does not contain.** *"3bet% 12.59% back in band"* —
      >    §5 quotes full-ring **4–7%** and tags the maniac extreme **DIRECTIONAL**.
      >
      > **Target reopened → slice W5-b4.** Do not treat 32.8% as the maniac's accepted VPIP.
- [ ] **FOLLOW-UP (W3R-1 finding, owner-tracked) — band sampler + parity mirror are context-BLIND.** W3-b/c/d made
      production (`play.bot_decision`) context-aware (position/street/texture via `PostflopContext`), but the S4
      harness `_play_hand`/`_persona_stats` band sampler AND the sim_session parity mirror
      (**the TEST** `backend/tests/test_sim_session.py::test_bot_decision_parity_with_harness:248` — NOT the
      service file `backend/app/services/sim_session.py`) still call
      `sample_postflop_decision` WITHOUT `context=`/`is_aggressor=`. So the statistical bands (WTSD/AF/FtC that gate
      the whole persona system) measure a SIMPLER context-blind bot, not the real one. W3R-1 exposed this via a
      parity break and applied the MINIMAL fix (threaded context into the parity mirror ONLY — bands untouched, my
      VPIP fit preserved). ~~**Deeper fix deferred:** decide whether the band sampler should become context-aware
      (→ re-record all bands) — likely fold into W4-b's single re-measure.~~ This is an estimator-parity-law gap.
      > **ESCALATED (C30, 2026-07-25) — no longer "deferred, likely fold into W4-b": this is a PREREQUISITE of
      > W3R-5, and it must name `street_aggressions`.** `_postflop_decision`
      > (`test_personas_postflop.py:1620-1643`) gates `context` / `is_aggressor` / `facing_raise` behind `_OMIT`
      > sentinels and has **no `street_aggressions` parameter at all** — so W3R-5's aggression-heat leg is
      > **invisible** to the AF/WTSD/FtC gate it is supposed to satisfy. **Absorbed by slice W5-a3-iii.**

- [x] **W3R-2 — Fish + station elasticity dials (#2, #3, #6) + station test re-pin — GATED on W3R-0.** ✅ 2026-07-24 (PR #101, `7d9aa85`). ⚠️ **RESTS-ON-BAD-DATA (C29) — see the block under W3R-0; its `FLOP_BANDS` targets are gated on W5-a2.** Author fish
      `call_looseness`≈0.95 (currently unset→stickiness 1.4); station `size_elasticity` 0.0→≈0.55 + `call_looseness`
      ≈1.6; **flip `test_fold_to_bet_monotone_in_faced_size` (`backend/tests/test_personas_postflop.py:554`) from station-must-be-flat(<0.05) → shallow-rise**
      (deliberate spec re-pin — the test currently codifies the very size-blindness the owner wants fixed).
      **Fixes hyp-2.** FIT SEEDS re-measured on W3R-0. **Pass/fail:** station FtC slope small 3–15% → overbet
      18–40%; fish overbet FtC 60–80% (both on the W3R-0 harness); `call_looseness↑` never lowers call freq.
      **No-gos:** no population WTSD/AF band re-anchor (deferred to W4-b). Appetite: ~1 large slice.

- [x] **W3R-3 — spr_commit ladder + finish the call_looseness split (#4, #12).** ✅ 2026-07-24 (PR #102, `112bde0`). ⚠️ **#5 RE-ROUTED (owner
      2026-07-24) — see below.** fish `spr_commit` 2.0→1.4 (it currently commits EARLIER than the station —
      backwards for a "scared" fish), maniac 4.0→3.3; **(#12, low-value tidy)** author explicit `call_looseness` on
      tag=0.6 / nit=0.6 / lag=0.55 (= current `stickiness`, byte-identical; roadmap's "tag≈0.55" was a slip) so the
      W2-a split is adopted roster-wide. **Pass/fail:** fish no longer commits earlier than station (H11/H76);
      per-persona AF stays in band; the three added `call_looseness` packs re-record byte-clean. **No-gos:** softmax
      fit-seed — re-measure AF; #12 is a tidy, not a behavior target. Appetite: ~1 slice.
      - **#5 ace-high call base — RE-ROUTED, NOT a global constant cut.** Building it as `_CALL_BASE[ACE_HIGH]
        0.40→~0.22` HARD-STOPPED: naked ace-high is ~34.6% of the fish's flop range, and W3R-2 already parked the
        fish ON its α fold-ceiling, so ANY meaningful global cut folds the fish PAST the exploitability ceiling
        (un-fishlike over-folding). The collision proves the global constant is the wrong tool — the real bug (H117)
        is naked ace-high FLOATING A RAISE, a facing-action spot. **Re-routed to a facing-a-raise-scoped ace-high
        fold damp — folded into W3R-6** (which already scopes one-pair raise-damp facing action). Do NOT re-attempt
        the global `_CALL_BASE[ACE_HIGH]` cut.

- [x] **W3R-4 — Shared-code base/ordering fixes (#7, #11).** ✅ 2026-07-24 (PR #103, `b8551ef`). ⚠️ **#14 SPLIT OUT (owner 2026-07-24, planning found
      it heavy) → its own slice below.** Scale `_BUSTED_RIVER_BLUFF` by `multiway_bluff_damp**(opp-1)` (currently
      added AFTER the damp at `personas_postflop.py:675` → multiway busted-flush bluffs over-fire, TAG H41 into 3
      callers); `_CALL_BASE[MIDDLE_PAIR]` 0.60→≈0.52 (mild, `:266`). **Pass/fail:** multiway busted-bluff mass
      strictly decays 1→3 opponents (heads-up byte-identical); middle-pair trim keeps every persona in band.
      **No-gos:** no `_made_bucket`/taxonomy edit (that's #14); no band re-anchor (in-band or STOP). Appetite: ~1
      small slice.

- [ ] **W3R-4b — Shared-board false "two pair" commit-inflation (#14) — TAXONOMY EDGE (split from W3R-4).** Fix the
      shared-board-pair→`TWO_PAIR_PLUS` commit inflation so an underpair over a paired board (99-on-7887-8, nit H61)
      stops force-committing. Edits `_made_bucket` (the strength-taxonomy hotspot — already carries the delicate "F7
      bug 1" pocket-underpair logic at ~`:125-137` — that quoted "F7" is a CODE-COMMENT string, **not** an
      F-namespace reference). **Pass/fail:** shared-board "two pair" no longer auto-commits at
      low SPR; genuine (unshared, both-hole-cards-play) two pair UNTOUCHED. **No-gos:** don't demote genuine two pair
      (§9-adjacent); grader/`spot_signature()` frozen; blast radius = bot side only. **Sequencing note:** taxonomy-
      adjacent to W3R-7 (OVERPAIR_TPTK bucket split, same `_made_bucket`) — consider ordering them back-to-back or
      folding together to touch the taxonomy once. Appetite: ~1 slice.
      **Absorbs W5-c1 — board-plays MONSTER guard (2026-07-25; the standalone W5-C entry was DELETED, this is its
      only home).** The same missing hole-card-participation predicate, one rung higher at `cat >= 4` — build both
      participation checks in ONE pass over `_made_bucket`.
      **Absorbed evidence:** `_made_bucket` (`backend/app/domain/personas_postflop.py:120-121`) returns MONSTER for
      `cat >= 4` with **no hole-card participation check**, though `cat == 3` has one and the #14 fix adds one at
      `cat == 2`. Verified by direct call: `Ad Kd` on `Jh 9h 8h 4h 3h` → **MONSTER**; `2c 3d` on `5h 6s 7d 8c 9h` →
      **MONSTER**. `_FOLD_BASE[MONSTER] = 0.0` — the engine's **only** hard-zero fold merit — and rung ≥ OVERPAIR
      fires `_commit_transform`, so the bot **cannot fold and will jam**: nit at SPR 3.3 measures raise **.622** /
      fold **.000**. Frequency **0.607% of random rivers = 4.3% of all river MONSTER spots** (200k-board sample,
      predicate `_best5(board) == _best5(hole+board)`). A nit stacking off with a chop-at-best board flush is the
      most persona-breaking line in the engine. **Solution:** extend the `cat >= 4` branch with that participation
      predicate → route through `_high_card_bucket(hole_hi)`.
      **Added pass/fail (from W5-c1):** both fixtures bucket as high-card and produce a **non-zero fold merit**; the
      genuine-two-pair guard stays green; **no band moves**. **Added no-go:** do **not** touch the `cat == 3` branch.

- [ ] **W3R-5 — Defense-side texture/scare fold brake (#8) — NEW MECHANIC.** The W3-d texture damps are BET-only;
      the FOLD side gets no board signal → scary-board call-downs (station H54 monotone / H100 four-flush, nit H41,
      raise-wars H61/H103/H117). Add a MULTIPLICATIVE fold-merit boost for one-pair-class buckets on
      monotone/paired/overcard boards + vs multiple aggressors. **MUST thread `range_estimate.py` the same context
      + a parity test** (the live bot now diverges from the streetless policy — estimator-parity law). **Pass/fail:**
      station/nit/fish fold more to bets on scary boards; estimator parity holds; it stays a boost, NEVER an asserted
      floor (A1 guardrail). **No-gos:** fold-side only (don't touch the W3-d bet-side scoping). Appetite: ~1 large slice.

      > **RE-SPEC'D (owner decision 2026-07-25).** The original spec above is retained as the correction record;
      > **build the re-spec below.** The first attempt HARD-STOPPED and the stop was structural, not a fit miss.
      >
      > **Problem (why the first build could not close):** as built, `_scare_texture_fold_boost` returns **1.0 on
      > dry** (`backend/app/domain/personas_postflop.py:487` — the dry `return 1.0`; `:479` was a WRONG anchor, it
      > is the `len(board) < 3` guard, and this line carries the whole one-sided-boost argument) and
      > **>1 everywhere else** — a **one-sided boost**, so it *necessarily*
      > raises the **aggregate** fold rate that the α ceiling gates. And its texture + overcard legs fire at
      > `street_aggressions == 1` — the facing-a-**BET** node that W3R-6's own landed comment (`:361-365`)
      > documents as forbidden. **No magnitude inside the original spec's ranges escapes this:** the gate and the
      > mechanic are architecturally incompatible, which is why the fit HARD-STOPPED.
      >
      > **Solution — make the texture leg MEAN-PRESERVING.** Require `E[boost] ≈ 1.0` over the arrival board
      > distribution (e.g. dry ≈**0.88**, connected **1.05**, paired **1.14**, monotone **1.22**). This is also the
      > better poker: **a texture read changes WHICH boards you defend, not how many** — aggregate defense
      > frequency is set by the price, not the board. The mechanic becomes **α-neutral by construction** and the
      > HARD-STOP dissolves **without touching the α test**.
      >
      > **Also fix, in the same slice:**
      > - Original pass/fail **(iv)** is **unbuildable as written** — mechanic-OFF scary−dry measures nit **−0.031**
      >   / fish **−0.017**, a **range-composition confound** (monotone boards carry made flushes, paired boards
      >   carry trips). Restate as **within-bucket** scary-vs-dry, or assert the **delta vs mechanic-off** — never
      >   the absolute partition.
      > - Original pass/fail **(vii)** is **invisible** until W5-a3-iii adds `street_aggressions` to the band sampler.
      > - Spec rationale **#2 is SUPERSEDED**: W3R-6 already landed `_ACE_HIGH_FLOAT_RAISE_DAMP = 0.55` (`:374`)
      >   on the **identical node**, so the two now compound **uncalibrated** on a bet→raise flop with naked
      >   ace-high ⇒ **§7 joint calibration required**.
      > - The **overcard leg is inert for ACE_HIGH** (`_overcard_count` falls back to `max(r1, r2)`, so an ace-high
      >   hand always counts **0** overcards) — only **2 of 3** legs fire for one of the three scoped buckets.
      > - The header says *"these four magnitudes"*; **seven** constants are actually defined. Fix the count.
      >
      > **Depends-on:** **W5-a3-iii** (band sampler `street_aggressions`) and **W5-c2** (full-board texture
      > classifier — today `texture.classify` reads `board[:3]` always
      > (`backend/app/domain/texture.py:31-37`), so W3R-5's own named target hand H100, the four-flush call-down,
      > is invisible to its own mechanic). **Both are W5-A/W5-C foundation slices that run BEFORE this one** (see
      > the wave-order correction R3) — the dependency runs W5 → W3R-5, one-way, never back.
      > **Note the direction of ownership:** `_scare_texture_fold_boost`, `_SCARE_PAIRED`, `_SCARE_MONOTONE` and the
      > other scare constants are **INTRODUCED BY THIS SLICE** — they do not exist at HEAD (they live only in the
      > uncommitted, HARD-STOPPED first attempt). No other slice may cite them as existing code.
      > **Pass/fail (re-spec):** `E[boost]` over the arrival board distribution is **1.0 ± 0.02**; the α fixture
      > passes **with headroom rather than on a lucky seed**; within-bucket scary−dry separation is positive and
      > measurable; joint calibration with `_ACE_HIGH_FLOAT_RAISE_DAMP` is documented.
      > **No-gos:** **never a fold FLOOR** (A1 guardrail); **no α-test edit here** — that is slice **W5-a4**
      > (promoted out of NEXT, R7).

- [x] **W3R-6 — One-pair RAISE damp facing action, pre-river (#9) + ace-high float damp (#5, re-routed) — NEW
      SCOPING (fixes M7).** ✅ 2026-07-24 (PR #104, `22e9598`). ⚠️ **The roadmap text below is SUPERSEDED by what landed — see the correction block.** `_RAISE_BASE` + the river-only raise-floor let made one-pair (MIDDLE/TOP) jam on
      flop/turn (TAG H117 99 on J-J-7, H32 88, H107 TPTK; maniac too). Damp the one-pair RAISE merit when FACING a
      bet/raise on flop/turn; **spare semi-bluff (draw) raises.** **ABSORBS #5 (re-routed from W3R-3):** also damp
      naked ACE_HIGH (no pair/draw) CALL/float merit when FACING A RAISE on flop/turn — the scoped version of the
      ace-high float fix that the global `_CALL_BASE[ACE_HIGH]` cut couldn't do without over-folding the fish (its
      range is ~⅓ ace-high, already on the α ceiling from W3R-2). Scoping to facing-a-raise avoids the global
      over-fold. **Pass/fail:** TAG/maniac stop re-raising bare one pair into heavy action; a flopped-draw
      semi-bluff raise still fires; naked ace-high folds to a raise (H117) WITHOUT busting any persona's α ceiling on
      its arrival range. **No-gos:** two-pair+ value raises untouched; don't cut the global ace-high base (that was
      the refuted W3R-3 approach). Appetite: ~1 large slice.
      > ⚠️ **CORRECTION (C11, 2026-07-25) — the text above describes a WIDER gate than the one that landed.**
      > It says the one-pair raise damp fires *"when FACING a bet/raise on flop/turn"*, but the landed code is
      > `facing_raise and street in (FLOP, TURN)` (`personas_postflop.py:903-909`) — it fires when facing a
      > **RAISE only**, never when facing a plain bet. Read the code, not this bullet.
      > **Consequence — raise-vs-flop-c-bet is unaddressed by the ENTIRE 14-fix program.** The most common
      > over-raise spot (facing a single c-bet) is outside every landed gate. Filed as NEXT item **N-raise**.

- [ ] **W3R-7 — OVERPAIR_TPTK bucket split (#10) — NEW GRANULARITY (heaviest).** Split the bucket so genuine
      top-pair-top-kicker (AK-on-K) gets the W3-d texture brake while true overpairs (AA-on-K) keep betting. Touches
      `_made_bucket` + all `_*_BASE` tables + `_VULNERABLE_ONE_PAIR` + the river floors. **Do NOT** just add
      OVERPAIR_TPTK to `_VULNERABLE_ONE_PAIR` (would damp real overpairs — §9 #7); split the taxonomy. **Pass/fail:**
      AK-on-monotone-K slows down (H54); AA overpair still bets; `spot_signature()`/grader untouched (frozen); the
      bluff-ordering pin re-anchored deliberately. **No-gos:** grader frozen; blast radius = bot side only.
      **Scope-check at `/ai-dlc`:** likely TWO slices — (a) split the taxonomy/`_made_bucket`, then (b) re-fit the
      `_*_BASE` tables + re-anchor the bluff-ordering pin. Appetite: ~1–2 large slices.

### W5 — band-correction remediation (from the 2026-07-25 target-provenance audit)

> **Why this wave exists.** Contract §9 ledger **#14** found the keystone's preflop VPIP/PFR rows carried **6-max**
> values while the reference pool is **9-max**. The follow-on three-agent audit (W3R/W4 · NEXT · LATER+gates) found
> the same class of defect in five more places: an **unverified postflop half** of the same table, a **measurement
> layer** that computes a different statistic than §6 defines, **preflop ranges authored at 6-max width**, and two
> small **engine-correctness** bugs. The softmax law makes this the project's most dangerous failure mode: fed a
> wrong target, the fit loop converges *confidently* onto wrong behavior and reports success.
>
> **Concurrency (C13; AMENDED R1, 2026-07-25):** **W5-A** (docs/tests) and **W5-B** (`content/personas/*.json`)
> touch **disjoint file sets and run in PARALLEL**; within W5-B, **serialize per pack** (one owner per JSON file).
> **W5-C is only PARTLY disjoint.** W5-c1 has been **deleted from this group** (it edited `_made_bucket` in
> `backend/app/domain/personas_postflop.py`, the serial spine) — its evidence and pass/fail now live **only**
> inside **W3R-4b**. That leaves **W5-c3** (`backend/app/services/sim_session.py`) as W5-C's **only genuinely
> disjoint** slice. **W5-c2 is NOT disjoint:** it edits `backend/app/domain/texture.py`, imported by
> `personas_postflop.py` (spine), `backend/app/domain/postflop.py:39` (the **grader** — §11 item 13 auto-FAILs a
> slice that changes grader behavior) and `backend/app/domain/srs.py:128` inside the **FROZEN** `spot_signature()`.
> Run W5-c2 serially against the spine, under the frozen-invariant no-gos in its own entry.
>
> **Wave order (R3):** W5-A and W5-C run BEFORE the W3R tail (W3R-4b / W3R-5 / W3R-7), because W3R-5 depends on
> W5-a3-iii + W5-c2 and W3R-4b absorbs W5-c1. W5-B is independent of the W3R tail and may run alongside it.
> The W3R-5 re-spec itself runs on the `personas_postflop.py` spine and stays serial with W3R.
>
> Every W5 slice keeps this file's conventions: `[ ]` checkbox, ICE score, **Problem / Solution / Pass-fail /
> No-gos / Appetite**, a fresh `refuter` **+** `persona-realism-theory-reviewer` at fan-in, a coaching seam-row
> (`track-F1`), and softmax-law FIT-SEED discipline.

#### W5-A — foundation (docs + tests; NO bot-behavior change)

- [x] **W5-a1 — Target-provenance gate.** ✅ 2026-07-25 (PR #111). Contract **§5a** registry + **§11 item 15** +
      a number-free clause in the theory-reviewer agent, with `backend/tests/test_contract_provenance.py` as the
      runnable tripwire (verified to bite: dropped row, emptied source cell, em-dash placeholder and orphaned
      registry entry all rejected; italic observational rows exempt). **The postflop half of §5 is now
      `[UNVERIFIED]` wholesale** — a provenance claim, not a correctness one — which makes **W5-a2** the gate on
      every band that rests on those rows. fold-to-c-bet / AF / WTSD stay HARD as *grandfathered*; their demotion
      is W5-a2's deliverable and no slice may add a NEW HARD gate on an `[UNVERIFIED]` row. *ICE 9·8·3.*
      **Problem:** no gate validates a **target**. D7 validates the *instrument*; the softmax law *consumes* a
      target, and against a wrong one it converges confidently onto wrong behavior and reports success — the
      project's strictest gate is also its most efficient error-propagator. The anti-laundering rule gives the
      *measured comparator* immutability + audit, while the **keystone table has neither**. Metric #3 (VPIP/PFR/gap)
      **is** live and is **never compared to §5 at all** — its only assertion is `0.0 <= pfr <= vpip <= 1.0`
      (`test_personas_postflop.py:2412`). So the wrong number was never load-bearing in CI: its harm channel was
      **human and agent judgement**, which is where the gate must sit — at the moment a target is *cited into a ticket*.
      **Solution:** contract **§5a** + **§11 item 15**. Every §5 row carries `(format, pool/stakes, source)`; a row
      whose format is not the §10 reference pool is `[UNVERIFIED]` and **DIRECTIONAL-only, never HARD-gatable**. Two
      obligations: **(1) citing gate** — a ticket citing a §5 target must quote its provenance triple; a bare number
      FAILs. Format-**SENSITIVE**: VPIP, PFR, 3-bet%, RFI-by-seat, c-bet, fold-to-c-bet, WTSD, turn barrel, multiway
      incidence. Format-**INVARIANT** (safe to transfer): the VPIP−PFR **gap**, **AF**, any ordering/monotonicity
      claim. **(2) the W3R-1 rule** — infeasibility is **evidence about the TARGET**: when a fit cannot reach a
      target with a legitimate range or lever, the slice **STOPS and re-opens the target's provenance** rather than
      widening the lever or the band. Plus one clause in `.claude/agents/persona-realism-theory-reviewer.md`,
      **deliberately number-free** (hardcoding numbers would duplicate the defect in a second place): target
      provenance is in scope and the contract is **not immune**; a format/pool mismatch, a target cited without
      provenance, or a target the slice could not reach with a legitimate lever ⇒ a **CONTRACT-DEFECT finding at
      HIGH**, and do not pass the slice on the contract's authority alone.
      **Pass/fail (RUNNABLE — R8, 2026-07-25):** a **committed** `backend/tests/test_contract_provenance.py`
      parses §5's tables out of `docs/ai-dlc/contracts/persona-realism-theory-contract.md` and **FAILS** if any §5
      row lacks a `(format, pool, source)` triple **or** an `[UNVERIFIED]` tag — so the provenance rule is a
      tripwire, not a convention, and W5-a2's audit becomes mechanically verifiable (it cannot land a row without
      provenance). Plus, non-executable but checklist-gated: §5a + §11 #15 exist; the reviewer-agent clause exists;
      a deliberately-bare-number citation is rejected by the checklist.
      **No-gos:** no band VALUES change here; **the only test added is the provenance parser** — no persona/band
      test edits. **Appetite:** ~1 small slice.

- [x] **W5-a2 — 9-max postflop band provenance audit + research pass (absorbs H6).** ✅ 2026-07-25 (PR #115,
      `642ca0d`). *ICE 9·7·5.* Five of six rows survive unchanged; WTSD tag 27–31→**25–29 ‡** and lag 28–33→**26–31 ‡**
      (the only postflop cells with two independent sources publishing 6-max and full ring side by side and
      agreeing). c-bet / fold-to-c-bet / turn barrel / AF **CONFIRMED UNCHANGED at conf LOW** — a withheld
      correction, not a certification. W$SD and c-bet LEVEL stay `[UNVERIFIED]`.
      ⚠️ **Two follow-ups opened by this slice, both still live:**
      **(1) W5-a2-f — demote the fold-to-c-bet and AF HARD gates.** Deferred, not dropped:
      `backend/tests/test_personas_postflop.py` was owned by a concurrent slice. **Must land before W4-b.**
      **(2) CONTRACT-DEFECT (HIGH, §11 item 15)** — §5a shipped its format-SENSITIVE/INVARIANT lists as
      *unsourced assertions*. Putting AF on the INVARIANT list is itself a transfer claim made with no citation:
      ledger #14's error one level up (an unsourced *licence to transfer*, rather than an unsourced number). It
      held, but on luck rather than process. Remedy in force: every list entry now carries a source or
      `[UNVERIFIED]`.
      **Problem:** §5's postflop rows (c-bet, fold-to-c-bet, AF, WTSD, turn barrel) were **never checked for table
      size** — the same defect ledger #14 corrected on the preflop half. **Two of them (fold-to-c-bet, AF) are wired
      as HARD CI gates today.** 5/6 personas miss the c-bet band (maniac **−20pp** measured aggressor-side at
      n=415), but 9-max's higher multiway incidence should push the *correct* c-bet number **down** — so the bots
      may be closer to right than the target is.
      **Solution:** research full-ring vs 6-max postflop population stats; for every §5 postflop row record
      `(format, pool, source)`; confirm or restate the 9-max value; any unsourceable row → `[UNVERIFIED]`
      DIRECTIONAL-only. Demote **fold-to-c-bet** and **AF** from HARD → **no-regression** until sourced.
      **Pass/fail:** every §5 postflop row carries a provenance triple or `[UNVERIFIED]` — **mechanically enforced
      by W5-a1's `backend/tests/test_contract_provenance.py`, which must pass on the edited contract**; both CI
      gates demoted with an in-file reason; a **written verdict** on whether the c-bet band moves.
      **Depends-on:** W5-a1 (the provenance parser + the `(format, pool, source)` triple format).
      **No-gos:** no bot behavior change; **no band FIT here** (that is W4-b).
      **Blocks:** NEXT item **N-cbet**; gates W3R-0 / W3R-2's band assertions (C29). **Appetite:** ~1 slice (research-heavy).

> **W5-a3 SPLIT INTO THREE (R9, 2026-07-25).** It was four independent repairs under one checkbox with four
> different consumers — un-plannable and un-verifiable as a unit. The shared problem statement is kept here; the
> three slices below own disjoint deliverables. **Only a3-iii blocks W3R-5.** The §6 doc refresh (iv) folds into
> whichever of the three lands LAST.
>
> **Shared problem:** **(i) metric #1 measures a different statistic than §6 defines** — it computes P(bet |
> first-in flop decision) for **any** tested seat, including cold-callers and blind defenders who check most flops,
> not aggressor-side c-bet. It under-reads: tag **0.417 vs 0.488**, nit **0.224 vs 0.326**, fish **0.196 vs 0.321**.
> `cbet_ip`/`cbet_oop` inherit the denominator, so **metric #5 cannot gate P1's direction-HARD claim** — on
> today's numbers **lag reads inverted** (IP 0.487 < OOP 0.515) and nit reads flat (0.227 / 0.223) despite
> `position_sensitivity: 1.0`. **P1 (W3-b) and P2 (W3-d) have already CLOSED against this metric.**
> **(ii)** §5 requires separating station from maniac *"by AF and raise-vs-call share, never FtC alone"*, but §6
> has **no raise-vs-c-bet metric** — and the live sample's most extreme deviation sits exactly there.
> **(iii)** the band sampler has no `street_aggressions` slot (C30). **(iv)** §6 is stale (C31): all six W0-b
> metrics compute (`ExtStats`, `backend/tests/test_personas_postflop.py:2147-2156`) but only **smoke-assert**
> (`:2392-2413`), while §6 still lists them "to BUILD".

- [x] **W5-a3-i — Metric #1 aggressor-side denominator.** ✅ 2026-07-25 (PR #112). *ICE 8·8·3.*
      **Solution:** fix metric #1's denominator to **aggressor-side** c-bet as §6 defines it, and **re-read**
      `cbet_ip` / `cbet_oop` (metric #5), which inherit it.
      **Pass/fail:** metric #1 matches its §6 definition on a fixture with a known aggressor; re-measured
      `cbet_ip`/`cbet_oop` **no longer read inverted for lag**; the re-read values for all six personas are
      recorded in-file (they are the input W3-b/W3-d closed against, so the record is the audit trail).
      > ⚠️ **STALE PREMISE — this entry's cited symptom did not reproduce (2026-07-25, W5-a1's W3R-1 rule).** The
      > "lag IP 0.487 < OOP 0.515" inversion quoted above is **not present on today's tree**: at n=4000 lag reads
      > IP **0.530** > OOP **0.476** under the *OLD* denominator and IP 0.552 > OOP 0.540 under the new one. So
      > pass/fail clause 2 was satisfied **vacuously** — the denominator fix is justified on §6's *definition*
      > alone, not on repairing an observed inversion. Most likely the six W3R preflop/dial slices merged after
      > that note was written shifted the shared-rng population. Per §5a's **W3R-1 rule** (infeasibility /
      > non-reproduction is evidence about the TARGET), this is recorded against the premise rather than ticked
      > as a fix. **Do not cite the 0.487/0.515 figures again.**
      > ⚠️ **COVERAGE DELTA (§11 item 14) — adjudicated, cost deferred to W5-a3-iii.** Aggressor-only c-bet
      > opportunities are ~1/hand vs ~3/hand under the old denominator, so at **n=200** (the CI smoke-test N)
      > metric #1 now falls under the harness's `>=30` floor and reads `None` for **4 of 6 personas** (station,
      > nit, fish, tag); previously all six carried a value. Accepted here — #1 only smoke-asserts today — but it
      > means **metric #1 cannot be promoted to a HARD gate at the current N**. W5-a3-iii's §6 refresh records the
      > constraint and the N a promotion would need; CI N is deliberately NOT bumped (the suite already runs ~117s
      > and n=4000 costs ~50s/side).
      **No-gos:** **measurement only** — no behavior change, no band re-anchor, no §5 edit.
      **Consumer:** the D7 gate for P1 (W3-b) / P2 (W3-d), retroactively. **Appetite:** ~1 slice.

- [ ] **W5-a3-ii — New metric #7: raise-vs-c-bet + its §5 keystone row.** *ICE 8·7·4.*
      **Solution:** add a **raise-vs-c-bet metric (#7)** to the harness and author its **§5 keystone row**.
      **Depends-on / SEQUENCE AFTER W5-a1** so the new row inherits the `(format, pool, source)` provenance triple
      at birth (a row without one FAILs `backend/tests/test_contract_provenance.py`).
      **Pass/fail:** metric #7 emits per persona on the existing fixture; the new §5 row carries a provenance
      triple or `[UNVERIFIED]`; the provenance parser stays green.
      **No-gos:** no behavior change; no band re-anchor; the row ships **DIRECTIONAL**, never as a HARD gate.
      **⚠️ Scope conflict, called out deliberately:** this slice **edits §5**, which the shared "measurement only"
      no-go otherwise forbids — the §5 row is in scope **for this slice alone**, and only to CREATE the new row.
      **Consumer:** NEXT item **N-raise**. **Appetite:** ~1 slice.

- [x] **W5-a3-iii — Band-sampler + parity-mirror context kwargs. ⛔ THE ONLY W3R-5 BLOCKER.** ✅ 2026-07-25
      (PR #118, `c8a535e`). *ICE 9·8·4.*
      ⚠️ **Its two new assertions were fitted to the PRE-W5-b1 packs and now FAIL on `main`** —
      `test_persona_stats_byte_identical_after_log_refactor` and `test_street_aggressions_effect_visible_to_af_gate`.
      A parallel-merge hazard, not a defect in either slice; see W5-b1's red-baseline block.
      **Solution:** added `street_aggression_count(action_history, street) -> int` to
      `table.postflop_context.py` (C30's missing raw count; `facing_raise` is now `count >= 2`, refactored onto it
      — byte-identical, verified by the existing `facing_raise` unit tests). `_play_hand` gained an opt-in
      `context_aware: bool = False` kwarg (threaded through `_persona_stats`, cache key extended to
      `(persona, n, context_aware)`) that, when `True`, derives `is_aggressor` / `latest_aggressor_contribution_bb`
      / `context` / `street_aggressions` EXACTLY as `play.bot_decision` does and passes them to `_postflop_decision`
      (which now also accepts `street_aggressions=`, deriving `facing_raise` from it when the caller doesn't supply
      the boolean directly — production has no raw-count parameter, so the count can only "thread" by producing the
      one boolean `sample_postflop_decision` actually consumes). Default `False` — every existing CI band/golden
      call site is untouched and unmodified. The parity mirror
      (`test_sim_session.py::test_bot_decision_parity_with_harness`) now threads `street_aggressions` (via the same
      helper) instead of a directly-computed boolean, which doubles as a self-check that the count-based derivation
      agrees with production's own `facing_raise()` call (an assert pins it).
      **Pass/fail:** ✅ the sampler accepts all four context kwargs; the parity mirror threads the same context and
      stays green (`test_bot_decision_parity_with_harness` unchanged pass, 3-hand-seed coverage). ✅ A
      `street_aggressions`-dependent effect is now **visible** to the AF gate: new
      `test_street_aggressions_effect_visible_to_af_gate` runs `_persona_stats(packs, "tag", 300, context_aware=...)`
      both ways — AF **2.769 → 1.667** (a facing-raise-gated drop from W3R-6's `_ONE_PAIR_RAISE_DAMP` /
      `_ACE_HIGH_FLOAT_RAISE_DAMP`, which never fired in the band sampler before this slice), both sides clearing
      the `>=30` occurrence floor (52/69), direction stable at n=250/350/400/500. This is a NEW, separate cache
      entry — it does NOT touch the `context_aware=False` (default) CI-frozen bands/goldens.
      **No band moved** — `test_persona_stats_byte_identical_after_log_refactor` (the golden tripwire) and
      `test_persona_postflop_bands` both pass unchanged; `context_aware` defaults `False` everywhere they call in.
      **No-gos:** measurement only — confirmed; no band re-anchor — confirmed (the visibility demonstration is an
      opt-in side channel, not a change to any existing assertion).
      **§6 refresh (iv), NOT applied to the contract file this round:** this slice lands LAST among a3-i/ii/iii, so
      it owns the refresh, but `docs/ai-dlc/contracts/persona-realism-theory-contract.md` was locked to a
      concurrently-running agent this round (owner-imposed, not this maker's call) — editing it here would race
      that edit. Recording the refresh content here instead, for whoever next has the contract file open to apply
      to §6 (currently stale: it lists all six W0-b metrics as "Metrics to BUILD (Wave 0)"):
      - All six W0-b metrics (`ExtStats` / ` _persona_stats_ext`, `test_personas_postflop.py:2320` +) **compute
        today** — none are "to BUILD" any more. Table row 1 (CBet-flop-overall) is now correctly aggressor-side
        (W5-a3-i); rows 2-6 (W$SD, VPIP/PFR/gap, size-bucketed FtC, IP/OOP split, turn-barrel%) compute but read
        DIRECTIONAL/smoke only (roadmap D7: a metric is HARD only once "live AND showing the expected direction"
        for the mechanic it gates, and none of rows 2-6 have had that direction check performed yet).
      - **D7 promotes to HARD today: none of the six.** The only HARD-today gates remain the pre-existing three —
        AF, fold-to-first-cbet, WTSD (`test_persona_postflop_bands`) — and per W5-a1/W5-a2 those two of the three
        (fold-to-cbet, AF) are GRANDFATHERED-HARD pending §5's provenance audit, not newly HARD from this metric
        framework.
      - **Metric #1 (aggressor-side CBet-flop) cannot be promoted to HARD at the CI smoke-test N (200).** W5-a3-i's
        audit trail (`test_personas_postflop.py:2271-2317`) measured aggressor-only opportunities at ~1/hand vs
        ~3/hand under the old denominator: at n=200 the `>=30` floor is missed for 4/6 personas (station, nit,
        fish, tag read `None`); at n=4000 the SPARSEST persona (calling_station, which rarely holds the preflop
        aggressor seat) clears the floor only barely (33 opportunities). **A promotion to HARD would need at least
        n≈4000 for every persona to clear the floor at all, and meaningfully more (rough estimate n≈10,000-12,000,
        scaling station's ~0.008 opportunities/hand up to a comfortable 3σ-stable occurrence count, not just the
        bare 30 minimum) for a non-fragile band.** That is far beyond what CI affords — n=4000 alone already costs
        ~50s/side, and the CI N is deliberately staying at 200 (§11 item 14's coverage-delta adjudication, W5-a3-i
        entry above). Metric #1 stays smoke/DIRECTIONAL only; do not gate a NEW HARD assertion on it without first
        revisiting the CI-N budget.

- [ ] **W5-a4 — Resolve the α-ceiling vs §5 fold-to-c-bet contradiction (N-α, PROMOTED from NEXT — R7,
      2026-07-25).** *ICE 9·8·4.* **Promoted because W4-b cannot close without it** — and NEXT is defined in this
      file as *"not yet spec'd"*, so a declared hard prerequisite of a NOW slice cannot live there.
      **Problem:** `test_fold_to_bet_respects_alpha_ceiling` (`backend/tests/test_personas_postflop.py:603`)
      asserts fold ≤ α+0.05 = **0.298 / 0.383 / 0.550 / 0.650** at ⅓ / ½ / pot / 1.5×pot. §5's grounded aggregate
      fold-to-c-bet: **nit 60–75, tag 50–60, lag 40–50, fish 35–50**. **At the modal ½–⅔-pot c-bet the ceiling is
      0.383 — nit's, tag's and lag's grounded targets are UNSATISFIABLE while the test is live.** Three independent
      slices hit this wall and each escaped by **node-scoping** instead of resolving it (W3R-2 re-scoped the fish to
      its arrival range; W3R-6 narrowed to facing-a-raise; W3R-5 HARD-STOPPED). The tree is worse than the comments
      say: tag has **0.42pp** of true headroom at ½-pot and the fish is **0.015 ABOVE** the ceiling **in
      expectation**, passing only because one seed realization lands 3.6pp under — **the gate currently passes on
      luck.**
      **Theory:** `α = f/(1+f)` is the maximum fold frequency that is unexploitable **against a balanced bettor**.
      §5's numbers are population observations against **real** villains who c-bet 55–70% of flops — far more than
      balanced — so folding 60% is the **correct exploit, not a leak**. The code already half-admits this (the nit
      is exempted as "its deliberate over-fold leak is a persona choice").
      **Solution:** move the α guardrail onto a **balanced-villain unit fixture** (where the identity actually
      holds), and replace the arrival-range **aggregate** assertion with the §5 grounded bands.
      **Pass/fail:** `test_fold_to_bet_respects_alpha_ceiling` asserts α only on the balanced-villain fixture and
      passes with **stated headroom, not a lucky seed** (report the margin per persona); the arrival-range
      aggregate assertion no longer contradicts §5; **no persona lever or magnitude changes** (the whole slice is a
      test re-scoping — any behavior diff means it went wrong); W3R-5's HARD-STOP condition is demonstrably lifted.
      **No-gos:** **never a fold FLOOR** (A1 guardrail); no persona/pack edits; **any §5 band cited here must carry
      its W5-a1 provenance triple, and an `[UNVERIFIED]` row may NOT become a HARD gate** — so this slice may not
      re-gate on the fold-to-c-bet row until **W5-a2** rules on it (sequence after W5-a2).
      **Prerequisite of:** **W4-b** (C27 #2); unblocks the W3R-5 re-spec's α headroom. **Appetite:** ~1 slice.

#### W5-B — preflop range width (`content/personas/*.json`; ONE OWNER PER PACK)

- [x] **W5-b1 — `unopened` ladder widening to the corrected 9-max bands.** ✅ 2026-07-25 (PR #119, `930eb20`).
      ⚠️ **MERGED NOT-GREEN — see the red-baseline block at the end of this entry.** *ICE 9·7·5.*
      **Shipped:** authored `unopened` width nit **7.5→27.4**, tag **16.4→34.0**, lag **22.6→53.7** (combo-weighted,
      first-mix-wins), hands ADDED family-wise in normal opening order; **not one call/limp weight touched** (nit's
      open-limp mixes preserved verbatim, moved to the front of their node so first-mix-wins keeps the identical
      limp frequency). By-seat ordering (tighter early, widest on the button) and per-node raise weights unchanged.
      Metric #3 at n=1200, **REPORTED only, no band committed as a CI gate** (single anchor is W4-b, §11 item 7):
      nit 6.4/4.4/2.0→**11.6/9.7/1.8**, tag 13.1/10.6/2.6→**16.4/13.1/3.3**, lag 17.9/12.9/4.9→**25.8/18.2/7.5** —
      VPIP+PFR now IN band for all three; lag's gap **+1.6 HIGH**.
      **Two W3R-1 findings recorded rather than engineered around:**
      **(1) maniac NOT edited** — its ladder is pinned byte-identical by W3R-1's committed invariants (reopening is
      **W5-b4**), and a 100%-of-all-hands `unopened` probe caps maniac PFR at **32.1** against a 38–48 band: the
      band is **unreachable through this lever at ANY width**.
      **(2) lag deliberately left SHORT of target** (owner ruling, 2026-07-25) — the width that reaches lag's PFR
      target opens `A2o` from middle position, which is a maniac wearing a lag's name, and every setting reaching
      the PFR target breaks the gap row. **Character over number**; the residual belongs in `vs_rfi` / `vs_limpers`
      (**W5-b2** / **W5-b4**), not in a wider open.
      **⚠️ RED BASELINE (owner-visible, 2026-07-25).** This slice merged with the suite at **10 failed / 1055
      passed / 1 skipped**, all outside its own file scope. Root cause is a **parallel-merge hazard, not a defect in
      either slice**: PR #118 (W5-a3-iii) added assertions fitted to the *pre-widening* packs and PR #119 then
      widened them; the two were built concurrently so neither PR's checks saw the other. Failing:
      `test_coverage_baseline`, `test_grade_map_turn_river::test_bot_driven_turn_barrel_grades_on_standard_open`,
      `test_limper_coverage_belt`, `test_personas::test_persona_stat_bands[nit|tag|lag]`,
      `test_personas_postflop::test_persona_stats_byte_identical_after_log_refactor` (calling_station AF 0.3974 vs
      golden 0.3788), `test_personas_postflop::test_street_aggressions_effect_visible_to_af_gate` (AF drop 0.368 vs
      a demanded 0.5), `test_range_estimate::test_four_bet_line_strict_subset_and_hand_computed_posterior`,
      `test_w3r1_preflop_cleanup::test_lag_sb_no_open_limp[J9o]`.
      **`test_persona_stat_bands` is the one NON-mechanical entry** — it gates **authored width** against
      **population PFR** targets, which are different quantities; the ruled re-scope to measured authored width did
      not land here. **Process note:** the authored→PFR conversion is **not linear** — measured ×0.50–0.54 at narrow
      widths falls to **×0.35 (nit) / ×0.34 (lag)** at the new widths, because wider opens mean more seats arrive
      already facing a raise. Do **not** derive a band by dividing a §5 PFR target by 0.50–0.54.
      **Green-up ownership is an open decision** (see W5-b2's entry). No threshold in the failing list may be
      loosened to make it pass — that is the W3R-1 violation this initiative exists to stop.
      **Problem:** the packs were authored as if unopened-raise width ≈ PFR — roughly true at 6-max, badly wrong at
      9-max where a seat usually **faces an open** and the residual routes to `vs_rfi` or `vs_limpers`. Measured
      authored width → observed PFR: nit **8.0→4.1** (×0.51), tag **16.4→8.8** (×0.54), lag **22.6→11.3** (×0.50),
      maniac **33.8→25.9** (×0.77). **The gap row passes 5/6 at n=1200**, so the call:raise ratio is already right —
      both legs are simply too tight. This is a **range-width deficit, not a call-weighting one** (call-weighting
      would *inflate* the gap).
      **Solution:** widen each pack's `unopened` ladder toward the widths required to hit the **corrected** §5 bands
      — nit ~**16–24%** (from 8.0), tag ~**22–31%** (16.4), lag ~**34–46%** (22.6), maniac ~**49–62%** (33.8). FIT
      SEEDS re-measured against metric #3, never drop-ins.
      **Pass/fail:** metric #3 VPIP/PFR land in the corrected §5 bands per persona; the **gap row stays in band for
      all six**; bluff-ordering and every §7 invariant unchanged. **Measure against the §5 band and REPORT; do NOT
      commit it as a CI gate — the single band anchor is W4-b.**
      **No-gos:** no postflop lever; no schema; **do not touch the call weights that produce the gap** — they are
      correct; **no population band re-anchor — deferred to W4-b** (contract §5 forbids writing an RP6 number into
      a test as a gate before the Wave-4 re-measure; §11 item 7 auto-FAILs it). **Appetite:** ~1 large slice.

- [ ] **W5-b2 — E1-a: actor-position `vs_rfi` + `vs_limpers`.** *ICE 9·8·4.* **Owns the north-star's ACTOR-position assertion (C2, as re-scoped by D1).**
      **Problem:** every `vs_rfi` and `vs_limpers` node in all six packs is `positions: null` — **one number for all
      eight non-opener seats**. Measured `vs_rfi` continue: station **55.7** · maniac **46.6** · fish **43.3** · lag
      **25.4** · **tag 15.5** · **nit 5.8**, each a single constant, so TAG's BB
      defence and its MP cold-call vs UTG are forced to the same number: the BB leg is far too tight while the MP
      leg is ~2× too **loose**. One node cannot be both. **No postflop lever or dial can reach it.**
      **Solution:** author per-**actor**-position `vs_rfi` and `vs_limpers` nodes. **JSON-only** —
      `backend/app/domain/personas.py:76-79` filters `node.positions` for **every** facing;
      `backend/app/domain/content/models.py:205-219` `_node_ordering` permits explicit-position nodes before the
      wildcard; tag/lag/maniac already ship nine explicit `unopened` position nodes, so the pattern is already in
      production. No schema, no plumbing.
      **Pass/fail (REPAIRED — owner decision D2, 2026-07-25; ACTOR-SEAT DELTAS ONLY):**
      (a) per-seat `vs_rfi` continue is **no longer a single constant** across the eight non-opener seats for the
      edited packs — the by-seat spread is non-zero and its ordering is **blind-seat-widest** (BB ≥ SB > MP > EP,
      the price/closing-action ordering);
      (b) tag's **BB `vs_rfi` continue rises to a seat-appropriate level, measurably distinct from its MP
      cold-call frequency** at the same node (the two numbers separate — that separation IS the fix);
      (c) the north-star's re-scoped **actor-seat** assertion (bots play differently from different SEATS) reads
      positive on `_persona_stats_ext`;
      (d) **no schema change appears in the diff.**
      > **Why the old pass/fail was replaced:** it demanded tag's BB defend-vs-RFI hit ≈**22–28%** *(vs EP)* and
      > ≈**40–50%** *(vs BTN)* — **two numbers keyed on WHO OPENED**, i.e. the very opener axis this slice's own
      > no-gos scope OUT. With actor-position nodes only, tag-in-BB has exactly ONE `vs_rfi` node and therefore
      > exactly ONE number: the criterion was **unsatisfiable inside its own no-gos**. Those two figures are also
      > tagged `[UNVERIFIED — needs an H-pass]` in LATER (E1-b's numeric correction), and W5-a1's rule is that an
      > `[UNVERIFIED]` row is **never HARD-gatable** — so they must not be a pass/fail gate anywhere in this file.
      **No-gos:** **the opener-position axis is NOT in scope** — that is **E1-b**, LATER, contract §9 #5, and it
      genuinely needs schema + plumbing. Do not conflate the two axes, and **do not smuggle an opener-keyed number
      into the pass/fail.** **No population band re-anchor — deferred to W4-b** (§5/§11 item 7: measure and report,
      never commit as a CI gate). **Appetite:** ~1 large slice.

- [ ] **W5-b3 — E1-c: position-aware `unopened` for nit / station / fish.** *ICE 7·8·2.*
      **Problem:** those three packs author only `['UTG']` + a wildcard, so **a nit opens a flat 8.0% from UTG1
      through BB** (verified identical at every seat; a real nit runs ≈4% UTG → 15–18% BTN).
      **Solution:** nine-position ladders, the same shape tag/lag/maniac already use.
      **Pass/fail:** per-seat RFI is **monotone non-decreasing UTG→BTN** for all three; metric #3 VPIP/PFR
      **measured against the §5 band and REPORTED — do NOT commit the band as a CI gate; the single band anchor is
      W4-b.** (The monotonicity assertion is a lever-identity pin and IS committable.)
      **No-gos:** JSON only; **no population band re-anchor — deferred to W4-b** (§5/§11 item 7).
      **Appetite:** ~1 small slice.

- [ ] **W5-b4 — W3R-1 target reopen: maniac `vs_limpers` iso + cold-call mix.** *ICE 8·7·4.*
      **Problem:** W3R-1 locked maniac VPIP at **32.8%** against a §5 band of **45–58** on a refuted mechanism claim
      (see the C12 correction block on W3R-1). Two **authored** causes remain: `vs_limpers` is `positions: null` at
      **31.1% raise**, in a lineup where the station limps **48.4%** and the fish **41.0%**; and the third `vs_rfi`
      mix is `{call: 0.9, fold: 0.1}` over ~**24% of the deck**, producing a **34% cold-call rate vs an RFI** — the
      same call-heavy shape **`audit-F11`** struck from the `"*"` catch-all, surviving in an enumerated mix. Maniac's
      **gap of 11.6** at n=1200 is the roster's **only** gap-row failure — the signature of exactly this defect.
      **Solution:** widen the maniac `vs_limpers` iso toward ~**60% raise** from late position; convert the tier-3
      flat mix to a **3bet/call/fold** split; widen EP/MP opens as needed.
      **Pass/fail:** maniac VPIP toward **45–58** and PFR toward **38–48** (metric #3) — **measured and REPORTED
      against the §5 band; do NOT commit either band as a CI gate, the single band anchor is W4-b**; **gap back
      under 10** (the gap is format-INVARIANT per W5-a1, so it IS committable); 3-bet moves toward the DIRECTIONAL
      maniac extreme **without** disturbing the full-ring **4–7%** pool anchor for the other five.
      **No-gos:** JSON only; **do not re-widen the offsuit-ace opens W3R-1 correctly trimmed**; **no population
      band re-anchor — deferred to W4-b** (§5/§11 item 7 auto-FAILs committing an RP6 number as a gate here).
      **Supersedes:** W3R-1's accepted-target note (which stays as a correction record). **Appetite:** ~1 slice.

#### W5-C — engine correctness (small, disjoint files)

> **W5-c1 (board-plays MONSTER guard) was DELETED from this group (R1, 2026-07-25) — it is NOT a parallel W5-C
> slice.** It edits `_made_bucket` in `backend/app/domain/personas_postflop.py`, the serial spine, and it was
> double-owned: listed both here and as absorbed by **W3R-4b**, with different pass/fail text in each place. Its
> problem statement, solution, pass/fail and no-go now live **only inside W3R-4b**, which builds both
> hole-card-participation predicates (`cat == 2` and `cat >= 4`) in one pass over the taxonomy.

- [ ] **W5-c2 — Street-aware texture classification.** *ICE 7·8·3.* **Serial against the `personas_postflop.py`
      spine — NOT a disjoint parallel slice** (see the amended concurrency note above).
      **Problem (restated against COMMITTED code only — R2, 2026-07-25):** `texture.classify`
      (`backend/app/domain/texture.py:31-37`) slices `cards = board[:3]` and therefore classifies **the flop,
      always**, even when handed a five-card board. `_wetness_bet_mult`
      (`backend/app/domain/personas_postflop.py:487` region) calls it with the **full board** and silently gets the
      flop answer — so a board that **pairs on the turn** or **rivers a monotone flush** is, to every persona
      mechanic, still the flop it started as. Inconsistent with `_overcard_count`, which *does* iterate the full
      board. **Provenance note:** `_scare_texture_fold_boost`, `_SCARE_PAIRED` (1.14) and `_SCARE_MONOTONE` (1.22)
      are **W3R-5-INTRODUCED — they do NOT exist at HEAD** (they live only in the uncommitted, HARD-STOPPED first
      W3R-5 attempt). This slice must not be specified or verified against them; they are the *downstream consumer*
      that W3R-5 will build **on top of** this classifier.
      **Solution:** street-aware classification — flop texture by default, opt-in turn/river re-classification —
      **preserving flop-only as the DEFAULT** for every existing caller.
      **Pass/fail:** a board that **pairs on the turn** and one that **rivers a monotone flush** classify
      **differently from their own flop** under the opt-in path; **every flop-only caller is byte-identical**
      (`_wetness_bet_mult` and the grader included); the full suite passes with no fixture re-record.
      **No-gos:** do **not** change any wetness/scare MAGNITUDE here — those are W3R-5's fit seeds.
      **No-gos — FROZEN-INVARIANT BOUNDARY (R10):** `texture.classify` is imported by
      `backend/app/domain/srs.py:128` **inside `spot_signature()`**, which the global no-gos declare **FROZEN**
      (changing it orphans SRS history), and by `backend/app/domain/postflop.py:39`, the **grader**, which §11
      item 13 **auto-FAILs** any slice from touching. Therefore: **flop-only remains the DEFAULT**;
      `srs.spot_signature()` and `postflop.py` / `grade_map*` stay **byte-identical**; note that grader call sites
      pass boards both pre-sliced (`postflop.py:1276,1389`) and whole (`:508,861,1053`) and rely on the internal
      `board[:3]`, so the default path may not change for either form; **pin with the existing
      `backend/tests/test_signature.py` hashes.**
      **Blocks:** the W3R-5 re-spec's texture leg. **Runs BEFORE W3R-5** (one-way dependency; W3R-5 does not
      block this slice — the earlier "Blocks the W3R-5 re-spec" ↔ "Depends-on W5-c2" pair read as circular).
      **Appetite:** ~1 slice.

- [x] **W5-c3 — Buy-in cap / per-hand stack normalization.** ✅ 2026-07-25 (PR #117, `3a18bdf`). *ICE 8·9·2.*
      `_apply_settlement` previously only rebought busted seats (<1bb), so a winning stack compounded unbounded.
      Added a **200bb cap** (2× the ~100bb reference pool §10 calibrates to): a stack winning past the cap is
      trimmed back between hands using the same net-invariant `buyins_bb`-absorbs-the-delta form the existing rebuy
      correction uses, so `net_bb` and table-wide chip conservation are untouched. **No schema change → no
      migration.** 200-hand seeded measurement (same entropy seed both sides): stack range
      **1.42–2475.28bb → 1.23–200.00bb**; SPR-commit gate **20.8% → 23.0%** overall, per-persona 7.4–44.8% →
      10.7–43.5% (**non-degenerate on both sides — not pinned**); single-hand dominance of total absolute movement
      **4.09% → 1.98%**, total absolute movement 34.7k → 21.1k bb over the same 200 hands.
      **Unblocks W3.5.**
      **Problem:** `sim_session.py:117-118,175` — `_REBUY_FLOOR_BB = 1.0`, rebuy only **below** 1bb, **no cap, no
      top-off**. Effective stacks ran **9bb–1374bb** against a contract calibrated to ~100bb (§10). Every
      `spr_commit` (1.2–3.3) is then **always-on or never-on**, and bb/100 is uninterpretable — in the measured
      150-hand sample **one hand was 86% of the net**.
      **Solution:** cap buy-ins (~100–200bb) with per-hand top-off, matching real capped-buy-in cash games.
      **Pass/fail:** effective stacks stay inside the cap across a **200-hand seeded run**; the SPR commit gate
      fires at a measurable **non-degenerate** rate; net bb/100 becomes interpretable.
      **No-gos:** no persona lever change; ship an Alembic migration if the schema moves.
      **Blocks:** **W3.5**. **Appetite:** ~1 slice.

### W3.5 — checkpoint (gates before the final re-anchor)

- [ ] **W3.5 — Human-realism playtest (D9) — RETAINED as a formal blinded gate (owner 2026-07-24).** Blinded seeded
      replays + short free-play, 2–3 poker-literate reviewers, **run on the W3R-REMEDIATED bots.** (The 2026-07-24
      agent-review + owner playthrough INFORMED the W3R fixes but the owner chose to keep a formal blinded human
      check before the final re-anchor — reviewers here don't know the persona labels.)
      **Pass/fail:** reviewers distinguish archetypes above chance AND flag no recurring persona-breaking lines; any
      flagged line feeds a fix before W4. Runs after W3R, before the W4 re-anchor.
      **Prerequisite (C28, 2026-07-25): W5-c3 (buy-in cap) must land first.** Effective stacks ran **9bb–1374bb**
      against a contract calibrated to ~100bb (§10), so `spr_commit` 1.2–3.3 is either always-on or never-on and
      bb/100 is uninterpretable. **A blinded playtest on that table measures stack depth, not persona.**
      **Added acceptance (C10) — an ABSOLUTE calibration question, not only a relative one.** The current acceptance
      is purely *relative* (*"reviewers distinguish archetypes above chance"*), so **a roster uniformly shifted ~4
      VPIP points tight PASSES** — which is exactly what happened. Ask per persona, in addition:
      > *"What format and stakes does this player's range suggest, and would you seat them at 9-max full ring?"*
      Carry the same absolute question into the D9 gate definition in **Cross-cutting discipline** above.

### W4 — highest regression risk, LAST

- [ ] **W4-a — Stack-depth commitment brake (B4, fixes `audit-F2`).** *ICE 7·6·4 — HIGHEST regression risk → sequenced LAST.*
      **Problem:** pricing is pot-fraction only, no stack-depth term — a scared fish never folds an overpair below SPR 2.
      **Solution:** a multiplicative brake on FOLD merit keyed on commitment fraction `c = to_call/stack`, with a
      dead-zone `c₀≈0.25–0.35` (no-op when shallow-cost → byte-identical on deep-stack tests). It's an SPR-interaction
      term (NOT orthogonal to pot price) — compose with, don't replace, the fitted MDF/α price math (RES-D).
      **Depends-on:** the stabilized W2/W3 price/fold equation; **W3.5 (D9 playtest) — any flagged persona-breaking
      line fixed before this slice starts.** Core term `c=to_call/stack` is stack-based (no A1 needed); A1 only if it
      also uses a pot-before/SPR-safety component.
      **Depends-on (ADDED C26, 2026-07-25) — re-fit W3R-3's `spr_commit` values.** The existing commit gate reads
      `stack_bb / pot_bb` (`personas_postflop.py:980`) — the **live pot**, the denominator contract §7 / ledger #12
      forbids. W3R-3's fitted values (**fish 1.4, maniac 3.3**) were measured *against that denominator*, so W4-a's
      denominator unification shifts the effective SPR of **every** gate. Re-fitting them is part of this slice, not
      a follow-up. (Also note **B11 shares this same fold merit** — it stays a LATER bet whose assumption is
      testable only once W4-a has landed; see LATER.)
      **Pass/fail:** a TAG folds ~80%-stack King-high while still stacking off a set; aggression-factor/fold-to-cbet
      survive; `test_clamp_and_jam_edge` green. **No-gos:** scope to facing-fold merit only. **Appetite:** ~1 large slice.
      *(Commit-factor archetype spread: let W2-a's `call_looseness` carry nit-vs-station separation first; widen the `D`
      exponent only if the spread measures too weak.)*

- [ ] **W4-b — Single combined band re-anchor (D11) + coaching seam batch handoff (`track-F1`).** *ICE 8·8·6 — the ONE authoritative re-anchor.*
      **Problem:** mid-spine re-anchors aren't final (population coupling); coaching seams must be handed off coherently.
      **Solution:** the ONE authoritative combined WTSD/AF population-band re-anchor + coverage re-record after the whole
      spine converges — **now absorbing all W3R lever moves too**, and using the **W3R-0 arrival-range FtC harness** so
      the fish/station absolute-band re-anchor is measured, not seeded; report the cumulative graded-coverage delta vs
      the immutable start snapshot; batch-file all accumulated seam-rows (incl. the 8 W3R slices) into
      `professional-teacher-rework` Next.
      **Pass/fail:** all six personas' bands hold with in-file justification; cumulative coverage delta adjudicated (not
      silently accepted); every mechanic slice has a filed seam-row. **No-gos:** no NEW behavior here — calibration +
      handoff only. **Appetite:** ~1 slice.
      > **MISSCOPED — five additions (C27, 2026-07-25).**
      > 1. **Add a PREFLOP leg.** Its pass/fail is postflop-only, but §5's VPIP/PFR rows were just corrected, metric
      >    #3 is their gate, and **6/6 personas miss PFR low**. As written it re-anchors postflop bands around a
      >    **preflop-broken bot**.
      > 2. **N-α resolution is a PREREQUISITE** (the α-ceiling vs §5 fold-to-c-bet contradiction) — **now NOW work
      >    as slice W5-a4**, promoted out of NEXT precisely because W4-b cannot close without it (R7).
      > 3. **Name the kwargs explicitly** — `context=` **and** `street_aggressions=` — not by reference to the
      >    FOLLOW-UP note. (**W5-a3-iii** supplies them.)
      > 4. **Declare, in-file, whether this pass re-anchors TO MEASUREMENT or converges TOWARD §5.** It cannot be
      >    left implicit; the two produce different numbers.
      > 5. **A provenance triple per band it anchors** (W5-a1's `(format, pool, source)`). "In-file justification"
      >    documents the *fitted value*, not the *target's provenance* — and W4-b is the single moment every band
      >    anchors.
      >
      > **Also record: the bands being re-anchored are ENGINE-anchored, not grounded.** `BANDS`
      > (`test_personas_postflop.py:2017-2057`) has a **0.0 fold-to-c-bet floor for four of six personas**
      > (verified: tag `(0.0, 0.55)`, maniac `(0.0, 0.61)`), so the "HARD-today" gate **cannot fail low** — which is
      > exactly why live **nit 0%** and **tag 0%** fold-to-flop-c-bet pass a green suite.

---

## NEXT — validated problems / committed items, not yet spec'd (ship a slice each)

> Direction is *indicated* (these are triaged, grounded problems) but NOT locked — the mechanic, magnitudes, and
> pass/fail belong to `/ai-dlc` slice planning when each is promoted to NOW. Treat the solution sketches as leads.

- **Villain-range rung (a) — coarse static preflop-range-by-position lookup (G1-a) — COMMITTED.** Give the engine a
  cheap, static, per-position preflop range *lookup* (data, not a solver — stays no-solver-compliant). Unlocks the
  **barrel-MORE-on-scare-cards** side of `audit-F3`/B2 (currently deferred) and "you're facing a [type]" reads. Ships with its
  validation: **the LBR-style exploiter harness (D10)** + an offline Spearman equity-correlation check (the only
  non-circular way to validate a range/texture proxy without a solver) + a focused **range-proxy research pass (H1)**
  and **draw-equity proxy validation (H7)**. Source: build-out Track G1 rung (a), Track D10, Track H1/H7.
  **SOUND — two no-gos ADDED (C24, 2026-07-25):**
  - **Ledger-#14 hazard.** This is the item most likely to bake a preflop range table from a **6-max solver
    source** — the exact mechanism of the correction just made, and far more expensive to undo in code than in a
    document. Carries an explicit no-go: ***"author at full-ring widths; 3-bet 4–7%, not 6–10%."***
  - **Boundary.** The barrel-more boost must be scoped **OFF** the made-pair cells W3-d already damps
    (`_overcard_bet_damp` / `_wetness_bet_mult` on MIDDLE_PAIR/TOP_PAIR BET), per contract §9 #8. If it touches
    them, **§7 joint calibration is mandatory**.
- **Preflop price/stack-aware responses — SPLIT (C20, 2026-07-25; MISSCOPED two ways).**
  - **(a) kwargs half — NON-SCHEMA.** Pass raise-size + effective stack + all-in state into the preflop sampler (new
    kwargs, default = today's behavior). A min-raise vs a shove must produce different continue frequencies at the
    same `facing`. Population coupling: re-anchor deferred to a combined pass, as in W4.
  - **(b) authoring half — NEEDS A SCHEMA DECISION.** *"Author price-elastic response nodes"* is **not** non-schema:
    `PersonaFacing` is a **closed 5-value Literal** (`backend/app/domain/content/models.py:65`) with **no size axis**, so this needs
    either a new node axis (schema) **or** a code-side transform on authored weights. Decide which before promoting.
  - **Actor-position half REMOVED from this item → it is now W5-b2** (NOW).
  - **The opener-position parenthetical is CORRECT and stays** (contract §9 #5): that axis genuinely needs a schema
    change → **E1-b**, LATER. The original defect was an *omission of the actor axis*, not a wrong statement.
- **Coaching concept cards per landed mechanic (`track-F2`) → feed teacher-rework.** Point-of-need cards for: position/equity-
  realization, SPR/commitment, river polarity (bluff-catch vs thin value), board texture/overcards, barreling & give-up,
  persona elasticity. Each rides on a landed mechanic; concept cards only (no browsable library); EVs labeled approximate;
  grading behind the async `StrategyProvider`. Owned by `professional-teacher-rework`.
  **SOUND — two notes (C25):** *"(F2)"* in the contract's **§4** namespace = the **stack-depth commitment finding**
  = **W4-a**, currently in NOW — do not resolve it to this card item. Cards must quote **42.9%** for the 3×-pot T1
  threshold (§9 #1) and must **not print any DIRECTIONAL band as a number**.
- **Delayed c-bet (B12-a) — REFILED FROM LATER (C8, 2026-07-25).** Checked-prior-street delayed-c-bet lines.
  **MISFILED as Later:** its stated blocker (A2/A3) **landed in W3-a (PR #96)**, and *"needs numbers"* is the normal
  **FIT-SEED condition** per contract §2, not a deferral reason — W3-c shipped `_STREET_AGG_MULT` on exactly that
  basis. Machinery is present: `postflop_context.py:41-46` `bet_prev_street`. *(The probe/stab half, **B12-b**, stays
  LATER — it needs a genuinely NEW derivation.)*
- **`tanh` soft-saturation aggression (M1) — FAULTY AS WRITTEN; RESCOPE OR DROP (C19, 2026-07-25).**
  - **Premise false:** ordering **already holds** (cap 5.6 > lag 3.2), and the `_AGGRESSION_CAP` docstring
    (`:504-528`) records a per-node exact-weight ordering test proving it. The cap makes the **lever** unresponsive
    above 5.6; it does **not** break the **ordering**.
  - ***"Replace the hard 5.6 cap"* is a direct fix of `audit-F12`**, which contract §8 / §11 item 8 make an
    **auto-FAIL**.
  - **Low yield:** top-pair unopened P(bet) is already **0.873** at the cap.
  - **Rescope to:** *"restore lever monotonicity above the `audit-F12` bound, asymptote preserved"* **+ a maniac W2-a
    opt-in** — maniac is the only pack with **neither** `call_looseness` **nor** `size_elasticity`, and its AF
    measures **3.19–3.32** against the HARD-today §5 band **4–6**. Otherwise **drop this item**.
- **Graded SPR-commit curve (M6) — SOUND premise, three corrections (C23, 2026-07-25).** Smooth commitment over
  (spr_commit − live SPR) × equity × draw × street, per-persona commit strength; keep TPTK able to fold rivers.
  *(Partly complemented by W4-a's fold-side brake — spec the boost-side here.)* Premise **verified**: `:980` is still
  a hard threshold and `made` (rung ≥ OVERPAIR_TPTK) zeroes fold, so TPTK cannot fold a low-SPR river; W2-b already
  made the **damp** side continuous, so only the **boost** side is a cliff — as written.
  **(a)** The old *"/F8"* tag is wrong: `audit-F8` = busted-draw river bluff, **shipped W3-c** (this item is
  `doc12-F8`, SPR-binary). **(b)** M6 and **W4-a** act on the **same fold merit at the same `c`** ⇒ §7
  stacked-multiplier joint calibration **forbids shipping them in different waves without a joint re-fit**.
  **(c)** maniac `spr_commit` is **3.3** today (W3R-3), not doc-12's 4.0.
- **Value/bluff/street/texture sizing overrides (N6) — MISSCOPED, ~¾ ALREADY SHIPPED (C21, 2026-07-25).** Street +
  texture sizing already exist as `sizing_by_node`; the bluff-size axis exists as the two-stage `_bluff_size_factor`
  (`:796-811`, `:1020-1021`). The only unshipped axis — **value-vs-bluff sizing keyed on strength** — is precisely
  the `audit-F14` **anti-sizing-tell no-go** (§8, §7, `test_sizing_spread_no_deterministic_strength_to_size`).
  **Either close this item, or restate it as the genuinely missing work:** `calling_station` and `passive_fish` have
  **no `sizing_by_node` at all**.
- **Bucket/kicker granularity (N4) — MISFILED, DUPLICATES NOW (C22, 2026-07-25).** "Board vulnerability" shipped in
  **W3-d** (`_overcard_bet_damp`, `_wetness_bet_mult`) and the fold side in **W3R-5**; the taxonomy split is
  **W3R-7**, in NOW. **Remaining scope = kicker + relative-nut class ONLY**, and it must sequence **after W3R-7**
  (both rewrite `_made_bucket` + every `_*_BASE` table). It re-anchors the bluff-ordering pin (§7).

### NEW NEXT items (2026-07-25 audit)

- **N-α — PROMOTED OUT OF NEXT → NOW as slice `W5-a4` (R7, 2026-07-25).** It was declared a **hard prerequisite of
  W4-b** while sitting in a column this file defines as *"not yet spec'd"* — anything a NOW slice cannot close
  without is NOW work. The full problem statement, theory, direction, runnable pass/fail and the test anchor
  (`backend/tests/test_personas_postflop.py:603`) now live in **W5-a4** under W5-A. Nothing was dropped.
- **N-raise — BET-vs-RAISE decoupling.** *(Replaces the faulty M4/`doc12-F6` framing — see C18 below.)* `agg_scale`
  multiplies **both** the unopened BET merit (`:924-926`) **and** the facing-a-bet RAISE merit (`:909-912`), so **no
  single `aggression` value** yields maniac's c-bet band **and** a human raise-vs-c-bet rate. Measured uniform-range
  raise-vs-flop-c-bet at ½ pot HU: nit **.089** · tag **.257** · lag **.338** · maniac **.462** · station **.021** ·
  fish **.125**; live lag **55.6%**, maniac **40%**; **human reference 12–20%**. There is **no lever, no §6 metric
  and no §5 keystone row** for this. W3R-6 built the right *shape* (`_ONE_PAIR_RAISE_DAMP = 0.35`) but gated it
  **facing-a-raise only**, so it never fires facing a single c-bet — the measured spot. **Needs W5-a3-ii's metric #7
  first.**
  > **Why M4/`doc12-F6` ("split `aggression` into value/bluff × bucket × street") is FAULTY (C18)** — kept as the
  > audit trail: value and bluff are **already split** (`personas_postflop.py:919` uses `bluff_mass` from
  > `bluff_freq` for the bluff cell, `:924` uses `agg_scale` from `aggression` for everything else;
  > `docs/research/12-persona-engine-and-realism-fixes.md:575` records this correction explicitly — the roadmap
  > condensation re-introduced the welded framing the source doc had struck). *"× street"* on the **value** side
  > breaches contract §4 **P4** (*"made `_AGG_BASE` does NOT decline"*) and **auto-FAILs §11 item 3**. The `F6` tag
  > was stale too: `audit-F6` = the P5 river bet floor, **shipped W1-a**. The real axis is N-raise.
- **N-donk — Donk-lead damp / check-to-the-aggressor.** The unopened branch (`:916-962`) applies `_AGG_BASE` /
  `_CHECK_BASE` **identically** whether or not the seat was the previous aggressor; `is_aggressor` is consumed only
  by `_sizing_dist` (`:623-629`) and only when `sizing_by_node` is set — which `calling_station` and `passive_fish`
  do **not** author, so it is **100% unread for both**. Measured: **station 19/36 bets (53%)** and **fish 14/32
  (44%)** are **leads into the previous street's aggressor**, vs tag 1/12, nit 1/5, lag 3/17, hero 1/15. Both of the
  station's two biggest pots were won this way. Needs a **`donk_lead` damp** on the unopened BET candidate when
  `not is_aggressor` **and** a live aggressor exists, scaled by a per-persona lever. **No existing dial reaches it.**
- **N-cbet — Bet-side combined-product re-level.** 5/6 personas measure **below** the §5 c-bet
  band, maniac by **20pp**. This is §7's own **stacked-multiplier warning realized**:
  `_MW_VALUE_DAMP**k × _overcard_bet_damp × _wetness_bet_mult × _position_agg_mult(OOP)` compound on the **same**
  TOP_PAIR/MIDDLE_PAIR BET cell. Worked example — TAG top pair, 1 overcard, two-tone, 3-way, OOP:
  `0.64 × 0.75 × 0.85 × 0.75 = 0.306`, taking P(bet) from **0.746 to 0.473**, a **27pp** drop. Every W3/W3R slice
  added a damp; **none added a compensating re-level**, and §7 requires the **combined** product be calibrated, not
  each factor. **W4-b cannot fix it** — it is explicitly *"calibration + handoff only, no NEW behavior"*, so its only
  tool would be widening bands away from the grounded targets, i.e. **band-laundering**. **Do not start until W5-a2
  rules on whether the c-bet band itself is right** — if that row is 6-max-derived, the engine may be closer to
  correct than the band, and this item shrinks to the maniac alone.

### Closed / refiled out of NEXT (2026-07-25)

- **CLOSED — Same-street 3bet+ under-folds (N2-claude) (C5).** **Shipped as W1-b.**
  `latest_aggressor_contribution_bb` (`personas_postflop.py:857-860`) is the pre-aggression denominator =
  `audit-F9` / contract §4 **P7**. The item's old `:468-474` anchor is **stale** — that range now holds W3R-5's
  scare-fold constants. **Residue:** the un-opted-in **legacy branch at `:858`**, which is the separately-filed
  estimator `to_call` item (LATER).
- **REFILED — Cleaner GTO-baseline for grading (`track-F3`) (C6).** Moved out of this roadmap; **owned by
  `professional-teacher-rework`.** It is **grader-side**, and contract §7 says this rework is **bot-side only** —
  §11 item 13 **FAILs any slice touching graders**. *(Tag collision: `track-F3` here is NOT `audit-F3` —
  overcard / range-favorability — which was built as W3-d.)*

## LATER — bets (problem · confidence · assumption to test) — the deferred / architecture tail

- **Villain-range rungs (b) + (c) (G1-b/c).** (b) persona-conditional range prior updated by the betting line — medium;
  (c) full equity-vs-range estimator — the only NO-GO-ADJACENT rung vs "no solver tables". **Confidence: med/low.** Assumption:
  whether rung (a) realism is enough, or the barrel-more/exploit payoff justifies climbing. Decide the rung at promotion.
- **Exploit-coaching in-program ("you're facing a [type], here's how to adjust") (`track-F4`).** *High-level placeholder — the owner
  wants this eventually.* Teach the hero to adjust vs each archetype (vs a station value-bet thinner / never bluff; vs a nit
  fold to aggression). **Depends on:** villain-range rung (a) exposed to the grader **+ a new research pass for adjustment
  magnitudes (H2)** — the grounding research explicitly deferred exploit-coaching. **Context/source docs:**
  `persona-realism-FULL-BUILDOUT.md` Track F4 + Track G1; audit `§10.5` + `§9.2` (coaching-scope = baseline+behavior only
  this pass); studies RP1/RP8. **Confidence: med.** Assumption: the coaching payoff justifies the villain-range + research cost.
- **Blocker / combinatorics awareness on the river (G2).** A hand representation richer than the 7-rung strength ladder so
  river value/bluff selection can use blockers/removal (the dominant modern river factor). **Confidence: low.** Assumption: a
  rank-only engine's river ceiling is unacceptable. (No "% of benefit" figure — that unsupported claim was struck.)
- **Multiway theory beyond a 4-way tier (G3).** Calibrated 5+way adjustments. **Confidence: low** (solver support for 3+way is
  thin). Direction-only until researched (H5). **Assumption:** that 5+way spots are frequent enough (measured
  **4.15%** below) for calibrated magnitudes to change any observable persona stat — test by measuring whether the
  4-way-tier cap is the binding error in multiway hands before commissioning H5.
  **NUMERIC CORRECTION (C9, 2026-07-25):** the old *"5-way ≈ 1.6% of hands"* is wrong. **Measured in this repo's own
  band harness** (`tests/test_personas_postflop.py::_play_hand`, **9-seat mixed roster, n=2000, seed 20260710**):
  exactly-5-way **3.60%**, 5+way **4.15%** — **2.3–2.6×** the cited figure. Same mechanism as the VPIP error: a
  number from a **reg-heavy / 6-max** frame carried into a **limp-heavy 9-max** pool (station limps **47.2%**, fish
  **39.5%**). **The deferral STANDS** — the conclusion survives at 4%.
- **Out-of-position equity-realization damp (B11).** An OOP facing-continue / bluff-catch realization damp (the R-factor's
  effect on CALLING, not just betting). **Confidence: med.** Deferred — risks colliding with the W4 commitment brake +
  faced-price defense. Do NOT claim W3-b already represents it.
  **SOUND — two additions (C16, 2026-07-25).** The *"do NOT claim W3-b already represents it"* warning is **verified
  correct**: `personas_postflop.py:959-960` applies `_position_agg_mult` **only** on the aggressor-side BET
  candidate; nothing reaches call or fold merit. **(i)** After W3R-5 and W4-a land, fold merit carries **two**
  multiplicative boosts, so B11 must arrive **with §7 joint calibration** and an explicit *"boost, never an asserted
  floor"* (A1 guardrail). **(ii) Assumption (replaces the old queue-position claim — R12, 2026-07-25):** that the
  roster's largest measured miss — nit/tag fold-to-flop-c-bet of **0%** — is **position-driven**, i.e. an OOP
  realization damp on the CALL/FOLD side is what moves it. **Test after W4-a lands** (W4-a acts on the same fold
  merit and would confound the read). Stated as an assumption on purpose: a LATER bet holds no queue position.
- **Probe / stab frequencies (B12-b).** Checked-prior-street **stab** lines. **Confidence: low** — solver-sanctioned
  but published only qualitatively; needs a research pass (H4) for numbers. **Assumption:** that the missing
  `prev_street_checked_through` derivation is worth building for the stab line alone — test by measuring how often
  a checked-through street even occurs in the band harness once B12-a (delayed c-bet) has landed.
  **SPLIT (C8, 2026-07-25): B12-a (delayed c-bet) was MISFILED and moved to NEXT.** B12-b stays here because it
  needs a **NEW `prev_street_checked_through` derivation** — the **opponent's** prior-street *non-aggression* —
  which `bet_prev_street` (the **bot's OWN** prior aggression) does **not** provide. The old *"Reuses A2 + A3
  machinery"* claim is therefore corrected: it covers **B12-a only**.
- **Opener-position-aware preflop defense (E1-b) + limper-count ranges (E3).** **Confidence: med.** Deferred — needs a
  `backend/app/domain/content/models.py` schema change (**opener**-position axis on `vs_rfi`) + sampler plumbing (A5/A6) + an
  Alembic-style data-shape migration + new tests. **Owner gate.**
  > **E1 SPLIT INTO THREE (C7, 2026-07-25).** **E1-a** (actor-position `vs_rfi` + `vs_limpers`) → **PROMOTED to NOW
  > as W5-b2**: JSON-only, no schema, no plumbing (`backend/app/domain/personas.py:76-79` filters
  > `node.positions` for **every** facing; `backend/app/domain/content/models.py:205-219` `_node_ordering` permits
  > explicit-position nodes before the wildcard;
  > tag/lag/maniac already ship nine explicit `unopened` position nodes — the pattern is in production).
  > **E1-b** (opener-position axis) → **stays LATER, this bullet** (contract §9 #5), Owner-gate retained.
  > **E1-c** (position-aware `unopened` for nit/station/fish) → **NOW as W5-b3.**
  >
  > **NUMERIC CORRECTION.** The old claim *"BB defends ~3–3.5× as wide vs a BTN open as vs a UTG open"* is struck.
  > Published full-ring BB continue is ~**22–28%** vs an EP open and ~**40–50%** vs a BTN open ⇒ **~1.7–2.0× on
  > total (call+3bet) continue frequency**. The original figure also had **no stated denominator** (the 3bet-only
  > ratio is far larger than total defense), so **as written it was undefined, not merely off.**
  > `[UNVERIFIED — needs an H-pass]`
- **Persona sub-types (multiple packs per archetype) (`track-F5`).** `VillainType` is enum-locked. **Confidence: med.** *Direct enabler
  for Hidden-persona mode, not for realism per se* — sequence it WITH that mode, not here (**that sequencing call is
  correct — keep it**). **Assumption:** that within-archetype variety (two different TAGs) is what makes the table
  feel real, rather than the six archetypes being individually correct — test by asking the D9 playtest reviewers
  whether the *sameness* of same-type seats, as opposed to any single bot's lines, is what breaks the illusion.
  **DE-RISKING NOTE (C17, 2026-07-25):** the natural fear — breaking the frozen `spot_signature()` — is
  **unfounded**. `srs.py:53,63` hash `spot.villain_type.value` as a **string**, so **ADDING** an enum member changes
  **no existing hash**. This bet is **lower risk** than the bullet implies.
- **Reference-pool recalibration on an ACTUAL pool change (H6′).** If the target pool ever *changes* from "online
  low-mid 9-max ~100bb," the whole keystone needs recalibration. **Confidence: n/a** — a genuinely conditional
  trigger, not a planned build. **Assumption:** that a pool change would be *noticed and declared* — the ledger-#14
  failure was a silent mismatch, not a declared change; test by checking that W5-a1's provenance triple makes the
  pool of every §5 row explicit enough that a future divergence is visible without an audit.
  > **H6 WAS MIS-SPECIFIED (C15, 2026-07-25) — split.** The old H6's trigger was *"if the target pool ever
  > changes"*, but the failure that actually occurred was the pool **NOT** changing while the keystone silently
  > encoded a **different** pool — a case that condition **can never be true for**. Contract §10 already confessed
  > global 6-max provenance and localized the consequence to one cell. So H6 is rewritten as an **UNCONDITIONAL
  > provenance audit and PROMOTED to NOW as W5-a2**; **H6′** (this bullet) keeps the genuinely-conditional half.
- **Solver-boundary revisit for kicker/equity precision (N4/N5 ceiling).** **Confidence: low.** Assumption: whether
  "simplified-but-winning" heuristics suffice, or this is the trigger to revisit the no-solver line. EVs stay *approximate* either way.
- **Rigorous semi-bluff F\* fold target (from W2-b).** W2-b shipped a *directional* below-T1 fold policy (existing price-
  aware fold merit stands) after both reviewers flagged the roadmap's "fold merit ≈ F\*" as conflating the OPPONENT's
  required-fold frequency with the BOT's own fold probability. A principled version would define the bot's own below-T1
  fold target q from a justified model and set fold merit last as `q/(1-q)·Σ(nonfold merits)` (the closed form both
  reviewers derived). **Confidence: low.** Assumption: whether the directional policy is realistic enough, or a
  defensible q model is worth the machinery. Pairs with the draw-equity proxy calibration (H7).

---

## Global out-of-scope / NO-GOS (inherited invariants — doc 12 §6.3)

- **No solver tables** — heuristic + interim EV only; EVs labeled *approximate*. *(Villain-range rung (a) is a static data
  lookup, NOT a solver — it stays inside this line; rung (c) is the no-go-adjacent one.)*
- **Grader untouched** — do NOT edit `grade_map*.py` / `postflop.py` graders; `spot_signature()` + `TAXONOMY_VERSION` stay
  **frozen** (they're the grader's, not the bots'). Blast radius = bot side only.
- **Domain purity** — `personas.py` / `personas_postflop.py` stay pure domain (no web/DB imports).
- **Action draw stays the FIRST `rng.choices`** — `range_estimate.py:278` replays it via a capture-rng; any new randomness
  comes *after* the action draw (`audit-F2`'s two-stage bluff-sizing is the template).
- **New args default to today's behavior** (mirror `is_aggressor=False`) so `range_estimate` + the population harness stay
  byte-identical until the live loop deliberately opts in.
- **Softmax law** — every magnitude is fit-to-observed-stat, not a drop-in constant (no cosmetic changes).
- **Re-anchor bands levers-first, ONCE per cluster** — tune pack levers before widening test bands; the ONE authoritative
  combined re-anchor is W4; widen only with in-file justification.
- **Re-record `coverage_baseline.json` deliberately** with each play-changing slice + report cumulative delta vs the
  immutable snapshot; any cumulative loss needs explicit adjudication.
- **Anti-sizing-tell** — value hands must not become size-readable (`test_sizing_spread_no_deterministic_strength_to_size`);
  `audit-F14` is an INTENTIONAL-LEAVE, do not "fix" it.
- **INTENTIONAL-LEAVE** — `audit-F12` (aggression cap compresses strong hands — a deliberate RES-D saturation fix) + `audit-F14` (sizing
  decoupled from strength on purpose). Do NOT "fix" these.
- **`test_bluff_ordering_across_personas_at_fixed_size`** pins `station < nit < fish < tag < lag < maniac` — any bluff-path
  change re-anchors it deliberately.
- **The architectural line** — range-blindness (`audit-F16`) is currently by design. The barrel-more range side, exploit-coaching,
  and villain-range rungs (b)/(c) push against "no solver tables"; building them past rung (a) is an owner-gated architecture
  decision, not a bug-fix.

---
*Handoff: on approval, the top unchecked NOW slice — **W3R-4b** (W0-a/b/c and W3R-0 are merged and ticked; note the
R3 wave-order correction sequences **W5-A + W5-C before the W3R tail**, so W5-a1 → W5-a2 → W5-a3-i/ii/iii → W5-a4 and
W5-c2 → W5-c3 land first where a W3R-tail slice depends on them) — goes to `/ai-dlc` for per-feature planning. One slice at a time;
re-read pass/fail state between slices (agents falsely mark work done); fresh `refuter` at each fan-in.*
