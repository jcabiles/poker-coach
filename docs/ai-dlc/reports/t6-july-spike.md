# T6 (S3) — Can the July-era ("campaign 1") engine produce a clean seeded export?

**Verdict: A) FEASIBLE.** The July-era engine, with the T2 export tool backported
unmodified, produces byte-for-byte the same table shape as today's export — including
`engine_node_key` and `hand_class_bucket` — with **zero degraded columns** and **zero
adaptations** to the export tool's logic. This was simpler than the ticket anticipated
because the domain functions the export tool depends on (`postflop_node_key`,
`strength_bucket`, `last_aggressor_position`) already existed, with identical
signatures, at the campaign-1 commit.

## 1. Engine commit — how established

Pinned commit: **`1f9e799684dc09faeb3ef4a93b8fb4518ddcf119`**
(`feat(history): on-demand villain reveal in the hand replayer`, 2026-07-26 02:43:04 -0700).

Source of the pin: `docs/ai-dlc/research/persona-realism-artifacts/review-250-hand/250-hand-review.md`
§Provenance (lines 11–21) — the document for the 250-hand review (2026-07-26), which the
ticket names as "campaign 1." It records:

```
Corpus         | sim_session 2323b226d800423c9f90499cd15e207f — 250 hands, 0 skipped, played 2026-07-26
Export tool    | backend/tools/export_session.py, tool SHA 1f9e799684dc (post-WWSF/WTSD fix)
Code reviewed at | HEAD 1f9e799, backend/app/domain/personas_postflop.py @ 938 lines
```

This is an explicit git-SHA pin recorded at the time of the review, not an inference —
no "nearest dated commit" fallback was needed. (A second, earlier artifact —
`hand-analysis-181/data/*.md` — independently pins a *different* commit,
`1652e3df2fde` / 2026-07-26 00:02:55, for the 181-hand review that preceded and fed
into the 250-hand review. Both are same-day, same-author-session commits ~40 minutes
apart; the ticket's own definition of campaign 1 ("the 250-hand persona-realism
review") makes `1f9e799` — the SHA the 250-hand doc cites for itself — the correct
pin. Noted for completeness, not treated as ambiguity requiring disclosure per step 1's
"no artifact pins one" clause, since an artifact *does* pin one.)

## 2. Content-pack state at that commit

`content/personas/*.json` (6 files: calling_station, lag, maniac, nit, passive_fish,
tag) last touched by commit `8bc96e1` (2026-07-25 21:12:34 -0700), i.e. unchanged
between that commit and the pinned engine commit. Combined sha256 of all six pack
files (sorted, concatenated `shasum -a 256` output, then hashed):
`350b2103c32a45a8fa5ceb4c13f58f45787683f217781c5f6cecbe0744d7579e`.

## 3. Backport patch

Copied `backend/tools/export_analytics.py` and `backend/tools/poker_events.odcs.yaml`
verbatim from the current export tool (branch `feat/flywheel-s3-t2-export`, HEAD
`05a8857`) into the July worktree. **No code changes were needed** — every domain
symbol the export tool imports (`postflop_node_key`, `strength_bucket`,
`last_aggressor_position`, `load_persona_packs`, `bot_decision`, `start_hand`,
`apply`, `legal_actions`, `settle`, `deal_hand`, `VillainType`, `ActionType`,
`PlayerStatus`, `Street`) already existed at the July commit with **identical
signatures** to today's. The patch is therefore two new files, not a diff against
existing July code — `backend/app/domain/` was not touched, confirmed by `git status`
showing only the two new files as changes.

- Patch file: `docs/ai-dlc/reports/t6-july-backport.patch` (796 lines, two new files)
- sha256: `0d5f624edddb2df76c1e97f6f4a01daa1212bf45a56822dcb4e30a37f06f366e`

## 4. Exact commands

```sh
# worktree
git -C /Users/johncabiles/Documents/Github/poker-coach worktree add --detach \
  "$TMPDIR/wt-s3-t6-july" 1f9e799684dc09faeb3ef4a93b8fb4518ddcf119

# backport (no source edits — copy only)
cp <T2-worktree>/backend/tools/export_analytics.py \
   "$TMPDIR/wt-s3-t6-july/backend/tools/export_analytics.py"
cp <T2-worktree>/backend/tools/poker_events.odcs.yaml \
   "$TMPDIR/wt-s3-t6-july/backend/tools/poker_events.odcs.yaml"

# run (shared main-repo venv already has pyarrow 25.0.0 from the export extra;
# PYTHONPATH pins imports to the July worktree, not the main checkout)
cd "$TMPDIR/wt-s3-t6-july/backend"
export PYTHONPATH="$TMPDIR/wt-s3-t6-july/backend"
/Users/johncabiles/Documents/Github/poker-coach/backend/.venv/bin/python3 \
  -m tools.export_analytics --hands <N> --seed 20260726 \
  --lineup tag,tag,calling_station,tag,passive_fish,lag,passive_fish,nit,maniac \
  --out <out_dir> --skip-contract-test
```

## 5. Isolation proof (venv-trap check)

```
app.__path__: ['/private/tmp/claude-501/wt-s3-t6-july/backend/app']
export_analytics.__file__: /private/tmp/claude-501/wt-s3-t6-july/backend/tools/export_analytics.py
```
Confirms the July worktree's domain code ran, not the main checkout's (shared venv,
but `PYTHONPATH`-scoped imports).

## 6. Smoke export (1,000 hands, seed 20260726, pinned lineup)

```
tag,tag,calling_station,tag,passive_fish,lag,passive_fish,nit,maniac
```

- Runtime: 2.5s wall (2.43s user)
- Rows: `hands`=1000, `seat_outcomes`=9000, `decisions`=17459
- Manifest `git_sha`: `1f9e799684dc09faeb3ef4a93b8fb4518ddcf119` (correctly captured
  from the July worktree's own git, proving the run recorded its true engine version)
- Schema (pyarrow read-back) — **identical column set to today's export**:
  - `hands`: hand_id, run_id, hand_no, button_seat, hand_seed, board, final_street,
    total_pot_bb, went_to_showdown, n_saw_flop, exported_at
  - `seat_outcomes`: hand_id, seat, persona, position, hole_cards, starting_stack_bb,
    invested_bb, delta_bb, final_status, saw_flop, went_to_showdown, won_pot,
    exported_at
  - `decisions`: hand_id, seq, seat, street, position, action, raise_to_bb,
    chips_committed_bb, pot_before_bb, to_call_bb, engine_node_key,
    hand_class_bucket, exported_at
- `engine_node_key` / `hand_class_bucket`: fully populated on all non-`post` rows (0
  unexpected nulls checked against 17,459 decision rows); sample non-post row:
  `{'action': 'fold', 'engine_node_key': 'vs_raise', 'hand_class_bucket': 'other', ...}`

## 7. Scale check (10,000 hands, same seed/lineup)

- Runtime: 24.0s wall (23.73s user) → **~417 hands/sec**
- Rows: `hands`=10000, `seat_outcomes`=90000, `decisions`=175996
- Extrapolated: a 50,000-hand batch ≈ **2 minutes**; five 50k-hand replicates
  (director's plan, seeds TBD) ≈ **~10 minutes total**, comfortably inside any
  reasonable execution-task budget. No memory/stability issues observed at 10k.

## 8. Degraded columns

**None.** Both `engine_node_key` and `hand_class_bucket` are produced at full
fidelity — the export-side derivations (`_preflop_facing_label`,
`_hand_class_bucket`) are pure export-tool code with no domain dependency, and the
domain reuse points (`postflop_node_key`, `strength_bucket`) both existed, unchanged,
at the July commit.

## 9. Dependency notes

- `pyarrow` is not in the July `pyproject.toml`'s `export` extra set (that extra was
  added later), but the **shared backend venv** (`backend/.venv`, main checkout) already
  has `pyarrow==25.0.0` installed — sufficient for a `PYTHONPATH`-scoped run against the
  July worktree. No separate venv build was required for this spike; a full 50k×5
  execution run should still confirm/pin the pyarrow version it uses (25.0.0 here) for
  reproducibility, since the July `pyproject.toml` doesn't pin it itself.
- `datacontract-cli` advisory check was skipped (`--skip-contract-test`); not required
  for feasibility (the row/schema check via pyarrow read-back is the load-bearing
  evidence here).

## Hand-count / lineup / seed plan (for the follow-up execution task)

- Seed: `20260726` (used above) + ≥4 more replicate seeds, TBD by director.
- Lineup: `tag,tag,calling_station,tag,passive_fish,lag,passive_fish,nit,maniac`
  (as specified in the ticket; matches campaign-1's roster).
- Hands per batch: 50,000 (per director's parquet-batch convention), ≥5 replicates.
- Estimated total runtime at ~417 hands/sec: ~10 minutes for 5×50k, plus manifest/
  contract-check overhead — well within a normal execution-task budget.

## Worktree state

`$TMPDIR/wt-s3-t6-july` left in place (detached HEAD at `1f9e799684d`, two untracked
files `backend/tools/export_analytics.py` + `backend/tools/poker_events.odcs.yaml` —
the backport). Director to remove per ticket boundaries. Smoke/scale outputs remain
under `$TMPDIR/t6-smoke-out` and `$TMPDIR/t6-scale-out` (scratch, not committed).
