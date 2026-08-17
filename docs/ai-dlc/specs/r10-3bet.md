# Delta spec — R10-3BET: vs-3-bet response differentiation (+ two parallel design passes)

> Slice of roadmap `docs/ai-dlc/roadmap/persona-realism.md` (R10-8 preflop lane, item at `:2042-2055`;
> lane-parallel design passes authorized at `:2318-2321`, owner approved 2026-07-30).
> Contracts: `docs/ai-dlc/contracts/r10-3bet.md`. Review ledger:
> `docs/ai-dlc/ledger/persona-realism-r10-3bet.md`. ICE 7·7·3. **v2 — post dual-review (refuter +
> Codex gpt-5.6-sol), 10 findings folded.**

## Goal (one line)

Author persona-differentiated `vs_3bet` continue/4-bet mixes in all six persona packs so the roster
stops uniformly folding to 3-bets (nit measured 20/20 folds as opener, QQ/AK/TT included); the two
parallel design passes (R9-DEFENCE, R10-TAIL) are ALREADY ANSWERED in existing local reports and only
need Director adjudication.

## Problem (provenance)

- R10-1c / R9-c6: every pack's `vs_3bet` node is a `positions: null` wildcard; nit's covers **AA/KK
  only** — any other class folds 100% at the node (sampler has no fall-through,
  `backend/app/domain/personas.py:76-91`).
- Measured: nit folded 20/20 as opener facing a 3-bet, CI [83.9, 100], holdings on record include QQ,
  AKs, AKo ×3, TT. (Stale-claim guard: "nit folds KK 100%" is WRONG at HEAD — KK is authored
  `call 1.0`; the defect is the missing QQ/JJ/AK tier.)

## Files / interfaces to touch

| File | Change |
|---|---|
| `content/personas/{nit,tag,lag,maniac,calling_station,passive_fish}.json` | Re-author the one `vs_3bet` node per pack (tiers + weights); bump pack `version` |
| `backend/tests/test_pack_range_lint.py` | Co-edit frozen inventory constants (`_ROW_GAPS`, `_WEIGHT_INTERLEAVING`, `_INERT_TOKENS`) — burn down fixed entries, add none silently |
| `backend/tests/test_personas_postflop.py` | New deterministic gate tests (①/②/freeze assertions below) + report-only six-persona fold-to-3bet helper with strata + Wilson CIs; re-record `_GOLDEN_STATS_N200`; re-record maniac cross-val band `test_node_action_first_in_raise_cross_validates_r10_corpus` (`:3679-3717`) if displaced — authorized, this slice is the lane's sole open fixture re-recorder |
| `backend/tests/test_limper_coverage_belt.py` | Re-record `_PRE_M3_FIRES` (`:175-220`) — stream displacement |
| `backend/tests/test_range_estimate.py` | Co-edit tag's pinned exact vs_3bet 4-bet posterior (`:190-198`) to the new authored raise-mass, with provenance comment |
| `backend/tests/data/coverage_baseline.json` (via `test_coverage_baseline.py`) | Re-record (stream displacement) |
| `docs/ai-dlc/ledger/persona-realism-r10-3bet.md` | Provenance + findings + fixture-delta accounting (W5-b4 template) |
| `docs/ai-dlc/roadmap/persona-realism.md` | Mark slice + design-pass state on completion |

**Risk register (touch NOT expected — breach = STOP):** `test_persona_postflop_bands` / BANDS dict
(`test_personas_postflop.py:2382-2400`) — population AF/fold-to-cbet/WTSD bands are frozen to the
single W4-b re-anchor. If any persona's band breaks after the vs_3bet edits, do NOT widen or
re-record: halt the slice and escalate to the owner (refuter R1).

## Authoring requirements (the build ticket)

- Legal action vocabulary at `vs_3bet` is exactly `{fold, call, 4bet}` (`models.py:87`); weights sum
  ≤ 1.0, remainder = implicit fold. **First-match mix semantics — order tiers strongest-first; a wide
  tier placed early shadows narrower tiers below it** (Codex C4-adjacent hazard).
- All six packs get dossier-grounded tiers. Differentiation axes: continue width, 4-bet width/polarity,
  edge slope (RR smooth-edge model: nit cliff-like, station/fish long shallow tail on the CALL side).
- **Frozen identity (owner, 2026-07-30), gate-enforced:** station keeps ZERO `4bet` mass anywhere in
  its `vs_3bet` node; fish's 4-bet mass is EXACTLY AA at 0.5 and zero elsewhere. Their CALL tiers may
  be re-authored. (Deterministic assertions — Codex C4.)
- **Nit 4-bet headroom:** nit's combo-weighted 4-bet share must stay comfortably below tag's ~1.69%
  or gate ② inverts (refuter R3).
- **Targets are conditioned on the ARRIVAL range** (what the persona actually opens/calls then faces a
  3-bet with), NOT uniform-over-169; the old "84–99%" figures are refuter-flagged wrong-denominator.
  Use dossier continue-range descriptions; cite provenance rows verbatim in the ledger.
- Positions stay `null` — opener-position axis is E1-b (LATER). Do not sneak it in.

## Pass/fail (roadmap-fixed, formulas pinned by review)

1. **Defect gate (deterministic, must flip):** nit's authored `vs_3bet` continue weight
   (call + 4bet) on **QQ, AKs, AKo** each > 0. Fails at HEAD (verified by both reviewers).
2. **Preservation (already passing, labeled per R9-3):** AA/KK continue > 0 in every pack;
   combo-weighted 4-bet share ordering **maniac > lag > tag > nit** (HEAD: 7.54/3.17/1.69/0.23%).
   **Share formula (Codex C5): `Σ over 169 classes (combo_count × EFFECTIVE first-match 4bet
   probability) / 1326`** with combo counts 6/4/12 (pair/suited/offsuit) — first-match resolution,
   never summing overlapping tiers twice.
3. **Freeze gates (new, deterministic — Codex C4):** station `4bet` mass = 0 across its node; fish
   `4bet` mass = exactly {AA: 0.5}.
4. **Measurement (REPORT-ONLY, never a CI gate):** six-persona fold-to-3-bet via `NodeActions`
   counters, printed by a NEW report-only helper (existing formatter is pooled + maniac-only — Codex
   C2), stratified per the counter docstring (`test_personas_postflop.py:2579-2591`, corrected labels
   per Codex C1): **cold facers = `first_hits`; opener-conditioned stratum = `all_hits −
   first_hits`** (re-entrants ≈ openers — this is the stratum comparable to external Fold-to-3bet).
   Report both strata with denominators + Wilson 95% CIs in the ledger. n≈20–40/persona underpowered
   — never gate on it.

## Design-pass tickets (parallel — ALREADY WRITTEN, adjudication only)

Both reports exist as local uncommitted docs (discovered at review, Codex C6):
- **R9-DEFENCE** — `docs/ai-dlc/reports/r9-defence-design.md`: answers the **FIVE** questions of
  `roadmap:1868-1905` (spec v1 said six — stale handoff line; the absolute-price tail belongs to
  R10-TAIL), pinned to commit `803e9dc`.
- **R10-TAIL** — `docs/ai-dlc/reports/r10-tail-design.md`: answers both tail questions
  (`roadmap:2056-2072`) with attribution-first method + ticket sketches.

Remaining work = Director reads both, adjudicates their recommendations (accept/reject per answer),
records the adjudication + roadmap state update. NO build work from their answers in this slice; no
fixtures touched (research docs stay local per repo convention).

## Out of scope

`content/preflop/vs_3bet.json` + `test_scenarios.py` (hero drill/grading system — same name, disjoint
consumer; DO NOT TOUCH) · engine/sampler code (`personas.py`, `play.py`, `sizing.py`) · `vs_4bet`
nodes · opener-position axis (E1-b) · W5-b3 · RR generator/RR-HOLES · building anything the design
passes recommend · new arrival-role instrumentation (rejected Codex C1 rider — docstring's ≈opener
approximation is the accepted instrument).

## Constraints (profile invariants + slice law)

Strategy lives in versioned `content/` data, not code · domain core stays import-pure · band VALUES
frozen — fixture re-record is slice-authorized for stream displacement ONLY (itemized in ledger);
frozen postflop BANDS are excluded from that authorization (breach = STOP, see risk register) ·
gate-design rule: already-passing criteria are labeled PRESERVATION, never sold as the defect gate ·
one fixture re-recorder at a time — the build ticket is it; design-pass adjudication records nothing.

## Verify-by

`./scripts/verify.sh` green (backend pytest incl. RR-LINT with co-edited inventory + new gate/freeze
tests + re-recorded fixtures; boot probe OK) · `cd backend && ruff check .` clean · deterministic gate
① demonstrably fails at HEAD~ and passes at HEAD (show both in ledger) · six-persona stratified
fold-to-3-bet grid printed via the new helper (`python -m pytest backend/tests/test_personas_postflop.py
-k node_action -q -s`) and transcribed with Wilson CIs into the ledger · `test_persona_postflop_bands`
still green WITHOUT band edits · design passes: adjudication of both existing reports recorded in the
ledger + roadmap state updated, zero non-doc diffs from them.
