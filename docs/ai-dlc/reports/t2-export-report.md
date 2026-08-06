# T2 (flywheel S3) — export extension report

Producer: `backend/tools/export_analytics.py`. Extends every `decisions` row with
two new nullable columns (`engine_node_key`, `hand_class_bucket`) for the
determinism guard (a check that groups decisions by street × node × hand-class
and expects near-identical action distributions within each group).

## engine_node_key

- Postflop rows: read-only reuse of the domain's pure `postflop_node_key`
  (`backend/app/domain/table/sizing.py`) — values: `flat`, `raise`,
  `cbet_dry`, `cbet_wet`, `cbet_mono`, `turn_barrel`, `river_value`.
- Preflop rows: an export-side-only facing-state label derived from public
  action history — `unopened`, `vs_limpers`, `vs_raise`, `vs_3bet_plus`.
  Deliberately coarser than the domain's internal facing split (3-bet and
  4-bet+ collapse into one bucket) because this is a grouping key, not a
  policy input.
- `action='post'` rows (forced blinds): NULL — excluded from determinism
  contexts.

## hand_class_bucket

- Preflop rows: export-side-only hole-card bucket — `pair`, `suited-ace`,
  `suited-broadway`, `offsuit-broadway`, `other`.
- Postflop rows: read-only reuse of the domain's pure `strength_bucket`
  (`backend/app/domain/personas_postflop.py`), which returns a
  `(StrengthBucket, DrawCategory)` pair. Encoded as a single string
  `"<strength>|<draw>"` (pipe-joined enum values) so the column stays a
  single VARCHAR per the vendored contract's `logicalType: string`.
  - `StrengthBucket`: `monster`, `two_pair_plus`, `overpair_tptk`,
    `top_pair`, `middle_pair`, `ace_high`, `air`
  - `DrawCategory`: `none`, `weak`, `strong` (always `none` on the river)
  - Examples: `"top_pair|weak"`, `"monster|none"`, `"air|strong"`.
- `action='post'` rows: NULL. Every other row (preflop non-post, all
  postflop) is non-NULL — this replaces the T2-partial-review draft's
  postflop-NULL gap (that draft's "no existing domain hand-class label is
  exposed to the export path" claim was FALSE; corrected per adversarial
  review finding #1).

## Known limitation: run_id/hand_id ignore lineup

`run_id = f"run-s{seed}-n{n_hands}"` does not include the lineup, so two runs
with the same `(seed, n_hands)` but different `--lineup` collide on
`run_id`/`hand_id`. Out of scope for T2 (S1's pinned per-persona counts
reference this exact format) — flagged here and in a code comment near
`run_id`, not fixed.

## CLI

Added `--lineup` (comma-separated persona names for the 9 seats, defaults to
`DEFAULT_LINEUP` — the 6 personas sorted, wrapped). Example:

```
python -m tools.export_analytics --hands 50000 --seed 20260805 \
  --out <dir> --lineup tag,tag,calling_station,tag,passive_fish,lag,passive_fish,nit,maniac
```

## Regenerated batches (pinned lineup, post-commit)

Lineup used for all 6 batches below (matches the S1 reference,
`docs/ai-dlc/research/persona-realism-artifacts/remeasure-2026-08-05/sim50k/_SUCCESS`):
`tag,tag,calling_station,tag,passive_fish,lag,passive_fish,nit,maniac`.

<!-- Filled in after regeneration — see final report update below the table. -->

| seed | hands | decisions rows | wall time (s) | hands/s | manifest git_sha |
|---|---|---|---|---|---|
| 20260805 | 50000 | TBD | TBD | TBD | TBD |
| 101 | 50000 | TBD | TBD | TBD | TBD |
| 102 | 50000 | TBD | TBD | TBD | TBD |
| 103 | 50000 | TBD | TBD | TBD | TBD |
| 104 | 50000 | TBD | TBD | TBD | TBD |
| 105 | 50000 | TBD | TBD | TBD | TBD |

## Per-persona decision-count comparison (seed 20260805, pinned lineup)

S1 pinned reference counts (`flywheel-s1.md`): tag 244555 · calling_station
138263 · passive_fish 230849 · lag 89439 · nit 71878 · maniac 109761.

TBD — filled in after regeneration; exact match expected if determinism holds
(same seed + same lineup + code changes don't touch RNG draw order for
existing columns). Any drift is reported here as a finding, not hidden.
