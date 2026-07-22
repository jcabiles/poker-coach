# Tickets — Epic 5 tail (M4–M7)

Autonomous `/parallel-waves` run. Scope locked (2026-07-22 interview): **all four M4–M7** ·
**3 waves [M4‖M5]→M6→M7** · **skip-and-document + auto-fix HIGHs** · **Codex dual-review ON** ·
one PR per wave, user merges. Branch off `main` (643f2d9). Spike docs LAW; specs under
`docs/ai-dlc/specs/epic5-m{4,5,6,7}-*.md`; contracts `docs/ai-dlc/contracts/epic5-m4-m7.md`.

## Wave plan (DAG)

```
main
 └── W1  feat/epic5-m4-m5   [ M4 ‖ M5 ]   (2 agents, additive, disjoint families)   → PR (M4+M5)
       └── W2  feat/epic5-m6   [ M6 ]      (mutates _apply_multiway; threads opp)     → PR (M6)
             └── W3  feat/epic5-m7 [ M7 ]  (opener/caller MW mappers; ≥30k re-measure) → PR (M7)
```

Deps: M6 ← M4 (composition: M6 changes `_apply_multiway` sig that M4 calls). M7 ← M6 (4-way scalars).
M4 ⊥ M5. Stacked branches; user merges bottom-up; lead re-syncs on each merge (`--ours` for
chain-owned files, watch duplicated blocks — Epic-4 lesson).

## Fan-in ownership (W1 — makes 2-wide safe)

Both M4 and M5 append to `postflop.py` + `grade_map_postflop.py` + `grade_map.py` + **TWO** enum
modules (refuter LOW: not one): `NodeContext` (`spot.py`, StrEnum — string-keyed, additive-safe) and
`LeakCategory` (`leaks.py`, **IntEnum** — hand-picked reserved ints, a numeric collision is a SILENT
semantic bug that text-level `git diff`/dedup won't catch). **Pre-assigned to avoid parallel
collision:** M4 `VS_CALLER_RAISE = 207`; M5 `LIMPED_LEAD = 208` (+ `LIMPED_VS_LEAD = 209` if it needs
a second) — 207/208/209 are the free postflop slots (200-206, 210-211 taken). Each maker edits ONLY
its own new functions/entries; the **lead serializes the shared files at fan-in** (concatenate
appended blocks, resolve import/chain order) and MUST run a duplicate-value assertion
`len(set(LeakCategory)) == len(LeakCategory)`. Makers use `$TMPDIR` scratch, commit early, no
`git commit` of shared files until lead integrates (W1 R3‖R4‖R5 precedent).

## Tickets

### Wave 1 — parallel
- **T-M4 — Caller-re-raise grader.** `_merits_vs_caller_raise` + `grade_vs_caller_raise` +
  `map_flop_vs_caller_raise` + dispatcher entry + `VS_CALLER_RAISE` enum. Owner: implementer/heavy.
  **Done:** spec M4 verify-by 1–7 green; `test_grade_map_caller_raise.py` incl. range-asymmetry +
  α-not-applied tests; refuter+Codex PASS.
- **T-M5 — HU limped-pot flop grader.** limped-flop preflop gate + `map_limped_flop_lead` /
  `map_limped_flop_vs_lead` + limped grader(s) + content thresholds + dispatcher entries. Owner: heavy.
  **Done:** spec M5 verify-by (a)–(d) green; `test_grade_map_limped_flop.py` incl. explicit 3-way→None;
  raised-pot pins byte-unchanged; refuter+Codex PASS.
- **T-W1-integrate — Lead fan-in.** Serialize the 3 shared files, dedup-check, full suite from
  `backend/`, `spot_signature`/coverage-baseline invariants, one W1 commit → PR (M4+M5). Owner: lead.

### Wave 2 — after W1
- **T-M6 — 4-way merit extension.** `_apply_multiway` gets `opp` + geometric `base**max(opp-1,0)`
  consts (base = today's constant); thread `opp` through ALL call sites; widen `map_mw_*` to fire
  4-way-hero-closes. Owner: heavy. **Done:** spec M6 verify-by 1–5 green; `test_apply_multiway_opp.py`
  (HU + 3-way byte-identical, monotone, direction-only, 4-way closes vs live-behind→None); refuter+Codex PASS → PR (M6).

### Wave 3 — after W2
- **T-M7 — Hero-seat widening.** opener + caller MW mappers + dispatcher entries; ≥30k re-measure.
  Owner: heavy. **Done:** spec M7 verify-by 1–4 green; `test_mw_hero_seat_widening.py`; re-measure
  rate + hero proxy recorded in done-note (ship even if <5/1000, documented); BB-path byte-unchanged;
  display==grade re-verified; refuter+Codex PASS → PR (M7).

### Cross-wave
- **T-roadmap — Mark M4–M7 `[x]`** with done-notes + deviations ledger; update memory
  `simulate-initiative-state.md`. Fold roadmap edit into each wave's first commit (carries forward).

## Per-slice cycle (each ticket)
brief (spec + contracts + injected invariants) → maker → fresh-context **refuter-on-diff ‖ Codex Sol**
(dual, review-only, `--model gpt-5.6-sol`, Sol one input never sole authority) → fold ALL findings,
auto-fix HIGHs in-cycle → re-verify (`verify.sh` + build) 3× stable → commit → PR. Pass/fail miss
after a fix cycle → document deviation in roadmap+PR body, move on (skip-and-document).
