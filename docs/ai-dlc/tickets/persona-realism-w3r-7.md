# W3R-7 tickets — OVERPAIR_TPTK bucket split (#10), in TWO PHASES

Spec: `docs/ai-dlc/specs/persona-realism-w3r-7.md`. **Scope-check result: TWO phases, one PR each** —
**(a) T1–T3 taxonomy split, byte-identical, ZERO fixture re-record**; **(b) T4–T6 behavior re-fit, ONE fixture
re-record**. Phase (a) must land green before phase (b) starts: its byte-identity is the only proof that rewiring 5
exhaustive merit tables introduced no accidental behavior change.

**Rebases on merged W3R-4b** (same `_made_bucket` hotspot). Single owner/worker throughout. No new lever/mechanic,
no band re-anchor, grader + `spot_signature()` frozen, no `content/` edit.

Owned files: `backend/app/domain/personas_postflop.py`, `backend/tests/test_personas_postflop.py`, and (phase b
only) `tests/data/coverage_baseline.json`, the `_GOLDEN_STATS_N200` pins (:2363), the limper belt.

---

## PHASE (a) — split the taxonomy (near-no-op)

### T1 — Introduce `OVERPAIR` + `TPTK`, rewire every consumer
Replace the `OVERPAIR_TPTK` member (:41) with **`OVERPAIR`** and **`TPTK`**. It is a bot-internal `StrEnum` — not
serialized to the API, FE, or `content/` (verified: zero non-engine hits) — so adding a member is safe. Route the two
existing producers: `_pair_bucket` (:108) → `TPTK`; the `cat == 1` pocket rule (:148, plus the W3R-4b pocket helper)
→ `OVERPAIR`. Rewire, preserving today's behavior exactly:
- `_RUNG` (:81): **both = 4** (documented tie); the commit gate (:812-813) reference becomes `_RUNG[OVERPAIR]`.
- `_AGG_BASE` :218 (0.70) · `_CHECK_BASE` :227 (0.30) · `_FOLD_BASE` :255 (0.05) · `_CALL_BASE` :264 (0.70) ·
  `_RAISE_BASE` :277 (0.25): **both members get today's value**.
- `_RIVER_RAISE_FLOOR` (:294-298): contains **both**. `_RIVER_BET_FLOOR` (:305): **neither** (unchanged).
- `_VULNERABLE_ONE_PAIR` (:342), `_MW_VALUE_BUCKETS` (:486), `_MW_CATCH_BUCKETS` (:471): **unchanged in phase (a)**.
- **Done-condition:** `strength_bucket` → `TPTK` for AK-on-K72 / AK-on-A92, `OVERPAIR` for QQ-on-952; `ruff` clean.
- **Owned:** `personas_postflop.py`.

### T2 — Re-key the tests + exhaustiveness guard
Update the bucket asserts: :92 (QQ on 952) → `OVERPAIR`; :95 (AK on A92) and :132 (AK on K72) → `TPTK`; `_RIVER_HOLES`
(:1361) keys `AA` under `OVERPAIR`; add `TPTK` to `_ONE_PAIR_FLOOR` (:1369) and the river-raise test (:1521);
`_COMMIT_TPTK` (:296) is now `TPTK` at rung 4 so the commit tests must pass **with no behavioral edit**.
Add a NEW **exhaustiveness guard**: every `StrengthBucket` member is a key in each of the 5 `_*_BASE` tables (they are
unguarded dicts — a missing key is a runtime `KeyError`).
- **Done-condition:** the re-keyed tests + the guard pass; no assertion VALUE changed (only bucket names).
- **Owned:** `test_personas_postflop.py`. **Depends-on:** T1.

### T3 — Prove byte-identity (NO re-record)
Run the full suite. `_GOLDEN_STATS_N200` must match at `abs=1e-9`, and `coverage_baseline.json` + the limper belt
must be **unmodified**.
- **Done-condition:** `./scripts/verify.sh` green with **zero fixture diffs**; report "phase (a) byte-identical".
- **HARD-STOP:** any fixture movement means the rewiring is not a no-op — find the mis-copied cell; **do NOT
  re-record to make it pass**. **Depends-on:** T1, T2.

---

## PHASE (b) — brake TPTK only (rebased on merged phase (a))

### T4 — Add `TPTK` to `_VULNERABLE_ONE_PAIR`; H54 + AA tests
Add **`TPTK` only** to `_VULNERABLE_ONE_PAIR` (:342) so the W3-d texture brake (:769-771) applies to it. `OVERPAIR`
stays excluded — §9 #7, never damp real overpairs. New tests:
- **H54:** `_br("tag", ("Ah","Kd"), ["Kc","8c","3c"], street=Street.FLOP) < _br("tag", ("Ah","Kd"), ["Kc","8s","3d"],
  street=Street.FLOP)` — a strict ORDERING (DIRECTIONAL; no target rate asserted). The driver is `_wetness_bet_mult`
  monotone ×0.55 (:371-381); `_overcard_count` is 0 for TPTK by construction, so do not credit the overcard damp.
- **AA untouched:** `_br("tag", ("Ah","Ad"), ["Kc","8c","3c"], street=Street.FLOP)` byte-identical to its pre-slice
  value and > 0.5; `test_overpair_and_set_still_bet_on_wet_boards` (:2871) green.
- **Done-condition:** both tests pass; `_VULNERABLE_ONE_PAIR` gained exactly one member.
- **Owned:** `personas_postflop.py:342`, `test_personas_postflop.py`.

### T5 — Re-measure bands; re-fit `_*_BASE[TPTK]` ONLY if needed
Re-measure every persona's AF / fold-to-c-bet / WTSD (:2429). **Levers-first:** only if a band busts, re-fit
`_AGG_BASE[TPTK]` (and, if it earns it, `_CHECK_BASE[TPTK]`) as a **FIT SEED** — state the target as a measured
stat, report measured before/after, never drop a constant in.
- **Done-condition:** every persona IN its existing frozen band; per-persona numbers reported; any changed
  `_*_BASE[TPTK]` value documented inline with its measurement.
- **HARD-STOP:** if no `_AGG_BASE[TPTK]` value keeps every persona in band, STOP and report — a band re-anchor is an
  owner decision (§7, frozen to W4-b; the W3R-2 fish+station exception is spent). **Depends-on:** T4.

### T6 — Bluff-ordering pin, fixture re-record, verify green
Check `test_bluff_ordering_across_personas_at_fixed_size` (:879). It reads the **AIR** cell, which this slice never
touches, so it is **expected green and unedited**. If it moved, that is evidence phase (b) leaked outside the TPTK
cell — **investigate the leak first**; only then re-anchor, and do it **deliberately (P2a): re-measure at the final
dials and write the old→new numbers + the causal reason inline in the test**. A silent re-pin is a FAIL.
Then re-record the seeded fixtures this authorized change moves (`coverage_baseline.json`, `_GOLDEN_STATS_N200`,
limper belt) with a dated "RE-RECORDED for W3R-7 (phase b)" docstring note.
- **Done-condition:** `./scripts/verify.sh` green; `ruff check .` clean; `content/` validates; report which fixtures
  moved and the **cumulative graded-coverage ratio vs the immutable
  `coverage_baseline.persona-realism-start.json`** (any loss adjudicated — anti-laundering); state explicitly
  whether the bluff-ordering pin held or was deliberately re-anchored. **Depends-on:** T4, T5.

---

## Sequencing
Phase (a) T1 → T2 → T3 (**merge**) → Phase (b) T4 → T5 → T6. One worker, two PRs.

**Cross-slice (shared hotspot):** `_made_bucket` is edited by **W3R-4b FIRST, then W3R-7**, back-to-back.
- They **MUST be built serially — never in parallel**: same function, and W3R-4b reroutes pocket-on-paired-board
  hands into the very pocket rule that W3R-7 turns into the `OVERPAIR` member.
- **W3R-7 branches from / rebases on merged W3R-4b** and re-runs every measurement on that base — never on a pre-4b
  base (its "byte-identical" phase-(a) claim is only meaningful against post-4b goldens).
- **One fixture re-record per behavior-changing slice** (W3R-4b: one; W3R-7 phase (a): none; phase (b): one), each
  reporting the **cumulative** graded-coverage delta vs the immutable start snapshot, so the taxonomy edits cannot
  launder each other's coverage movement.
