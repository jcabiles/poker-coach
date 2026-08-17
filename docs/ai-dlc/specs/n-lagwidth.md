# Delta spec — N-LAGWIDTH: lag late-seat width trim (CO/BTN/SB)

**Slice of:** `docs/ai-dlc/roadmap/persona-realism.md` (wave-5 filing `N-LAGWIDTH`, theory MED,
CONTRACT-DEFECT class). Unblocked by PR #154 (§5a per-seat governance ruling) — per-seat RFI is
provenance-governed: one-sided bounds + within-persona shape only; cross-persona orderings stay
`[UNVERIFIED]`. Owner interview 2026-08-01: **modest trim**, both side effects accepted.

> **Rev 2 (2026-08-01):** amended after dual review (Claude refuter Sonnet + Codex Terra) — see
> `docs/ai-dlc/ledger/n-lagwidth.md` for every finding + adjudication. Material changes: prerequisite
> T0 (main is RED — fixture repair first), the two N-3BSTRATA lag gates added with a conditional
> vs_3bet retune escape hatch, the SB J9o pin, corrected CO window (47.632, 49], corrected citations,
> corrected `_STATS_EXT_CACHE` claim.

## Goal (one line)

Trim the LAG persona's authored late-seat first-in opening widths — BTN 65.973 → **56–58**,
CO 53.122 → **(47.632, 49]** (floored by the untouched HJ = 47.632 + strict spec-side monotonicity),
SB 51.855 → **45–47** (all % of combos, DIRECTIONAL targets; illustrative feasible landing
CO 48.6 / BTN 57.8 / SB 46.4) — by removing **offsuit combos only**, so LAG sits clearly between
TAG and maniac instead of near-maniac. Offsuit-only implies CO offsuit 26.606 → ~20.5–22.5,
BTN 36.561 → ~26.6–28.6, SB 26.244 → ~19.4–21.4 — all remain above tag's (11.765 / 22.172 / 13.575).

## Prerequisite — T0: main is RED (verified 2026-08-01, blocks everything)

`main` @ 47d642d fails two tests on a clean checkout — `test_persona_stats_byte_identical_after_log_refactor`
(pins 2.6812; code yields 2.5522 — the wave-6 #157 maniac golden move never reached this pin) and
`test_limper_coverage_belt.py::test_limper_coverage_fires_on_organic_play` (UTG2 fire count 91 != 87).
The wave-6 squash chain lost a re-record (its own learning #1). **Ship a separate `chore/` fixture-repair
PR restoring the reviewed wave-6 values FIRST**; the slice's Verify-by is unreachable until then.

## Anchor provenance (§5a rule c — cite or fail)

The only late-seat anchor is `docs/ai-dlc/research/rfi-seat-provenance.md:127`: *"a LAG UTG ≈ 15–18
and BTN ≈ 50+ is the recalled folklore **[UNVERIFIED]**"*. Per §5a rule (a), NO per-seat target here
is gate-grade; the committed gates are **one-sided ceilings + within-persona shape** only. The
defect evidence is intra-roster: authored lag CO/BTN (53.1/66.0) sit nearer maniac (63.5/73.3)
than tag (post-#153 BTN ≈ 43.9).

## Files / interfaces to touch

| File | Change |
|---|---|
| `content/personas/ladders/lag.unopened.json` | Reduce CO/BTN/SB **offsuit** depths (top-anchored cut from the bottom of each ladder — expressible today; the wheel-ace/keep-token limitation is not triggered by a bottom cut); update the per-seat `raise_pct` annotations in the same commit (test `test_rr_emit.py:424-436` enforces). Version bump. |
| `content/personas/lag.json` | Re-emitted output of the spec via `backend/tools/rr_emit.py` (byte-identity proving gates `test_rr_emit.py:351-406` enforce spec↔pack agreement). Version bump. |
| `backend/tests/test_personas.py` | (a) **NEW red-first defect gate:** one-sided authored-width **ceilings** at CO/BTN/SB (≤49 / ≤58 / ≤47) — FAILS at HEAD, proof recorded: CO 53.122 > 49, BTN 65.973 > 58, SB 51.855 > 47. (b) Update `_LAG_OFFSUIT_CEILING` (`:727-731`) values downward to re-pin the new composition. (c) Re-pin `BANDS["lag"]` open-freq rows (`:403`, exact-width ±2pp — seat-average falls ~2pp) with the standard in-file old→new disclosure. |
| `backend/tests/test_personas_postflop.py` (N-3BSTRATA gates) | **Watched gates (reviewer HIGH, convergent):** opener fold-to-3bet component pin `0.6166 ± 0.02` (`:5136`) and production opener blend band `[0.43, 0.53]` @ n=12000 (`:5265`). The trim strengthens the opener's arriving range, so the blend FALLS — precedent: N-LAGLADDER's cut hit 0.4242, under floor. Mandatory **stable-n pre/post measurement**. **Conditional scope:** if the blend leaves band, the established remedy — vs_3bet opener-table call-weight retune + component re-pin (update-the-pin law) — is IN scope, with disclosure. The component pin re-pins as needed (it is arrival-weighted; the trim moves it by construction). |
| `backend/tests/test_w3r1_preflop_cleanup.py:236` | **Preservation pin (reviewer HIGH/MED, convergent):** `test_lag_sb_no_open_limp` requires SB **J9o → raise exactly**. The SB depth cut must keep J9o in the raising core (verify against the chosen cut line), else re-pin with disclosure. |
| `backend/tests/test_personas_postflop.py`, `test_coverage_baseline.py`, `test_limper_coverage_belt.py` | Seeded-fixture re-records (rng-stream displacement), atomic with the pack change, in-file disclosure per the single-recorder custom. |
| `docs/ai-dlc/roadmap/persona-realism.md` | Mark N-LAGWIDTH shipped; add PFR-dip to the W4-b watch list; note the cliff-ratio report worsens (accepted, stays filed with the lag-lane cliff item). |

## Preservation gates that MUST stay green (labeled per the gate-design rule — passing at HEAD is their job)

- `test_maniac_first_in_ladder_above_lag` (`test_personas.py:615`) — trim only widens the margin.
- `test_lag_first_in_ladder_above_tag_preservation` (`:957`) — builder verifies per-seat margin vs the ACTUAL post-#153 tag pack before choosing exact depths.
- `test_lagcomp2_late_seat_suited_covers_the_tag` (`:888`) — **suited rows byte-untouched** at CO/BTN/SB; this is why the trim is offsuit-only.
- `test_lag_offsuit_width_at_least_tag_preservation` (`:857`) — lag offsuit ≥ tag offsuit at LJ/HJ/CO/BTN/SB; bounds the trim depth from below; builder verifies numeric headroom first.
- `test_lag_first_in_ladder_monotone_and_sb_under_btn_preservation` (`:974`) — **non-decreasing** UTG→BTN + SB < BTN (equality passes here). The STRICT increase is enforced spec-side by `test_rr_emit.py:414` (`test_lag_ladder_widths_strictly_increase_toward_the_button`) — that gate is why **CO's floor is the untouched HJ width 47.632** (never touch HJ); SB < BTN holds (45–47 < 56–58). SB is deliberately outside `monotone_seats` in the ladder spec.
- `test_lag_premium_unopened_never_folds_preservation` (`:546`) — premiums out of trim reach.
- RR-LINT frozen inventory (`test_pack_range_lint.py:~147-224` inventory, `:277` assertions) — emitter output is contiguous by construction; no new row gaps.
- `test_lag_ladder_widths_strictly_increase_toward_the_button` (`test_rr_emit.py:414`) — the STRICT spec-side monotone gate (see CO/HJ floor above). Note the rr_emit proving gates (`:351-406`) compare parsed combo sets + weights (semantic identity), not serialized bytes.

## Population effects (measure pre/post in a separate process as a precaution — note the cache is now pack-fingerprint-keyed since #155, `test_personas_postflop.py:2827`; the old "pack-blind" hazard is FIXED)

- **Primary (must hold, §5 + #154 ruling), asserted as a PAIR:** VPIP stays in 21–27 AND VPIP−PFR gap ~unchanged (a trimmed open becomes a fold — leaves both terms equally). Measured baseline @600 hands: VPIP 23.889 / PFR 17.222 / gap 6.667 (small-n; use stable-n for the exit reading).
- **Accepted side effects (owner 2026-08-01):** PFR (17.36, floor 17, derived-DIRECTIONAL per #154) may dip below 17 — disclose the measured value + add to the W4-b watch list; cliff ratio BTN/UTG (report-only `test_tagwidth_cliff_ordering_reported_not_gated`) falls further below tag's — disclosed, the lag-lane cliff item stays filed.

## Out of scope (explicit)

Early seats (UTG..HJ) and BB · suited classes anywhere · `vs_*` response nodes **except** the
conditional vs_3bet opener-table retune above (fires only if the blend gate leaves band) · the cliff-inversion
fix · any frozen BANDS value other than the lag open-freq re-pin · the RR-EMIT except/keep token
(filed separately) · any `personas_postflop.py` / spine code · schema changes.

## Constraints (profile invariants)

Strategy stays in versioned `content/` data (this slice is pack + spec + tests only) · no
`app/domain/` web/DB imports · `spot_signature()` untouched · estimator parity is automatic
(`range_estimate.py` reads the same pack object at runtime — no mirror to update).

## Verify-by (end-to-end)

0. **T0 first:** main green on a clean checkout (the two currently-red tests fixed in their own `chore/` PR).
1. New CO/BTN/SB ceiling gate demonstrably RED at the T0 tip (proof: 53.122>49, 65.973>58, 51.855>47), GREEN after.
2. `./scripts/verify.sh` → "BACKEND VERIFY OK" (full suite incl. proving gates, lint belt, N-3BSTRATA gates, `test_lag_sb_no_open_limp`, re-recorded fixtures).
3. `cd backend && ruff check .` clean.
4. Separate-process stable-n population read: lag VPIP in 21–27 AND gap ~unchanged (paired primary), PFR value disclosed + W4-b watch note.
5. Stable-n pre/post opener-blend reading recorded; if a vs_3bet retune fired, its disclosure + component re-pin present.
6. Fixture disclosures present in all three re-recorded files; roadmap + watch-list edits present.
