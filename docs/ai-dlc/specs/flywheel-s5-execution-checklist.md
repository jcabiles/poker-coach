# S5 execution checklist — owner runbook for launching reachability-study waves

**Bottom line:** this is the step-by-step the owner follows to launch and close out each
S5 sweep wave (stage 1, stage 2, stage 3, and stage-3 confirmation). Every wave runs from
a checkout parked at the frozen engine commit — never from a `main` that has since moved
— and every step below is a gate, not a suggestion: skipping one produces data the
analysis layer will refuse. Full design: `flywheel-s5.md`; identities every step must
match: `poker-analytics:docs/methods/s5-study-pins.md`. Every command below is written to
run as-is from the stated working directory — no flag or variable is placeholder prose.

**Working directories used below:**
- `$COACH` — the frozen poker-coach checkout (set once in step 0.2).
- `$ANALYTICS` — the poker-analytics checkout (`~/Documents/Github/poker-analytics` unless
  you've relocated it).

## 0. Pre-study, one time (before wave 1 — do this before anything else)

1. Merge the sweep-runner workers-knob PR (adds the optional `workers` field to the
   sweep-spec JSON) into poker-coach `main`.
2. **Re-freeze the study checkout**: check out `main` at the post-merge commit into a
   fresh, dedicated directory (`$COACH`) and record its commit sha — this becomes the NEW
   frozen sha (superseding the one already recorded in the pins doc).
3. Re-run the baseline rebuild at the new frozen sha. The orchestrator regenerates
   `scripts/owner-run.sh` fresh against the new sha at this step — that script is
   **local-only by owner ruling, never tracked in git**, so don't look for it in the repo;
   describe the step by what it does: it re-exports the 5 baseline replicates, rebuilds
   the wave-wide Σ_sim covariance artifact, and rebuilds `a5_baseline_z.json`. Run whatever
   script the orchestrator hands you at this point.
4. Update `s5-study-pins.md` (poker-analytics) with the new frozen sha and the new
   covariance artifact id. Wave 1 may not launch while any pin still reads the old sha
   or `PENDING`.
5. **Initialize the budget manifest** (one time; refuses to run twice over an existing
   file — if it already exists, skip this and go straight to step 1.1):
   ```
   cd $ANALYTICS && .venv/bin/python analysis/reachability.py --budget-check \
     --manifest analysis/budget-manifest.json --init
   ```
   (`--init` and the manifest's `dryrun` stage — 17 runs, used by step 0.6 below — both
   shipped with the S5 analytics branch; this command works as written once that branch
   is merged.)
6. **Dry-run wave** (after the re-freeze, before wave 1 — proves the whole pipeline end
   to end; the orchestrator can run this one, it's ~35 minutes, not an overnight wave):
   a real 2-persona mini-sweep, 16 runs + 1 mandatory rerun-check = 17 runs.
   1. Author a 2-persona, small sweep-spec JSON by hand (2 personas × 8 configs × 1 seed,
      or equivalent — 16 (config, seed) arms) pointing at `$ANALYTICS` and the frozen-sha
      covariance artifact.
   2. Launch it:
      ```
      cd $COACH/backend && .venv/bin/python -m tools.sweep_runner --spec <dryrun-spec.json> --keep-raw
      ```
   3. Score + a5-check every resulting batch (see step 4 below for the exact `a5-check`
      form) and join the outputs — same procedure as a real wave's post-wave step, just
      on 17 runs instead of hundreds.
   4. Retire the raw Parquet once every batch's a5 output is saved.

**Binding for the whole study:** every sweep, score, and analysis run happens inside
that ONE frozen-sha checkout (`$COACH`). Any later merge to poker-coach `main` —
including unrelated work — must never touch the parked checkout; `engine_git_sha` is
stamped from `HEAD` at export time, so a moved checkout silently produces data keyed to
the wrong sha and the scorer's covariance-artifact binding will refuse it (or worse,
silently match the wrong thing if the sha happens to collide with nothing pinned).

## 1. Pre-wave (every wave, before launch)

1. Project the wave against the running budget manifest, naming the real stage and the
   total executed-count-after-this-wave (not just this wave's own run count):
   ```
   cd $ANALYTICS && make budget-check STAGE=<stage-name> RUNS=<executed-so-far + this-wave's-runs>
   ```
   Valid `<stage-name>` values (from `analysis/reachability.py`'s `STAGE_BUDGETS`):
   `baseline_replicates`, `stage1`, `stage2`, `stage3_combinations`, `confirmation`,
   `rerun_checks`, `probes`. A refusal here IS the §f escalation trigger surfacing; do not
   override it — go to step 7 (Escalation).
2. Verify the parked checkout's sha still equals the sha recorded in `s5-study-pins.md`
   (`git rev-parse HEAD` in `$COACH` vs. the pins doc). Any mismatch means the checkout
   moved — stop and investigate before spending compute on data that will be refused.

## 2. Generate configs + spec

Run `gen-waves` (poker-analytics) with the pinned study seed (`MASTER_SEED=20260809` —
never a different seed, and never omitted) and the stage-appropriate inputs. This writes
the config JSON files and one sweep-spec JSON per persona wave into `OUT_DIR`.

**Stage 1** (one persona varied, others canonicalized baseline):
```
cd $ANALYTICS && make gen-waves MASTER_SEED=20260809 STAGE=1 \
  BASE_PACK_HASH=<frozen checkout's live pack hash> \
  OUT_DIR=analysis/output/s5-waves OUT_ROOT=<sweep out_root> \
  ANALYTICS_REPO=<absolute path to $ANALYTICS> COV_ARTIFACT=<pinned wave-wide cov id> \
  PERSONAS=<comma-separated persona subset, or omit for all six>
```

**Stage 2** (needs stage 1's top-decile box):
```
cd $ANALYTICS && make gen-waves MASTER_SEED=20260809 STAGE=2 \
  BASE_PACK_HASH=<frozen checkout's live pack hash> \
  OUT_DIR=analysis/output/s5-waves OUT_ROOT=<sweep out_root> \
  ANALYTICS_REPO=<absolute path to $ANALYTICS> COV_ARTIFACT=<pinned wave-wide cov id> \
  BOX_FILE=<path to stage-1 top-decile-box JSON>
```

**Stage 3** (per-persona top-decile pools, 20 roster combos):
```
cd $ANALYTICS && make gen-waves MASTER_SEED=20260809 STAGE=3 \
  BASE_PACK_HASH=<frozen checkout's live pack hash> \
  OUT_DIR=analysis/output/s5-waves OUT_ROOT=<sweep out_root> \
  ANALYTICS_REPO=<absolute path to $ANALYTICS> COV_ARTIFACT=<pinned wave-wide cov id> \
  POOLS_FILE=<path to per-persona top-decile-pools JSON> N_COMBOS=20
```

**`OUT_ROOT` must be unique per wave — one folder per persona, not one folder for the
stage.** The sweep runner writes its `sweep_manifest.json` (the record of which runs
succeeded, plus the determinism re-run check) to the top of `out_root` and overwrites any
file already there, with no guard. Six persona waves sharing `.../stage1` therefore leave
only the last wave's manifest on disk and silently destroy the other five, which are the
evidence the post-wave verification step reads. `gen-waves` forwards a single `OUT_ROOT`
verbatim into every spec it generates, so it cannot produce per-persona roots on its own:
after generating, set each spec's `out_root` to `<stage root>/<persona>` before launching.
Batch directories themselves never collide (they are keyed by config hash, which is unique
across personas) — the manifest is the only casualty, which is what makes the loss quiet.
Stage-1 specs were corrected this way on 2026-08-09 and re-validated through the real
`load_spec`/`validate_configs`/`build_items` path: 730/730 configs, 0 duplicate hashes.

**Confirmation** has no `gen-waves` support (its generator only takes `--stage 1|2|3`) —
hand-author the 10-finalist, 5-fresh-seed sweep-spec JSON per §a.6/§g.4 instead; the
orchestrator will produce it against the current frozen sha and current finalist list.

## 3. Launch

```
cd $COACH/backend && .venv/bin/python -m tools.sweep_runner --spec <wave-spec.json> --keep-raw
```

`--keep-raw` is mandatory — the post-wave a5-check step below needs the retained
Parquet; without it the runner deletes raw data immediately after scoring and there is
nothing left to check. Every generated spec already pins `workers: 2` (the ruled worker
count — 3 workers measured 341–345 hands/sec, under the 350 floor; 2 workers measured
399–400, clears it) and the ratified 9-seat lineup; do not edit either by hand.

### 3.1 One overnight run for all remaining waves (owner ruling, 2026-08-09, rev 2)

> **Superseded 2026-08-11 (owner ruling): S5 (the reachability study this runbook drives) is CLOSED, stopped early.** Stage 1 alone falsified the space; stage 2, stage 3, and confirmation below never ran. Kept for provenance only — see `bot-realism-flywheel.md`'s S5 close-out.

**All remaining waves run back to back in a single invocation** — roughly 13 hours from
cold for all six. One command, always the same:

```
bash ~/Documents/Github/poker-coach/scripts/owner-run.sh
```

Order and sizes: tag (130 configs), lag (130), nit (120), maniac (110), passive_fish (120),
calling_station (120) — 730 configs plus one determinism re-run per wave, 736 runs charged
to the budget. Each wave runs end to end on its own: budget gate, sweep, a5 check on every
batch, budget record, raw-Parquet retirement, completion marker. Then the loop takes the
next persona.

**Which stage runs is set by `STAGE`, and an unknown stage is refused rather than run.**
The per-persona config counts live in the runner's `STAGE_NCONFIGS` table, one row per
stage, and the config runs are charged to the budget stage of the same name. A stage with
no row exits immediately with an error: falling back to a default count would assert the
wrong wave size and could mark a short wave complete. Determinism-dup arms always book to
`rerun_checks` whatever the stage, so a dup arm is never counted twice under two names.
The `continue_ref` mechanism probe runs as `STAGE=probes bash …` with 6 configs per
persona.

*Ruling history: this was briefly one-wave-per-invocation (2026-08-09) when the owner could
not keep the machine awake for long blocks. That constraint lifted the same day. The
per-wave behaviour is unchanged and is still the unit of work — only the loop around it is
new, and `ONE=1 bash …` still stops after a single wave when only a couple of hours are
available.*

**The script is restartable, not resumable.** Re-running the same command after any
interruption picks up at the next unfinished wave, because completion is recorded per wave
on disk. But there is no resume point *inside* a wave: the sweep runner has no
skip-completed-configs logic, so an interrupted wave restarts from its first config. Batch
directories left behind by an interrupted attempt are orphans — unscored, in no manifest,
and never charged — so the script deletes them before re-sweeping rather than risk a stale
`_SUCCESS` from the old attempt being read as fresh output.

**A blocked wave does not end the night.** If a wave cannot finish, it is marked
`.WAVE_BLOCKED` and the loop moves to the next persona, so one bad wave cannot waste the
remaining ten hours. Two conditions do stop the night, because they make every later wave
untrustworthy or unaccountable: the engine identity changing mid-run (every batch produced
after that point is attributed to an engine revision that did not produce it), and a budget
charge of unknown status (further waves would be charged on top of bookkeeping nobody can
trust). Everything else — a partial sweep, an a5 refusal, a failed quality gate, a
determinism-check failure — blocks only its own wave.

The run ends with a summary: waves complete, waves blocked with their reasons, and the
running budget total against the 1,500 cap.

**Ground-truth rule (from the 2026-08-09 code review of the script): success is read from
the manifest and the a5 verdicts, never inferred from a file existing.** Two traps make
file-existence tests actively wrong here. `sweep_runner.main()` writes `sweep_manifest.json`
on its failure paths too — both the `sweep_status: "partial"` path and the `_crash_manifest`
path — before exiting non-zero, so the manifest's presence says only that the runner ran, not
that it worked. And `poker-analytics:scorer/constraints.py:main` writes its `--out` file and exits 0 even when
`a5_pass` is false, so an `a5.json` on disk may be a recorded *failure*. A script that keys on
either would charge the budget for a truncated wave, delete the raw Parquet that is the only
evidence for diagnosing the failures, and stamp the wave complete. Read
`canonical.sweep_status`, every `canonical.runs[].run_status`, `canonical.producer_rerun_check.passed`,
and each batch's `a5_pass` — and treat anything unexpected as a stop, not a warning.

Per-wave state lives in four markers inside each persona folder:

- `.WAVE_COMPLETE` — the wave finished cleanly. Written last, and only after every expected
  batch carries a passing a5 result.
- `.BUDGET_RECORDED` / `.BUDGET_IN_FLIGHT` — a two-marker pair, because the budget charge
  mutates `budget-manifest.json` before any single marker could be written. `IN_FLIGHT` goes
  down first; `RECORDED` replaces it after the write lands. Finding `IN_FLIGHT` without
  `RECORDED` means a kill landed inside that window, so the charge is of unknown status: the
  script stops and asks for the manifest to be checked by hand rather than risk a second charge.
- `.WAVE_BLOCKED` — the wave hit something needing a decision. It holds the reason on line 1.
  Blocked waves are skipped by the wave picker so the remaining waves can still run, are
  reported prominently at the top of every subsequent invocation, and prevent the script from
  ever announcing that stage 1 is done.

**The budget is charged from the manifest's own run list, as early as possible, and exactly
once.** Runs are spent the moment the exporter executes them — §4.2 above says the seeds of
failed runs "are already spent against the budget" — so the charge happens as soon as the run
list is readable, *before* any quality verdict. A wave that sweeps cleanly but stumbles in the
a5 check is still charged; otherwise real spend would silently accumulate outside the 1,500
cap. The count comes from `len(canonical.runs)` plus the rerun-dup arm inferred from
`volatile.producer_rerun_check.dup_dir` — never from the config count in the spec.

If a run dies after the sweep but before the follow-up steps, the next invocation sees the
existing `sweep_manifest.json` and resumes from the a5 check instead of re-sweeping —
re-sweeping would spend the wave's runs a second time against the 1,500 cap.

**Engine identity is checked before AND after the sweep.** `export_analytics._git_sha()`
stamps `engine_git_sha` from `HEAD` with no dirty-tree probe and no `-dirty` suffix, so an
uncommitted edit under `backend/` or `content/` would be recorded as the frozen sha — and this
working tree is shared with other agent sessions. The script therefore requires both
`HEAD == <frozen sha>` and a clean `git status --porcelain -- backend content` at launch, and
re-checks both after the sweep; a change during the wave blocks it, because every batch just
produced is attributed to an engine revision that did not produce it. Residual gap worth
knowing: a dirty state that appears and is reverted entirely within the wave still slips
through, since only the endpoints are sampled.

**Splitting does not touch the §f escalation clause, and must not be read as if it
did.** §f's escalation trigger ("past 6 worst-bound nights" → the §a.3 emulator fallback
activates) counts *compute*, not calendar: a "night" there is an 8-hour owner-capped block
derated by 0.8, i.e. 28,800 s × 0.8 = 23,040 s = 6.4 compute-hours of usable throughput.
That is the divisor §f itself uses (`28,800 × 0.8 / 56.93 ≈ 404.7 configs/night`), and it
is why §f can state a run count as a fraction of a night. Chopping the same 736 stage-1 runs into six 2.5-hour sittings
spread across whatever days suit the owner changes zero compute, so the trigger cannot
move. Do not later compare elapsed calendar days against the 6-night threshold and
conclude escalation fired — that misreading would wrongly activate the emulator fallback
and inject its error term into Σ*. Arithmetic at the ruled 2 workers (~400 hands/sec per
batch, two batches concurrent ⇒ ~62.5 s/config): ~369 configs per compute-night, so
stage 1 ≈ 2.0 nights and the full 1,500-run cap ≈ 4.1 nights — under 6, consistent with
the ledger's ≈3.5–4 nights, and the source of the ~2.0–2.5h per-wave estimate above.

**Operating rules for the machine, in priority order:**

1. **Keep it plugged in.** A sleeping laptop that runs the battery flat kills the run.
2. **Closing the lid is safe.** macOS suspends the processes rather than killing them, and
   the throughput measurement is unaffected: the exporter times each batch with
   `time.monotonic()`, which on macOS is `mach_absolute_time()` — a clock that stops while
   the machine sleeps. Sleep time is invisible to the a5 rule-5 throughput floor, so no
   batch is wrongly disqualified. The work simply pauses and resumes on wake.
3. **Never Ctrl-C a wave.** There is no resume point inside a wave; the runner has no
   skip-completed-configs logic, so an interrupt discards up to 2.5 hours and the restart
   re-spends those runs.
4. **Run it on an idle machine.** The 350 hands/sec floor fails under contention — the dry
   run measured 72–123 hands/sec on a busy laptop versus 391–417 serial when idle.

## 4. Post-wave (per batch, after the sweep completes)

1. For every batch in the wave, save the a5 output (never let it go to stdout only):
   ```
   cd $ANALYTICS && make a5-check DIR=<batch> OUT=<batch>/a5.json COV=<wave's pinned cov artifact>
   ```
2. Filter to batches whose sweep-manifest `run_status` is `"ok"` — read this from the
   wave's `sweep_manifest.json` `runs` entries, never assume every launched arm succeeded.
   For any batch whose `run_status` is NOT `"ok"`:
   1. Author a FRESH spec containing only the failed configs — fresh seeds, never the
      failed run's original seeds (they're already spent against the budget).
   2. Budget-check it (step 1 above) and launch it (step 3 above).
   3. Record it (step 5 below) once it completes.
3. Only after every `"ok"` batch's a5 output is SAVED (step 4.1's `OUT=` file on disk) —
   and every failed batch has been replaced per 4.2 and its replacement's a5 output is
   also saved — may the raw Parquet be retired (delete the retained Parquet for every
   batch in the wave). Disk note: the largest stage-1 wave holds ~6–8GB of Parquet at
   peak transient before retirement — plan disk headroom for that, not steady state
   (~0 once retired).

## 5. Record the wave

Append the wave's executed run count to the running budget manifest
(`analysis/budget-manifest.json`, poker-analytics) — this is what step 1 of the NEXT wave
checks against the cap.

**Executed count = number of configs × seeds + 1** (the mandatory producer-rerun check
that every `sweep_runner` invocation performs once, regardless of how many configs/seeds
it covers). Do not compute this from `len(configs)` alone — read the true count from the
wave's `sweep_manifest.json`: count the entries in its top-level `runs` list (one entry
per executed arm) and add the rerun-dup arm counted separately under
`producer_rerun_check`. 23 rerun-check runs are already budgeted across the whole
program (`rerun_checks` stage, floor=upper=23) — don't double-count them as ordinary
stage runs when appending to the manifest.

## 6. Stage 2 / stage 3 / confirmation flow

- **Mechanism probes** (`STAGE=probes`) repeat steps 1–5 per persona and are the only
  stage that unfreezes a frozen dial. Configs come from
  `poker-analytics:analysis/gen_probe_configs.py` rather than from the sweep designer,
  because a probe anchors on measured stage-1 results instead of on a fresh design. Two
  rules are specific to this stage and neither is optional:
  - **Every config that moves the frozen dial must carry its own `probe_declarations`
    entry.** Without one the engine refuses the config outright. That refusal is the
    mechanism by which a frozen axis is unfrozen *by declaration* rather than bypassed, so
    a probe wave that loads without declarations is a bug, not a convenience.
  - **A probe persona's config must never author both `postflop.continue_ref` and
    `postflop.call_looseness`.** The engine rejects that pair for one persona regardless of
    intent, because co-varying them pins their ratio and destroys the attribution the probe
    exists to make. The generator drops `call_looseness` so it reverts to the shipped pack
    default; the consequence is that a probe's anchor is not any stage-1 configuration and
    its distance must be measured rather than looked up.
  - The `continue_ref` probe is six waves of 6 configs each — 36 config runs charged to
    the `probes` budget stage and 6 determinism-dup arms to `rerun_checks`, which will take
    the study from 758 to 800 of the 1,500-run cap. **Not yet executed as of 2026-08-11.**
- **Stage 2** repeats steps 1–5 per persona, generating from stage 1's top-decile box.
- **Stage 3** repeats steps 1–5 for the 20 roster-combination configs.
- **Confirmation is two-phase** (never a single sweep pass):
  - **Phase 1** — export + gate the fresh-seed batches for the 10 closest-by-D finalists
    (`--keep-raw`, same launch form as step 3); the sweep-wide covariance artifact scores
    these batches too, but that score is thrown away for the verdict, not used.
  - **Phase 2** — per finalist: build a finalist-specific covariance artifact from its 5
    fresh-seed batches:
    ```
    cd $ANALYTICS && make confirm-cov BATCHES="<batch1> <batch2> <batch3> <batch4> <batch5>"
    ```
    (`BATCHES` is intentionally unquoted in the Makefile recipe — argparse `nargs="+"`
    relies on the shell's word-splitting; pass the five directories space-separated,
    exactly as shown, with no path containing a space.) Then score each batch directly
    against THAT artifact:
    ```
    cd $ANALYTICS && make score DIR=<batch> OUT=<batch>/score.json COV=<finalist artifact id>
    ```
    then run `make a5-check DIR=<batch> OUT=<batch>/a5.json COV=<finalist artifact id>`
    per batch, then retire the raw data (same OUT-then-retire rule as step 4).
  - Confirmation uses **5 fresh seeds per finalist** (§g.4 amendment, R2 ruling) — never
    3, and never seeds already used in design-stage selection (winner's-curse guard).

## 7. Escalation

If a pre-wave `make budget-check` refuses a wave for exceeding the 1,500-run cap, that
refusal is itself the §f escalation trigger — stop, do not force the wave through, and
bring it to the owner/roadmap for the emulator-fallback or amendment decision. This is
the only escalation path; there is no silent-growth option.
