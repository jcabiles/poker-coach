# Build ledger — flywheel S3 (realism score v0 + validation), 2026-08-06 → 2026-08-07

Gate 2 approved 2026-08-06 (5–7d appetite; floor = hard gate — later superseded, see
rulings). 8 tickets executed as planned (T1∥T2∥T3 → T4 → T5 · T6 after T2 · T7 · T8).
Every maker ticket adversarially reviewed (maker ≠ checker); T1 and the T4+T5+T7 tail
dual-reviewed cross-family (Claude refuter + Codex `gpt-5.6-sol`).

## Headline result

**The realism score FAILED retrospective validation with the wrong sign — and the
preregistered stop-gate held.** All three §e legs negative under F0 (ρ=−0.2036,
p=0.572; stratified τ-b=−0.1652, p=0.728; LOPO entirely below the 0.60 floor) and
under the one-shot §e.3 revision F1 (ρ=−0.3770 — worse, exactly as §g.1.6 pre-derived
in writing before any score existed). Negative within each campaign independently, so
not a between-campaign artifact. Status = `exploratory-surrogate` for both formula
triples; §e.3 is spent (no F2); S5 may not issue a score-only verdict; S4 may use
scores as smoke data only. Both final reviewers independently reproduced **every**
number (ρ to 1e-10, all 720 permutations, 84 stat values across both campaigns, Σ
assembly by hand, F1 = exactly 25 rows doubled): the failure is real, not an
implementation artifact.

Interpretation boundary (owner-ruled + contract-pinned): this is a retrospective
face-validity result against n=12 ratings from two campaigns; it says the v0
distance-to-population-targets construction does not rank the roster the way expert
review did. It does NOT say which side is wrong. Feeds the flywheel phase-3 ceiling
question directly.

## Owner rulings folded (all 2026-08-06, during the slice)

1. Gate 2: go at 5–7 days; floor = hard executable constraint (initial).
2. Post-review: per-persona floor gate **DELETED** (dual review proved it vacuous on
   the informative coordinates — nit/fish would pass VPIP at any value 0–100); floor
   demoted to non-gating diagnostic; §a.5 keeps five rules.
3. §e validation pre-labeled **retrospective** (mapping authored after §e.1 ratings
   were visible; closed-form + adverse-direction mitigations recorded but not label-
   sufficient per both reviewers).
4. GGPoker source: **use + disclose** despite its internal contradiction
   (recreationals defined VPIP>45, published 35–38); sensitivity computed (only
   passive_fish's treatment flips under any consistent reading).
5. Mapping VPIP intervals: frozen as declared contract constants; research-band
   discrepancy tabled beside them.
   Director adjudications: §e.3 doubling subset stays 3 rows; ratified lineup (not
   DEFAULT_LINEUP) governs sim50k identity.

## What shipped (poker-analytics, branch `feat/flywheel-s3-t7-validation` @ dcb9349)

- **Amendment 2026-08-06-A** (§g.1, revs 1–5) + `data/targets/registry-v2.json`
  (final sha256 `b83043ae…01528c1d`): two-tier score, 40-cell GGPoker snapshot with
  per-value provenance (720 raw + 44 diagnostic values), frozen σ recipes, mapping,
  degeneracy report (2 distinct target vectors; PFR separation 0.0).
- **Parameterized ingestion gate** (`ingest/validate.py --dir`, `make validate DIR=`)
  + `_GATE_OK.json` marker w/ content hash; 156/156 checks on the new-column batches.
- **ODCS 1.1.0** canonical + vendored: nullable `engine_node_key`,
  `hand_class_bucket`.
- **Scorer** (`scorer/score_realism.py` + modules): pool tier (§a.3 verbatim) +
  per-persona tier (k_p=7, S_p, avg, non-gating floor), λ-sensitivity (no flip),
  keyed Σ_sim covariance artifacts (per campaign), canonical byte-identity, refusals:
  ungated batch / post-gate mutation / registry-hash mismatch / wrong-campaign
  covariance artifact. 0.71 s per 50k batch.
- **Five §a.5 checkers** (`scorer/constraints.py`): 10-stat identity+separation
  (frozen baseline artifact), legality, directional (roster-pooled), per-persona
  determinism guard (street×node×bucket, posts excluded), runtime+reproducibility
  fail-closed. August batch 5/5 pass; July negative control committed (rule 2 fails
  there — checkers bite).
- **Validation** (`analysis/`): both campaigns, exact 720-perm legs, stratified τ-b,
  LOPO, BCa (pinned, 95% two-sided), F1 fired once, invocation guards, known-answer
  tests. 82/82 suite green; `make validate-s3` byte-identical on rerun.

## What shipped (poker-coach)

- Branch `feat/flywheel-s3-t2-export` @ 05a8857: export tool + vendored ODCS +
  schema tests + canonical patch + t2-export-report. Regenerated sim50k with the
  **pinned** lineup reproduced S1's per-persona decision counts **exactly** — free
  engine-determinism proof.
- July feasibility spike (reports/t6-july-spike.md + .patch): July engine 1f9e799
  exports cleanly, zero adaptations; used by T7 for the campaign-1 reconstruction.
- Docs: roadmap S3 ticked with result; PRD R1 synced two-tier/retrospective; spec +
  tickets carry the owner-ruling banners; this ledger.

## Review economics (what each round caught)

- T3 refuter: stale gate-marker survival on `_SUCCESS` deletion (H, reproduced).
- T1 dual: floor vacuity numbers, source self-contradiction, uncited intervals,
  F1-counterproductive derivation, mixed σ_target semantics, PRD n=13 staleness —
  14 accepted findings; arithmetic 0 mismatches.
- T2 refuter: postflop bucket false premise (`strength_bucket` existed), pre-commit
  manifests, DEFAULT_LINEUP vs ratified lineup (run_id collision) — 3H.
- T4 (scorer's own run) caught what three doc reviews missed: §g.1.8 named the wrong
  duplicated personas (checked against a source constant, not a batch manifest).
- Final dual: cov-artifact acceptance without key check, roster-pooled vs unweighted
  mean, per-persona determinism/ranges, throughput proxy, min-p floor, stale dissent
  text — 16 findings, none changing any verdict; all fixed or explicitly deferred.

## Declared gaps / deferred

- Producer-rerun reproducibility check (rule 5b full form) → S4; T2's exact-count
  reproduction stands as the engine-determinism evidence.
- `run_id` ignores lineup (identity collision wart) — disclosed in code + report.
- `config_hash` in covariance keys = sentinel until S4.
- Campaign-1 measurement is a 50k same-engine reconstruction, not the 250 rated
  hands — disclosed as a validation-input limitation.
- Committed a5-control `offending_contexts` ordering is nondeterministic (cosmetic).

## Process notes

- Sandbox: settings.json edits apply LIVE (no restart); `!`-prefix commands run
  INSIDE the sandbox (owner must use a real terminal for settings edits).
- Director once violated the no-pipe rule (`make | tail` masked a red test before a
  commit); failure was the known transient, but logged as a defect of process.
- Worker died on session restart mid-T2; partial worktree state audited and resumed
  per worker-failure protocol — no loss.
