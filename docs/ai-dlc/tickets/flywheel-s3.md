# Tickets — flywheel-s3 (spec: ../specs/flywheel-s3.md rev 2)

status: approved  # Gate 2 cleared 2026-08-06 — owner: go @ 5–7d appetite; floor = hard
                  # executable constraint confirmed; no Fable; owner to widen sandbox
                  # write allowlist to poker-analytics + add bluffaces.com to network.

DAG: T1 ∥ T2 ∥ T3 (independent starts) → T4 → T5 · T6 after T2 · T7 after T1+T4+T5+T6 ·
T8 fan-in. Parallelizable: T1/T2/T3 (disjoint repos/files). Owner pushes all
poker-analytics landings and the T2 poker-coach PR.

## T1 — Contract amendment + registry v2 (poker-analytics + poker-coach docs)
One §g amendment implementing spec A1 items 1–11 + `data/targets/registry-v2.json`
(frozen + content-hashed before any scoring). Companion poker-coach commit: roadmap S3
pass/fail + PRD R1 wording synced to the two-tier shape; this ledger set committed.
**Owned files:** `poker-analytics:docs/methods/estimand-contract.md`,
`poker-analytics:data/targets/registry-v2.json`, poker-coach roadmap/PRD (wording only).
**Blocked by:** owner adds `bluffaces.com` to the sandbox allowlist + restart.
**Done when:** amendment PR open with degeneracy report + σ recipes + mapping
justification inside; registry hash recorded; dual-reviewed before the PR goes to owner.

## T2 — Export extension + ODCS bump + regeneration (poker-coach)
`backend/tools/export_analytics.py`: nullable `engine_node_key` (preflop = export-side
facing-state label; posts NULL) + `hand_class_bucket`; ODCS bump canonical + vendored per
compatibility policy; landing order per spec A2; regenerate sim50k + ≥5 seed replicates.
**Owned files:** `backend/tools/export_analytics.py`, both `poker_events.odcs.yaml`
copies, regenerated local batches (gitignored).
**Done when:** contract checks cover the new columns and all pass; corrupted-batch
negative test fails; `git diff backend/app/domain/ content/` empty; export ≥350 hands/s
recorded.

## T3 — Parameterized ingestion gate (poker-analytics)
`ingest/validate.py` + Makefile: `make validate DIR=...` binds the ODCS model paths to
the given batch; scorer-facing entry refuses ungated batches.
**Owned files:** `poker-analytics:ingest/validate.py`, `poker-analytics:Makefile`.
**Done when:** gate passes on the regenerated sim50k by path; corrupting one parquet in a
copy makes it fail; hardcoded-dir behavior preserved for existing targets.

## T4 — Scorer core (poker-analytics) — after T1+T2+T3
`scorer/score_realism.py`: pool tier (§a.3 verbatim) + per-persona tier (A1: k_p subsets,
S_p, avg, floor) + λ-sensitivity over both tiers + covariance-artifact interface + output
identity (verbatim producer_manifest, registry hash, formula ID F0, canonical
byte-identity excluding volatile fields). Update Makefile `score`, poker-coach bridge
script, WORKING-AGREEMENT §2 note.
**Owned files:** `poker-analytics:scorer/*`, `poker-analytics:Makefile` (score target),
bridge script, `poker-analytics:docs/WORKING-AGREEMENT.md` (§2 note only).
**Done when:** two same-seed runs → identical canonical payloads; <5 min; refuses ungated
or registry-hash-mismatched input.

## T5 — §a.5 constraint checkers — after T2+T4
~~All six rules (incl. the new persona floor)~~ **FIVE rules (persona-floor gate
DELETED by owner ruling 2026-08-06; floor stays a non-gating diagnostic in scorer
output)** emitting `a5_pass` + per-rule evidence; pinned baseline z-scales;
determinism contexts exclude posts.
**Owned files:** `poker-analytics:scorer/constraints.py` (or module per repo style) +
its tests.
**Done when:** baseline run produces all six verdicts with evidence; runtime +
reproducibility evaluated as constraints, not prose.

## T6 — July-campaign feasibility spike (poker-coach) — after T2, timebox 0.5 day
Worktree at the campaign-1-era engine commit; attempt seeded export (backport patch if
needed, hash it); print `__file__`. Deliverable: fully pinned snapshot recipe + ≥5
replicates plan, OR an infeasibility STOP note for the owner (fallback = one-campaign
amendment decision).
**Owned files:** none in-repo (worktree + spike note in `../reports/`).
**Done when:** recipe-or-STOP written; timebox respected.

## T7 — Validation run + report — after T1, T4, T5, T6-resolution
Execute §e as amended on both campaign snapshots: leg 1 (exact 720-perm ρ, sign + p),
leg 2 (stratified τ-b per amendment), leg 3 (LOPO vs 0.60), BCa CI (pinned), §e.3/F1 at
most once, stop-gate honored. Status written into scorer output + a validation report in
poker-analytics.
**Owned files:** `poker-analytics:analysis/validation-s3*` + report doc.
**Done when:** report carries realized criticals, exact p's, signs, LOPO range, labeled
CI, formula ID, registry hash, and the resulting score status — or the recorded
one-campaign STOP.

## T8 — Fan-in (director)
Verify-by 1–5 from the spec run end-to-end; dual review of the built slice; ledger
updated; roadmap S3 `[x]` ONLY if its (synced) pass/fail actually passes; memory updated.
**Done when:** all verify-by steps green + review verdicts recorded.
