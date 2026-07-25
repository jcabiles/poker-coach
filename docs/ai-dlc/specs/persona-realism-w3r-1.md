# W3R-1 — Maniac (+ lag) preflop range cleanup (CONFIG-ONLY)

**Slice of:** `docs/ai-dlc/roadmap/persona-realism.md` → W3R (bot-review remediation). Adjustment-plan fixes **#1**
(delete any-two `vs_rfi "*"` cold-call + SB open-limps) and **#13** (trim HJ+ offsuit-ace opens). **The root of
hyp-1** (owner flag: "maniac too aggressive with marginal hands"). Harness-independent — content JSON only, no
postflop lever, no engine code.

## Goal (one line)
Stop the maniac cold-calling **any two cards** vs an RFI, stop the maniac + lag SB **open-limping**, and trim the
maniac's weakest **offsuit-ace opens** (HJ/CO/BTN) — so its junk plays no longer feed the postflop barrels the
review flagged (H119/H84/H30/H74).

## Why (the gap / root cause)
The reviewer traced hyp-1 to CONFIG, not the postflop engine. The opening RAISES are already suited>offsuit +
position gated and are NOT the problem. The junk comes from three content leaks:
1. **`vs_rfi "*"` any-two cold-call** (`maniac.json`): a catch-all mix `{call:0.55, fold:0.45}` that flat-calls an
   RFI with literally any two cards (J2o, 72o, …) → those junk hands then barrel postflop.
2. **SB open-limp** (`maniac.json` + `lag.json`): an `unopened SB` mix with `{limp:...}` — a weak, exploitable
   open-limp from the small blind.
3. **Ungated offsuit-ace opens** (`maniac.json` HJ/CO/BTN): opens offsuit aces down to `A2o+`, the weakest tail.

Engine default (verified, `personas.py:73/90-91`): "no matching node/mix => fold." So DELETING a mix makes its
hands fall through to fold — the exact intended effect, no engine change needed.

## Owner decisions (2026-07-24 interview)
1. **Lag IS in scope** for the SB open-limp: delete both `maniac.json` AND `lag.json` SB open-limps. (Only the
   maniac has the any-two `vs_rfi "*"` catch-all — lag's `vs_rfi` is already explicit, untouched.)
2. **Offsuit-ace trim is position-scaled** (matches owner's "early position is worse" intuition): **HJ → `A7o+`**,
   **CO → `A5o+`**, **BTN → `A5o+`** (all currently `A2o+`). Suited aces and the raise-first gating stay untouched.
3. **(build-time revision, 2026-07-24)** The initial plan DELETED the `vs_rfi "*"` any-two mix outright, leaving the
   maniac 3bet-or-fold vs a raise → voluntary-play collapsed to ~24% (the maniac was ~38% pre-edit, NEVER the 43–55
   the plan wrongly targeted — 43–55 is the audit's *aspirational* endpoint needing an opening-range widen). Owner
   chose **Path 2: REPLACE the any-two catch-all with a real loose flat-calling range** — keep the maniac loose vs
   raises, but with legitimate hands (pairs/suited/connected), never any-two. See the new `vs_rfi` structure below.
   The pinned S3 `vs_rfi-continue` band (`test_personas.py`, was `(45,70)` codifying the old any-two behavior) is
   AUTHORIZED for re-anchoring to the new measured value; the "VPIP 43–55" gate is corrected (see Pass/fail).
4. **(build-time finding, 2026-07-24) VPIP structurally caps ~33% with a legit range — owner ACCEPTS ~33%.** Three
   calibrated measurements proved the pre-edit 36% VPIP was produced ENTIRELY by the any-two `vs_rfi` catch-all: in
   a 9-max lineup the maniac rarely faces a lone RFI, so the flat range barely fires (call freq 0.72→1.0 moves VPIP
   ~1pp; ceiling ~33.3%). Reaching 34–38% is physically impossible via flatting — only widening the OPENING ranges
   (Path 3) would, which the owner declined (re-loosens the disciplined junk). **Owner accepts the legit ceiling
   ~32–33%** (≈ passive_fish, far above the 24% collapse; the maniac's identity is aggression + wide opens, not
   junk-calling). Two consequent fixes: (a) restore tier-2 to `{3bet:0.45, call:0.55}` so the maniac 3bet% stays in
   its pinned `[12,20]` band (the 0.45→0.35 drop had pushed it to 10.95%) — this does NOT change VPIP (3bet & call
   both = playing); (b) re-anchor the `vs_rfi-continue` band to the measured ~41%. The 3bet band is NOT re-anchored
   (fixed via tier-2 restore instead — keeps the maniac 3bety rather than weakening the band).

## Scope / files to touch (CONFIG + gated test re-anchor)
- `content/personas/maniac.json` — `vs_rfi` node REPLACED (3-tier flat range) + SB open-limp deleted + HJ/CO/BTN
  offsuit-ace trims (see Exact edits).
- `content/personas/lag.json` — one edit (SB open-limp).
- `backend/tests/test_personas.py` — re-anchor ONLY the `test_persona_stat_bands[maniac]` `vs_rfi-continue` band to
  the new measured value (authorized spec re-anchor, like W3R-2's station-flat flip). Touch no other band/persona.
- Re-record the seeded-sim fixtures that observe maniac/lag preflop behavior (golden / coverage / limper belt), per
  the P1/P2a owner-authorized re-record precedent — behavior IS intended to change here.
- **NO** edits to `app/domain/` (engine), no postflop lever, no `spot_signature()`.

## Exact edits
**`maniac.json`:**
- **`vs_rfi` node** — REPLACE its mixes with the approved 3-tier loose-flat structure (Path 2). The any-two `"*"`
  mix is gone; the maniac now flats a wide LEGITIMATE range and folds only true offsuit trash:
  1. `{ "combos": "TT+, AJs+, AQo+", "weights": { "3bet": 1.0 } }` (unchanged premium 3bet).
  2. `{ "combos": "22-99, A2s+, K9s+, Q9s+, J9s+, T9s, 98s, 87s, 76s, 65s, A9o+, KJo+, QJo, JTo",
     "weights": { "3bet": 0.45, "call": 0.55 } }` — strong playable: 3bet or FLAT (never folds to one raise). The
     `3bet:0.45` is RESTORED (not 0.35) so the maniac's overall 3bet% stays in its pinned `[12,20]` band; VPIP is
     unaffected (3bet and call both = playing the hand).
  3. wide marginal loose flat (WIDENED to hit the ~36% VPIP target — owner chose "widen flats"). Suited:
     `K2s, K3s, K4s, K5s, K6s, K7s, K8s, Q4s, Q5s, Q6s, Q7s, Q8s, J6s, J7s, J8s, T6s, T7s, T8s, 95s+, 85s+, 74s+,
     63s+, 52s+, 43s`. Offsuit: `A2o, A3o, A4o, A5o, A6o, A7o, A8o, K8o, K9o, KTo, Q8o, Q9o, QTo, J8o, J9o, JTo,
     T8o, T9o, 98o, 87o, 76o`. Weights `{ "call": 0.9, "fold": 0.1 }` — **the call freq is a near-DEAD lever
     (0.72→1.0 moves VPIP ~1pp; the flat range barely fires in a 9-max lineup). Fixed at 0.9 (near the ~33% legit
     ceiling); NO fit-loop needed — just verify VPIP lands ~32–33%.**
  Every hand not matched by a mix folds (engine default). Offsuit trash (J2o, Q7o, 72o, K5o, 92o …) → fold. Mix
  order matters (first-match-wins): premiums 3bet, strong playable 3bet/flat, marginal flat, rest fold.
  **NOTATION (parser limit — prior worker HIT this):** `app/domain/content/notation.py` supports dash-ranges ONLY
  for pairs. Non-pair suited/offsuit dash tokens (`K2s-K8s`) raise `unsupported range token` — so they are
  ENUMERATED above. The `X Ys+` gapper forms (`95s+, 85s+, 74s+, 63s+, 52s+`) parse natively. Do NOT reintroduce
  non-pair dash ranges.
- **`unopened SB` node** — DELETE the third mix `{ "combos": "J2s, T3s, 32s, 42s, 52s, K2o, Q4o, Q5o, J6o, T6o,
  87o, 76o, 65o", "weights": { "limp": 1.0 } }`. (Keeps the two `{raise}` mixes; those hands now fold.)
- **`unopened HJ` node** — in the first mix, `A2o+` → `A7o+` (drops A2o–A6o).
- **`unopened CO` node** — in the first mix, `A2o+` → `A5o+` (drops A2o–A4o).
- **`unopened BTN` node** — in the first mix, `A2o+` → `A5o+` (drops A2o–A4o).

**`lag.json`:**
- **`unopened SB` node** — DELETE the third mix `{ "combos": "54s, 43s, 32s, 98o, J9o, T9o", "weights": {"limp":
  0.7, "fold": 0.3} }`. (Keeps the `{raise}` + `{raise,fold}` mixes; those hands now fold.)

## Pass/fail
- **No any-two cold-calls:** for `maniac`, `sample_preflop_action(facing="vs_rfi")` on OFFSUIT trash (J2o, 72o,
  92o, Q4o, K5o) returns `fold` (never `call`) — no mix matches them.
- **Real hands still flat vs RFI (Path 2):** maniac flats (returns `call` in >0 of N draws) for tier-2 hands
  (e.g. `55`, `87s`, `KQs`) and tier-3 hands (e.g. `K5s`, `A5o`, `T9o`); premiums (`AKo`, `QQ`) still 3bet.
- **No SB open-limp:** neither maniac nor lag ever returns `limp` from `unopened SB` (all limp mass gone → fold).
- **Trimmed opens fold:** maniac HJ `A6o` folds (was raise); CO/BTN `A4o` folds; **but** maniac HJ `A7o`, CO/BTN
  `A5o`, and ALL suited aces (`A2s+`) still open — the trim is offsuit-tail-only.
- **Maniac VPIP ~32–33% (legit ceiling — accepted):** measured on the texture-lineup sim (seat-8, seed 20260710,
  the calibrated method — reproduces the ~24% collapse + ~36% pre-edit exactly). Ground truth: calling_station ~47%
  is the actual loosest; passive_fish ~33–35%; maniac pre-edit 36% was the any-two junk. **Accept ~32–33%** (above
  the 24% collapse, ≈ the fish). Assert VPIP is in a snug window around the measured value AND ≥ 30% (well above the
  collapse). Drop the wrong "43–55" / "≥34" / "highest-VPIP" clauses.
- **3bet band stays green via tier-2 restore (NOT re-anchored):** with tier-2 `3bet:0.45`, `test_persona_stat_bands
  [maniac]` 3bet% must land back inside its pinned `[12,20]` — verify, do NOT edit that band.
- **`vs_rfi-continue` band re-anchored:** UPDATE ONLY that band in `test_personas.py` to a snug window around the
  measured continue-rate (~41%). Authorized (the old `(45,70)` codified the removed any-two behavior). Do NOT widen
  to "pass anything"; touch no other band/persona.
- **Untouched nodes byte-identical:** UTG/UTG1/UTG2/LJ/BB opens, `vs_limpers`, `vs_3bet`, `vs_4bet`, all suited
  ranges, and the entire `postflop` block unchanged.

## Out of scope
No postflop lever/engine change · do NOT touch the correctly-gated EP (UTG–LJ) opens or suited-ace ranges · do NOT
touch the maniac `vs_limpers` limp (that's limping BEHIND limpers, a milder/defensible play — only the SB
OPEN-limp is deleted) · no lag `vs_rfi` change (already explicit) · no band re-anchor of population WTSD/AF (W4-b).
Note (out-of-scope observation): after the HJ→A7o+ trim, maniac UTG2 (`A6o+`) is momentarily looser than HJ — a
pre-existing minor non-monotonicity the owner scoped to HJ+; left alone.

## Invariants honored
Strategy lives in versioned `content/` data (this is a pure content edit) · domain core untouched · softmax law
untouched (JSON weights only; the engine still clamps+normalizes+`rng.choices`) · `spot_signature()` frozen ·
results stay freq+EV · every fixture re-record is the AUTHORIZED consequence of an intended behavior change (P1/P2a
precedent), tolerance BANDS unchanged.

## Verify-by
`./scripts/verify.sh` green after fixture re-record; the pass/fail assertions above hold; `content/` JSON still
validates against its schema; `cd backend && ruff check .` clean. A diff review confirms ONLY the five listed mixes
changed across the two JSON files and nothing in `app/domain/` or `postflop` blocks.
