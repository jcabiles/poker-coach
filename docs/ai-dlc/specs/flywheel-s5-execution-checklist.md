# S5 execution checklist — owner runbook for launching reachability-study waves

**Bottom line:** this is the step-by-step the owner follows to launch and close out each
S5 sweep wave (stage 1, stage 2, stage 3, and stage-3 confirmation). Every wave runs from
a checkout parked at the frozen engine commit — never from a `main` that has since moved
— and every step below is a gate, not a suggestion: skipping one produces data the
analysis layer will refuse. Full design: `flywheel-s5.md`; identities every step must
match: `poker-analytics:docs/methods/s5-study-pins.md`.

## 0. Pre-study, one time (before wave 1 — do this before anything else)

1. Merge the sweep-runner workers-knob PR (adds the optional `workers` field to the
   sweep-spec JSON) into poker-coach `main`.
2. **Re-freeze the study checkout**: check out `main` at the post-merge commit into a
   fresh, dedicated directory and record its commit sha — this becomes the NEW frozen
   sha (superseding the one already recorded in the pins doc).
3. Re-run the baseline rebuild at the new frozen sha. This is `scripts/owner-run.sh`'s
   job (the orchestrator regenerates it against the new sha — don't hand-write it): it
   re-exports the 5 baseline replicates, rebuilds the wave-wide Σ_sim covariance
   artifact, and rebuilds `a5_baseline_z.json`.
4. Update `s5-study-pins.md` (poker-analytics) with the new frozen sha and the new
   covariance artifact id. Wave 1 may not launch while any pin still reads the old sha
   or `PENDING`.

**Binding for the whole study:** every sweep, score, and analysis run happens inside
that ONE frozen-sha checkout. Any later merge to poker-coach `main` — including
unrelated work — must never touch the parked checkout; `engine_git_sha` is stamped from
`HEAD` at export time, so a moved checkout silently produces data keyed to the wrong sha
and the scorer's covariance-artifact binding will refuse it (or worse, silently match
the wrong thing if the sha happens to collide with nothing pinned).

## 1. Pre-wave (every wave, before launch)

1. `make budget-check` (poker-analytics) against the running budget manifest — refuses if
   this wave would push the study over the 1,500-run cap. A refusal here IS the §f
   escalation trigger surfacing; do not override it.
2. Verify the parked checkout's sha still equals the sha recorded in `s5-study-pins.md`
   (`git rev-parse HEAD` in the frozen checkout vs. the pins doc). Any mismatch means the
   checkout moved — stop and investigate before spending compute on data that will be
   refused.

## 2. Generate configs + spec

Run `make gen-waves` (poker-analytics) with `--master-seed 20260809` (the pinned study
seed — never a different seed, and never omit it) and the stage-appropriate inputs
(stage 1: persona list; stage 2: each persona's top-decile box from stage 1; stage 3:
per-persona top-decile pools). This writes the config JSON files and one sweep-spec JSON
per persona wave into the wave's output directory.

## 3. Launch

```
python -m tools.sweep_runner --spec <wave-spec.json> --keep-raw
```

`--keep-raw` is mandatory — the post-wave a5-check step below needs the retained
Parquet; without it the runner deletes raw data immediately after scoring and there is
nothing left to check. Every generated spec already pins `workers: 2` (the ruled worker
count — 3 workers measured 341–345 hands/sec, under the 350 floor; 2 workers measured
399–400, clears it) and the ratified 9-seat lineup; do not edit either by hand.

## 4. Post-wave (per batch, after the sweep completes)

1. `make a5-check DIR=<batch> COV=<wave's pinned cov artifact>` against the retained
   Parquet, for every batch in the wave.
2. Only after every batch's a5-check has run: retire the raw data (delete the retained
   Parquet). Disk note: the largest stage-1 wave holds ~6–8GB of Parquet at peak transient
   before retirement — plan disk headroom for that, not steady state (~0 once retired).

## 5. Record the wave

Append the wave's executed run count (per stage) to the running budget manifest
(`budget-manifest.json`, poker-analytics) — this is what step 1 of the NEXT wave checks
against the cap.

## 6. Stage 2 / stage 3 / confirmation flow

- **Stage 2** repeats steps 1–5 per persona, generating from stage 1's top-decile box.
- **Stage 3** repeats steps 1–5 for the 20 roster-combination configs.
- **Confirmation is two-phase** (never a single sweep pass):
  - **Phase 1** — export + gate the fresh-seed batches for the 10 closest-by-D finalists
    (`--keep-raw`); the sweep-wide covariance artifact scores these batches too, but that
    score is thrown away for the verdict, not used.
  - **Phase 2** — per finalist: build a finalist-specific covariance artifact
    (`make covariance BATCHES=<finalist's fresh-seed batches>`), then score each batch
    directly against THAT artifact (`make score DIR=<batch> COV=<finalist artifact>`),
    run `make a5-check` against it, then retire the raw data.
  - Confirmation uses **5 fresh seeds per finalist** (§g.4 amendment, R2 ruling) — never
    3, and never seeds already used in design-stage selection (winner's-curse guard).

## 7. Escalation

If a pre-wave `make budget-check` refuses a wave for exceeding the 1,500-run cap, that
refusal is itself the §f escalation trigger — stop, do not force the wave through, and
bring it to the owner/roadmap for the emulator-fallback or amendment decision. This is
the only escalation path; there is no silent-growth option.
