# Finding ledger — N-LAGWIDTH spec review (2026-08-01)

Reviewers: Claude refuter (Sonnet) + Codex Terra (`gpt-5.6-terra`), parallel, spec+contracts+HEAD.
Complexity tier: EASY (pack-data slice) per the owner's 2026-08-01 reviewer-tiering rule.
R# = refuter finding, C# = Codex finding. Convergent findings adjudicated once.

| # | Sev | Finding | Adjudication |
|---|---|---|---|
| R1+C1 | HIGH | Spec missed the two N-3BSTRATA lag gates driven by unopened composition: opener fold-to-3bet component pin `0.6166 ± 0.02` (`test_personas_postflop.py:5136`) and production blend band `[0.43, 0.53]` @ n=12000 (`:5265`). Precedent: N-LAGLADDER's cut dropped the blend to 0.4242 (under floor) and required a vs_3bet opener-table retune, recorded in the test's own docstring as "not optional". | **ACCEPTED — spec amended.** Both tests added as watched gates with mandatory stable-n pre/post measurement. Conditional scope added: if the blend leaves band, the established N-LAGLADDER remedy (vs_3bet opener-table call-weight retune + component re-pin per the update-the-pin law) is IN scope, with disclosure. Component pin re-pinned as needed (arrival-weighted; the trim changes the weights by construction). |
| R2+C4 | HIGH/MED | `test_w3r1_preflop_cleanup.py:236` pins lag SB unopened outcomes incl. **J9o → raise exactly**; an SB offsuit cut can flip it. | **ACCEPTED — spec amended.** Added as preservation constraint: SB depth cut must keep J9o in the raising core (J9o stays comfortably above the cut line at the target width; builder verifies), else re-pin with disclosure + owner note. |
| R3 | HIGH | **main (47d642d) is RED on a clean checkout**: `test_persona_stats_byte_identical_after_log_refactor` (expects 2.6812, code yields 2.5522 — the wave-6 #157 maniac golden move never landed in this test's pin) and `test_limper_coverage_belt.py::test_limper_coverage_fires_on_organic_play` (UTG2 fire count 91 != 87). | **ACCEPTED — VERIFIED by orchestrator re-run.** Wave-6 squash chain lost a re-record (the exact failure mode wave-6's own learning #1 documented). Filed as **prerequisite ticket T0**: a separate `chore/` fixture-repair PR restoring the reviewed wave-6 values on main BEFORE the slice lands. Codex did not flag (did not run the suite); no conflict — refuter ran it, orchestrator confirmed. |
| C2 | HIGH | Claims the per-seat `maniac > lag` / `lag > tag` hard gates violate §5a's "cross-persona orderings may never be HARD". | **REJECTED.** §5a's bar covers orderings sourced from the provenance doc's per-seat *bands/magnitudes* (the demoted cliff gate is the precedent). The ladder ordering gates were owner-adjudicated on **definitional archetype grounds** (roadmap R10-PRE2: "the roster's DEFINITIONAL archetype ordering — theory contract §1 idealized-distinct caricatures... NOT the dossier seat bands"), the same basis as the pinned cross-persona `bluff_freq` ordering. They stand as preservation gates. Recorded so the disagreement is visible. |
| R4+C5 | MED | Spec's `_STATS_EXT_CACHE` "pack-blind" hazard is STALE — wave-6 #155 added `_packs_fingerprint(packs)` to the key (`test_personas_postflop.py:2827`). Baseline numbers also stale: current 600-hand read VPIP 23.889 / PFR 17.222 / gap 6.667. | **ACCEPTED — spec + contracts corrected.** Separate-process measurement kept as a precaution only. Population exit stated as paired VPIP+gap (primary) with PFR disclosed. |
| R5+C3 | MED | Citation errors: strict monotonicity lives in `test_rr_emit.py:414` (the `test_personas.py:974` gate is non-decreasing only); the rr_emit proving gates compare parsed combo sets + weights (semantic), not bytes; RR-LINT frozen inventory starts ~`:147/153`, not `:101`. | **ACCEPTED — citations corrected in spec + contracts.** |
| R6+C6 | LOW | CO's feasible window is **(47.632, 49]**, not 47–49 (untouched HJ = 47.632 and strict increase is enforced spec-side). Codex table of actual widths: HJ 47.632 / CO 53.122 / BTN 65.973 / SB 51.855; offsuit-only implies CO offsuit 20.5–22.5, BTN 26.6–28.6, SB 19.4–21.4 — all stay above tag's. Illustrative feasible landing: CO 48.6 / BTN 57.8 / SB 46.4. | **ACCEPTED — spec targets restated.** |
| R7+C7 | LOW | Red-first proof should be recorded with actual numbers: HEAD CO 53.122>49, BTN 65.973>58, SB 51.855>47. | **ACCEPTED — recorded in spec + ticket.** |

Verdicts as returned: refuter FAIL (pre-amendment) · Codex FAIL-WITH-FINDINGS (pre-amendment).
All accepted findings folded into `docs/ai-dlc/specs/n-lagwidth.md` rev 2 (same date). No unresolved
reviewer conflict remains except C2, rejected with recorded reasoning above.

---

# Build fan-in review (2026-08-01, build commit d0d14fb on `feat/persona-realism-n-lagwidth`)

Reviewers: fresh Sonnet refuter + `persona-realism-theory-reviewer`, parallel, git-READ-ONLY.
Codex skipped per ticket T4 (the conditional vs_3bet retune never fired — blend held 0.4722 in band).

| # | Reviewer | Sev | Finding | Adjudication |
|---|---|---|---|---|
| F1 | theory | MED | Component pin left riding 79% of its ±0.02 tolerance (measured 0.6012 vs pin 0.6166); docstring line "lands at 0.6166 (deterministic)" now false; N-LAGLADDER precedent re-pinned a constructed move of similar size. | **ACCEPTED — folded.** Re-pinned 0.6166→0.6012 with disclosure; both watched-gate docstrings gain the N-LAGWIDTH pre/post readings (component 0.6170→0.6012; blend 0.4914→0.4722 @n=12000, CI [0.447,0.498]). |
| F2 | theory | MED | Relocated defect: flooring CO on the untouched HJ manufactures a near-plateau (HJ 47.63 → CO 48.60, +0.97pp between two +9pp steps); lag HJ/early seats stay over-wide (UTG 24.9 vs folklore 15–18 [UNVERIFIED]). Not a slice defect (HJ out of owner-approved scope; no contract level-target exists upstream of CO). | **ACCEPTED-AND-FILED** as roadmap NEXT item **`N-LAGHJ`** (with the cliff-inversion close-out riding on it). Do NOT widen CO back. |
| F3 | theory | LOW | `_doc` per-row cut description wrong (BTN rows dropped two classes each, not one; SB Jo omitted). | **ACCEPTED — folded** (wording corrected). |
| F4 | theory | LOW | SB opens T8o+ full-weight while BTN only T9o — cross-seat To-row inversion, cosmetic, ungated. | **ACCEPTED-DOCUMENTED** — carried inside the `N-LAGHJ` filing; no change now. |
| F5 | both | LOW | T4 bookkeeping (roadmap mark, W4-b watch adds, PR) absent from the build diff. | **EXPECTED** — T4 is the orchestrator's ticket; completed this session (roadmap edited, this ledger updated, PR opened after the fold commit). |

Refuter verdict: **PASS** — independently re-derived every numeric claim (widths to 3 decimals,
suited/pairs byte-identity both directions, corpus 127 with the exact dropped set, red-first proof
against the base pack, BANDS center 41.487, budget-bump non-masking via standalone re-run, population
n=12000 pre/post with pack-swap-and-restore). Theory verdict: **GO-WITH-ISSUES** (above), §11
checklist 15/15 PASS, C2 rejection re-confirmed standing.
