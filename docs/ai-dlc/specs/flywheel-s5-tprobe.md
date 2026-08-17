# S5 T-probe — `continue_ref` mechanism probe

status: DRAFT rev 2 (post-review), awaiting Gate 2 (owner)
slice of: `../roadmap/bot-realism-flywheel.md` → S5, the preregistered mid-slice trigger
in `../tickets/flywheel-s5.md` ("if stage results put NOT-REACHABLE in play, insert
T-probe"). Review findings and their adjudication: `../ledger/flywheel-s5-tprobe.md`.

## Bottom line

Stage 1 searched every setting the bots were allowed to have and found nothing that plays
close enough to a human while still behaving like its own character. The strongest dial —
how readily a bot calls — is already pressed against the edge of its permitted range in
every persona's best result, so searching harder inside that space has nowhere left to go.
This probe tests the one lever stage 1 never touched: `continue_ref`, a calldown
calibration anchor frozen out of all 730 runs by design. Forty-two simulation runs, about
three quarters of an hour, answer whether that frozen lever moves the result at all. If it
does not, the ceiling inside the declared space is real and diagnosed, and the remaining
question — whether the declared space itself was drawn too tight — becomes an explicit
owner decision rather than a silent assumption.

## Goal

Measure the effect of `postflop.continue_ref` on the distance-to-human-band measure `D`, at
fixed measured levels across its full declared range, for each of the six personas.

## Why this axis, and why it is legitimate

`continue_ref` is axis #7 of the estimand contract's dial table, declared range
`[0.05, 8.0]`. The contract froze it out of the wave-1 sweep and designated it "its own axis
in dedicated mechanism probes only". This slice is that dedicated probe — inside the
preregistered design, not an amendment to it. Unfreezing requires a `probe_declarations`
entry per config (`probe_kind: "continue_ref"`, persona, paths, written rationale);
`counterfactual.py` rejects the config otherwise.

## The constraint that shapes this design (found in review, verified in source)

**`continue_ref` can only be varied while `call_looseness` sits at the persona's shipped
default.** `counterfactual.py:620` refuses any config where both appear in the same
persona's overrides. The check is presence-based, so it cannot distinguish "varying both"
from "holding one fixed while probing the other" — it fires either way. Omitting
`call_looseness` does not rescue the anchor: `canonicalize()` at line 783 fills it from the
shipped pack, not from whatever a caller intended.

Relaxing that check is **rejected**: it lives in `backend/`, so changing it moves the engine
off the frozen study commit `a0de83e` that all 730 stage-1 results are keyed to. One probe
is not worth the comparability of the whole study.

**Consequence, stated plainly:** this probe cannot ask "can `continue_ref` rescue our best
configuration?", because our best configurations all have `call_looseness` far from default.
It asks the answerable question instead — "does `continue_ref` move `D` at all, from the
best starting point the engine permits?" A null result still diagnoses the ceiling; a
positive result is a lead, not a rescue.

## Design

**Ladder, all six personas, anchored at each persona's best surviving stage-1 configuration
with `call_looseness` reverted to its shipped default.**

- **Anchor** — every dial at the values of the persona's lowest-`D` gate-passing stage-1
  config, except `call_looseness`, which is omitted so it falls back to the pack default.
  Because that reversion changes the config, the anchor's own `D` is **not** known from
  stage 1 and must be measured: one anchor run per persona, with `continue_ref` at its
  shipped value. That run is the reference every probe level is compared against.

  Source configs (stage-1 `D` shown for provenance only — it is *not* the reference, since
  reverting `call_looseness` changes the config):

  | persona | source config (first 16) | its stage-1 `D` | seed | shipped `continue_ref` |
  |---|---|---|---|---|
  | tag | `21b7b8880a85ac06` | 9.146 | 8187834505050185387 | 0.60 |
  | lag | `9f2d3b17ae91d975` | 9.225 | 3925646646930440611 | 0.55 |
  | nit | `9e045fb6069a3d7e` | 9.687 | 8171410787333953434 | 0.60 |
  | maniac | `fd678f4dcd6815e5` | 9.416 | 4143296704372445340 | 0.55 |
  | passive_fish | `834da91f493f92a5` | 9.214 | 4540570775526807628 | 0.42 |
  | calling_station | `799af0df65df2d7b` | 7.004 | 2928073416226796024 | 4.00 |

  *maniac note:* maniac's pack leaves `call_looseness` unauthored and inherits `stickiness`,
  which also feeds the raise-scaling numerator. P1 must confirm maniac's anchor reverts
  cleanly rather than silently desyncing the anchor, and report if it does not.

- **Levels — five, a true 5-point logarithmic grid across the declared range:**
  `0.05, 0.178, 0.632, 2.249, 8.0`. Logarithmic because the range spans more than two orders
  of magnitude and the dial acts as a ratio anchor. Both declared endpoints are included,
  satisfying the endpoint-evaluation rule. *(Rev 1 listed only four of these points and left
  an unprobed gap between 0.63 and 2.25 — a review finding, corrected here.)*

- **Runs: 42.** Per persona, 1 anchor run + 5 probe levels = 6; times six personas = 36
  configs, plus one determinism re-run per wave = 6. Six waves, one per persona, each
  reusing that persona's stage-1 seed.

  **Correction, found in build review and verified in the engine: reusing the seed does
  NOT pair the hands across a wave.** The exporter creates one random-number generator per
  run and draws both each hand's deal and each bot's action from it
  (`export_analytics.py:333-350`). `continue_ref` changes the raise-merit scale, and a bet
  or raise consumes an extra draw that a check or fold does not
  (`personas_postflop.py:1351-1376`). So the first hand where a probe level changes an
  action desynchronizes every hand after it: the arms share a starting seed but not a hand
  sample. Two consequences, both kept rather than papered over. First, a difference in `D`
  between two arms carries ordinary sampling noise from different deals, not just the
  effect of the dial — so the comparison noise is about √2 times the single-run figure,
  roughly 0.078 rather than 0.055, and the materiality threshold must be applied at that
  wider figure when comparing a level against its anchor. Second, this is a property of the
  frozen engine that every one of the 730 stage-1 runs shares; it is not new to the probe
  and it is not grounds for an engine change mid-study.

- **Budget:** the 36 config runs are charged to the `probes` stage; the 6 determinism-dup
  arms are charged to `rerun_checks`, per the execution checklist's standing rule that dup
  arms never book to the wave's own stage. Total after this probe: 800 of the 1,500 cap.
  Runtime ≈ 45 minutes at 2 workers.

## Preregistered verdict mapping — fixed BEFORE any probe runs

**Verdicts are per persona.** Each persona gets its own row below, recorded separately. The
**aggregate rule**, also fixed here: the probe as a whole reads "ceiling confirmed" only if
*every* persona lands in row 1; if any persona lands in row 2 or 3, the aggregate is that
persona's row, named with the persona; any other mixture is row 4.

The **materiality threshold** is the standard deviation of `D` across the five pinned
baseline replicates, computed and written to the ledger *before* the probe launches. It is
**0.054814** for a single run. Because the arms do not share a hand sample (see the runs
paragraph above), a level counts as beating its anchor only if it does so by more than
**0.0775** — the same figure widened by √2 for the noise in both arms of the comparison.

**The anchor is off-grid and must not be read as a sixth grid point.** Each persona's
anchor sits at its shipped `continue_ref` (0.42 to 4.00 depending on persona), which is
not one of the five levels. It is the reference the levels are measured against; row 3's
monotonicity reading applies to the five levels in order, never to the anchor mixed in
among them.

| # | What the probe shows (per persona) | What it means |
|---|---|---|
| 1 | No level beats the anchor run's `D` by more than the materiality threshold | The frozen lever is inert for this persona. Combined with `call_looseness` exhausted at its floor, the operational ceiling **within the declared space is confirmed and diagnosed**. |
| 2 | Some level puts `D` below the cutoff (5.159) **and** passes the behaviour gates | A candidate exists. It does **not** support a REACHABLE verdict on its own: §a.4 defines REACHABLE only via a stage-3 combination run, so this feeds stage-3 composition first, and only then the 5-fresh-seed confirmation under the winner's-curse guard. |
| 3 | `D` falls materially and monotonically toward a declared endpoint without crossing the cutoff | The declared boundary binds. This is the trigger for an explicit owner decision on widening the range — a contract amendment, deliberately **not** pre-authorized here. |
| 4 | **Anything else** — material improvement that is non-monotonic, or crosses no threshold, or disagrees across personas | INCONCLUSIVE for this persona. Recorded as such; no further inference drawn. |

**On the materiality threshold's known weakness.** The contract itself warns that baseline
seed-noise "need not be conservative for extreme configs", and these anchors are not the
baseline config. We use it anyway, with the direction of the error stated: an *understated*
noise floor makes an improvement *easier* to declare, so a row-1 (no-effect) finding reached
against an understated threshold is conservative — the null survives a test biased against
it. A row-2 or row-3 finding gets no such protection and is therefore a lead requiring
confirmation, never a conclusion. Any conclusion resting on the threshold must cite this
paragraph.

No verdict from this probe may exceed INCONCLUSIVE on its own: §e.3 is enforced in
`reachability_verdict` and requires detection-pilot evidence, and the S3 stop-gate bars any
score-only verdict. This probe diagnoses a mechanism; it does not deliver the study's verdict.

## Out of scope

Widening any declared range (contract amendment, owner decision) · changing `counterfactual.py`
or anything else under `backend/` (breaks the frozen engine identity) · `sizing_by_node`
probes (contract-gated on the sizing stat family failing, not established) · stage 2 and
stage 3 · any change to the engine, personas, or packs · any fix recommendation.

## Constraints

Frozen engine sha `a0de83e` and covariance artifact `cov-525e183a12f269e3` unchanged ·
configs validate through the same `load_spec`/`validate_configs` path as stage 1 · identity
discipline fail-closed · budget charged from the sweep manifest · raw Parquet retained, not
retired, until the S5 verdict settles.

## Verify-by

1. All 36 configs pass `counterfactual.load_config`, **and** a config with its
   `probe_declarations` entry removed is rejected with the freeze-rationale error — proving
   the freeze is unfrozen by declaration, not bypassed.
2. No config authors both `continue_ref` and `call_looseness` for the same persona.
3. `./scripts/verify.sh` passes and `ruff check .` is clean.
4. The six waves complete through the existing runner with no blocked wave.
5. The budget manifest shows +36 on `probes`, +6 on `rerun_checks`, 800 total.
