# W3R-4b — Shared-board false "two pair" commit-inflation (#14) — TAXONOMY EDGE

**Slice of:** `docs/ai-dlc/roadmap/persona-realism.md` → W3R (bot-review remediation). Fixes **#14**, split out of
W3R-4 by owner decision (2026-07-24) because it edits the `_made_bucket` strength-taxonomy hotspot. Source finding:
nit **H61** — *"99 raises A-high flop then stacks off 'two pair' on paired board — shared-board-pair →
`TWO_PAIR_PLUS` commit inflation"* (`persona-realism-artifacts/bot-review-2026-07-24/persona_findings_digest.md:39`).

> **TAXONOMY ORDERING (owner sequencing note):** W3R-4b and **W3R-7** (OVERPAIR_TPTK split) both edit `_made_bucket`.
> They ship **back-to-back and STRICTLY SERIAL — 4b FIRST**, W3R-7 rebases on it. Never in parallel: same hotspot,
> and 4b's output feeds W3R-7's `OVERPAIR` member (see §Interaction below).

## Goal (one line)
A pocket pair on a paired board must stop classifying as `TWO_PAIR_PLUS` — the second pair is the *board's*, shared by
everyone — so an underpair over a paired board (H61) stops force-committing at low SPR. Genuine two pair untouched.

## Why (the gap / root cause)
`_made_bucket` (`personas_postflop.py:111-155`), `cat == 2` (two pair) POCKET branch at **:124-137**:

```
if pocket:                                   # :125
    if rank[1] == r1:                        # :135  pocket is the TOP pair of the best five
        return StrengthBucket.TWO_PAIR_PLUS  # :136  <-- the bug
    return StrengthBucket.MIDDLE_PAIR        # :137  ("F7 bug 1" — pocket BELOW the board pair)
```

A pocket pair contributes **exactly one** pair to the best five. Whenever `_eval5` reads "two pair" for a pocket hand,
the *second* pair is necessarily a **board** pair — shared with every opponent, so it adds no relative strength. The
existing "F7 bug 1" comment (:126-134) already made exactly this argument, but only for the pocket **below** the board
pair (`22 on 883`); the pocket-**above** case kept the `TWO_PAIR_PLUS` promotion. That promotion is what inflates the
commit: `TWO_PAIR_PLUS` is `_RUNG` 5 (:82), the low-SPR gate is `_RUNG[bucket] >= _RUNG[OVERPAIR_TPTK]` (=4) at
**:812-813**, so the hand takes `_commit_transform` and its fold merit is zeroed. H61's 99 on an A-high paired board
(`rank[1] == 9 == r1` → `TWO_PAIR_PLUS`) is thus force-committed as a monster while it is really a **pocket underpair
to the ace**.

## The taxonomy rule (the one decision this slice makes)
- **False (shared-board) two pair** = the `cat == 2` **pocket** branch. Second pair is board-only ⇒ NEVER
  `TWO_PAIR_PLUS`. Map it to the **same one-pair rule the unpaired-board pocket case already uses** (`cat == 1` pocket,
  **:145-149**): `OVERPAIR_TPTK if pocket_rank > board_top else MIDDLE_PAIR`.
- **Genuine two pair** = **both hole cards play** — `r1 in board_ranks and r2 in board_ranks` (**:138-139**). This line
  is **byte-untouched**; it is the roadmap's own definition of genuine ("unshared, both-hole-cards-play") and the
  central regression guard. Deliberately NOT widened to a "both best-five pair ranks are hole ranks" test: that would
  demote `54 on KK54`, which the roadmap's definition calls genuine (§9-adjacent no-go).
- The `cat == 2` one-hole-card branch (**:140-143**) already routes to `_pair_bucket` — correct today, untouched.

Consequences (the complete behavior delta, all pocket-on-paired-board):

| hand | today | after 4b | why |
|---|---|---|---|
| 99 on A-8-8-x (H61) | TWO_PAIR_PLUS (commits) | **MIDDLE_PAIR** (rung 2 → no auto-commit) | pocket below board top |
| 22 / 55 on 8-8-3 | MIDDLE_PAIR | MIDDLE_PAIR (byte-identical) | F7 bug 1, preserved |
| TT on 8-8-3 | TWO_PAIR_PLUS | **OVERPAIR_TPTK** (rung 4 → still commits) | it is an overpair, not two pair |
| K9 on K-9-2 | TWO_PAIR_PLUS | TWO_PAIR_PLUS (byte-identical) | genuine, :138 untouched |
| A8 on 8-8-3 | MONSTER (trips) | MONSTER | `cat == 3` path, untouched |

The `rank[1] == r1` special case disappears — after the fix the pocket branch is literally the `cat == 1` pocket rule,
so the two should collapse into ONE shared helper (e.g. `_pocket_bucket(pocket_rank, board_top)`) called from both
sites. That is the whole engine diff.

## Scope / files to touch
- `backend/app/domain/personas_postflop.py` — `_made_bucket` **:124-137** only (+ the small shared pocket helper and
  its second call site at :145-149, which must stay behaviorally identical). **No table, no floor, no lever, no new
  bucket** (the new bucket is W3R-7).
- `backend/tests/test_personas_postflop.py` — new H61 repro + commit test + genuine-two-pair guards; **one deliberate
  re-pin**: `test_f7_under_pocket_pair_on_paired_board_is_middle_pair` **:121** currently asserts `TT on 883 ==
  TWO_PAIR_PLUS` ("genuinely strong two pair: kept") — it flips to `OVERPAIR_TPTK` with the rationale inline.
- Re-recorded seeded fixtures: `tests/data/coverage_baseline.json`, the `_GOLDEN_STATS_N200` pins
  (`test_personas_postflop.py:2363`), the limper belt — one re-record for this slice.

## Pass/fail (HARD)
1. **H61 exact path (runnable):** `strength_bucket(("9h","9d"), ["Ac","8s","8d","4c"])[0] is MIDDLE_PAIR` (today:
   `TWO_PAIR_PLUS`). **T0 gate:** first reproduce H61's real board from the hand log and assert it routes through the
   `cat == 2` pocket branch. If the logged board is double-paired/trips such that `_best5` returns `cat >= 4` (a real
   boat → `MONSTER` at :120-121), this fix does NOT touch H61 — **HARD-STOP and report**, the diagnosis is different.
2. **No auto-commit (runnable):** at an SPR below the persona's `spr_commit`, `nit` holding 99 on `A-8-8-x` facing a
   ½-pot bet has **P(fold) > 0** (today exactly `0.0` via `_commit_transform`). Mirror the existing
   `_commit_fold_prob` helper (`test_personas_postflop.py:299`).
3. **Genuine two pair UNTOUCHED (the regression guard):** `strength_bucket(("Kh","9d"), ["Kc","9s","2h"])[0] is
   TWO_PAIR_PLUS` (existing test :83-86 stays green, unedited) **and** the same hand at low SPR still commits
   (P(fold) == 0.0). `test_f7_unpaired_board_sentinels_unchanged` (:127-132) stays green unedited.
4. **F7 bug 1 preserved:** `22 / 55 on 883 → MIDDLE_PAIR` unchanged.
5. **Bands:** every persona's **AF / fold-to-c-bet / WTSD** stays **IN its existing frozen band**
   (`test_persona_postflop_bands`, :2429). **HARD-STOP** if any band busts — §7 freezes every band to W4-b (the only
   authorized exception is the W3R-2 fish+station WTSD re-anchor, already spent). Re-anchoring here is an owner call.
6. **Fixtures:** re-record the seeded fixtures this authorized behavior change moves; report the **cumulative
   graded-coverage delta vs the immutable `coverage_baseline.persona-realism-start.json`** and adjudicate any loss.
7. `./scripts/verify.sh` green; `ruff check .` clean.

## Out of scope
No new `StrengthBucket` member and no `OVERPAIR_TPTK` split (that is W3R-7) · no `_*_BASE` / floor / brake retune ·
no `_RUNG` change · no grader touch (`spot_signature()` frozen) · no band re-anchor · the `cat == 2` both-hole-cards
and one-hole-card branches (:138-143) and the `cat >= 3` paths stay byte-identical.

## Invariants honored
Softmax law — this is a **classification correctness fix**, not a magnitude, so there is no fit seed to tune; its
effect is proven by the exact-path bucket + commit tests plus in-band population stats (§2's "no un-fit constant"
clause is satisfied by there being no new constant) · §9 "don't demote genuine two pair" — :138 untouched · domain
purity (no new import) · grader / `spot_signature()` frozen · results freq+EV · action draw stays the first
`rng.choices` (no new randomness) · **estimator parity is automatic**: `range_estimate.py:350` groups combos through
the SAME `strength_bucket`, so the live bot and the estimator move together — no context threading needed, but a
parity check is part of verify · bands frozen (in-band or STOP) · cumulative coverage delta reported.

## Interaction with W3R-7 (why this order)
After 4b, the pocket-on-paired-board case flows through the same pocket→overpair mapping as an unpaired board. W3R-7
splits that destination into `OVERPAIR` (true pocket overpair) vs `TPTK`, so 4b's rerouted hands land in `OVERPAIR`
for free. Doing W3R-7 first would force the split to be re-reasoned against the `TWO_PAIR_PLUS` promotion still in
place. **4b first, then W3R-7 rebased on it — serial, never parallel.**

## Verify-by
`./scripts/verify.sh` green; the H61 bucket + no-auto-commit tests pass; the genuine-two-pair guard and the F7
sentinels pass unedited; report per-persona re-measured AF/FtC/WTSD (each IN band), which fixtures moved, and the
cumulative graded-coverage ratio vs the immutable snapshot; `ruff check .` clean.
