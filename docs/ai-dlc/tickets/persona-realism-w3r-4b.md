# W3R-4b tickets — shared-board false "two pair" commit-inflation (#14)

Spec: `docs/ai-dlc/specs/persona-realism-w3r-4b.md`. Single owner/worker — one `_made_bucket` edit plus its test +
fixture re-record. **Taxonomy hotspot:** this and **W3R-7** both edit `_made_bucket`; they are **strictly serial,
4b FIRST** (W3R-7 branches/rebases on merged 4b). Never build them in parallel. No new bucket, no table/floor/lever
change, no band re-anchor, grader frozen.

Owned files: `backend/app/domain/personas_postflop.py` (`_made_bucket` :124-137 + the shared pocket helper and its
:145-149 call site ONLY), `backend/tests/test_personas_postflop.py`, the re-recorded fixture data files
(`tests/data/coverage_baseline.json`, `_GOLDEN_STATS_N200` at :2363, the limper belt).

## T0 — Reproduce H61 on the real board (GATE, do this first)
Pull nit **H61** from the 2026-07-24 bot-review hand log and assert, in a test, which `_made_bucket` branch it takes.
The expected path is `cat == 2` → pocket branch (:125) → `rank[1] == r1` (:135) → `TWO_PAIR_PLUS` → commit at
:812-813.
- **Done-condition:** a runnable test pins the H61 hand's current bucket as `TWO_PAIR_PLUS`.
- **HARD-STOP:** if the logged board makes `_best5` return `cat >= 4` (a genuine boat → `MONSTER`, :120-121), this
  slice does NOT fix H61 — stop and report; the diagnosis is different and the owner re-scopes.
- **Owned:** the new test.

## T1 — Pocket-on-paired-board never classes as two pair
In `_made_bucket`'s `cat == 2` pocket branch (:124-137), delete the `rank[1] == r1 → TWO_PAIR_PLUS` promotion. A
pocket pair contributes exactly ONE pair; the second pair is the board's, shared by everyone. Map the branch to the
same rule the `cat == 1` pocket case already uses (:145-149): `OVERPAIR_TPTK if pocket_rank > board_top else
MIDDLE_PAIR`. The two branches become identical — factor them into ONE small helper (e.g.
`_pocket_bucket(pocket_rank, board_top)`) called from both sites; the :145-149 call site must stay behaviorally
byte-identical. Keep/extend the "F7 bug 1" comment to record the widened argument.
**Do NOT touch :138-139** (`r1 in board_ranks and r2 in board_ranks` — genuine, both-hole-cards-play two pair) or
:140-143 (one hole card + board pair → `_pair_bucket`, already correct).
- **Done-condition:** `strength_bucket(("9h","9d"), ["Ac","8s","8d","4c"])[0] is MIDDLE_PAIR`; `22`/`55 on 883` still
  `MIDDLE_PAIR`; `A8 on 883` still `MONSTER`; `K9 on K92` still `TWO_PAIR_PLUS`.
- **Owned:** `personas_postflop.py:124-137` + the shared helper.

## T2 — Commit + genuine-two-pair tests
Add (a) the **no-auto-commit** test: at an SPR below `spr_commit`, `nit` with 99 on `A-8-8-x` facing a ½-pot bet has
**P(fold) > 0** (today `0.0`) — mirror `_commit_fold_prob` (`test_personas_postflop.py:299`); (b) the **genuine two
pair guard**: `K9 on K92` is still `TWO_PAIR_PLUS` **and** still commits (P(fold) == 0.0) at the same SPR.
Re-pin exactly ONE existing assertion: `test_f7_under_pocket_pair_on_paired_board_is_middle_pair` **:121**
(`TT on 883 == TWO_PAIR_PLUS`) flips to `OVERPAIR_TPTK` — an overpair on a paired board is an overpair, not two pair
— with that rationale written inline. `test_strength_bucket_two_pair_plus` (:83) and
`test_f7_unpaired_board_sentinels_unchanged` (:127) stay green **unedited**.
- **Done-condition:** both new tests pass; the :121 re-pin is the ONLY edited existing taxonomy assertion.
- **Owned:** `test_personas_postflop.py`.
- **Depends-on:** T1.

## T3 — Fixture re-record + band re-measure + verify green
Re-record the seeded fixtures this authorized bot-behavior change moves (`coverage_baseline.json`,
`_GOLDEN_STATS_N200`, limper belt) with a dated "RE-RECORDED for W3R-4b" note in the module docstring, per the
P1/P2a precedent. Re-measure every persona's AF / fold-to-c-bet / WTSD.
- **Done-condition:** `./scripts/verify.sh` green; `ruff check .` clean; `content/` JSON validates; every persona's
  AF/FtC/WTSD **IN its existing frozen band** (NO re-anchor); report per-persona numbers, which fixtures moved, and
  the **cumulative graded-coverage ratio vs the immutable `coverage_baseline.persona-realism-start.json`** (any
  cumulative loss adjudicated explicitly, anti-laundering).
- **HARD-STOP:** if any band busts, STOP and report — bands are frozen to W4-b (§7); the W3R-2 fish+station WTSD
  exception is spent and does not extend here.
- **Depends-on:** T1, T2.

## Sequencing
T0 (gate) → T1 → T2 → T3. Single owner/worker, one PR.

**Cross-slice (shared hotspot):** `_made_bucket` is edited by **W3R-4b then W3R-7**, in that order, back-to-back.
- These two **MUST be built serially — never in parallel**: same function, and W3R-7's new `OVERPAIR` member is the
  destination 4b reroutes pocket-on-paired-board hands into.
- **W3R-7 rebases on merged W3R-4b** and re-runs its own measurements on top (never on a pre-4b base).
- **Each slice does its OWN single fixture re-record** (golden / `coverage_baseline` / limper belt) and reports the
  **cumulative** graded-coverage delta vs the immutable start snapshot — one re-record per slice, cumulative delta,
  so the two taxonomy edits cannot launder each other's coverage movement.
