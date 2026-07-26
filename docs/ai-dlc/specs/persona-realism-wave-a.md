# Delta spec — persona-realism Wave A (measure-first + verified cheap fixes)

**Roadmap slice of:** `docs/ai-dlc/roadmap/persona-realism.md` → **R8** (`W-ARR` + the `N-*` NEXT items).
**Contract map:** `docs/ai-dlc/contracts/persona-realism-wave-a.md`.
**Evidence:** `docs/ai-dlc/research/persona-realism-artifacts/hand-analysis-181/SYNTHESIS.md` (+ `findings/`).

---

## Goal (one line)

Make bot-realism work **measurable before it is tuned** — add arrival instrumentation, correct the
stack distribution everything else is fitted against, and take the three verified cheap correctness
fixes — without changing any persona's authored strategy.

## Why this wave, in this order

The 181-hand review's central finding: the dominant defect class is **arrival** (which nodes get
visited), not **policy** (what the bot does once there). Nothing in the repo measures arrival. That is
why W5-b1 (#119) widened the nit/tag/lag opening ladders, moved the aggregate marginals, closed green,
and changed almost nothing in late position — the button reaches the `unopened` node **8%** of the time.
That work is correct and **stranded**, and today the project cannot tell *stranded* from *broken*.

Wave A builds the instrument first. Wave B then tunes behaviour against it.

## Outcome-link

Persona-realism north star — bots a poker-literate reviewer would seat at 9-max full ring. Wave A moves
no realism metric by itself; it makes the Wave B metrics **attributable**. Its own success measure is
that the review's headline arrival numbers become reproducible from the harness.

## Appetite

~1 epic, 8 tickets. Two touch the `personas_postflop.py` serial spine.

---

## Files / interfaces to touch

| Ticket | Owned files |
|---|---|
| **T-EXPORT** | `backend/tools/export_session.py` (NEW) · `backend/tools/__init__.py` (NEW — sole owner) |
| **T-STACK** | `backend/app/services/sim_session.py` · `backend/tests/test_sim_session_buyin_cap.py` (**rewrite**) |
| **T-ARR** | `backend/tests/test_personas_postflop.py` (`_persona_stats_ext`, `HandResult`, `_play_hand` capture site) |
| **T-REJECT** | `grade_map_reject.py` (NEW) · `tools/reject_counts.py` (NEW) · `tests/test_grade_map_reject.py` (NEW) · **`grade_map_postflop.py`** (owner decision B1) · `tests/test_domain_purity.py` |
| **T-TRACE** | `backend/tests/node_trace.py` · `backend/tests/test_node_trace.py` |
| **T-ANCHOR** | `backend/app/domain/personas_postflop.py` (lines 825–871 only) · `backend/tests/test_personas_postflop.py` (new test only) |
| **T-STICKY** | `backend/app/domain/content/models.py` · `content/personas/{passive_fish,calling_station}.json` · `backend/tests/test_personas_postflop.py` (mechanical fixes only) |
| **T-REVIEWER** | `.claude/agents/persona-realism-theory-reviewer.md` |

**Single-owner contention:** `backend/tests/test_personas_postflop.py` is touched by T-ARR (additive),
T-ANCHOR (new test) and T-STICKY (mechanical). Disjoint line regions, but **sequence T-ANCHOR before
T-STICKY** — T-ANCHOR is the only behaviour-changing one and must own any fixture re-record.
`backend/tools/__init__.py` is owned by **T-EXPORT only**.

**⚠️ SHARED-FIXTURE ORDERING — T-STACK must land before T-ANCHOR (added post-review, `refuter`).**
Both tickets move the **same** seeded fixture set — `_GOLDEN_STATS_N200`, `coverage_baseline.json`, the
limper belt — by different routes: T-STACK via the SPR-distribution shift (`spr_commit` is a step
function), T-ANCHOR via live-bot-path context threading. Built in parallel, whichever lands second
re-records fixtures the first already moved, and the anti-laundering "cumulative delta vs
`coverage_baseline.persona-realism-start.json`" report becomes **unattributable**. That is precisely
the failure that produced the current red `main` (#118 and #119 built concurrently, neither seeing the
other). **Rule: T-STACK lands and re-records first; T-ANCHOR then re-records on top of it, and each
reports its own delta separately.** This supersedes the "parallel-safe" grouping for these two tickets.

---

## Out of scope

**Explicitly not in this wave**, and a worker must not pull any of it in:

- Every Wave B realism defect: `vs_limpers` positional scoping (`N-limp`), maniac range width
  (`N-maniac`), the D8 assertion surface (`N-d8gate`), the `cbet_flop` band (`N-cbet`).
- Every W4-cluster item: river-air calling (`N-riverair`), nested logit (`N-logit`), vector-valued fit
  loop (`N-vecfit`). All are band-movers gated on the single re-anchor.
- **Widening any mapper.** T-REJECT ships counters only; widening is `T-cover` in
  `professional-teacher-rework.md`, blocked behind this work.
- **Converting `stickiness` → `size_elasticity` for nit/tag/lag/maniac.** Band-moving; deferred.
- All teacher-initiative items (`T-cover`, `T-agentcoach`, `T-oppo`, `T-blinddef`).
- Any change to authored persona strategy — no range edits, no lever-value edits.

---

## Constraints

**Invariants (from `docs/ai-dlc/profile.md`):** domain core `backend/app/domain/` has no web/DB imports
(test-enforced — `grade_map_reject.py` lands *inside* the purity boundary and must stay clean) ·
results are frequency + EV, never boolean · grading stays behind the one async `StrategyProvider` ·
strategy lives in versioned `content/` data · every schema change ships an Alembic migration —
**this wave ships none and needs none** · `spot_signature()` is frozen · FE types hand-maintained.

**Wave-specific constraints:**

1. **Softmax law.** No ticket may close on "the constant is in the code." Every done-condition is an
   **observed number plus a runnable command**. This is the rule #119 satisfied only in form.
2. **CI budget frozen at ≤12s** for `test_personas_postflop.py`. T-ARR's counters must ride the existing
   `_play_hand` loop; a second simulation loop is a no-go.
3. **`net_bb` invariant.** `net_bb = stack_bb - buyins_bb` is rendered live in `SimLedger.tsx`. T-STACK's
   reset must absorb its delta into `buyins_bb` every hand or the user-facing P&L breaks.
4. **Anti-laundering.** Any fixture re-record reports the cumulative graded-coverage delta vs the
   immutable `coverage_baseline.persona-realism-start.json`.
5. **No band edits.** No `BANDS` entry moves in this wave. A band edit is a red flag, not a fix.

**Auth:** none — local single-user app.

---

## ✅ BLOCKER RESOLVED 2026-07-26 — PRs #121–#124 merged, constants re-verified

`#121` → `#124` merged (main now at `8bc96e1`). The three previously-failing tests pass:

```
pytest tests/test_coverage_baseline.py::test_coverage_never_regresses \
       tests/test_personas_postflop.py::test_persona_stats_byte_identical_after_log_refactor \
       tests/test_personas_postflop.py::test_street_aggressions_effect_visible_to_af_gate
  → 3 passed in 8.13s
```

**Every pinned constant was re-measured against the merged baseline and HELD.** The caution below was
warranted but the numbers survived:

| Ticket | Constant | Pre-merge | Post-merge | Verdict |
|---|---|---|---|---|
| T-ANCHOR | IP:OOP ratio — nit / tag / lag | 1.6394 / 1.5157 / 1.2260 | **1.6373 / 1.5156 / 1.2258** | holds (drift < 0.003) |
| T-ANCHOR | station / fish / maniac ratio | 1.0 exactly | **1.0 exactly** | holds |
| T-ANCHOR | post-fix absolutes tag / lag | 0.2373→0.1424 / 0.3779→0.2793 | **derive to 0.2374→0.1424 / 0.3780→0.2794** | holds |
| T-TRACE | nit dry-board bet, ctx None / IP / OOP | 0.4230769 / 0.4782609 / 0.3548387 | **bit-identical** | holds |
| T-TRACE | river busted draw, None → ctx | 0.0156444 → 0.3656979 | **bit-identical** | holds |
| T-ARR | BTN `unopened` / roster-wide | 8% / 38% | **8% / 36%** (n=600 fresh sim) | holds; both bands still contain it |

Two notes. #122's texture change did **not** reach T-TRACE's spot. And T-ANCHOR's post-fix absolutes are
*predictions*, not current readings — inverting the broken normalization from the measured IP values
recovers the drafted figures exactly (tag `bluff_mass` ≈ 0.18989 → 0.2374/0.1424; lag ≈ 0.32866 →
0.3780/0.2794), which independently confirms both the drafted numbers and the fix's arithmetic.

**T-STICKY's baseline digest must still be captured on the merged `main` before editing** — it was never
measured pre-merge, by design.

<details><summary>Original blocker text (kept for the record)</summary>

### ⛔ Wave A cannot start until `main` is green

Both reviewers independently measured the baseline. `refuter` ran it twice:

```
./scripts/verify.sh                    → FAILS at the pytest step
cd backend && python -m pytest -q      → 11 failed, 1054 passed, 1 skipped  (~130s)
cd backend && ruff check .             → clean
cd frontend && npm run typecheck && build → clean
```

Failures include `test_persona_stats_byte_identical_after_log_refactor`
(calling_station AF `0.3973509933774834` vs golden `0.3788300835654596`),
`test_coverage_never_regresses` (hand stream drifted `1290 → 1218`), and
`test_street_aggressions_effect_visible_to_af_gate` — the very test the contract map flags for
T-ANCHOR re-verification. Root cause is PR #119 (W5-b1) cascading through the shared-rng sim into
postflop goldens that were never re-recorded. **This contradicts #119's own "closed green" claim and
the note in MEMORY.md.**

**Verify-by condition #1 is unattainable today and no Wave A ticket scopes fixing it.** Wave A is
blocked behind open PRs **#121–#124** (#124 is the green-up; it edits `test_personas.py`, where #121
names the one non-mechanical failure).

**Consequence for the numbers in the tickets:** every constant in T-ANCHOR, T-TRACE, T-ARR and
T-STICKY was measured against this red `main`. #122 changes `texture.py` (feeds the spine, the grader
and frozen `spot_signature()`); #124 changes `content/personas/lag.json` (moves lag's readings *and*
the arrival distribution T-ARR measures). **Re-measure every pinned constant after those merges, before
starting the build.** The commands are pinned in the tickets, so this is a re-run, not a re-derivation.

**Consequence for the T-ANCHOR tripwire:** the golden is *already red*, so a worker cannot use its
red/green state to tell "my change broke it" from "it was broken when I started." Until #124 lands,
the golden is not a usable discriminator and the worker must diff numeric deltas by hand. The two
bluff-ordering tests are unaffected — both reviewers confirmed they currently **pass** and are
mechanically immune.

## Known consequences to expect (not bugs)

- **T-STACK reverses part of W5-c3 (PR #117).** `test_sim_session_buyin_cap.py` exists to pin carry-over;
  `test_cap_leaves_stacks_inside_band_untouched` asserts the literal opposite of this change. The file is
  rewritten, not re-run. Owner adjudicated the deep-stack table a bug on 2026-07-25.
- **T-STACK will move persona AF/WTSD without touching a persona file.** `spr_commit` is a step function
  with zero gradient; resetting stacks changes every hand's SPR distribution. Do not "fix" this by
  re-tuning a lever.
- **T-ANCHOR moves live bot frequencies for nit/tag/lag** (OOP c-bet/barrel bluffs). The frozen golden and
  both bluff-ordering tests are provably unaffected — see the tripwire below.

## Tripwires (inverted assertions — movement proves a specific bug)

- **T-ANCHOR:** `test_bluff_ordering_across_personas_at_fixed_size` routes through `_air_bet_weight`, which
  passes no `context`, so the multiplier is identity and the test **cannot** move. **Any movement proves
  double-application** (the worker added the pre-complement multiply and left the post-hoc one live).
  Never re-anchor it.
- **T-ARR:** `occupancy["UTG"]["unopened"] == 1.000` exactly. UTG always acts first post-blinds. A reading
  below 1.0 proves the worker counted every preflop decision instead of the seat's first, and every other
  cell is contaminated.
- **T-REJECT:** `UNCLASSIFIED == 0`. Any non-zero value is taxonomy drift from the live mappers, not a
  valid bucket.
- **T-STICKY:** byte-identical by construction. Any fixture, band, or golden movement proves the worker
  extended the deletion into a pack where `stickiness` is still read (maniac reads it in **both** branches).

---

## Verify-by (end-to-end)

Wave A is done when all of the following hold on one branch:

1. `./scripts/verify.sh` → `BACKEND VERIFY OK`.
2. `cd backend && ruff check .` → clean.
3. `cd frontend && npm run typecheck && npm run build` → clean (T-STACK touches `net_bb` semantics that
   `SimLedger.tsx` renders; nothing else is FE-visible).
4. `cd backend && python -m tools.export_session --session <id>` writes per-persona packets that reproduce
   the review's per-persona VPIP/PFR/AF table for session `adaadc548`.
5. `cd backend && python -m pytest tests/test_personas_postflop.py -k "occupancy" -q` → green, with
   `occupancy["UTG"]["unopened"] == 1.000` and BTN `unopened` in `[0.05, 0.12]`.
6. `cd backend && python -m tools.reject_counts --session adaadc548d6f499c965821a617c900df` → reasons sum to **62**,
   `UNCLASSIFIED == 0`.
7. `cd backend && python -m pytest tests/test_node_trace.py -q` → green, with `flop_ip_toppair_dry` and
   `flop_oop_toppair_dry` reading **different** bet probabilities (proving context is threaded).
8. The T-ANCHOR identity holds: IP:OOP bet-rate ratio equals the authored position-multiplier ratio to
   1e-9 for all six personas.
9. A fresh sim session's per-hand starting stacks are ~100bb (median ≈ 100, none > ~100 at hand start), and
   `SimLedger` still shows a cumulative non-zero `net_bb` per seat after several hands.
10. Zero `BANDS` edits in the diff.

---

## Owner decisions — 2026-07-26 (post-review, binding)

- **B1 — T-REJECT: refactor the gates to report a reason.** The shared gate predicates in
  `grade_map_postflop.py` gain a **typed internal diagnostic** read by both the live mappers and the new
  classifier; **public mapper signatures stay `Spot | None`**. Rejected alternatives: coarse reasons with a
  large unclassified bucket (would swallow most of the 62 and defeat the purpose), and dropping T-REJECT
  from the wave (loses the before/after window while the bots are still changing). Consequence: T-REJECT
  now owns a shared file, byte-identity becomes test-enforced rather than structural, and its primary
  tripwire is that **none of the six mapper test files should need an edit**.
- **Build mode — parallel where the DAG allows.** Run the genuinely independent tickets concurrently
  (`T-EXPORT`, `T-TRACE`, `T-REVIEWER`, and `T-REJECT` — which touches nothing else in the wave), then
  **serialise the fixture-touching chain T-STACK → T-ANCHOR → T-STICKY**, with `T-ARR` merging after
  T-ANCHOR. ⚠️ The forced serialisation is not optional: parallel agents re-recording the same seeded
  fixtures is exactly what produced the broken `main` this wave had to wait on (#118/#119).

## Open questions carried into tickets

- **O1 — T-TRACE scope.** Contract-mapper wants a "facing a raise" spot added so the facing-raise damps
  become visible; the specialist draft scopes it out, arguing facing-node position-inertness is *correct*
  today (the OOP defence damp is an unbuilt later slice). **Spec resolves in favour of the draft** — add
  the OOP twin only, and file the facing-raise spot as Wave B. Rationale: adding it invites a worker to
  "fix" the inertness by editing `_position_agg_mult`, colliding with T-ANCHOR on the serial spine.
- **O2 — `sim_session.py:119-127`** carries the W5-c3 rationale comment tying the 200bb cap to a ~100bb
  reference pool. T-STACK must update it rather than leave code and comment contradicting.
