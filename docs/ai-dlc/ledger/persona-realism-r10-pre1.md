# Finding ledger — R10 preflop lane slice 2 (R10-PRE1)

Slice: maniac premium unopened no-fold (R10-1b). Branch `feat/persona-realism-r10-pre1`
(built in isolated worktree per the concurrent-session git rules), commits `933de26` (build) +
`88c5c82` (review folds). PR #137. Reviewers (git-READ-ONLY): `refuter`,
`persona-realism-theory-reviewer`, Codex `gpt-5.6-sol`.

## Done-condition

Deterministic authored-shape gate: maniac premium (TT+, AK, AQs) unopened fold weight = 0 at every
seat — FAILED pre-fix (72 nonzero-fold entries, refuter-verified), passes post-fix. LAG preservation
pin. Instrument REPORTED: maniac first-in raise EP 0.197→0.209, aggregate 0.236→0.245 (in-band, no
band edits). `BACKEND VERIFY OK` 1131/1, ruff clean.

## Findings

| # | Source | Sev | Finding | Adjudication |
|---|--------|-----|---------|--------------|
| C-1 | Codex | MED | Gate helper iterated authored nodes, not seats — a deleted seat node would vanish from the gate instead of reading fold 1.0 | **ACCEPTED — FIXED** `88c5c82`: helper iterates every `Position`, resolves first matching node exactly like the sampler |
| T-1 | theory | MED | Coverage-baseline re-record skipped the conventional "RE-RECORDED for <slice>" docstring block with the cumulative-vs-immutable ratio (anti-laundering rule) | **ACCEPTED — FIXED**: block appended — 28.0% (329/1176) vs immutable 28.3% (349/1233), pre-existing mapper-track dip, improved slice-over-slice |
| T-2 | theory | LOW | Helper overwrite-on-duplicate could mismatch first-node-wins if unopened nodes ever overlapped | **SUBSUMED by C-1 fix** |

Verdicts: refuter **PASS, zero issues** (independently reproduced both fixture states by swapping only
maniac.json — re-records fully attributable; carve-out parses to exactly the 8 premium classes) ·
theory **PASS/GO** (realism: 100% pure premium raise is right for the caricatured maniac — limp-trap
is the fish tell, F11 deleted maniac open-limps; R10-1a ladder honestly deferred to R10-PRE2) ·
Codex FAIL→resolved.

## Fixture re-records (slice-authorized, stream displacement only)

coverage_baseline 1215/336 → 1176/329 (ratio UP 27.6%→28.0%) · limper-belt `_PRE_M3_FIRES` ·
`_GOLDEN_STATS_N200` (station AF/FtC/WTSD + tag WTSD only; maniac row byte-identical at seed) ·
W3R-1 maniac open-shape pins re-pinned with the carve-out. Population bands frozen to W4-b.
