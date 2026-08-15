# Contract map — persona de-robotization (phase-3 ruling A, slice 1)

**Bottom line: three contracts constrain this slice, and two of them will fail
silently rather than loudly if violated. First, the villain-range estimator
requires that the action draw stay the sampler's very first `rng.choices()`
call, so no new random draw may be inserted ahead of it. Second, hero's
turn/river grading only recognises bot bets that land within 0.06bb of a fixed
pot-fraction grid, so continuous jitter of postflop bet sizes would silently
delete hero grading coverage — the exact defect `T-cover` already tracks.
Third, one shared random-number stream drives every decision in a run, so
adding any draw anywhere re-rolls every hand after it; before-and-after
comparisons must therefore be distributional, never hand-matched.**

Scanned 2026-08-15 by the `contract-mapper` agent plus direct director reads.
Every claim below carries a `file:line` reference and was verified against the
code, not inferred from documentation.

## 1. The decision call chain

**Preflop.** `table/play.py:209-232` `bot_decision()` derives the facing state
(`_preflop_facing`, `play.py:86-102`) and the arrival stratum
(`_preflop_opener`, `play.py:105-118`), then calls `_preflop_decision()`
(`play.py:121-151`), which calls `personas.sample_preflop_action()`
(`personas.py:61-110`). That function performs a first-match-wins scan over the
pack's `preflop` nodes and makes exactly **one** `rng.choices()` call
(`personas.py:107`). If the drawn action is a raise, the size is computed by
`table/sizing.py:preflop_raise_to()` (`sizing.py:190-214`) — a pure
deterministic formula with **no randomness at all**.

**Postflop.** `bot_decision()` (`play.py:233-287`) assembles pot, opponent
count, aggressor flag, pre-aggression pot, and the context objects, then calls
`_postflop_decision()` (`play.py:154-195`) →
`personas_postflop.sample_postflop_decision()`
(`personas_postflop.py:816-1383`). That function makes one `rng.choices()` call
for the action and a second for the bet size, the second reached only on
BET/RAISE (`personas_postflop.py:1364,1376`).

**Hand loop.** `advance_to_hero()` (`play.py:290-332`) drives `bot_decision()`
until the hero seat acts or the hand ends. Callers:
`services/sim_session.py:256` (live product), `tools/export_analytics.py:243`
and `tools/detection_corpus.py:597` (both seeded harnesses).

## 2. Contract 1 — the action draw must stay the first RNG call

`table/range_estimate.py:344-361` defines `_CaptureRng`, a duck-typed stand-in
that implements **only** `.choices()` and short-circuits on the first call in
order to capture the action distribution the sampler would have drawn from.
The samplers' own comments state the rule explicitly
(`personas_postflop.py:902-905`, `:1205-1208`).

*(Precision added 2026-08-15 after review: the capture path is **postflop
only**. Preflop range estimation mirrors the pack probabilities directly and
never calls `sample_preflop_action` (`range_estimate.py:292`). The rule below
still governs both samplers as a design discipline, but the live breakage risk
is postflop.)*

Consequences for this slice:

- A new draw inserted **before** the action draw either raises `AttributeError`
  (if it is not `.choices()`) or silently captures the wrong distribution and
  corrupts the villain-range feature the hero sees.
- A new draw **after** the action draw is safe for the estimator, which never
  reaches the sizing stage (`range_estimate.py:350-351,361`).
- **Preflop sizing jitter is safe by construction**: `preflop_raise_to()` runs
  after `sample_preflop_action()` has already returned, so it cannot precede
  the action draw.

## 3. Contract 2 — bot bet sizes must stay on the recognised grids

Hero's grading maps a live decision to a gradeable spot only if the villain's
bet sizes are recognisable. Two separate bands apply.

**Postflop — a fixed pot-fraction grid with a 0.06bb tolerance.**
`grade_map_postflop._is_canonical_bet()` (`grade_map_postflop.py:175-184`)
accepts a bet only when it is within `_CANON_BET_TOL = 0.06` bb
(`grade_map_postflop.py:172`) of one of `RECOGNIZED_BET_FRACS = (0.33, 0.5,
0.75, 1.0, 1.5)` times the pot (`sizing.py:58`). The comment at
`grade_map_postflop.py:164-171` records that an earlier, tighter version of this
check produced **zero postflop facing offers in 1,123 hands** — the same class of
failure as the open `T-cover` item.

At a 10bb pot the tolerance is 0.6% of pot. Continuous jitter of the drawn
pot-fraction would therefore push most bets off-grid and silently un-map
hero's turn and river lines.

> **Design consequence, binding on this slice: postflop de-robotization is
> re-weighting of the existing on-grid fraction distributions only. No
> continuous postflop size jitter. `RECOGNIZED_BET_FRACS` and the grader are
> not touched.**

**Preflop — value bands with hard caps.** `grade_map_preflop.py:47-60` pins
`_STD_OPEN_CAP = 3.0` (hero's own open inside a 3-bet/4-bet pot),
`_OVERSIZE_OPEN_CAP = 4.5` (largest villain open still mapped when hero faces
it), `_THREEBET_MULT_CAP = 3.5`, and `_FOURBET_MULT_CAP = 2.4`. Opens above
4.5bb return `None` — ungradeable.

Three personas sit **exactly on a cap** today, so symmetric jitter would push
half their draws off the gradeable band:

| Persona | Lever | Value | Cap | Jitter direction permitted |
|---|---|---|---|---|
| maniac | `open_bb` | 4.5 | 4.5 | downward only |
| tag, lag, nit | `threebet_mult` | 3.5 | 3.5 | downward only |
| tag, **lag** | `fourbet_mult` | 2.4 | 2.4 | downward only |
| maniac | `fourbet_mult` | 3.0 | 2.4 | already above cap (pre-existing) |

*(Corrected 2026-08-15 after review: lag's `fourbet_mult` is also exactly at
the cap and was omitted from the first draft of this table.)*

**These caps are a simplification — grading is path-dependent.** A villain open
faced directly by hero may reach 4.5bb, but in a hero-3-bet line the villain's
open must be ≤3.0 and the 3-bet cap is 3.5 × the *canonical position open*, not
3.5 × the actual faced open (`grade_map_preflop.py:142,174`). Lines mixing
calls and raises are rejected before sizing is examined at all
(`grade_map_preflop.py:91`), so there is no gradeable iso band in the current
mapper. The table above is the outer envelope, not the full rule.

> **Design consequence: every jittered preflop size is DRAWN FROM a valid
> truncated interval, never sampled symmetrically and then clamped. Clamping
> piles probability mass on the boundary — recreating a determinism at exactly
> the value neither gate can see — and for a lever already outside the band it
> collapses every draw to the boundary, which is a centre shift rather than
> variance. At-cap levers draw one-sided downward.**

## 4. Contract 3 — one shared RNG stream per run

The seeded harnesses create a single `random.Random(seed)` and pass that **same
object** to every `bot_decision()` call for every hand of the run
(`detection_corpus.py:585-597`, `export_analytics.py:243,347-349`). The live
product deliberately does the opposite: bot actions draw from
`random.Random(secrets.randbits(256))` per call and are documented as
permanently non-replayable (`sim_session.py:16,197-198,256`).

Consequences:

- Adding or removing any draw anywhere shifts stream consumption for **every
  subsequent decision and every subsequent hand**. Seeded runs stay
  reproducible (same code plus same seed still gives the same bytes) but they
  do not stay *comparable* to pre-change runs.
- **Before-and-after comparison must be distributional over a large sample.**
  Hand-by-hand diffing of a pre-change and post-change run is meaningless.
- Golden-digest tests over the harnesses need deliberate regeneration:
  `test_buyin_spread.py:181`, `test_export_analytics_schema.py:212`,
  `test_detection_analysis.py:729`.

## 5. What is safe to change

- **`spot_signature()` is unaffected.** `srs.py:48-68` hashes `villain_type`
  but no probability, size, or merit value. Changing persona distributions,
  sizing menus, and merit tables does not orphan SRS history. Renaming a
  persona or altering the `VillainType` enum (`archetypes.py:9-14`) would.
- **Hero grading logic is unaffected.** No grader module imports the persona
  samplers (verified by grep). Grading judges hero against an independent
  baseline. The only grading coupling is the *size recognition* of §3.
- **The live product has no replay contract to break** (§4).

## 6. The change target — deterministic constructs

**Preflop sizing is fully deterministic.** `PersonaSizing`
(`content/models.py:137-142`) holds one `open_bb`, one `threebet_mult`, one
`fourbet_mult` per persona — scalars, not distributions. `preflop_raise_to()`
(`sizing.py:190-214`) applies them verbatim: `open` is `open_bb`; `iso` is
`open_bb + 1.0 × limpers`; `3bet` and `4bet` are their multiplier times the
faced raise. Shipped values:

| Persona | `open_bb` | `threebet_mult` | `fourbet_mult` |
|---|---|---|---|
| calling_station | 3.5 | 3.0 | 2.2 |
| lag | 3.0 | 3.5 | 2.4 |
| maniac | 4.5 | 3.3 | 3.0 |
| nit | 3.0 | 3.5 | 2.3 |
| passive_fish | 4.0 | 3.0 | 2.2 |
| tag | 3.0 | 3.5 | 2.4 |

Every open from every seat in every hand is one of six numbers. The open size
alone identifies the persona.

**Preflop ranges contain 75 fully deterministic mixes** (a single action at
weight ≥0.99), counted across the six packs: calling_station 7, lag 17, maniac
15, nit 12, passive_fish 10, tag 14. Two distinct defects live here:

- *Hard range boundaries.* Everything inside the range takes one action 100% of
  the time and everything outside folds 100% of the time. Real players have a
  fuzzy boundary.
- *Position-blind wildcard nodes.* The `vs_rfi`, `vs_limpers`, `vs_3bet` and
  `vs_4bet` nodes carry `positions: None`, so the persona answers identically
  from every seat. This is the mechanism behind the measured "tag folds to a
  raise at a flat 83% from every seat" and "nit at a flat 94%" constants
  (re-measure SYNTHESIS §4 family C).

**Postflop sizing is already a distribution, but a narrow one.** Each pack
authors `postflop.sizing` and optionally `sizing_by_node`
(`content/models.py:253-257`) over the recognised grid. The defect is
composition, not determinism: the maniac's menu contains no small size at all
(0.75/1.0/1.5 only) and the 0.5 fraction is under-weighted table-wide
(re-measure family D).

**Postflop merit floors produce near-binary behaviour.** These are literal
`0.0` merits, not gates to delete: `_FOLD_BASE[MONSTER] = 0.0`
(`personas_postflop.py:260`), `_RIVER_RAISE_FLOOR` (`:301-305`),
`_RIVER_BET_FLOOR` (`:312`), the river air-never-calls rule (`:1010-1011`), and
the SPR commit transform which zeroes FOLD (`:686-699`). The measured "station
folds no-pair rivers 48 times out of 49" is emergent from this merit
arithmetic; there is no single branch to remove.

## 7. Measurement — the gates already exist and must be reused

**The frozen pre-fix roster baseline already exists and is valid at the branch
point.** `poker-analytics:scorer/artifacts/a5_baseline_z.json` pins
`engine_git_sha a0de83eb134b071d849837835407ddafe537d805`, seed 601, 50,000
hands, a fixed nine-seat lineup, and `min_pairwise_distance 1.792042` over the
ten scored statistics. `git diff a0de83e origin/main -- backend/app/domain
content/personas backend/app/services` is **empty**, so persona behaviour at
the branch point `d1fb76b` is identical to the behaviour the baseline
measured. This artifact is the frozen pre-fix roster; it must be preserved and
compared against, never rebuilt.

**Both gates are already implemented and tested** in
`poker-analytics:scorer/constraints.py`:

- Separation floor — `rule1_label_and_separation` (`constraints.py:201`):
  nearest-centroid label preservation for all six personas, plus minimum
  pairwise distance ≥ `SEPARATION_FLOOR_FRACTION = 0.70` of the baseline
  (`constraints.py:81`), computed on the pinned baseline z-scales rather than
  recomputed from the candidate.
- Determinism guard — `rule4_determinism` (`constraints.py:422`): over decision
  contexts of street × `engine_node_key` × `hand_class_bucket` observed at
  least `DETERMINISM_MIN_OBS = 50` times for a persona, the modal action's
  share may reach `DETERMINISM_MODAL_SHARE = 0.98` in at most
  `DETERMINISM_MAX_SHARE_OF_CONTEXTS = 0.20` of those contexts
  (`constraints.py:83-85`).

The candidate batch is produced by `poker-coach:backend/tools/export_analytics.py`,
which already emits the `engine_node_key` and `hand_class_bucket` columns
`rule4_determinism` groups on. `duckdb` is **not currently installed** in the
backend environment; `pyarrow` 25.0.0 is.

## 8. Tests that will need deliberate regeneration

These pin current behaviour by design and will fail when distributions change.
Failing is expected; each needs a reviewed update, and none should be deleted.

- Preflop range composition: `test_personas.py:1544,1622`
  (`test_tagwidth_*_pinned`), `test_rr_emit.py:207,412,548`
  (byte-deterministic range-ladder emission).
- Merit vectors: `test_price_tail.py:281,315`, and the numerous
  `*_byte_identical` / `*_pinned` tests through `test_personas_postflop.py`.
- Harness goldens: `test_buyin_spread.py:181`,
  `test_export_analytics_schema.py:212`, `test_detection_analysis.py:729`.

**How to tell an expected failure from a real regression.** Many of the
`byte_identical` tests exist to prove a *new* lever is a no-op for packs that
have not opted into it. If such a test fails for a persona or bucket this slice
did not intentionally touch, that is a genuine regression, not a pin to
refresh. `test_personas.py:302` `test_same_seed_is_deterministic` asserts the
general reproducibility contract rather than specific values and must keep
passing throughout.
