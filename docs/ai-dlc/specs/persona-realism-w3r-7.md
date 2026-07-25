# W3R-7 — OVERPAIR_TPTK bucket split (#10) — NEW GRANULARITY (heaviest)

**Slice of:** `docs/ai-dlc/roadmap/persona-realism.md` → W3R. Fixes **#10**: *"`_VULNERABLE_ONE_PAIR` EXCLUDES
`OVERPAIR_TPTK`, so ace-kicker top pair barrels monotone boards unbraked (**H54**)"*
(`persona-realism-artifacts/bot-review-2026-07-24/persona_findings_digest.md:28`).

> **SCOPE-CHECK RESULT (the roadmap asked for one): TWO PHASES, ONE PER PR.**
> **(a) taxonomy split — provably byte-identical**, **(b) behavior re-fit**. The reason is evidence, not size: the
> split touches 5 exhaustive merit tables + `_RUNG` + 2 floors + ~8 test call-sites, and the ONLY way to prove that
> mechanical rewiring introduced no accidental behavior change is to ship it with **zero fixture movement** (the
> W3-a walking-skeleton precedent). Bundling (a) and (b) makes every golden diff ambiguous between "the brake" and
> "a mis-copied table cell". Phase (a) needs **no** fixture re-record; phase (b) needs exactly one.

> **TAXONOMY ORDERING:** ships **immediately after W3R-4b**, rebased on it — both edit `_made_bucket`, **strictly
> serial, never parallel** (see §Sequencing in the ticket).

## Goal (one line)
Split `OVERPAIR_TPTK` into **`OVERPAIR`** (pocket pair above the board — AA on K) and **`TPTK`** (a hole card pairs
the board's top card with an ace/king kicker — AK on K) so the W3-d texture brake can slow TPTK down on wet boards
while true overpairs keep betting.

## Why (the gap / root cause)
The W3-d texture brake is gated by `_VULNERABLE_ONE_PAIR = (MIDDLE_PAIR, TOP_PAIR)` (`personas_postflop.py:342`,
applied at :769-771). `OVERPAIR_TPTK` is excluded **for a correct reason** — the contract's §9 #7 forbids damping real
overpairs (AA on K-high must not slow down). But the bucket **bundles two structurally different hands**: an overpair
(the board can't out-flush/out-straight your pair-strength story the same way, and it is rarely dominated) and TPTK
(AK on a monotone K-high flop is a one-pair hand that is genuinely in trouble). Because they share a bucket, the only
two options today are "brake both" (violates §9 #7) or "brake neither" (H54). **The taxonomy is the bug** — hence a
split, NOT a `_VULNERABLE_ONE_PAIR` membership change.

The split is clean because the bucket already has exactly **two disjoint producers** in `_made_bucket`:
- `_pair_bucket` (:103-108) returns it when a **hole card** pairs the board top with kicker ≥ A/K ⇒ **TPTK**.
- the `cat == 1` pocket rule (:145-149) returns it when a **pocket pair** is above the board top ⇒ **OVERPAIR**
  (post-W3R-4b, the pocket-on-paired-board case funnels through this same rule — another reason 4b goes first).

## Consumer blast radius (the complete list — this is the point of the slice)
Every reader of `OVERPAIR_TPTK` today, and what each does with the split:

| Consumer | Line | Phase (a) — no-op split | Phase (b) — behavior |
|---|---|---|---|
| `StrengthBucket` enum | :41 | replace member with `OVERPAIR` + `TPTK` (bot-internal StrEnum; **not** serialized to API/FE/content — greppable-clean) | — |
| `_RUNG` | :81 | **both = 4** (a documented tie) so ordering comparisons are unchanged | unchanged |
| `_pair_bucket` return | :108 | → `TPTK` | — |
| `_made_bucket` pocket rule | :148 (+ the W3R-4b pocket helper) | → `OVERPAIR` | — |
| `_AGG_BASE` | :218 | both = 0.70 | re-fit `TPTK` **only if** a band busts (levers-first) |
| `_CHECK_BASE` | :227 | both = 0.30 | idem |
| `_FOLD_BASE` | :255 | both = 0.05 | idem |
| `_CALL_BASE` | :264 | both = 0.70 | idem |
| `_RAISE_BASE` | :277 | both = 0.25 | idem |
| `_RIVER_RAISE_FLOOR` | :294-298 | contains **both** (today's behavior: the whole one-pair class never value-raises the river) | unchanged |
| `_RIVER_BET_FLOOR` | :305 | contains **neither** (MIDDLE_PAIR only — both keep the thin river value bet) | unchanged |
| `_VULNERABLE_ONE_PAIR` (W3-d brake) | :342, applied :769-771 | unchanged (excludes both) | **+ `TPTK`** — the fix. `OVERPAIR` stays excluded (§9 #7) |
| low-SPR commit gate | :812-813 | reference becomes `_RUNG[StrengthBucket.OVERPAIR]` (== 4) — both still commit | unchanged (out of scope) |
| `_MW_VALUE_BUCKETS` / `_MW_CATCH_BUCKETS` | :486 / :471 | exclude both | unchanged (out of scope) |
| `bluff_cell` | :651 | AIR/ACE_HIGH only — untouched | untouched |
| `postflop_context.busted_draw_kind` | `postflop_context.py:136` | tests `not in (AIR, ACE_HIGH)` — untouched | untouched |
| `range_estimate.py` grouping | :350 | groups via the SAME `strength_bucket`; the new key appears automatically ⇒ **estimator parity is structural**, no threading needed | idem |
| tests: bucket asserts | `test_personas_postflop.py:92` (QQ on 952) | → `OVERPAIR`; `:95` (AK on A92) and `:132` (AK on K72) → `TPTK` | — |
| tests: `_COMMIT_TPTK` | :296 (AK on A93) | now `TPTK`, rung 4 ⇒ commit tests **byte-identical** | unchanged |
| tests: `_RIVER_HOLES` / `_ONE_PAIR_FLOOR` | :1361 / :1369 | `AA` keys `OVERPAIR`; add `TPTK` to `_ONE_PAIR_FLOOR` + the river-raise test (:1521) | unchanged |
| tests: `test_overpair_and_set_still_bet_on_wet_boards` | :2871 | green (AA) | **green — the AA-untouched guard** |
| **bluff-ordering pin** | :879 | AIR cell only ⇒ expected **green, unedited** | see below |

**Bluff-ordering pin (`test_bluff_ordering_across_personas_at_fixed_size`, :879).** It measures the normalized BET
weight of an **AIR** hand, whose merits this slice never touches — so it is **expected to stay green in both phases**.
Treat a move as a **signal, not a chore**: if it moves, phase (b) leaked outside the TPTK cell — investigate first.
Only after that investigation may it be re-anchored, and then **deliberately, P2a-style: re-measure at the final
dials and document the old→new numbers + the causal reason inline in the test**. A silent re-pin is a FAIL.

## Scope / files to touch
- `backend/app/domain/personas_postflop.py` — the rows above. **No new lever, no new mechanic**, no `_made_bucket`
  logic change beyond routing the two existing producers to the two new members.
- `backend/tests/test_personas_postflop.py` — the re-keyed asserts above, an **exhaustiveness guard** (every
  `StrengthBucket` member is a key in each of the 5 `_*_BASE` tables — the tables are unguarded dicts, a missing key
  is a `KeyError` at runtime), the H54 brake test, the AA-untouched test.
- Phase (b) only: `tests/data/coverage_baseline.json`, `_GOLDEN_STATS_N200` (:2363), the limper belt — one re-record.

## Pass/fail (HARD)
**Phase (a) — split, byte-identical**
1. `strength_bucket` returns `TPTK` for `AK on K-7-2` / `AK on A-9-2`, and `OVERPAIR` for `QQ on 9-5-2` (runnable).
2. **Byte-identity:** `_GOLDEN_STATS_N200` (AF/FtC/WTSD) matches to `abs=1e-9` with **no re-record**, and
   `coverage_baseline.json` / the limper belt are **unmodified**. Any fixture movement in phase (a) means the
   rewiring was not a no-op → fix it, do not re-record.
3. Exhaustiveness guard passes; `test_overpair_and_set_still_bet_on_wet_boards` (:2871) and the commit tests
   (`_COMMIT_TPTK`, :296) pass unedited-in-behavior.

**Phase (b) — brake TPTK only**
4. **H54 (runnable):** `AK on a monotone K-high flop` bets **strictly less** than the same hand on a dry rainbow
   K-high flop — e.g. `_br("tag", ("Ah","Kd"), ["Kc","8c","3c"], street=Street.FLOP) < _br("tag", ("Ah","Kd"),
   ["Kc","8s","3d"], street=Street.FLOP)` (today they are equal). The effect comes from `_wetness_bet_mult`
   (monotone ×0.55, :371-381); note `_overcard_count` is 0 for TPTK by construction, so the overcard damp is
   normally the identity here — do not claim it.
5. **AA UNTOUCHED (the §9 #7 guard):** `_br("tag", ("Ah","Ad"), ["Kc","8c","3c"], street=Street.FLOP)` is
   **byte-identical** to its pre-slice value and stays > 0.5 (:2871).
6. **Direction only, softmax-honest:** the H54 assertion is a strict **ordering** (DIRECTIONAL per contract §4 P2 —
   per-texture bet-rate has no live metric). Do NOT assert a target bet-rate number. The combined P2 damp stays
   ≥ 0.25 (§4). Any `_*_BASE[TPTK]` re-fit is a **FIT SEED**: state the target as a measured stat, report the
   measured before/after — no dropped-in constant closes this slice.
7. **Bands:** every persona's **AF / fold-to-c-bet / WTSD** stays **IN its existing frozen band** (:2429).
   **HARD-STOP** if any busts — bands are frozen to W4-b (§7); the W3R-2 fish+station WTSD exception is spent.
   Levers-first: re-fit `_AGG_BASE[TPTK]` before ever contemplating a band move (which is an owner decision).
8. **Bluff-ordering pin:** green unedited, or — if it genuinely moved — investigated, re-anchored deliberately, and
   documented inline with old→new numbers and cause (P2a). Never silent.
9. **Frozen:** grader / `spot_signature()` untouched; domain purity holds; `content/` unchanged (no persona JSON
   touches this — it is a shared mechanic).
10. **Fixtures (phase b only):** one re-record; report the **cumulative graded-coverage delta vs the immutable
    `coverage_baseline.persona-realism-start.json`**, any loss adjudicated.
11. `./scripts/verify.sh` green; `ruff check .` clean.

## Out of scope
Do **not** add `OVERPAIR_TPTK`/`OVERPAIR` to `_VULNERABLE_ONE_PAIR` (§9 #7 — the whole point of splitting) · no
`_RUNG` demotion for TPTK (the low-SPR commit gate is untouched; a TPTK commit brake would be a separate slice) · no
`_MW_VALUE_BUCKETS` / `_MW_CATCH_BUCKETS` membership change · no `_RIVER_BET_FLOOR` change · no fold-side texture
brake (that is W3R-5) · no one-pair raise damp (W3R-6) · no band re-anchor · no grader touch · no content/JSON edit.

## Invariants honored
Softmax law (any re-fit magnitude is a measured fit seed; the H54 gate is an ordering, self-labeled DIRECTIONAL) ·
§9 #7 "never damp real overpairs" — enforced structurally by the split, and guarded by the AA byte-identity test ·
metric-DoD (no new metric is claimed; the HARD gates remain AF/FtC/WTSD) · frozen bands (in-band or STOP) ·
stacked-multiplier order unchanged — TPTK simply enters the existing W3-d step (made-value damps on `_AGG_BASE`,
before street/position/multiway) · domain purity · grader + `spot_signature()` frozen · action draw stays the first
`rng.choices` · estimator parity structural (shared `strength_bucket`; verified by a phase-(a) parity/byte-identity
run) · anti-sizing-tell untouched · cumulative coverage delta reported.

## Verify-by
Phase (a): `./scripts/verify.sh` green with **zero fixture diffs** and the goldens matching at `abs=1e-9`; the new
bucket asserts + exhaustiveness guard pass. Phase (b): H54 ordering test passes, AA bet weight byte-identical,
per-persona AF/FtC/WTSD reported and IN band, bluff-ordering pin green (or deliberately re-anchored with inline
numbers), one fixture re-record with the cumulative coverage ratio vs the immutable snapshot; `ruff check .` clean.
