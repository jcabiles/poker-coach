# Findings — persona-realism Wave A wave 2 (T-ANCHOR)

Pass 1 — 2026-07-29 · commit `9b52743` (branch `feat/persona-realism-wave-a-w2`) · three concurrent reviewers per the wave's mandatory protocol: `refuter` (NEEDS-WORK) · `persona-realism-theory-reviewer` (PASS, full §11 checklist) · Codex Sol high (DO-NOT-SHIP — solely on the red test). Director adjudication below; nothing auto-folded.

## Unanimous on the fix itself

All three independently verified: position multiplier applied exactly once per path (bluff cell pre-complement at `:833-841`, non-bluff inside the `else:` at `:877-879`, RAISE path exactly 1.0 via the BET gate) · facing branch `:744-824` / `_position_agg_mult` / `_POSITION_AGG_DELTA` / pre-multipliers `:724-742` untouched · double-application tripwire (`test_bluff_ordering_across_personas_at_fixed_size`) structurally immune and green · pinned script all six OK to 1e-9, absolutes match ticket predictions · new test catches both the original bug and double-application (refuter reconstructed both analytically) · `_PRE_M3_FIRES` re-record legitimate, every `_WANT_*` shape fires · `coverage_baseline.json` untouched (336/1215, cumulative delta vs immutable baseline unchanged).

## The red test — `test_street_aggressions_effect_visible_to_af_gate`

| Finding | Source | Adjudication |
|---|---|---|
| Worker's diagnosis (proxy sign-unreliable; divergence in rng tail; damps still context-visible) is SOUND | Sol (independent parent-run: pre-fix af_on 2.043 at n=1000; n=300/500/700 match parent exactly; damps→1.0 gives 2.028) + theory reviewer (same n-ladder reproduction; spot probe: facing_raise flips tag top-pair RAISE 0.287→0.124, ace-high CALL 0.253→0.157) | **ACCEPTED** |
| MED — but the flip is DIRECTLY CAUSED by T-ANCHOR's own (correct) fix, not free-floating fragility: A/B with pre-fix sampler loaded side-by-side — old passes (+0.164), new fails (−0.060), identical ≤n=700. Completion-note framing understated causation | refuter | **ACCEPTED** — commit message amended at fix-round commit; owner decision made on the corrected causal claim |
| Instrument unsound by construction: `_ONE_PAIR_RAISE_DAMP` cuts AF numerator (down), `_ACE_HIGH_FLOAT_RAISE_DAMP` cuts denominator (up); effect ≈0.1 vs noise ≈±0.15 | theory reviewer + Sol | **ACCEPTED** |
| Remedy: replace with deterministic spot-level merit assertion (the test's own comment prescribes it); never threshold/n/band retune; not a bare xfail | all three converged | **OWNER DECISION 2026-07-29: redesign NOW** (scope grant to this ticket) rather than leave red (red-main cost proven in #118/#119 era) or xfail (guard would go dark) |

## Other findings

| Sev | Finding | Source | Adjudication |
|---|---|---|---|
| LOW | `_SeededCaptureRng` docstring cites a nonexistent "persona noise draw" (`noise` is a fixed default at `personas_postflop.py:651`; no `uniform()` on this path) | Sol | **ACCEPTED** (Director verified at `:1032-1034`) — fixed in fix round |
| LOW | Theory reviewer could not reproduce worker's damps-neutralized 2.028 (its probe read 2.330) | theory reviewer | **REJECTED as a discrepancy** — different experiments: theory reviewer neutralized the position multiplier; worker (and Sol, who reproduced 2.028 exactly) neutralized the two C30 damps. No conflict |
| MED · file-forward | Estimator parity: `range_estimate.py:99-102` deliberately threads `facing_raise` alone, so the villain-range reveal stays position-blind while live bots are position-tilted; T-ANCHOR widens the air-cell gap to the FULL authored multiplier (up to ±25% relative for nit/tag; live tag IP air 0.237 vs estimator 0.190). Pre-existing gap, magnitude newly widened | theory reviewer | **ACCEPTED as forward-file** — owed a note when `in_position` is eventually threaded to the estimator (metric-#5 / W4 line). No code owed by this slice |
| MED · CONTRACT-DEFECT, file-forward | Air bluff cell is texture-blind (only made hands get W3-d texture awareness): tag c-bets pure air on the driest board (Kc9s3h rainbow, HU, IP) only 23.7% — the passivity class the 181-hand review scored. Fix correct; theory incomplete at this node | theory reviewer | **ACCEPTED as forward-file** — motivating datum for the deferred F3/F16 air-side board-texture work |
| LOW | Limper-belt comment lists BB fire counts that are not pinned (only `_WANT_BB` ≥1 enforced) — pre-existing pattern, not introduced here | refuter | **NOTED**, no action this ticket |

---

Pass 2 — 2026-07-29 · Codex Sol (high) on the owner-authorized test redesign only (the redesign was Director-built after the Opus worker died on four consecutive API-529s without landing an edit — maker ≠ checker therefore required an independent pass). Verdict NEEDS-WORK, 2 findings, both ACCEPTED after Director verification by execution:

| Sev | Finding | Adjudication |
|---|---|---|
| HIGH | `af_on != af_off` cannot isolate `facing_raise` — `context_aware` also switches position/sizing-node/aggressor-contribution; Sol showed both damps neutralized to 1.0 still passes | **ACCEPTED** — added leg 1b: same seeded harness with both damps monkeypatched to 1.0 must read differently than unpatched (cache popped/restored around the patched run). Deleting the damps now fails the test — verified by execution |
| MED | Expected ratios referenced the production constants themselves, so a silent retune (or 1.0 no-op) moves expected and actual together | **ACCEPTED** — damp values pinned as literals (`== 0.35`, `== 0.55`); a retune must consciously trip the test and re-anchor (W4-b) |

Post-fix: test green at HEAD, FAILS under damp deletion (Sol's kill-scenario), full suite 1116/1 skip, ruff clean, `BACKEND VERIFY OK`. Review-loop stop condition reached (fixes are Sol's own prescriptions, verified by execution; no new question outstanding). Shipped as the amended single ticket commit → PR #131.

## Verdict-conflict record

Sol DO-NOT-SHIP vs theory PASS vs refuter NEEDS-WORK is **not a substantive conflict**: all three cleared the fix; the spread is entirely their stance on shipping with a red test, and all three prescribe the same remedy (spot-level redesign, no retune). Surfaced to owner as the single gate decision; owner chose redesign-now.
