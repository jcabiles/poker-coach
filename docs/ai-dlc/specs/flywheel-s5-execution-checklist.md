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
