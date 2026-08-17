# Tickets — R9-LOOSEFIT rev 4

status: **approved (owner, 2026-08-04, Gate 2 — serial single-agent build authorized; T6 by an independent agent)**
spec: `specs/r9-loosefit-rev4.md` · ledger: `ledger/r9-loosefit.md` · contracts: `contracts/r9-loosefit.md` (REV-2 SCAN block)
base: **branch from `origin/main` = b63dfaa, NOT from `7736156`** (the halted build's accessor is not part of this slice)

**SERIAL — T2/T3/T4/T5 all own `backend/tests/test_personas_postflop.py`.** Single agent T1→T7,
except T6 which MUST be a different agent from whoever wrote T2/T3 (maker ≠ checker). No parallel
waves; this slice is small and the file is a single-owner hotspot.

## T1 — pack edit + blast-radius confirmation

Set nit's `call_looseness` 0.6 → **0.45**; add a `_doc` version array (nit lacks one); bump
`version` from 1.5.0. **`continue_ref: 0.6` and `stickiness: 0.6` byte-untouched.**
- Owned: `content/personas/nit.json`.
- Done-condition: `git diff` shows one file and only those fields; full suite run unpiped from a
  file shows **exactly two failures** — `test_persona_stats_byte_identical_after_log_refactor` and
  `test_limper_coverage_fires_on_organic_play`. **Anything else that moves is a finding to report
  before continuing, not a re-record to perform.**

## T2 — the contribution-aware node helper + G-NODE panel

Add a helper that calls `sample_postflop_decision` with `latest_aggressor_contribution_bb`
supplied and **asserts the engine's computed faced fraction equals the node's declared fraction**
(to 1e-9). Do NOT use `_dist_for_pack` — its missing parameter is what mispriced rev 3.
Then the panel: P1–P4 and C5, **self leg only (≥ 0.040)**, plus non-degeneracy in [0.01, 0.99] on
every legal action, both personas, both lever values. **Do NOT add an identity leg** — it is
algebraically subsumed by the self leg (spec S-9); the cross-persona claim belongs to T3's sweep.
- Owned: `backend/tests/test_personas_postflop.py`.
- Done-condition: panel green at 0.45; every node's measured baseline recorded in a comment;
  docstring states the identity leg's composition (self + pre-existing aggression gap) and the
  0.071797 ceiling. Suite green unpiped.

## T3 — G-SWEEP (the population gate)

The re-priced canonical sweep: `pot_bb = pre_bet_pot + to_call`, `contribution = to_call`, faced
fractions {⅓, ⅔, 1, 2}, SPR held at the grid's intent. **Pin that re-pricing in the test** — without
it the gate silently reverts to measuring 600×-pot bets. Two legs: ≥ 800 of the non-degenerate
cells show nit@0.45 folding strictly more than tag; ≥ 650 by more than 0.02. **Enumerate the
denominator, do not assert 970** — it depends on the arbitrary [0.01, 0.99] constant.
- Owned: `backend/tests/test_personas_postflop.py`.
- Done-condition: both legs green (measured 970 and 826); denominator printed in the failure
  message; a comment recording the HEAD baseline (384 / 300) that makes the gate red-at-HEAD.

## T4 — correct the five statements this slice makes false

`:6899`, `:6925`, `:7208`, `:8468`, `:8610` — "authored value" → "calibration anchor". **Assertions
unchanged**; this is wording only, and it is in scope because the slice makes them false.
- Owned: `backend/tests/test_personas_postflop.py`.
- Done-condition: the five sites corrected; no assertion edited; suite green.

## T5 — the two fixture re-records

`_GOLDEN_STATS_N200` per the protocol at `:3316-3448`; `_PRE_M3_FIRES` per `:44-287`. Both need a
"RE-RECORDED for R9-LOOSEFIT" block and **attribution proven by revert**, per each fixture's own
documented rule.
- Owned: `backend/tests/test_personas_postflop.py` (golden block), `backend/tests/test_limper_coverage_belt.py`.
- Done-condition: both green; the revert evidence recorded in the ticket report.

## T6 — sensitivity + mutant proof (INDEPENDENT agent)

Run by someone who did not write T2 or T3.
(a) Revert nit to 0.6 → every G-NODE self leg red, every identity leg red, G-SWEEP-a red at
384/970; restore byte-for-byte.
(b) Kill the named mutants: a `call_looseness` no-op (lever read, result discarded) must die on the
self leg AND G-SWEEP-a. **Disclosed non-kill:** a mutant scaling CALL but not RAISE survives every
G-NODE leg and G-SWEEP. Ownership is delegated to N-LOGIT's G1 invariance gate — **demonstrate that
G1 kills it on BOTH the shipped (mispriced) construction AND a correctly-priced one.** G1 runs at
faced fractions of 600 and 1200, a regime this spec excludes from its own panel as degenerate. If
G1 discriminates only at the broken prices, STOP and report — that escalates `N-NLOGITPRICE` from
filed to blocking.
(c) `./scripts/verify.sh` → BACKEND VERIFY OK · `ruff check .` · full suite unpiped ·
`test_price_tail.py`, `test_node_trace.py`, `test_mw_catch_toppair.py`, `test_arrival_range_ftc.py`
green **without edit**.
- Owned: none (read/execute; every temporary mutation byte-restored).
- Done-condition: a per-mutant kill table plus the revert evidence.

## T7 — docs

New `docs/ai-dlc/reports/r9-loosefit-rev4-measurement.md`: the panel table, the sweep distribution
and histograms, the ceiling derivation. Roadmap: mark built; file `N-LADDER-PREMISE`,
`N-NLOGITPRICE`, `N-ANCHORSTALE` (narrowed to the 41-site audit), `N-TAGPIN`, `N-SIMFLAKE`.
- Owned: `docs/ai-dlc/reports/r9-loosefit-rev4-measurement.md`, `docs/ai-dlc/roadmap/persona-realism.md`.
- Done-condition: greps for the five filings and the report's three sections.

## DAG

T1 → T2 → T3 → T4 → T5 → T6 (independent agent) → T7 → dual review + `persona-realism-theory-reviewer`
at fan-in, findings adjudicated into `ledger/r9-loosefit.md`.
