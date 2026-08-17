# Finding ledger — S5 T-probe (`continue_ref` mechanism probe)

Spec: `../specs/flywheel-s5-tprobe.md` · Tickets: `../tickets/flywheel-s5-tprobe.md`

## Bottom line

One review round on the spec, before any code or any simulation run. Seven findings, all
seven accepted. One of them was fatal to the design as first written and forced a change of
approach that the owner then ruled on. Every finding was verified against source before
being accepted — the reviewer's citations were checked, not trusted.

## Round 1 — spec review, 2026-08-10

**Reviewers:** Claude `refuter` (Sonnet, fresh context, blind to the requirements interview)
returned `FAIL` with 7 findings. Codex `gpt-5.6-sol` (high effort) was launched in parallel
per the owner-approved dual review but **produced no final report** — it spent its run
reading source and stopped before synthesising. The dual-review call is authorised to fail
open, so adjudication proceeded on the refuter's findings alone; this is recorded rather
than hidden. Codex's search output did independently corroborate the design intent behind
finding 1 (the config inventory's axis-14 row: `continue_ref` "may be swept independently as
its own axis").

| # | Severity | Finding | Adjudication |
|---|---|---|---|
| 1 | high | The probe's configs cannot be built. `counterfactual.py:620` refuses any config where `continue_ref` and `call_looseness` both appear in one persona's overrides — a *presence*-based check that cannot distinguish co-varying from holding-one-fixed. Omitting `call_looseness` does not help: `canonicalize()`:783 fills it from the shipped pack, not the anchor. Every one of the 730 stage-1 configs authors `call_looseness`, so "the anchor's config with only `continue_ref` moved" is unbuildable. | **ACCEPTED — verified in source** (both line ranges read directly; stage-1 configs checked and all three sampled personas author the dial). Fatal to rev 1. Relaxing the check was **rejected**: it lives in `backend/`, so changing it moves the engine off the frozen study commit `a0de83e` and costs comparability with all 730 stage-1 runs. Escalated to the owner, who ruled: anchor at the best surviving config with `call_looseness` reverted to its shipped default, and measure that new anchor (+6 runs). Spec rev 2 states the consequence plainly — the probe can no longer ask "can this rescue our best config". |
| 2 | med | The verdict mapping is written as one verdict but the design runs six independent single-seed persona waves. No rule for combining six per-persona outcomes. | **ACCEPTED.** Rev 2 makes verdicts explicitly per persona and states the aggregate rule in advance. |
| 3 | med | No row covers "material improvement that is not monotonic and does not cross the cutoff" — a plausible outcome with no preregistered home, inviting a post-hoc call. | **ACCEPTED.** Rev 2 adds an explicit catch-all row mapping any uncovered pattern to INCONCLUSIVE. |
| 4 | med | "Spaced geometrically" was numerically wrong: the four listed points are points 1, 2, 4, 5 of a 5-point log grid, leaving the interval 0.178→2.249 spanning two log-steps and an unprobed gap between ~0.63 and ~2.25. | **ACCEPTED — arithmetic confirmed.** Rev 2 uses the true 5-point log grid `0.05, 0.178, 0.632, 2.249, 8.0`. |
| 5 | med | The materiality threshold (SD of `D` across the 5 baseline replicates) is baseline seed-noise applied to comparisons at extreme anchor configs; the contract itself warns baseline noise "need not be conservative for extreme configs". | **ACCEPTED, resolved by stating the direction of the error rather than by adding runs.** An understated noise floor makes an improvement *easier* to declare, so a no-effect finding reached against it is conservative — the null survives a test biased against it. A positive finding gets no such protection and is a lead, not a conclusion. Rev 2 says this explicitly and requires any threshold-dependent conclusion to cite it. |
| 6 | med | Verdict row 2 implied a below-cutoff probe config could go straight to 5-fresh-seed confirmation, but §a.4 defines REACHABLE only via a stage-3 combination run; a probe config has five personas at baseline and is not structurally eligible. | **ACCEPTED.** Rev 2 routes a row-2 hit through stage-3 composition before any confirmation, and says it cannot support REACHABLE on its own. |
| 7 | low | The spec charged all 42 runs to the `probes` budget stage, contradicting the checklist's standing rule that every wave's determinism-dup arm books to `rerun_checks`. | **ACCEPTED.** Rev 2 splits it: 36 to `probes`, 6 to `rerun_checks`. |

## P0 — the materiality threshold, pinned before any probe config exists

**The threshold is `0.054814`.** A probe level counts as having moved `D` only if it beats
its persona's measured anchor by more than this. Recorded 2026-08-10, before any probe
configuration was generated and before any probe run was executed — which is what makes a
"no material improvement" reading a preregistered claim rather than a post-hoc one.

**What it is.** The sample standard deviation (the n−1, Bessel-corrected form) of the pool
distance `D` across the five pinned baseline replicates. Those five runs are the same
configuration simulated five times under different random seeds, so the spread between them
is pure run-to-run randomness with no change of settings involved. Anything smaller than
that spread is indistinguishable from luck.

| replicate seed | `D` |
|---|---|
| 601 | 9.692431 |
| 602 | 9.749715 |
| 603 | 9.695153 |
| 604 | 9.721814 |
| 605 | 9.825818 |

- mean `D` = 9.736986 · sample SD (n−1) = **0.054814** · population SD (n) = 0.049028 ·
  min–max spread = 0.133387.
- The n−1 form is used because five replicates are a sample of the seed distribution, not
  the whole of it. It is the larger and therefore the more conservative of the two.

**Provenance, so this is reproducible.** Batches `~/s5-t0-pins-final/rep-{601..605}`, each
carrying `_GATE_OK.json` and `_SUCCESS`, scored on 2026-08-10 with
`poker-analytics: scorer/score_realism.py --covariance cov-525e183a12f269e3`. Every one of
the five reports `engine_git_sha = a0de83eb134b071d849837835407ddafe537d805` (the frozen
study commit), one shared baseline config hash
`9273b753b9de041a9750557f21c72d4a7482b344d73be7d378b3df56c21375f8`, five distinct canonical
sha256 digests (confirming five genuinely separate runs rather than one result copied), and
`score_status = exploratory-surrogate` (the S3 stop-gate, which bars any score-only verdict).
The score payloads were written outside the repository as session-temporary files and are
regenerable in about one second each; the numbers above, not those files, are the record.

**Its known weakness, and which way the error runs.** This is baseline seed-noise, measured
at the shipped default configuration, but it will be applied to comparisons at anchors far
from that default. The estimand contract warns at line 192 that baseline seed-noise "need
not be conservative for extreme configs". The spec keeps it anyway and states the direction
of the error: an *understated* noise floor makes an improvement *easier* to declare, so a
row-1 finding of no effect, reached against a threshold biased toward finding an effect, is
conservative — the null survives a test stacked against it. A row-2 or row-3 finding gets no
such protection and is a lead requiring confirmation, never a conclusion. Any conclusion
resting on this number must cite this paragraph.

**One observation the scoring surfaced, recorded because it bears on the ceiling reading.**
The all-defaults baseline scores `D` ≈ 9.74. The best surviving stage-1 configuration of
five of the six personas lands between 9.15 and 9.69, and calling_station's reaches 7.00.
So the entire 730-configuration search bought between roughly 0.05 and 2.7 of distance,
against the roughly 4.6 that separates the baseline from the 5.159 cutoff. This is context
for the probe rather than a finding of its own, and it is not a substitute for the
per-persona anchor runs — those anchors revert `call_looseness` to its default and so must
still be measured.

## Build record — P1, P2, P3, 2026-08-10

**Built and verified; nothing has been simulated yet.** The 36 configurations and 6 wave
specifications exist, every one of them validates through the engine's own loaders, and the
runner is wired for the probe stage and proven against failure paths. What remains is the
owner running the six waves, then P4.

**Anchors were re-derived from the evidence, not copied from the spec.** Each persona's
lowest-`D` gate-passing stage-1 configuration was found two independent ways — by hashing
all 730 stage-1 config files through `counterfactual.canonicalize`/`config_hash` and
matching against the join, and by the ordering correspondence between each wave's sweep
spec and its manifest — and the two agree on all six. The gate-passing counts also match
the stage-1 record (tag 91, lag 49, nit 21, maniac 76, passive_fish 4, calling_station 70,
of 730 total).

| persona | anchor source config | its stage-1 `D` | seed |
|---|---|---|---|
| tag | `config-stage1-tag-041.json` | 9.145544 | 8187834505050185387 |
| lag | `config-stage1-lag-072.json` | 9.224764 | 3925646646930440611 |
| nit | `config-stage1-nit-095.json` | 9.686669 | 8171410787333953434 |
| maniac | `config-stage1-maniac-074.json` | 9.415596 | 4143296704372445340 |
| passive_fish | `config-stage1-passive_fish-082.json` | 9.213976 | 4540570775526807628 |
| calling_station | `config-stage1-calling_station-041.json` | 7.003575 | 2928073416226796024 |

**Levels as emitted:** `0.05, 0.177828, 0.632456, 2.249365, 8.0` — the five-point
logarithmic grid across the declared range, both endpoints included, rounded to six
decimals so the emitted document and therefore the config hash are reproducible.

**Verify-by results, each checked against the engine rather than against our reading of it.**

- All 36 configs load through `counterfactual.load_config`, and produce 36 distinct config
  hashes — no accidental duplicates.
- No config authors both `postflop.continue_ref` and `postflop.call_looseness` for one
  persona.
- Removing a config's `probe_declarations` entry is rejected with the frozen-calibration-anchor
  error, so the freeze is unfrozen by declaration and not bypassed.
- Every level of every persona canonicalizes to the SAME `call_looseness`, equal to that
  persona's shipped pack value (tag 0.6, lag 0.55, nit 0.45, maniac 0.55, passive_fish 0.42,
  calling_station 4.0). This is the property the whole design rests on: any movement in `D`
  is attributable to `continue_ref` alone.
- Each config's `base_pack_hash` matches the live packs.
- All six wave specs load through `sweep_runner.load_spec`.
- `./scripts/verify.sh` passes (1,901 tests) and `ruff check .` is clean in poker-coach.

**maniac reverts cleanly — the special case is resolved, not merely noted.** maniac's pack
leaves `call_looseness` unauthored and inherits `stickiness`, which also feeds the
raise-scaling numerator through `continue_ref`, so the concern was that moving `continue_ref`
would drag `call_looseness` along with it and destroy the attribution. It does not: the
contract's canonicalization step fills `call_looseness` from the SHIPPED pack, so all six of
maniac's configs resolve to 0.55 no matter where `continue_ref` sits. The probe's premise
holds for maniac exactly as it does for the other five.

**One defect found and fixed while wiring the runner, worth recording because no test would
have caught it.** The runner deletes each batch's raw Parquet once the batch passes its
quality check — correct for a 730-config sweep, where the scored outputs are what the study
reads and the raw data is hundreds of gigabytes of duplication. But the T-probe spec's
constraints require raw data to survive until the S5 verdict settles, precisely because a
probe exists to diagnose a mechanism and diagnosis may need to go back to the hands. Left
alone, the probe would have quietly destroyed its own evidence on the way to a clean-looking
completion. Retention is now a per-stage policy: sweep stages retire, probe stages keep.

**The runner changes were proven against failure paths, not a happy path.** A dry harness
drives the runner's own wave-verification block over fabricated probe waves: 25 checks over
seven scenarios. It confirms a clean wave charges 6 to `probes` and 1 to `rerun_checks` and
keeps its raw data; that behaviour-gate failures still complete the wave and are counted as
ruled out rather than faulted; that a runtime-check failure blocks the wave, charges the
budget anyway because spent runs are spent, and deletes nothing; that re-running a charged
wave does not double-charge; that a short wave and a failed determinism check are both
refused; and that a sweep-stage wave still charges `stage1` and still retires raw data, so
stage 1's behaviour is unchanged. The harness is kept at
`docs/ai-dlc/research/persona-realism-artifacts/reachability-s5/dry-harness-wave-verify.py`.

**Budget, simulated against a throwaway copy of the manifest:** six waves take the study
from 758 to exactly 800 of the 1,500-run cap, with 36 on `probes` and 6 on `rerun_checks`.
The real manifest is untouched and will not move until the owner runs the waves.

**One deliberate lint exception.** `gen_probe_configs.py` imports `Mapping` and `Sequence`
from `typing` rather than `collections.abc`, which poker-coach's stricter ruff configuration
flags. It matches its neighbour `gen_wave_specs.py`, and poker-analytics runs no Python
linter of its own; consistency with the surrounding module was preferred over a rule that
repository does not enforce.

## Round 2 — build review, 2026-08-11

**Both reviewers returned FAIL, and both were substantially right.** Eleven findings between
them, ten accepted and one narrowed. Nothing had been simulated yet, so every defect was
caught before it could cost a run. The two reviewers overlapped on exactly one finding
(the tests validating stand-ins rather than the shipped artifacts), which is the sort of
agreement worth noticing: independently arrived at, from different starting points.

**Reviewers:** Claude `refuter` at Opus tier, fresh context, blind to the build conversation.
Codex `gpt-5.6-sol` at high effort, run in parallel on the same brief. Unlike round 1, Codex
produced a full report this time. Both were told the engine is frozen, both were forbidden
from running the wave runner or touching the budget manifest, and both were asked to attack
the design's central claim hardest.

**What neither reviewer could break, each verified independently against the live engine:**
all 36 configs validate; the merged pack differs by exactly one field — `postflop.continue_ref`
— across each persona's six configs, `maniac` included; the grid is a true five-point
logarithmic grid with both endpoints in bounds; all 730 stage-1 config hashes recompute with
zero mismatches and every anchor matches an independent recomputation; the budget simulates
to exactly 800; `backend/` is untouched.

| # | Severity | Finding | Adjudication |
|---|---|---|---|
| 1 | fatal (Codex) | `RETAIN_RAW=0` on the environment overrides the probe stage's retention policy and deletes the raw Parquet the spec requires be kept. The Python side treats only the literal `"1"` as retention, so any other value falls into the deletion branch. | **ACCEPTED, severity agreed.** The escape hatch was introduced by this slice. A deletion that cannot be undone must not sit one environment variable away from happening. A retaining stage now REFUSES a conflicting override rather than obeying it, and a value that is neither `0` nor `1` is refused rather than silently read as "not 1". |
| 2 | high (Codex) | The spec claimed that reusing each persona's stage-1 seed makes common random numbers hold within a wave. It does not: the exporter draws both each hand's deal and each bot action from one shared mutable generator, so the first hand where a probe level changes an action desynchronizes every hand after it. | **ACCEPTED — verified in `export_analytics.py:333-350` and `personas_postflop.py:1351-1376`.** The claim was false as written. The spec now states the correction and its consequence: a level must beat its anchor by **0.0775**, not 0.0548, because the comparison carries sampling noise from both arms. Note this is a property of the frozen engine that all 730 stage-1 runs share — it is not new to the probe and is explicitly NOT grounds for an engine change mid-study. |
| 3 | high (Codex) | Batch directories left by an interrupted wave are deleted and re-run while being asserted "never charged", contradicting the script's own rule that a run is spent the moment the exporter ran it. A wave could be re-spent while the ledger read as though it had not been. | **ACCEPTED, with the scope narrowed.** Codex implied any crash reaches this path; it does not — `sweep_runner`'s outermost handler always lands a manifest, so the window is a hard kill only. The defect is real inside that window and predates this slice. Fixed anyway, because budget integrity is the study's accounting backbone: orphans carrying `_SUCCESS` are now charged before being cleared, and a kill between the charge and the delete overcounts rather than undercounts — the safe direction against a hard cap. |
| 4 | med (Claude) | The execution checklist stated in the past tense that the probe "ran six waves… taking the study from 758 to 800". It has not run; `probes.executed` is 0. | **ACCEPTED.** A document asserting a state that does not exist is the worst kind of error in a study whose whole value is its record. Rewritten in the future tense with an explicit not-yet-executed date stamp. |
| 5 | med (Claude) | The one-time analytics bootstrap marker lived beside the stage's waves, so a new stage looked un-bootstrapped and re-entered a block that is one-time by construction — and by then the local budget manifest has legitimately diverged from origin, so the block would exit 1 and kill the unattended run the first time analytics `main` moved for any unrelated reason. | **ACCEPTED — the marker was confirmed present only under `stage1/`.** It would not have fired today (origin/main is currently an ancestor of the local HEAD) but it is a live trap. The marker is now study-scoped, with a migration so an already-bootstrapped machine does not pay the cost again. |
| 6 | med (both) | The compose tests validate synthetic documents built in a temporary directory; they never load the 36 emitted configs or the 6 emitted specs. The suite would stay green if the shipped artifacts drifted. | **ACCEPTED — the only finding both reviewers reached independently.** A new test class loads the real files: all 36 validate and are distinct, no config authors both dials, each persona covers the grid exactly once plus one anchor, `call_looseness` is identical across every level AND equal to the shipped value, and — stronger than any earlier check — `continue_ref` is the ONLY field that varies within a wave. The class was then verified to fail against a deliberately drifted copy, so it is known to be capable of failing. |
| 7 | low (Claude) | `test_maniac_anchor_reverts_cleanly` asserted only that the resolved value was constant, not what it was, so a constant-but-wrong resolution would pass. | **ACCEPTED.** The test now pins the value to the shipped pack's, matching its `tag` counterpart. |
| 8 | low (Claude) | The dry harness hardcoded a `/tmp` path and drove a hand-copied duplicate of the runner's Python block rather than the script itself, and did not exercise the shell-level changes P3 credited it with. | **ACCEPTED.** The harness now extracts the block from the runner on every run, so it cannot drift from what it claims to cover, and adds direct checks of the shell guards: the stage table, the retention refusals, and the interrupted-export accounting. 33 checks over nine scenarios. |
| 9 | low (Claude) | The generator's docstring justified its weaker ordering guard by claiming the coach engine cannot be imported in this repository, while the tests in the same repository import it and run unskipped. | **ACCEPTED.** The justification was overstated. Rewritten: the real reason is that generation should not take a runtime dependency the tests can take freely, and the anchors were separately confirmed by a full 730-config hash recomputation. |
| 10 | low (Claude) | The runner's header still described an overnight run, ~13 hours, and a 2.5-hour interruption cost — all stage-1 figures. | **ACCEPTED.** The header now states the cost per stage. |
| 11 | optional (Claude) | The anchors sit at each persona's shipped `continue_ref` (0.42 to 4.00), which is off-grid, so P4 must not read the anchor as a sixth grid point when judging monotonicity. | **ACCEPTED into the spec** as a preregistered instruction rather than left as a note for the analyst to remember. |

### What this round says about the process

- **The reviewers found what three green test suites did not, for the second time on this
  slice.** Round 1's fatal finding was invisible from the documentation; round 2's fatal
  finding was invisible from the tests, because the tests exercised the behaviour the author
  intended rather than the behaviour the script permits. A passing suite is evidence about
  the paths it takes, and nothing at all about the paths it does not.
- **The most valuable finding was the one about a claim, not about code.** The
  common-random-numbers correction changes no line of the build; it changes what the probe
  is allowed to conclude, and it widened the threshold that decides the verdict by forty
  per cent. A build review that only looked for broken code would have missed it.
- **Reviewer severity is a suggestion, not a verdict.** One finding was downgraded in scope
  after reading the engine's crash path, and one was fixed despite being out of the stated
  scope. Both calls came from reading source, not from weighing the reviewer's confidence.

## P4 — the probe result, 2026-08-11

**Bottom line: the frozen dial moves the measure, and it is nowhere near enough.** All six
waves ran clean. The preregistered mapping lands on row 3 for `maniac` — its distance falls
steadily all the way to the top of the dial's permitted range, which is the signature of a
boundary that binds — so the aggregate reads row 3, named with `maniac`. That row is the
trigger for an owner decision on widening the declared range. The evidence assembled below
argues against taking it: the largest gain anywhere is 0.3735 against a remaining gap of
3.9616, and the gain is visibly running out inside the range already measured.

**Execution was clean.** Six waves, 36 configurations plus 6 determinism duplicates, about
59 minutes. Every wave reports `sweep_status: complete`, every run `run_status: ok`, and
every determinism re-run reproduced byte-identically. The budget stands at exactly 800 of
1,500, with 36 on `probes` and 12 on `rerun_checks`, matching the preregistered projection
to the run.

### Results

`D` is the distance from the human reference band; lower is better and the cutoff is 5.1586.
The anchor is each persona's own reference, measured in this probe. A level counts as
beating it only by more than **0.0775** — the pinned threshold widened for the fact that the
two arms do not share a hand sample.

| persona | anchor `D` | best surviving level | its `D` | gain | verdict |
|---|---|---|---|---|---|
| tag | 9.6466 | 2.2494 | 9.6268 | +0.0198 | row 1 — inert |
| lag | 9.4859 | 2.2494 | 9.3854 | +0.1005 | row 4 — inconclusive |
| nit | 9.7075 | 0.1778 | 9.5793 | +0.1282 | row 4 — inconclusive |
| maniac | 9.4937 | 8.0000 | 9.1202 | +0.3735 | **row 3 — boundary binds** |
| passive_fish | 9.0492 | 2.2494 | 8.8654 | +0.1838 | row 4 — inconclusive |
| calling_station | 7.4067 | 8.0000 | 7.4155 | −0.0088 | row 1 — inert |

**No configuration came close to the cutoff.** The best distance anywhere in the probe is
calling_station's anchor at 7.4067, still 1.44 times the cutoff; `maniac`'s boundary-binding
best is 9.1202, or 1.77 times it. Row 2 — a gate-passing configuration below the cutoff —
did not fire for any persona, so nothing here feeds stage-3 composition.

### A defect in the preregistered mapping, found in review and recorded rather than resolved by fiat

**Row 3 was not written precisely enough to be applied without an interpretation, and the
two available readings disagree about calling_station.** The row says `D` "falls materially
and monotonically toward a declared endpoint". It does not say whether the fall is measured
against the anchor or across the grid, and the rows were never given a precedence order
despite not being mutually exclusive.

- Read **against the anchor** (the reading used above, and the one rows 1 and 2 are
  explicitly written in): calling_station is row 1, because its best level is 0.0088 *worse*
  than its anchor. maniac is row 3.
- Read **across the grid**: calling_station's five levels also fall monotonically, by 0.2399
  end to end, so it too would be row 3. maniac is row 3 either way.

**The aggregate is row 3 under both readings, and the recommendation is unchanged**, because
maniac triggers it regardless and calling_station's grid fall never approaches the cutoff
either. The ambiguity is recorded because a preregistered rule that needs an interpretation
after the results are in has lost part of what preregistration buys, and because the next
probe should fix the wording rather than inherit it. A third reading — requiring every step
to be material, not just the total — would take maniac out of row 3, since its final step
gains only 0.0420. That reading is noted for completeness and was not the one applied.

### Checks on the measurement, with their real strength

- **Each anchor's distance sits close to the nearest grid point**, within 0.005 to 0.033.
  This was originally described as agreement "at the shipped setting" and as an independent
  validation. Both claims were too strong and are withdrawn. The nearest grid point is not
  the shipped setting — for passive_fish it is 0.632456 against a shipped 0.42, and for
  calling_station 2.249365 against a shipped 4.00 — and the anchor and its neighbour share a
  seed and differ in one dial, so closeness is what continuity predicts rather than
  independent evidence. It is a weak local sanity check: it would not survive a gross
  pipeline error, but a fault shared by both arms would pass it.
- **Not one ruled-out configuration was an improvement.** **Eight** of the 30 levels failed
  the behaviour gates (the ledger previously said nine, which was a miscount): tag 1, lag 2,
  passive_fish 2, calling_station 3, with nit and maniac clean. Every one of the eight sits
  at the LOW end of the dial and every one has a worse distance than its anchor, by between
  0.079 and 1.259. So whether to count gate-failing configurations when reading row 1 is
  moot: including them changes no verdict. Worth noting in its own right — pushing this
  calldown anchor down does not merely fail to help, it makes bots stop being recognisably
  themselves.
- **No verdict depends on the threshold dispute.** Re-running the mapping at the unwidened
  0.054814 gives the same six rows as at 0.077520. Only one measurement falls between the
  two figures — nit at level 0.05, gaining 0.0569 — and it does not change nit's row. The
  √2 widening is therefore an argument about rigour, not about this result.

### Why widening the range is not recommended, despite row 3 firing

**The decisive argument is arithmetic, not extrapolation: one persona's seat is too small to
move the pool statistic far enough, at any dial setting whatsoever.** This came out of the
round-3 review, which produced a stronger case than the draft's own, and it was reproduced
independently before being adopted.

The distance `D` is almost entirely a linear function of one pooled statistic — the share of
flops that reach showdown. Across all 36 probe configurations, `D = 0.3113 × WTSD − 7.2948`
with R² 0.993, where WTSD is that share in percentage points. Reaching the 5.1586 cutoff
therefore requires a pooled WTSD of about **40.0**, against an observed range of 47.2 to
56.6.

The probe moves one persona at a time, and `maniac` sits in one seat of nine, accounting for
**17.0%** of all flops seen. In its best configuration the pool sits at 52.83. Setting
maniac's own showdown rate to **zero** — an impossibility, not a target — would take the
pool only to **44.92**, implying `D ≈ 6.69`. That is still 1.53 above the cutoff. **No value
of `continue_ref`, inside the declared range or beyond it, can bring a single-persona
configuration to the cutoff.** Widening the range cannot fix an arithmetic shortfall.

Two honest limits on that argument. It rests on the near-linear relationship between `D` and
pooled WTSD, which is a strong empirical regularity across these 36 configurations rather
than a law of the scorer. And it is a statement about **single-persona** probes only — a
stage-3 configuration moving all six personas at once faces no such seat-share ceiling,
which is precisely why §a.4 defines REACHABLE through a stage-3 combination run and not
through probes like this one.

**The curve-fitting argument is retained only as corroboration, and downgraded.** Against
`log10(continue_ref)`, maniac's distance falls 0.4292 per factor of ten (R² 0.958), implying
about 9.2 further factors of ten to close the gap — a dial value near 1.4 × 10¹⁰, roughly
1.7 billion times the declared ceiling. That is a **conditional illustration, not a bound
and not a forecast**: five points and three residual degrees of freedom, extrapolated nine
factors of ten past the last observation, with a slope standard error of 0.0517 whose 95%
interval spans 6.7 to 15.0 decades. An earlier draft called it an optimistic bound, which
claimed more than a five-point fit can carry.

What the observations do support without any extrapolation: **the improvement is already
running out inside the measured range.** maniac's last grid step gained 0.0420, 12% of the
0.3369 the previous step gained, and every other persona flattens or reverses at the top
end. Fitting the first four points and predicting the fifth overshoots by 0.196 — 2.5 times
the comparison noise — so the flattening is real and not a reading of the last point's luck.
Saturation observed up to 8.0 is still not proof of saturation beyond it; the seat-share
argument above is what does the work.

**Recommendation to the owner: record the row-3 trigger as fired, and decline the amendment.**
The seat-share arithmetic is the reason: at 17.0% of flops, `maniac` cannot carry the pooled
statistic to the cutoff even at a physically impossible extreme, so widening its dial's range
cannot deliver what the widening would be for. Three further considerations point the same
way — the gain is visibly saturating inside the measured range, an amendment costs
comparability with all 730 stage-1 runs, and one seed per level cannot carry a strong causal
claim in either direction.

The honest counter, stated rather than buried: this probe never measured beyond 8.0, so it
cannot directly refute the possibility that something changes out there. The recommendation
rests on the seat-share arithmetic holding, which in turn rests on `D` remaining near-linear
in pooled WTSD.

### Owner ruling, 2026-08-11: the trigger fired and the amendment is DECLINED

The owner was shown the row-3 result for `maniac`, the saturation evidence, and both
options, and ruled: **record the boundary-binds trigger as fired, and decline to widen the
declared range.** The declared range of `postflop.continue_ref` stays `[0.05, 8.0]`; the
estimand contract is not amended; the study stays comparable to all 730 stage-1 runs.

The residual doubt is recorded rather than argued away: nothing beyond the boundary was
ever measured directly, so the case rests on a flattening curve rather than on an
observation. That inference is stated with its own evidence above and can be revisited if
some later result makes the dial look more promising than it does now.

### What this settles, and what it does not

- **It answers the mechanism question the probe was built to ask, within the range it
  measured.** Across the whole declared range of the one dial stage 1 never touched, no
  gate-passing configuration gets within 2.2 of the cutoff, and the best gain any persona
  achieves is 0.3735 against a gap of 3.9616. That is a strong observation about
  `[0.05, 8.0]`. It is NOT a demonstration that the dial is causally inert, nor proof of a
  ceiling: one seed per level and a one-standard-deviation materiality convention can
  establish "no material effect observed", which is a weaker and more honest claim. Read
  together with stage 1's finding that the dominant dial is pressed against its floor, the
  operational ceiling inside the declared space is now well evidenced rather than merely
  suspected.
- **It does not deliver the study's verdict, and cannot.** §e.3 is enforced in
  `reachability_verdict`: nothing stronger than INCONCLUSIVE is available without
  detection-pilot evidence, which the S6 pilot still owes. The realism score also remains an
  exploratory surrogate after S3's validation failure, so no score-only verdict is
  permitted regardless.
- **No verdict here is threshold-dependent, and the spec's conservatism argument does not
  apply in the direction it was written.** Any threshold between 0.0198 and 0.1005 leaves all
  six rows identical, so both candidate figures — 0.054814 and 0.077520 — give the same
  answer, and tag's row 1 needs a threshold under a third of one standard deviation to flip.
  The spec argued that an *understated* threshold makes improvement easier to declare, so a
  no-effect finding is conservative. The √2 widening moves it the other way: an *overstated*
  bar makes no-effect easier to declare, so row-1 findings are less protected than that
  paragraph claims. It does not matter here only because nothing sits near the boundary.
- **The row-4 "material improvement" findings are weaker than the word suggests, and should
  not be carried forward as leads without more evidence.** Expressed in comparison
  standard deviations they are lag 1.30, nit 1.65, passive_fish 2.37 — across 30 comparisons
  judged against a one-standard-deviation bar. At that multiplicity, results near 1.3 and
  1.6 are what noise alone produces. Only passive_fish's would survive any correction for
  the number of comparisons made, and none of the three is load-bearing for anything above.
- **The aggregate is row 3, not row 1, and the language above should be read accordingly.**
  Row 1's text — "the operational ceiling within the declared space is confirmed and
  diagnosed" — is granted by the preregistered aggregate rule only if *every* persona lands
  in row 1. Two did. What the probe supports is the narrower statement written above: across
  the full declared range of this dial, no gate-passing configuration comes close, and the
  seat-share arithmetic explains why none could.

## Round 3 — analysis review, 2026-08-11

**Both reviewers returned FAIL, neither could break a single verdict, and both were right
about the reasoning around them.** The six per-persona rows, the aggregate, the joined
dataset (36 of 36 distances and gate results match disk exactly), the shipped dial values,
and the claim that no ruled-out configuration was an improvement all survived independent
recomputation. What failed was the justification: four claims in the supporting prose did
not hold, and one number was simply wrong.

**Reviewers:** Claude `refuter` at Opus tier and Codex `gpt-5.6-sol` at high effort, both
fresh-context, both given the raw joined results and told the mapping was preregistered.
They agreed independently on five findings, which is worth noting given they were not shown
each other's work.

| # | Severity | Finding | Adjudication |
|---|---|---|---|
| 1 | high (both) | Row 3 has no stated referent for "materially", and the rows were never given a precedence order despite not being mutually exclusive. calling_station's five levels also fall monotonically to the endpoint, by 0.2399, so a grid-relative reading puts it in row 3 alongside maniac; only an anchor-relative reading keeps it in row 1. The draft resolved this silently. | **ACCEPTED — verified: calling_station's grid is strictly monotone decreasing.** A real defect in the preregistration, not in the arithmetic. Both readings are now stated, along with a third that would take maniac *out* of row 3. The aggregate is row 3 under every reading, and the recommendation does not move. The next probe must define the referent before it runs. |
| 2 | med-high (Claude) | **The extrapolation was answering the wrong question.** `D` is near-linear in the pooled share of flops reaching showdown (R² 0.993); the cutoff needs about 40.0 percentage points; `maniac` occupies 17.0% of flops, so zeroing its showdown rate entirely reaches only 44.92, implying `D ≈ 6.69`. No dial value can bring a single-persona configuration to the cutoff. | **ACCEPTED and PROMOTED to the lead argument, after independent reproduction** (seat share 16.99%, floor 44.92, implied `D` 6.69). This is arithmetic where the draft offered a curve fit, and it is decisive where the fit was merely suggestive. Recorded with its two limits: it depends on the near-linearity holding, and it constrains single-persona probes only — a stage-3 combination faces no seat-share ceiling, which is why §a.4 routes REACHABLE through stage 3. |
| 3 | med (both) | The extrapolated 1.4 × 10¹⁰ was called an optimistic bound. It is neither a bound nor a forecast: five points, three residual degrees of freedom, extrapolated nine factors of ten, slope standard error 0.0517 giving a 95% interval of 6.7 to 15.0 decades. | **ACCEPTED.** Demoted to corroboration and relabelled a conditional illustration, with the interval stated. |
| 4 | med (both) | The "independent consistency check" was neither independent nor at the shipped settings. It compared each anchor to the nearest grid point — 0.632456 against passive_fish's shipped 0.42, 2.249365 against calling_station's 4.00 — under the same seed, and every difference is below the document's own comparison noise. | **ACCEPTED.** Both claims withdrawn; it is now described as a weak local sanity check that a fault shared by both arms would pass. |
| 5 | med (both) | The √2 widening inverts the spec's own conservatism argument, which was written for an understated threshold. An overstated bar makes a no-effect finding *easier*, not harder. Multiplicity went unmentioned: 30 comparisons judged at a one-standard-deviation bar, with the row-4 findings at 1.30, 1.65 and 2.37 comparison standard deviations. | **ACCEPTED, and it changes how the row-4 results should be carried forward.** The inversion is now stated. The row-4 "material improvements" are recorded as probably noise at that multiplicity — only passive_fish's would survive any correction — and explicitly not to be carried forward as leads. Nothing above depended on them. |
| 6 | low (both) | The gate-failure count was nine; it is eight. | **ACCEPTED — recounted: tag 1, lag 2, nit 0, maniac 0, passive_fish 2, calling_station 3.** The claim it supported holds exactly: all eight are worse than their anchors. |
| 7 | low (Codex) | "Ten billion times the permitted maximum" conflated the projected value with its ratio to the ceiling. 1.36 × 10¹⁰ ÷ 8.0 is 1.7 × 10⁹. | **ACCEPTED.** Corrected. |
| 8 | low (Claude) | The threshold-sensitivity list named tag as threshold-dependent. Its best gain is 0.36 of one standard deviation; any threshold between 0.0198 and 0.1005 leaves all six verdicts identical. | **ACCEPTED.** Rewritten to state that no verdict here is threshold-dependent, which is a stronger and truer claim than the one it replaces. |

### What this round says about the process

- **A review of reasoning found more than either review of code did, and the biggest finding
  was not an error at all.** Finding 2 did not correct a mistake in the analysis; it replaced
  a weak argument with a strong one that the analysis had not thought to make. The draft
  reached the right recommendation for thinner reasons than were available.
- **The verdicts survived; the story around them did not.** Everything mechanical — the
  joins, the rows, the aggregate, the exhaustive gate-failure claim — held under independent
  recomputation by two reviewers. Every accepted finding was about an interpretation, a
  characterisation, or a number quoted in prose. That is a useful signal about where the risk
  actually sits in this kind of work.
- **Preregistration only pays out if the rule is operational.** Row 3 was written in good
  faith and fixed before any data existed, and it still needed an interpretation once the
  results arrived — which is exactly the discretion preregistering was supposed to remove.
  Writing "materially" without saying "relative to what" cost most of the protection.

## Process notes worth keeping

- **The fatal finding was invisible from the documentation alone.** The estimand contract
  says `continue_ref` may be "swept independently as its own axis", which reads as
  permission. Only the shipped validator reveals that "independently" is enforced as
  *`call_looseness` must be absent*, which is a much stronger constraint than the prose
  implies. Specs that cite a contract without reading the code that enforces it will keep
  hitting this class of defect.
- **The frozen engine sha is a design constraint, not just a bookkeeping rule.** It removed
  the obvious fix from the table entirely. Any future slice that wants an engine change
  mid-study is really proposing to end the study's comparability.
