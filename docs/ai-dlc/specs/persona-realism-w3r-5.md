# W3R-5 — Defense-side texture/scare fold brake (#8) — NEW MECHANIC

**Slice of:** `docs/ai-dlc/roadmap/persona-realism.md` → W3R (bot-review remediation). Builds **#8**. From the
2026-07-24 hand-history review: station H54 (monotone call-down), station H100 (four-flush call-down), nit H41,
raise-wars H61/H103/H117. **NEW MECHANIC** — the first board-texture signal on the DEFENSE side.

> **The W3-d damps are BET-only.** `personas_postflop.py:769–771` applies `_overcard_bet_damp` × `_wetness_bet_mult`
> to the unopened BET candidate for MIDDLE_PAIR/TOP_PAIR. The facing-chips branch (`:690–747`) has **zero board
> signal**: `fold_merit` at `:722` is `_FOLD_BASE[bucket] × _price_factor(...)`, optionally `× _MW_CATCH_TIGHTEN **
> (opponents-1)` at `:725–726`. Price and headcount, never texture, never aggression heat. A calling station calls
> a monotone-board barrel with second pair at the same rate it calls a dry rainbow one.

## Goal (one line)
Give the FOLD side the board signal the bet side already has: a bounded MULTIPLICATIVE fold-merit **boost** for
one-pair-class buckets on monotone / paired / overcard-heavy boards and into multi-aggression streets — a boost that
enters normalization, **never** an asserted fold floor.

## Why (the gap / root cause)
1. **No defense-side texture (F3/F20 fold half).** The vulnerability brake was built one-directional. Betting one
   pair slows on a wet board; *calling down* with it does not. On a monotone flop a station's second pair is drawing
   near-dead to the villain's flush half of the time and the merit ladder cannot see it (H54, H100).
2. **No aggression-heat signal.** `opponents` (headcount) is threaded; the number of BET/RAISE actions on the current
   street is not. Facing a bet **and** a raise is a different world from facing one c-bet — the engine prices them
   identically. This is the raise-war leak (H61/H103/H117) and the exact residual `_FOLD_BASE`'s ACE_HIGH comment
   (`:242–251`) deferred: *"the H117 leak is specifically a FACING-A-RAISE float, so the fix is re-routed to a
   raise-scoped damp in a later slice."* This is that slice.
3. **Why a boost and not a base cut.** W3R-3 #5 MEASURED and DROPPED a global `_FOLD_BASE[ACE_HIGH]` cut: it pushes
   the fish's arrival-range fold above the RES-D α = f/(1+f) ceiling. A **conditional** boost — live only on scary
   boards / heated streets — is the narrow tool the global constant could not be.

## Scope / files to touch
- `backend/app/domain/personas_postflop.py` — NEW fold-side helpers placed adjacent to the bet-side ones (after
  `_wetness_bet_mult`, `:371–381`), MIRRORING their derivation and REUSING `_overcard_count` (`:345`),
  `texture.classify` (`:27`) and `_VULNERABLE_ONE_PAIR` (`:342`) — **no second texture taxonomy, no new bucket**:
  - `_OVERCARD_FOLD_BOOST(count)` — 0 → 1.00, 1 → ~1.15, 2+ → ~1.30 (FIT SEEDS; the inverse-direction mirror of
    `_overcard_bet_damp`, deliberately gentler — the fold side is α-ceilinged).
  - `_scare_texture_fold_boost(board)` — first-match chain mirroring `_wetness_bet_mult`'s shape:
    monotone ~1.30 · paired/trips ~1.18 · connected ~1.12 · else 1.00. `len(board) < 3` → 1.0.
  - `_AGGRESSION_FOLD_TIGHTEN ** min(max(street_aggressions - 1, 0), _AGGRESSION_FOLD_CAP)` — seed ~1.25, cap 2
    extra aggressions. `street_aggressions <= 1` ⇒ exponent 0 ⇒ **byte-identical**.
  - `_SCARE_FOLD_CAP` — the combined product is capped (~2.0). The structural mirror of the bet side's floor ≥0.25.
  - **Call site: `:727` ONLY** — the boost multiplies `fold_merit` after the `_MW_CATCH_TIGHTEN` block (`:725–726`)
    and before `entries.append((ActionType.FOLD, fold_merit))`. Scoped to `_VULNERABLE_ONE_PAIR` + ACE_HIGH.
  - NEW kwarg `street_aggressions: int = 1` on `sample_postflop_decision` (`:593–607`).
- `backend/app/domain/table/postflop_context.py` — NEW pure helper `street_aggression_count(action_history, street)`
  = the number of BET/RAISE actions by ANY seat on `street` (sibling of `bet_prev_street`, `:88–105`). Counts the
  actor's own bet, so hero-bet→villain-raise reads 2 (the H117 facing-a-raise float) and a lone faced c-bet reads 1.
- `backend/app/domain/table/play.py` — derive it next to `derive_postflop_context` (`:218`) and pass it through
  `bot_decision` → `_postflop_decision` (`:140–159`, `:229–232`).
- `backend/app/domain/table/range_estimate.py` — **estimator-parity law.** New `_Ctx.street_aggressions` field
  (`:86–98`), counted in `_replay_contexts` (reset on the street change at `:131–136`, incremented on the BET/RAISE
  branch at `:191–201`), passed at the `sample_postflop_decision` call (`:278–289`). The texture legs need NO new
  threading — the estimator already passes the real `board`, so they are in parity for free.
- Tests: `backend/tests/test_personas_postflop.py` (capture-weight unit tests), `backend/tests/test_postflop_context.py`
  (the counter), `backend/tests/test_range_estimate.py` (parity, template at `:405`),
  `backend/tests/test_arrival_range_ftc.py` (the seeded scary-vs-dry directional check).
- Re-record the seeded fixtures this moves (golden / coverage_baseline / limper belt), P1/P2a precedent.
- **A new SCALAR kwarg, NOT a `PostflopContext` field** — deliberate. Constructing a `PostflopContext` inside the
  estimator would default `in_position=False`, which ACTIVATES the W3-b OOP damp (`_position_agg_mult`, `:586–590`)
  for every position-sensitive persona on every unopened node — a silent estimator behavior change. A scalar with
  default 1 has no such coupling.
- **No new persona lever, no JSON/pack change, no new bucket, no taxonomy edit, grader frozen.**

## Pass/fail (HARD)
- **(i) Texture direction — exact-weight, no sampling.** Capture-rng weight test: for a MIDDLE_PAIR (and TOP_PAIR)
  hand facing the SAME bet at the SAME price with the SAME `opponents`, the FOLD merit on a **monotone** board and on
  a **paired** board and on a **2-overcard** board is each **strictly greater** than on a dry rainbow no-overcard
  board. Dry rainbow zero-overcard is **byte-identical** to today (all legs = 1.0).
- **(ii) Aggression direction — exact-weight.** Same spot, `street_aggressions` 1 → 2 → 3: fold merit is strictly
  increasing, and flat from 3 → 4 (the `_AGGRESSION_FOLD_CAP` tier). `street_aggressions=1` (the default) is
  **byte-identical** to today.
- **(iii) Bounded.** The combined multiplier is ≥ 1.0 always and ≤ `_SCARE_FOLD_CAP` on the worst-case stacked spot
  (monotone + paired + 2 overcards + 3 aggressions) — asserted directly on the helper.
- **(iv) Seeded directional target.** In `test_arrival_range_ftc.py`, partition each persona's flop arrival spots by
  `classify(board)` into SCARY (monotone or paired) vs DRY (rainbow + unpaired): fold-to-bet at a fixed size is
  strictly HIGHER on the scary partition than the dry one for `calling_station`, `nit` and `passive_fish`. This is
  the roadmap's directional pass condition, made runnable and baseline-free.
- **(v) Estimator PARITY.** New test on a scripted monotone-board bet-then-raise node: `_postflop_action_dist(...)`
  equals a direct `_CaptureFirstChoices` capture of `sample_postflop_decision(..., street_aggressions=k)` on the same
  inputs, for the SAME k the replay derived — and the k=1 distribution DIFFERS (the equality is discriminating).
  Mirrors `test_estimator_river_dist_equals_live_polarized_policy` (`test_range_estimate.py:405`).
- **(vi) Fold-side ONLY — regression guard.** The bet-side W3-d scoping (`:769–771`) is untouched: the existing
  overcard/wetness BET tests stay green unmodified, and a test asserts the unopened BET merit for a one-pair hand on
  a monotone board is UNCHANGED by this slice (the brake never reaches the aggressive candidate).
- **(vii) Bands.** **Every persona's AF / WTSD / fold-to-c-bet band stays IN its existing frozen band** and the LIVE
  T4 arrival bands (`test_arrival_range_ftc.py` `FLOP_BANDS`: station 0.33 ≤ 0.15 and 1.5 ≤ 0.40; fish 0.33 ≤ 0.38
  and 1.5 ≤ 0.80) still pass — these upper edges are the α-ceiling proxy and they BIND on this mechanic.
  **HARD-STOP:** if no magnitude set inside the ranges below satisfies (iv) AND (vii) together, STOP and report — a
  band re-anchor is an owner decision (§7; the W3R-2 exception was fish+station WTSD ONLY).
- **FIT SEED ranges** (measure the exact value in, never drop it in): overcard 1 → 1.08–1.25, 2+ → 1.15–1.45 ·
  texture monotone 1.15–1.45, paired 1.08–1.30, connected 1.05–1.20 · `_AGGRESSION_FOLD_TIGHTEN` 1.10–1.45 ·
  `_SCARE_FOLD_CAP` 1.7–2.5. Under the softmax law a ×1.3 fold merit against a station's `call_looseness` 4.0 call
  merit moves observed fold only a few points — below ~1.10 per leg the change is COSMETIC and fails the slice.
- `./scripts/verify.sh` green; `ruff check .` clean; `content/` JSON validates; cumulative graded-coverage delta vs
  the immutable snapshot reported.

## Out of scope
- **NO fold floor. NO asserted minimum fold frequency.** (A1 guardrail — see Invariants.)
- The BET side (W3-d scoping at `:769–771`) — do not re-scope, re-tune, or extend it.
- The CALL / RAISE merits in the facing branch (`:731–747`) — the boost touches `fold_merit` only; call/raise absorb
  the complement through normalization, as F1 does.
- The unopened / matched-with-option branch entirely.
- `in_position` / `bet_prev_street` estimator threading — a PRE-EXISTING W3-b/W3-c parity gap (the estimator passes
  `context=None`); not created by this slice, not fixed by it. Flag it, do not widen scope.
- Villain-range-aware defense (F16), blocker logic, turn/river absolute fold bands (ungrounded), any preflop/JSON
  change, any grader touch (`spot_signature()` frozen), any band re-anchor (bust ⇒ owner STOP).

## Invariants honored
- **A1 GUARDRAIL — BOOST, NEVER A FLOOR.** The mechanic is a multiplicative factor on `fold_merit` BEFORE
  normalization. No code path clamps, `max()`es, or lower-bounds a fold merit or a fold FREQUENCY; no α/MDF-derived
  quantity is asserted as a minimum. Every acceptance test is a **relative** inequality (scary > dry, k=2 > k=1) or a
  bounded-range check — **no test asserts "fold rate ≥ X"**. The only absolute fold assertions in the suite remain
  the pre-existing two-sided T4 bands, whose UPPER edges this slice must not bust.
- Softmax law — magnitudes are FIT SEEDS measured to a target stat, merits clamp ≥0 → normalize → `rng.choices`,
  never argmax.
- Stacked-multiplier discipline (§7): the combined product is capped, and it is the COMBINED product that is
  calibrated against the T4/AF/WTSD gates, not each leg independently.
- Default-off byte-identity: `street_aggressions=1` and dry-rainbow-zero-overcard reproduce today exactly. The action
  draw stays the FIRST `rng.choices` (the boost is a pre-draw merit edit).
- Estimator parity (§7, Codex-Sol HIGH): the aggression context is threaded to `range_estimate.py` with a parity
  test; the texture legs are in parity by construction (board is already an argument).
- Domain purity (no web/DB in `app/domain/`) · results freq+EV · `spot_signature()` + `TAXONOMY_VERSION` frozen ·
  one strength classifier, one texture classifier · frozen bands respected (in-band or STOP) · anti-sizing-tell
  untouched · `_MW_CATCH_TIGHTEN` semantics unchanged (this composes with it, does not replace it).

## Verify-by
`./scripts/verify.sh` green; the texture-direction, aggression-direction, bound, fold-side-only regression, seeded
scary-vs-dry, and estimator-parity tests all pass; every persona's AF/WTSD/ftc band IN-band and the four T4 arrival
bands green; `ruff check .` clean. Report: the fitted magnitudes for all four constants, per-persona re-measured
AF/WTSD/ftc, the scary-vs-dry fold deltas for station/nit/fish, the T4 curve movement, which fixtures re-recorded,
and the cumulative coverage delta.
