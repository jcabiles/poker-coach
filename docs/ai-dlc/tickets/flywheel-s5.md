# Ticket DAG — S5 (reachability study)

status: approved (Gate 2, owner, 2026-08-08 — "Approved — build T0–T6"; no Fable;
R1 = benchmark-first, R2 = amend to 5 seeds. See spec rulings block.)

**EXECUTION STATE 2026-08-09 (read this before resuming):** T0–T6 all done and MERGED
(coach PR #179; analytics PRs #16 analysis layer, #17 final pins, #18 portfolio-notes
pointer — all three merged on origin). Final pins: frozen engine sha `a0de83e`, wave-wide
covariance artifact `cov-525e183a12f269e3`, master seed 20260809, 2 workers, 5
confirmation seeds (§g.4). Dry-run wave (17 runs) proved the pipeline end to end; budget
manifest shows 22/1,500 executed. Stage-1 wave specs for all six personas are generated +
validated at `docs/ai-dlc/research/persona-realism-artifacts/reachability-s5/stage1/`
(gitignored). T7 remains. §e.3 stop-gate: no verdict stronger than INCONCLUSIVE until the
S6 judging run has executed.

**Execution model 2026-08-09 (owner ruling, rev 2): all remaining waves in ONE overnight
invocation** — ~13h from cold. `scripts/owner-run.sh` (local-only, never tracked) loops:
same command every time, reads the on-disk markers, runs the next unfinished persona wave
end to end (budget gate → sweep → a5 → budget record → Parquet retirement → completion
marker), then takes the next one. Order: tag 130, lag 130, nit 120, maniac 110,
passive_fish 120, calling_station 120 = 730 configs + 6 determinism re-runs = 736 runs.
`ONE=1` stops after a single wave. A blocked wave does NOT end the night — the loop moves
on — except for two study-wide conditions: engine identity changing mid-run, and a budget
charge of unknown status. Full runbook: execution checklist §3.1.

*Ruling history: this was briefly one-wave-per-invocation earlier the same day, when the
owner could not keep the machine awake for long blocks; that constraint lifted. The
per-wave behaviour never changed — only the loop around it. Restartable, not resumable: a
wave has no internal resume point, so an interrupted wave restarts from its first config
and its orphaned batch dirs (unscored, in no manifest, never charged) are cleared first.*

Three defects were found and fixed while making that change — all three predate the
split and would have bitten the original night-based plan too:

1. **Shared `out_root` destroyed five of six sweep manifests.** All six specs pointed at
   one folder; the runner overwrites `sweep_manifest.json` there with no guard, so each
   wave erased the previous wave's manifest — the exact evidence the post-wave
   verification step reads. Fixed by giving each persona its own subfolder
   (`~/s5-waves/stage1/<persona>`); a one-field edit per spec, re-validated through the
   real `load_spec`/`validate_configs`/`build_items` path (730/730 configs, 0 duplicate
   config hashes, all other bytes provably unchanged). Rule recorded in checklist §2.
2. **The `[ -f x ] && [ -f y ] && cmd` idiom under `set -euo pipefail` aborts the script**
   when the first test is false. The a5 loop uses that idiom over a glob that now always
   includes a `_rerun_check` directory with no `_SUCCESS` at its top, so the script would
   have exited immediately after a completed sweep. Rewritten as explicit `if`/`then`.
3. **The analytics checkout was three commits behind origin** with untracked local copies
   of the pin artifacts, which makes `git pull --ff-only` refuse. The old script pulled as
   its first action, so night 1 would have died in seconds. The script now syncs
   fail-closed: it re-proves each file's hash against `origin/main` and aborts rather than
   guessing if any differs.

**The runner was then dual-reviewed (2026-08-09, high effort: 4 finder angles, 36
candidates, 22 independent verifiers, 3 refuted, 10 upheld) and all 10 findings were
fixed.** The review's central charge was correct and structural: the first version decided
what had happened from *file existence* alone, which cannot distinguish success from
failure here — `sweep_runner.main()` writes `sweep_manifest.json` on its partial and crash
paths before exiting non-zero, and `scorer/constraints.py:main` writes its output file and
exits 0 even when `a5_pass` is false. A failed wave therefore looked exactly like a clean
one: full budget charged, raw Parquet deleted, wave stamped complete, holes in the design
invisible until stage-1 screening. The rewrite reads `sweep_status`, every `run_status`,
`producer_rerun_check.passed`, and each batch's `a5_pass`, and stops on anything
unexpected. Also fixed: the budget is now counted from the manifest's run list rather than
a hardcoded config count (checklist §5 forbids the latter explicitly) and charged before
any quality verdict, since spent runs are spent regardless; an a5-checker refusal collects
and reports instead of aborting mid-loop (which would have re-entered the same batch every
invocation and wedged that wave and all later ones); Parquet is retired only for batches
that actually passed a5; the engine-identity gate now also requires a clean
`backend`/`content` tree and re-checks after the sweep; the budget charge is bracketed by
an in-flight marker so a kill mid-write is detected rather than double-charged; a
truncated `a5.json` is redone rather than trusted; the analytics origin-sync is a one-shot
bootstrap (re-checking it every wave would have hard-blocked waves 2–6 the moment
origin/main moved, since this script mutates the budget manifest by design); waves that
cannot finish are marked `.WAVE_BLOCKED` with a reason, skipped by the picker so the other
waves still run, and reported at the top of every later invocation. One checklist
arithmetic error was corrected: a §f "night" is 28,800 s × 0.8 = **6.4** compute-hours,
not 8 — the derived figures were already right, only the prose was wrong.

Verified against nine simulated failure paths, none of which the original happy-path dry
run could reach: clean wave, partial sweep, crash manifest with an empty run list,
`run_status` mismatch under a `complete` status, determinism-re-run failure, a5-checker
refusal, `a5_pass` false, interrupted budget write, dirty engine tree — plus
adjudicated-resume (no second charge) and blocked-wave isolation.

NEXT: owner runs the six stage-1 waves at their own pace. After each wave: verify that
wave's `sweep_manifest.json` (`canonical.sweep_status`, per-run `run_status`), confirm
`a5.json` per batch, run the NROY join over that wave's batches, sanity-check the budget
manifest. After all six: stage-1 analysis (NROY join across waves → SRRC screening per
stat family per persona → `top_decile_box` per persona) → stage 2 → stage 3 →
confirmation, per the execution checklist.

Spec: `../specs/flywheel-s5.md` (rev 3). Tickets small, one owner each; hotspots
single-owner. **T0 blocks everything; T1–T3 parallelizable after T0; T4 needs T1+T2;
T5 needs T1–T4; T6 needs T5; T7 runs last.** Rulings R1/R2 must be resolved before T5's
wave-1 launch artifacts are finalized (they parametrize worker count + confirmation
seeds), but T1–T4 build can start beforehand.

- [x] **T0 — Pre-study pins** (interim: sha 6fa679d + cov-b637fbc20b001a24; re-pins once after the 2-worker knob merge, per R1 resolution). Freeze study engine sha; re-export 5 baseline replicates at
  it; `make covariance` → pin new wave-wide artifact id; build + pin `a5_baseline_z.json`.
  Done when: both artifact ids recorded in a study-pins doc; scorer accepts a baseline
  batch against the new artifact. Owns: poker-analytics `scorer/artifacts/` additions +
  `docs/methods/` study-pins note. (Owner launches the 5 exports — ~11 min serial.)
- [x] **T1 — Maximin LHD generator** (`analysis/lhd_generator.py` + tests). Persona-aware
  d (12,12,12,13,13,11); §a.2 paths only; probe-path refusal; maximin best-of-K seeded;
  byte-deterministic. Done when: rejection tests + maximin-beats-random test +
  determinism test green.
- [x] **T2 — NROY join + identity gate** (`analysis/reachability.py` part 1 + tests).
  `canonical.pool_tier.D < cutoff_c` AND five a5 rules; fail-closed triple/citation/ODCS
  check; partial-manifest consumption; budget-manifest checker (`make budget-check`).
  Done when: join tests on S4-fixture score/a5 files green; over-cap refusal test green.
- [x] **T3 — SRRC screening** (built as own module `analysis/srrc.py`, orchestrator call — same-wave file-ownership conflict with T2) (part 2 + tests). |SRRC|≥0.10, R²≥0.3 adequacy, INCONCLUSIVE
  collapse; synthetic-fixture tests with known coefficients. Done when: fixture tests
  green incl. rank-deficient input → clean "inadequate" verdict.
- [x] **T4 — Confirmation workflow + confirmatory-mean NROY** (part 3 + `confirm-cov`
  target). Two-phase per-finalist flow; imports scorer distance functions (no
  reimplementation); forced-INCONCLUSIVE branches enumerated with branch tests. Done
  when: end-to-end test on synthetic finalist batches produces a confirmatory-mean
  verdict object with every branch reachable in tests.
- [x] **T5 — Wave specs + execution checklist** (R1/R2 resolved 2026-08-09: workers=2 via new sweep-spec field, 5 confirmation seeds via §g.4) (poker-coach docs). Wave-1..N spec JSONs
  (seeds, lineup, cov id, `--keep-raw`, worker count per R1); owner runbook with
  a5-then-retire ordering + disk note; load_spec+load_config validation test. Done when:
  verify-by items 4+6 pass. BLOCKED BY: R1, R2, T0–T2.
- [x] **T6 — Dry run + verdict template** (synthetic in-suite; the REAL 17-run mini-sweep is checklist step 0.6, post-re-freeze). Mini-LHD end-to-end (byte-identical re-run);
  `reachability-verdict-s5.md` template with full §a.4 checklist + forced-INCONCLUSIVE
  slots mapped to artifacts. Done when: verify-by items 2+5 pass.
- **T7 — Close-out (post-execution).** After owner runs waves + analysis: verdict doc
  filled from structured outputs only; dual review of the verdict; FLYWHEEL-STATUS +
  roadmap tick + ledger close + memory. Done when: verdict merged, S5 box ticked.
  **Added 2026-08-09 (owner ruling) — the verdict doc MUST carry the clone limitation.**
  Every wave sweeps the ratified nine-seat lineup, in which seats sharing a persona are
  identical: three copies of one tag, two of one passive_fish. The study therefore cannot say
  whether a table of *varied* bots of the same type reads as more human than a table of
  clones. This is a boundary of the engine, not an oversight in the design — a seat binds to a
  persona name (`backend/tools/export_analytics.py:329`), the six names are a fixed enum
  (`backend/app/domain/archetypes.py:8`), the pack is looked up by that name, and the
  counterfactual layer overrides packs rather than seats, so an override to `maniac` moves
  every maniac at once. State the boundary explicitly; do not let a reader infer it was
  covered. The question itself is routed to the phase-3 gate as a structural capability gap
  (roadmap NEXT, "Phase-3 gate packet & decision"), NOT to S5 and NOT to S6.

Mid-slice trigger (recorded, per Gate 1): if stage results put NOT-REACHABLE in play,
insert **T-probe** (≈0.5 day): probe-declaration config path + endpoint probe waves,
budget-manifest counted.

**FIRED and RESOLVED, 2026-08-11.** Stage 1 returned zero NROY configurations out of 730,
with the dominant dial pressed against its declared floor in every persona's best result —
which is NOT-REACHABLE in play, so the trigger fired and T-probe was inserted. Spec
`../specs/flywheel-s5-tprobe.md`, tickets `flywheel-s5-tprobe.md`, findings and result
`../ledger/flywheel-s5-tprobe.md`.

Outcome: the probe swept `postflop.continue_ref` across its whole declared range for all six
personas (36 configs + 6 determinism duplicates, 59 minutes, budget 758 → 800 of 1,500, all
waves clean). No gate-passing configuration came within 2.2 of the 5.1586 cutoff; the largest
gain any persona achieved was 0.3735 against a remaining gap of 3.9616, and the gain
saturates inside the measured range. The preregistered mapping returned row 3 for `maniac`
(its distance falls to the top of the declared range), which triggered an owner decision on
widening that range; **the owner declined it on 2026-08-11**, so the declared range and the
estimand contract are unchanged and the engine stays at the frozen study commit.

Stage 2 is NOT resumed by this result: it would refine inside a box whose dominant dial is
exhausted. **S5's verdict still cannot exceed INCONCLUSIVE until the S6 detection pilot
supplies evidence** — §e.3, enforced in `reachability_verdict`.
