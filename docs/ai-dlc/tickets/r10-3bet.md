# Tickets — R10-3BET (+ design-pass adjudication)

> Spec: `docs/ai-dlc/specs/r10-3bet.md` (v2). Contracts: `docs/ai-dlc/contracts/r10-3bet.md`.
> Ledger: `docs/ai-dlc/ledger/persona-realism-r10-3bet.md`.
> Build tickets T1–T6 are SERIAL (T2–T6 share `backend/tests/test_personas_postflop.py` or depend on
> T1's authored packs — one owner, one branch). T7 is doc-only and PARALLEL to all of them.
> Hotspot note: no profile hotspot files are touched; `test_personas_postflop.py` is single-owner
> within this slice.

## T1 — Author six-pack `vs_3bet` mixes
Re-author the one `vs_3bet` node in each of `content/personas/{nit,tag,lag,maniac,calling_station,passive_fish}.json` per spec authoring requirements (tiers strongest-first, dossier-grounded, arrival-conditioned targets, station zero-4bet / fish AA@0.5 frozen, nit 4-bet share < ~1.69%); bump each pack `version`.
- **Owned files:** `content/personas/*.json`
- **Done when:** packs load (pydantic validators pass) and T2's gates pass against them.

## T2 — Gate + freeze tests (dep: T1)
Add deterministic tests: ① nit QQ/AKs/AKo continue weight each > 0; ② combo-weighted 4-bet share ordering maniac > lag > tag > nit using the pinned first-match formula; ③ station `4bet` mass = 0, fish `4bet` mass = exactly {AA: 0.5}; plus AA/KK continue > 0 per pack (PRESERVATION-labeled).
- **Owned files:** `backend/tests/test_personas_postflop.py`
- **Done when:** ① shown failing at pre-T1 HEAD and passing after; all gates green.

## T3 — Six-persona stratified fold-to-3bet report helper (dep: T1)
Report-only helper printing, for all six personas at `vs_3bet`: cold stratum (`first_hits`), opener stratum (`all_hits − first_hits`), denominators, Wilson 95% CIs. Never asserts rates.
- **Owned files:** `backend/tests/test_personas_postflop.py`
- **Done when:** `pytest -k node_action -q -s` prints the grid; integrity test (counters≡occupancy) still green.

## T4 — RR-LINT frozen-inventory co-edit (dep: T1)
Update `_ROW_GAPS` / `_WEIGHT_INTERLEAVING` / `_INERT_TOKENS` to the new authored state — burn down entries the re-author fixes; any NEW gap/inert/interleave entry must be intentional and ledgered.
- **Owned files:** `backend/tests/test_pack_range_lint.py`
- **Done when:** `pytest tests/test_pack_range_lint.py -q` green; inventory delta listed in ledger.

## T5 — Fixture re-records + content-pin co-edits (dep: T1–T4)
Re-record `coverage_baseline.json`, `_GOLDEN_STATS_N200`, `_PRE_M3_FIRES` (`test_limper_coverage_belt.py`), maniac cross-val band if displaced; co-edit tag's exact 4-bet posterior pin in `test_range_estimate.py:190-198` with provenance comment. **BANDS check:** if `test_persona_postflop_bands` breaks — STOP, escalate to owner, do not touch BANDS.
- **Owned files:** `backend/tests/data/coverage_baseline.json`, `backend/tests/test_limper_coverage_belt.py`, `backend/tests/test_range_estimate.py` (+ fixture blocks in `test_personas_postflop.py`)
- **Done when:** `./scripts/verify.sh` green + `ruff check .` clean; every delta itemized in ledger.

## T6 — Ledger build section + roadmap bookkeeping (dep: T5)
Append build section to ledger (W5-b4 template: done-condition before/after, provenance rows quoted verbatim, fixture deltas, report grid with CIs); mark R10-3BET state in roadmap; open PR `feat/persona-realism-r10-3bet`.
- **Owned files:** `docs/ai-dlc/ledger/persona-realism-r10-3bet.md`, `docs/ai-dlc/roadmap/persona-realism.md`
- **Done when:** PR open with ledger complete; preflop lane closable.

## T7 — Design-pass adjudication (PARALLEL, doc-only, Director-run)
Read existing `docs/ai-dlc/reports/r9-defence-design.md` (five answers) + `r10-tail-design.md` (two answers); adjudicate each recommendation accept/reject; record adjudication + roadmap design-pass state. NO build work, NO fixtures, reports stay local.
- **Owned files:** `docs/ai-dlc/roadmap/persona-realism.md` (state lines only — coordinate with T6 if concurrent), adjudication note in ledger
- **Done when:** every answer has an adjudicated status; follow-on tickets (if any) filed as roadmap NEXT items only.
