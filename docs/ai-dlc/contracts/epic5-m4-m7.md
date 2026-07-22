# Contracts — Epic 5 tail (M4–M7)

Read-only scan of the surface M4–M7 touch, on `main` (643f2d9, post-Epic-4). Spike docs
`RES-G/H/I` are LAW; this maps the *code* those slices land in and the invisible contracts each
must preserve. Persisted per `/ai-dlc` step 2.

## The two hot files + the dispatcher

| File | Role | M4 | M5 | M6 | M7 |
|---|---|---|---|---|---|
| `backend/app/domain/postflop.py` | graders + `_apply_multiway` + `_MW_*` consts | **append** `grade_vs_caller_raise` + `_merits_vs_caller_raise` | **append** limped-flop grader(s) (may reuse `_merits_*`) | **MODIFY** `_apply_multiway` sig + `_MW_*` consts | — (reuses M6 scalars) |
| `backend/app/domain/table/grade_map_postflop.py` | mappers | **append** `map_flop_vs_caller_raise` (+gate helper) | **append** `map_limped_flop_lead` / `map_limped_flop_vs_lead` (+limped-preflop gate) | **MODIFY** `map_mw_*` (thread `opp`, fire 4-way) | **append** opener/caller MW mappers |
| `backend/app/domain/table/grade_map.py` | dispatcher `map_decision_point` (:39, `or`-chain by street) — **hotspot, lead-owned** | +import +chain entry | +import +chain entries | — | +import +chain entries |
| `content/` | strategy data | reuses `VS_RFI` gate (no new content) | **new** limped-flop thresholds | — | reuses existing |
| `NodeContext` / `LeakCategory` enums (domain) | taxonomy | +`VS_CALLER_RAISE` (additive) | +limped-lead ctx (additive) | — | — |

**Collision reading:** M4 ⊥ M5 are both *additive* (new function bodies, disjoint node families) —
safe to build in parallel on one branch under the proven "disjoint-function ownership, lead
serializes the 3 shared files at fan-in" model (W1 R3‖R4‖R5 precedent). M6 *mutates* the shared
`_apply_multiway` body M4 composes with → must land AFTER W1. M7 appends mappers that lean on M6's
opp-aware scalars → after M6. ⇒ waves **[M4‖M5] → M6 → M7**.

## Invisible contracts every slice must preserve (verify, don't assume)

1. **`spot_signature()` / `_postflop_signature()` frozen** — new `NodeContext`/`LeakCategory` enum
   values are additive and only affect NEW spots; existing-node hashes must stay byte-identical
   (`test_signature.py` zero diff). `TAXONOMY_VERSION` bumps ONLY if an existing node's taxonomy
   changes — a new node family alone does not force it (RES-H §5-H1 #6, RES-G §6-C(c)).
2. **`_apply_multiway` is called on the facing side by every facing grader** (`grade_vs_cbet`,
   `grade_vs_check_raise`, and M4's new grader) under `if is_multiway(spot)`. M6 changes its
   signature (adds `opp`) → M6 must thread `opp` through EVERY call site, incl. M4's (that's why
   M6 follows W1). M6's contract: `opp=2` (3-way) ⇒ `base**1` == today's flat constant ⇒ 3-way
   AND HU byte-identical (HU never enters the `is_multiway` gate).
3. **Facing-side α is a CEILING, not applied to raise-response** (RES-H §3.4): M4 must NOT call
   `_calibrate_catcher_fold`. A marginal hand may fold ABOVE the α ceiling vs a value-heavy raise.
4. **`_is_canonical_bet` blast radius** (RES-I §5, HIGH): shared by HU turn/river mappers +
   `map_mw_*` + S10/S11 display==grade. M1 already widened recognition to `RECOGNIZED_BET_FRACS`;
   M4/M5/M7 must reuse it, never fork a private fraction set, and any newly recognized faced size
   must map to a defined RES-E bucket (never collapse into 0.33).
5. **Multiway = DIRECTION only** — no per-opponent MDF / n-th-root constants; geometric
   `base ** max(opp-1,0)` only (F4 shape). M6/M7.
6. **"No baseline yet" (`None`) is first-class** — M5: any 3+ limped flop → explicit
   `len(live)!=2 → None`. M6/M7: 4-way with a live player behind hero → `None`; 5+ stays binary
   bucket. Never silently HU-grade a MW pot or fabricate a 4-way frequency.
7. **Results freq+EV never boolean; `is_mixed` correct; EVs labeled approximate**; domain purity
   (no web/DB imports in `app/domain/`); grading behind the one `StrategyProvider`.
8. **Coverage baseline harness** (`tests/data/coverage_baseline.json`, total **1233 frozen**):
   content/recognition changes move *graded* count UP, total UNCHANGED. Re-record only
   deliberately (M4/M5/M7 raise graded; M6 is behavior-direction, may not move graded count).

## Grading path (how a mapped spot reaches a grader)

`sim_session.py` (orchestration, `check_is_free` fallback lives here) → `map_decision_point`
(`grade_map.py:39`, Simulate-only; Practice uses `scenarios.build_spot` directly) → per-node
`map_*` mapper builds a `Spot` → domain grader (`postflop.py`) returns `EvaluationResult`. New
mappers plug into the `or`-chain; new graders are pure domain functions the mapper's node_context
routes to.
