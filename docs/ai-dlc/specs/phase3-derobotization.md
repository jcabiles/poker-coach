# Spec — persona de-robotization (phase-3 ruling A, improvement slice 1)

**Bottom line: remove the three mechanical tells that make the villain bots
readable as machines — a single fixed raise size per persona, hand ranges with
hard 100%/0% boundaries, and identical responses from every seat — while
proving the six personalities stay distinguishable and hero's grading coverage
does not shrink. Postflop bet sizes are re-weighted inside their existing grid
and never jittered continuously, because continuous jitter would silently
delete hero's turn and river grading. The two reused statistical gates are
blind to bet sizing and to position, so this slice adds its own positive tests
for the things the gates cannot see. Engine and stack work is excluded by the
ruling; invest-then-fold and calldown are later slices.**

- Governing ruling: `docs/ai-dlc/specs/phase3-decision-matrix.md` §4 (option A,
  ratified 2026-08-15).
- Protocol: estimand-contract amendment (g.5), full text in
  `docs/ai-dlc/specs/phase3-consolidated-amendment-draft.md`.
- Contract map: `docs/ai-dlc/contracts/phase3-derobotization.md`.
- Defect evidence: `remeasure-2026-08-05/SYNTHESIS.md` §4 families C and D
  (adjudicated column authoritative); probe ledger
  `docs/ai-dlc/ledger/phase3-probe.md`.
- Review findings and their adjudication: `docs/ai-dlc/ledger/phase3-derobotization.md`.

## 1. Goal

Make each villain bot's decisions vary the way a person's do — different raise
sizes in the same spot, a soft edge to its opening range, different answers
from different seats — without the six personalities blurring into each other
and without changing what any of them is fundamentally trying to do.

The measured target is family C ("context-blind constants and determinisms")
plus the composition half of family D ("sizing ecology"), in the order the
ruling fixed.

## 2. What "believable" means here

The roadmap draws a distinction this slice must respect
(`roadmap/bot-realism-flywheel.md:40-47`): a seat being *recognisable as a
type* is desirable, because real players are readable; a seat being
*recognisable as a machine* is the defect. Every change below targets the
second and is gated against damaging the first.

## 3. Scope

### In scope

1. **Preflop raise-size variation** for the open, iso-raise, 3-bet and 4-bet
   levers, drawn from a valid truncated interval (§6.2).
2. **Range-boundary softening** — mixed weights at the *edge* of each persona's
   range, so marginal hands are sometimes played and sometimes not.
3. **Positional response gradients** — split the wildcard `vs_rfi`,
   `vs_limpers`, `vs_3bet` and `vs_4bet` nodes into position-aware nodes.
4. **Postflop size-mix rebalancing** — re-weight each pack's existing on-grid
   pot-fraction distributions to give the 0.5 fraction real presence and the
   maniac a small size at all. **On the existing grid only.**
5. **The gate runner** (§5) and the positive tests the gates cannot provide
   (§7.2).

### Explicitly out of scope

- **Engine and stack work** — cut from this phase by the ruling.
- **Invest-then-fold** (next slice) and **calldown** (the slice after, and the
  declared scope valve).
- **Any grader change.** `RECOGNIZED_BET_FRACS`, `_CANON_BET_TOL`, and every
  `grade_map_*` module stay untouched.
- **Continuous postflop bet-size jitter.** Forbidden by contract map §3.
- **The maniac's 4-bet multiplier.** It is 3.0 against a grading cap of 2.4, so
  it is already ungradeable, and jittering-then-clamping it would silently
  re-centre it on 2.4 — a behaviour change disguised as a variance change. It
  is left exactly as shipped and recorded as a pre-existing gap.
- **Rebuilding the pinned baseline artifact** `a5_baseline_z.json`.
- **Retuning the shared merit constants** (`_AGG_BASE`, `_PRICE_*`,
  `_BUCKET_ALPHA`, other fit seeds) beyond what a named defect requires.
- **`spot_signature()`, the `VillainType` enum, persona names.** Frozen.
- **Detection deck, judging trees, finale machinery.** Untouched.

## 4. Files and interfaces

| File | Change |
|---|---|
| `backend/app/domain/content/models.py` | Optional weighted size-mix fields on `PersonaSizing`, with `extra="forbid"` and finiteness validation. |
| `backend/app/domain/table/sizing.py` | `preflop_raise_to()` gains an optional `rng` and draws from an **enumerated weighted mix**, never sample-then-clamp (§6.2). |
| `backend/app/domain/table/play.py` | Thread `rng` into `preflop_raise_to` so only the live bot loop opts in. |
| `content/personas/*.json` (6) | `sizing` mixes; `preflop` boundary mixes and positional nodes; `postflop.sizing` / `sizing_by_node` re-weighting. |
| `content/schema/persona.schema.json` | Regenerated from the model, with a sync test so drift cannot stay silent. |
| `backend/tools/derobo_gate.py` (new) | Export a candidate batch at the pinned seed and lineup, then invoke the analytics-side check as a subprocess. |
| `poker-analytics:analysis/derobo_gate_check.py` (new) | Call `scorer.constraints` rule 1 and rule 4 against the pinned baseline; emit PASS/FAIL JSON. **New integration glue — §5.1.** |
| `backend/tests/test_coverage_baseline.py` | Refresh the recorded baseline when a change moves the hand stream, per that file's existing ratio convention (§7.1). |

Default-off contract: every new schema field is optional, and a pack that omits
it behaves byte-identically to today.

## 5. The gates

Two statistical gates already exist, implemented and unit-tested, in
`poker-analytics:scorer/constraints.py`. This slice adds no new metric
definitions and no new thresholds.

- **Separation floor** — `rule1_label_and_separation` (`constraints.py:201`):
  nearest-centroid label preservation 6 of 6, and minimum pairwise distance at
  least 0.70 of the baseline's `1.792042`, on the pinned baseline z-scales.
  The floor is therefore ≈1.2544, and the closest baseline pair is lag/tag.
- **Determinism guard** — `rule4_determinism` (`constraints.py:422`): over
  decision contexts of street × `engine_node_key` × `hand_class_bucket`
  observed at least 50 times for a persona, the modal action's share may reach
  0.98 in at most 20% of those contexts.

**The baseline is valid at this branch point.** `a5_baseline_z.json` pins
`engine_git_sha a0de83e`; the diff to branch point `d1fb76b` touches no file
under `backend/app/domain/`, `content/personas/`, or `backend/app/services/`.

### 5.1 The runner is new code and is treated as such

The two *rules* are tested. The *runner that calls them* is new integration
glue and is the highest-risk artifact in this slice, because a wrong gate
manufactures false confidence — the failure mode of both the S3 contract defect
and the S6 shakedown.

It bypasses `run_checks()`, because that entry point begins with
`gate_mod.require_gated(batch)` and then runs all five rules, three of which
(legality, directional checks, runtime/reproducibility) need a registry, a
covariance artifact, timing logs, and an ingestion marker this slice has no
business producing. Calling rule 1 and rule 4 directly means assembling, by
hand: a duckdb connection over the batch (`stats_mod.open_batch`), the seat →
persona lineup, and per-persona measured values for the full ten scored
statistics (`seat_counters` → `pool_counters` → `stat_values`).

**Therefore the runner must reproduce two known answers before it is trusted:**

1. Run against **unchanged** packs and reproduce the baseline's recorded
   `min_pairwise_distance` of `1.792042`.
2. Recompute the per-persona statistic vectors and match the baseline
   artifact's stored `raw_vectors` for all six personas.

Both are exact-value checks against an artifact built by a different pipeline,
so passing them exercises the whole path end to end. A runner that cannot
reproduce a known answer does not get to judge a change.

### 5.2 Dependencies and invocation

`scorer.constraints` imports `numpy` and `duckdb` at module level; the backend
environment has **neither** (`pyarrow` 25.0.0 is present). Rather than install
the analytics stack into the poker-coach virtual environment, the coach-side
runner shells out to poker-analytics' own interpreter and parses the JSON
result. The analytics repo owns its dependencies; the coach repo gains none.

### 5.3 Cadence — one seed gates a ticket, five seeds gate the slice

A single 50,000-hand run at seed 601 is a deterministic smoke gate, not
statistical proof. Rule 4 is discontinuous at both its thresholds (49
observations are excluded where 50 qualify; 49 of 50 modal actions is
deterministic where 48 is not), and a candidate sitting near the separation
floor can change verdict on seed noise alone.

- **Per ticket:** seed 601, 50,000 hands. About 3.3 minutes, measured on this
  machine at 253 hands/second.
- **Slice acceptance:** the five-seed design the analytics repo already retains
  in `cov-525e183a12f269e3.json` (seeds 601–605). Every seed must pass. About
  17 minutes.

**The determinism guard passes on the unchanged roster** (measured, T0). Its
threshold is not binding at the current level of defect, so it is a regression
guard rather than a progress meter — a green gate is never evidence that
de-robotization worked. §7.2 carries that burden.

### 5.4 Recorded deviation — the separation floor's status

`roadmap/bot-realism-flywheel.md:48-59` states the separation floor "is not yet
measurable" and should be an interpretive principle, not a pass/fail criterion,
while `phase3-decision-matrix.md:64` mandates it as a per-change gate.

These are reconcilable. The roadmap objects to an **absolute** floor — "blind
identification must stay high", one-sided, no threshold, no human comparator,
which taken literally makes ever-greater identifiability monotonically better.
The ruling's gate is **relative**: separation against the frozen pre-fix
roster. A relative floor is falsifiable, has a declared threshold, and cannot
reward increasing identifiability, because it fires only when separation
*degrades*. This slice applies the relative form and claims nothing about
absolute identifiability.

**Flagged for owner confirmation; recorded here rather than resolved
silently.**

## 6. Binding design constraints

### 6.1 No new random draw may precede the action draw

`range_estimate._CaptureRng` (`range_estimate.py:344-361`) captures the first
`rng.choices()` call. Preflop size jitter satisfies this by construction:
sizing runs after the action has been drawn. (Precision, per review: the
capture path is postflop-only — preflop estimation mirrors pack probabilities
directly and never calls `sample_preflop_action`. Keeping sizing after the
action draw remains the rule.)

### 6.2 Draw from a valid interval; never sample-then-clamp

Hero's preflop grading is **path-dependent**, not a set of scalar caps: a
villain open faced directly by hero may reach 4.5bb, but in a hero-3-bet line
the villain's open must be ≤3.0 and the 3-bet cap is 3.5 × the *canonical
position open* rather than the actual faced open; lines mixing calls and raises
are rejected before sizing is examined at all, so there is no gradeable iso
band in the current mapper.

Sampling a symmetric jitter and clamping into that space is therefore wrong
twice over. It piles probability mass onto the clamp boundary — recreating a
determinism at exactly the value the gate cannot see — and for a lever already
outside the band it collapses every draw to the boundary, which is a centre
shift, not variance.

**Every jittered lever declares an explicit valid interval and draws inside
it.** Levers already at a cap draw one-sided downward:

| Persona | Lever | Value | Cap | Interval |
|---|---|---|---|---|
| maniac | `open_bb` | 4.5 | 4.5 | one-sided downward |
| tag, lag, nit | `threebet_mult` | 3.5 | 3.5 | one-sided downward |
| tag, lag | `fourbet_mult` | 2.4 | 2.4 | one-sided downward |
| maniac | `fourbet_mult` | 3.0 | 2.4 | **excluded from this slice** |

The existing `_clamp(v, min_bb, max_bb)` in `preflop_raise_to()` bounds the
*engine's legal-raise bracket* (up to the whole stack, `engine.py:175`) and
enforces no grading cap whatever. A second, distinct bound is required. Forced
jam brackets (`min_bb == max_bb`) legitimately collapse and are excluded from
any "must vary" assertion.

### 6.3 Postflop sizes stay on the recognised grid

Re-weighting only, over {0.33, 0.5, 0.75, 1.0, 1.5}. `_validate_bucket_dist`
accepts *any* positive fraction, so this slice adds the invariant that enforces
grid membership.

**The check is a test, not a model validator, and that placement is
deliberate.** `RECOGNIZED_BET_FRACS` lives in the table layer, which imports
the content layer and never the reverse, so enforcing it inside
`PersonaSizing` would invert an established dependency. More concretely: the
same `_validate_bucket_dist` helper now serves the preflop size mixes, whose
keys are bb amounts and multipliers. A grid check placed in that shared helper
would reject every preflop key — "3.0" is not a member of the pot-fraction grid
— and the two features would fight. Grid membership therefore belongs to the
postflop fields alone, and a test proves a preflop mix survives it.

### 6.4 First-match-wins means a softened mix can be dead code

`sample_preflop_action` scans mixes in list order and takes the first whose
combo set contains the hand (`personas.py:100`); combo overlap between mixes is
**not** validated (only node-level position overlap is, `models.py:343-379`).
A new fuzzy-edge mix placed after an existing hard mix that already covers
those hands has no effect at all, and nothing fails.

This is the most likely way this slice silently accomplishes nothing, so §7.2
tests for it directly.

### 6.5 Positional nodes must cover every position

Node validation rejects overlap and ordering errors but does **not** require
complete position coverage. A seat omitted when splitting a wildcard node
silently reaches the sampler's implicit-fold path and that persona folds 100%
from that seat.

### 6.6 Comparisons are distributional

One shared RNG stream drives deals *and* decisions, so an added draw changes
which cards are dealt in every later hand, not merely how they are played. Pre-
and post-change runs are independent samples of different hand populations —
never hand-matched, never compared as raw counts.

## 7. Acceptance

### 7.1 Per ticket

- `./scripts/verify.sh` reports `BACKEND VERIFY OK`; `ruff check .` clean.
- Both gates PASS at seed 601 against the pinned baseline.
- **Hero grading coverage holds as a ratio, measured by the existing harness.**
  `backend/tests/test_coverage_baseline.py` is the repo's established measuring
  stick and already documents this exact problem: bot changes drift the hand
  stream so both numerator and denominator move, and its recorded history
  therefore tracks the graded/total *ratio*, not the raw graded count. The raw
  count is meaningless here — the analytics export is nine-bot self-play
  containing no hero decisions at all, so it cannot measure hero coverage.
  A ticket must not reduce the ratio; a moved baseline is refreshed with a
  recorded reason.
- Every behaviour-pinning test that fails is individually reviewed and either
  updated with a recorded reason or fixed as a genuine regression. None is
  deleted.
- Packs not opting into a new field are byte-identical.

### 7.2 Positive tests — what the gates cannot see

Neither gate measures bet sizing (rule 1's ten statistics are all
frequency/rate; rule 4 groups on action type, not size) and neither conditions
on position. Both would therefore pass a completely no-op implementation of
this slice — indeed the unchanged roster passes them, which is precisely the
runner self-check. These tests carry the actual goal:

1. **Sizes genuinely vary.** Each opted-in sizing node produces at least two
   distinct non-forced sizes over a seeded sample, with bounded mass at any
   interval boundary. Forced jams excluded.
2. **Edge combos are genuinely mixed.** Every combo declared a range edge has
   an action probability strictly between 0 and 1.
3. **No shadowed mixes.** No mix is unreachable because an earlier mix in the
   same node already covers its combos (§6.4).
4. **Positional coverage is complete**, and named position pairs produce
   *different* action vectors — the point of splitting the node (§6.5).
5. **Grid membership** holds for every authored postflop sizing key (§6.3).
6. **Core ranges stay pinned.** Non-edge combos keep their current
   probabilities, so softening an edge cannot quietly rewrite a range.

### 7.3 Slice acceptance

All four in-scope changes shipped; both gates pass with all of them combined
across the **five-seed** set; a combined gate report and the coverage ratio
recorded in the ledger.

## 8. Verify-by

```bash
./scripts/verify.sh                        # backend pytest + boot probe
cd backend && ruff check .                 # lint
python -m tools.derobo_gate --check        # both gates, seed 601, vs pinned baseline
python -m tools.derobo_gate --check --seeds 5   # slice-level acceptance
```

The runner is itself verified by the two known-answer reproductions in §5.1
before any pack edit lands.

## 9. Risks

- **A wrong gate is worse than no gate.** Mitigated by reusing the tested
  rules, by the two known-answer reproductions, and by an independent recompute
  during review.
- **The gates are blind to this slice's headline change.** Mitigated by §7.2;
  without those tests a no-op implementation would show all green.
- **Softening boundaries could blur the archetypes.** That is what the
  separation floor measures; if it fires, jitter and mixing widths come down.
- **`duckdb`, `numpy` and `PyYAML` are absent** from the backend environment.
  Resolved by running the check under the analytics interpreter (§5.2).
- **The behaviour-pinning test surface is large.** Budget real time to review
  each failure. Bulk-regenerating goldens is how a real regression gets
  laundered into an accepted change.
