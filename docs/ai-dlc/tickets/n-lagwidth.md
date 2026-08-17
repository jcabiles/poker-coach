# Tickets — N-LAGWIDTH (spec: specs/n-lagwidth.md rev 2 · ledger: ledger/n-lagwidth.md)

Serial chain (every ticket after T0 touches the same pack/fixture surfaces — one owner at a time,
single-fixture-recorder custom). No parallelism.

## T0 — repair the red main baseline (PREREQUISITE, own `chore/` PR, merges first)
Fix the two tests red on clean main @ 47d642d: `test_persona_stats_byte_identical_after_log_refactor`
(pin 2.6812 vs actual 2.5522 — apply the wave-6 #157 maniac golden move this pin missed) and
`test_limper_coverage_belt.py::test_limper_coverage_fires_on_organic_play` (UTG2 fires 91 != 87).
Restore the reviewed wave-6 values (cross-check the pre-squash branch tips if available); re-record
ONLY what the wave-6 chain demonstrably lost, with in-file disclosure naming this incident.
**Owned files:** `backend/tests/test_personas_postflop.py` (the one pin), `backend/tests/test_limper_coverage_belt.py`.
**Done:** full suite green on the PR tip from a clean checkout; disclosure comments in both files.
**Depends:** none. Blocks T1–T4.

## T1 — pre-measure + choose exact widths (no pack edit yet)
On the T0 tip: (a) record stable-n lag baseline — VPIP/PFR/gap + the N-3BSTRATA opener blend
(`test_personas_postflop.py:5265` methodology, n=12000) + component pin value; (b) pick exact emitted
per-seat widths inside CO (47.632, 49] / BTN 56–58 / SB 45–47, offsuit-only cuts, verifying: lag offsuit
≥ tag offsuit per seat (actual post-#153 tag pack), SB J9o stays in the raising core, strict HJ<CO<BTN
spec-side. Record the chosen class cuts in the ticket file.
**Owned files:** none (analysis only; writes a short note into this file's T1 section).
**Done:** chosen widths + class lists recorded; predicted blend direction noted.
**Depends:** T0.

## T2 — ladder-spec edit + re-emit + gates
Edit `content/personas/ladders/lag.unopened.json` (CO/BTN/SB offsuit depths + `raise_pct` annotations,
version bump) → re-emit `content/personas/lag.json` via `backend/tools/rr_emit.py` (version bump).
Add the NEW one-sided ceiling defect gate (red-first proof at T0 tip: 53.122>49 / 65.973>58 / 51.855>47);
update `_LAG_OFFSUIT_CEILING`; re-pin `BANDS["lag"]` with disclosure.
**Owned files:** the two content files + `backend/tests/test_personas.py`, `backend/tests/test_rr_emit.py` (annotation/proving updates only).
**Done:** ceiling gate green; proving gates green; RR-LINT green; all preservation gates in the spec's list green; `ruff` clean.
**Depends:** T1.

## T3 — post-measure + conditional vs_3bet retune + fixture re-records
(a) Stable-n post reading: VPIP 21–27 AND gap ~unchanged (paired primary); PFR disclosed; opener blend
vs [0.43, 0.53]. (b) **Only if** the blend left band: vs_3bet opener-table call-weight retune (the
N-LAGLADDER remedy) + component re-pin per the update-the-pin law, with disclosure. (c) Re-record the
three seeded fixture surfaces (goldens / coverage_baseline / limper belt) atomically with in-file
disclosures (single-recorder).
**Owned files:** `backend/tests/test_personas_postflop.py`, `test_coverage_baseline.py`, `test_limper_coverage_belt.py`, (+`content/personas/lag.json` only if the retune fires).
**Done:** `./scripts/verify.sh` → BACKEND VERIFY OK on the branch tip; all measurements recorded in the PR body.
**Depends:** T2.

## T4 — bookkeeping + PR
Roadmap: mark N-LAGWIDTH shipped; add lag PFR dip to the W4-b watch list; note the cliff-ratio report
worsening (accepted, lag-lane item stays filed). Push by OID, open PR (base main, after T0 merges),
triple-review at fan-in per the wave custom (refuter + theory reviewer; Codex on the retune only if it fired).
**Owned files:** `docs/ai-dlc/roadmap/persona-realism.md`.
**Done:** PR open with measurements + disclosures; reviews adjudicated.
**Depends:** T3.
