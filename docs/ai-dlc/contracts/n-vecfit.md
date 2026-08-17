# Contracts — N-vecfit (vector-valued fit loop for the two identity levers)

> **Status note (2026-08-03, post-measurement):** this scan mapped the ORIGINAL (tool) shape of the
> slice. §7's "needs a working joint-fit tool" is **superseded by `specs/n-vecfit.md` (rev 2)** —
> the vector-tool premise was measured unsupported where tested and the slice reshaped to a doc
> amendment; see `reports/n-vecfit-premise.md`. The scan's facts below (harness, lever mechanics,
> pack layer, downstream consumers) remain valid.

> Contract scan at pinned `origin/main` = `b63dfaa` (2026-08-03, contract-mapper).
> Scope of the slice: amend `persona-realism-fit-loop.md` to a vector-valued loop,
> add a runnable fitting tool, run a measured scalar-vs-vector comparison.
> **NO pack values change in this slice.**

## 1. The methodology doc + its referrers

- `docs/ai-dlc/contracts/persona-realism-fit-loop.md:16-31` — the loop is currently **scalar**:
  step 2 "seed the multiplier" (singular), step 4 "adjust the seed" — one lever, one target.
- `:33-40` — precedent pointer cites `test_personas_postflop.py:1337-1480` — **STALE at b63dfaa**:
  the `BANDS` dict + fit-history comments now live at `:2563-2603`, `_persona_stats` at `:2634-2709`;
  1337-1480 holds unrelated W2-a elasticity-split tests. Amendment should fix the citation.
- `:44-47` — **Metric-DoD (D7)**: HARD gates need a live metric showing direction. N-vecfit changes no
  pack values → produces no behavior movement → its deliverable is process/infra; the amendment should
  state explicitly how D7 reads on a procedure slice.
- `:48-53` — **D11 single re-anchor**: `BANDS` move once, at W4-b, never mid-spine. N-vecfit must not
  touch `BANDS` (`test_personas_postflop.py:2563-2603`).
- Referrers that may quote fit-loop *step numbers* (become misdirected once steps renumber):
  roadmap `:584-589, 2001-2011, 2162-2173, 2500`; `specs/persona-realism-w0-foundation.md:12,23-24,141,146,151-152,177,232`;
  `specs/persona-realism-w1.md:7`; `tickets/persona-realism-w0-foundation.md:32,34,43`;
  `specs/persona-realism-w3r-1.md:72`; `tickets/persona-realism-w3r-1.md:48`; `tickets/persona-realism-w3r-2.md:5,101`.

## 2. Measurement harness (`backend/tests/test_personas_postflop.py`)

- `_persona_stats(packs, persona, n, *, context_aware=False)` — `:2634`. 9-seat lineup (3× tested
  persona + 6 round-robin fillers, `:2656-2658`); returns `(af, ftc, wtsd, call_count,
  cbet_opportunities, saw_flop_hands)` — `:2707`. Each rate stat is `None` below its own `n>=30`
  denominator floor (`:2704-2706`) — a vector fit reading several stats at once must budget `n` so
  **all** clear the floor.
- Memoized per `(persona, n, context_aware, pack-content-fingerprint)` (`:2630-2652`;
  `_packs_fingerprint` `:2606-2627`, SHA-256 over `model_dump_json()`). Mutating a lever correctly
  busts the cache — this was previously a live bug (`:2609-2614`).
- `_persona_stats_ext(packs, persona, n) -> ExtStats` — `:2952`; six W0-b metrics (cbet flop/ip/oop,
  barrel, WTSD-win, VPIP/PFR, size-bucketed FtC, node occupancy). **No `context_aware` kwarg.**
- `BANDS` precedent (`:2563-2603`): measure → 3σ CI (binomial/delta-method) → round outward. The
  established fitting method; reuse, don't invent a second (`fit-loop.md:36-37`).
- `node_trace.py:1-33` — seeded replay recording the normalized action-probability vector per node
  (not raw merits, by design `:12-17`). The anti-"right stat, WRONG node" check (fit-loop step 5).
- Harness flags: `context_aware` default `False` (`:2646-2650`); `line_aware` default `False`,
  three-valued (`False`/`True`/`_LINE_OBSERVE`) (`:2079,2087-2098,2124,2131-2133`). CI runs frozen at
  `False`; production opts in. **W4-b precondition (R9-DEFENCE-a ledger): re-anchor must run
  `context_aware=True` AND `line_aware=True`.** A vector-fit measurement wanting a production-faithful
  Jacobian needs the same posture.

## 3. The two levers in the engine (`backend/app/domain/personas_postflop.py`)

- `looseness = pf.call_looseness ?? pf.stickiness` — `:881`. Feeds:
  - facing-node CALL merit ×looseness — `:979`;
  - B5b SPR-commit draw-damp — `:1098`;
  - **N-LOGIT raise scale** `rscale = looseness / continue_ref`, applied only when
    `ActionType.FOLD in by_kind` — `:1239-1248`. This is why `call_looseness` reaches the RAISE leg
    (freed CALL mass routes to FOLD *and* RAISE `:1188-1198`) — the source of the off-diagonal.
- `agg_scale = min(pf.aggression, _AGGRESSION_CAP=5.6) * noise` — `:889`, cap at `:451`. Feeds:
  - facing-node RAISE merit — `:999-1002`;
  - unopened BET / matched RAISE merit — `:1026-1028`;
  - B5b damp — `:1100`.
- `continue_ref` — read-only frozen anchor; runtime range `_CONTINUE_REF_MIN/MAX = 0.05/8.0`
  (`:460-461`); reason-to-exist comment `:1200-1207`. Re-syncing it with the live lever silently
  deletes N-LOGIT; a lifecycle test (G9) pins it doesn't move under a refit.
- `line_sensitivity` (R9-DEFENCE-a) — `:1104-1184`; scales CALL and RAISE together by `exp(-λ_p)`;
  deliberately orthogonal to `rscale` (both scalar multiplies before the single normalization).
- **Block-triangularity, mechanical source:** `looseness` appears only in the facing branch
  (`:924-1005`), never the unopened branch (`:1006-1062`); `agg_scale` appears in both. Hence
  `∂CBet/∂ln(call_looseness) = 0` exactly (roadmap `:2001-2011`); cond(J) ≈ 2-3 generally,
  **14.3 for the station on an air-heavy range**; pair targets with non-parallel Jacobian rows
  (FtC + CBet separates; FtC + RaiseShare does not).

## 4. Pack + model layer

- `models.py:170` `aggression: gt=0.0` (no model-side cap; cap is engine mechanics);
  `:188` `stickiness` legacy fallback; `:197` `call_looseness: gt=0.0`;
  `:221` `continue_ref: ge=0.05, le=8.0`; `:242` `line_sensitivity: ge=0.0, le=2.0`.
- Authorship validators `:253-301` are **key-presence-based** (absence = opt-out; explicit null
  rejected). `model_copy(update=...)` bypasses them — experimental lever mutation is possible but
  runtime guards still apply.
- Current values: nit agg 0.6 / cl 0.6 / ref 0.6 · tag 2.4 / 0.6 / 0.6 (**cl identical to nit — the
  R9-LOOSEFIT defect**) · lag 3.2 / 0.55 / 0.55 · maniac agg 15.0 (clamps 5.6), **no
  `call_looseness`** (falls back to `stickiness`), ref 0.55 · station 0.5 / 4.0 / 4.0 ·
  fish 0.6 / 0.42 / 0.42.
- FROZEN-anchor comment (tag.json:11-16, lag.json:12-17, maniac.json:10-18): never re-sync
  `continue_ref` with the calling lever. **Sharpest invariant for the tool: any experimental fit of
  `call_looseness` must hold `continue_ref` at its frozen value or the measured Jacobian is wrong
  for production.**

## 5. Tool precedent (`backend/tools/`)

- `rr_emit.py:1-9` — CLI shape `cd backend && python -m tools.rr_emit <spec.json>`; tools may import
  `app.domain.*` one-directionally; domain never imports tools.
- `test_domain_purity.py:10-24` — enforced list is a fixed set of `app.domain.*` modules; a new file
  under `backend/tools/` **cannot** trip it.
- Testing precedent: `test_rr_emit.py` pins spec↔emitted-pack equivalence; `reject_counts.py` is
  untested. A proving-gate test for a fitting tool follows the rr_emit pattern.

## 6. Re-grep verdict (the roadmap's self-flagged weakest claim)

Checked every `call_looseness`/`looseness` hit in the roadmap: all are mechanism descriptions,
historical (shipped W3R-2/W3R-3), guardrails (R9-N2/R9-N3 forbid premature fixes), or harness sweeps.
**The only filed slice planning to lower `call_looseness` for nit/tag/lag is `R9-LOOSEFIT` itself
(`:2162-2173`), explicitly sequenced AFTER N-vecfit. Claim holds; no scope collision.**

## 7. Downstream consumers

- **R9-LOOSEFIT** (`:2162-2173, 2203`) — needs (a) the vector-valued doc, (b) a working joint-fit
  tool, (c) the fold-share/raise-share-jointly discipline (`:2168-2169`).
- **W4-b** — indirect: a mis-specified fit loop corrupts every lever value W4-b re-anchors against.
- **N-logit** (merged) is N-vecfit's prerequisite; the well-conditioned-Jacobian claim was measured
  on top of N-logit's fix.

## SURPRISES (from the scan)

1. Fit-loop doc's precedent line-range citation is stale (see §1).
2. No spec/ticket exists for N-vecfit — greenfield-within-brownfield; nearest tool precedent does a
   different job (emission/counting, not statistical fitting).
3. Jacobian not uniformly well-conditioned — station/air-heavy cond 14.3; target-pair choice is a
   real design constraint the tool should check, not just document.
4. **`_persona_stats` surfaces no direct RaiseShare/FoldShare** — AF, FtC, WTSD only. The counts
   needed (`bet_raise`, `call_count`, `folds_to_first_cbet`, `cbet_opportunities`) exist inside the
   function (`:2661-2707`) but are not returned. A joint fit on fold-share/raise-share coordinates
   needs a derived stat.
5. **maniac has no `call_looseness`** — falls back to `stickiness`; a tool assuming both levers
   authored everywhere needs a maniac branch or exclusion (editing `stickiness` moves the CALL leg
   AND the effective looseness feeding `rscale`).
