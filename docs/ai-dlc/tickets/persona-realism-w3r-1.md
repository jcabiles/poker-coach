# W3R-1 tickets — Maniac (+ lag) preflop range cleanup (CONFIG-ONLY)

Spec: `docs/ai-dlc/specs/persona-realism-w3r-1.md`. Content-JSON only; NO engine/lever change. Single owner
(both JSON files belong to this one slice). Behavior change IS intended → seeded fixtures re-record under the
P1/P2a owner-authorized precedent (bands unchanged).

Owned files: `content/personas/maniac.json`, `content/personas/lag.json`, and the re-recorded fixture data files
(golden / coverage_baseline / limper belt) + any new assertion test. Do NOT edit `app/domain/` or any postflop
block.

## T1 — Maniac: REPLACE `vs_rfi` with the 3-tier loose-flat range + delete SB open-limp
In `maniac.json`: (a) REPLACE the `vs_rfi` node's mixes with the approved 3-tier structure (premium 3bet /
strong-playable 3bet-or-flat / wide-marginal flat / rest fold — see spec "Exact edits" for the exact combos +
weights); (b) DELETE the `unopened SB` third mix `{ ... "weights": { "limp": 1.0 } }`. Engine default is fold for
unmatched hands (`personas.py:73/90-91`).
- **Done-condition:** a test asserts `maniac` `sample_preflop_action(facing="vs_rfi")` returns `fold` (never
  `call`) for OFFSUIT trash {J2o, 72o, 92o, Q4o, K5o}; **flats** (returns `call` in >0 of N draws) for tier-2
  {55, 87s, KQs} and tier-3 {K5s, A5o, T9o}; premiums {AKo, QQ}→3bet. And returns `fold` (never `limp`) from
  `unopened SB` for the deleted limp classes {J2s, 32s, K2o, 65o}. Seed-pinned, N large enough that a >0-frequency
  action is reliably observed.
- **Owned:** `maniac.json` + the assertion test.

## T2 — Maniac: position-scaled offsuit-ace open trim
In `maniac.json` `unopened` nodes, first mix only: HJ `A2o+`→`A7o+`, CO `A2o+`→`A5o+`, BTN `A2o+`→`A5o+`.
- **Done-condition:** a test asserts maniac HJ `A6o`→fold and `A7o`→raise-mix; CO/BTN `A4o`→fold and `A5o`→
  raise-mix; and a suited control (`A2s` from each of HJ/CO/BTN) STILL opens (raise-mix) — proving the trim is
  offsuit-tail-only. UTG/UTG1/UTG2/LJ/BB opening ranges assert byte-identical (untouched).
- **Depends-on:** T1 (same file — serialize; do not let a second worker touch `maniac.json`).

## T3 — Lag: delete SB open-limp
In `lag.json` `unopened SB` node, DELETE the third mix `{ "combos": "54s, 43s, 32s, 98o, J9o, T9o", "weights":
{ "limp": 0.7, "fold": 0.3 } }`.
- **Done-condition:** a test asserts `lag` `sample_preflop_action(unopened, SB)` returns `fold` (never `limp`) for
  {54s, 32s, J9o}; lag's other SB mixes and its `vs_rfi` node assert byte-identical (untouched).
- **Owned:** `lag.json` + the assertion test. Independent of `maniac.json` (different file) but same slice/worker.

## T4 — Fixture re-record + S3 band re-anchor + VPIP verification
Re-record the seeded-sim fixtures that observe maniac/lag preflop behavior (golden / coverage_baseline / limper
belt) — behavior changed intentionally, so recorded reference VALUES re-anchor (P1/P2a precedent); tolerance bands
on OTHER personas stay unchanged. Additionally re-anchor the ONE pinned maniac band that codified the removed junk:
`test_persona_stat_bands[maniac]` `vs_rfi-continue` in `test_personas.py` — set a SNUG window around the new
measured continue-rate (do NOT widen it to pass-anything). Touch no other band/persona.
- **Done-condition:** `./scripts/verify.sh` green; **maniac VPIP on the texture-lineup sim ~32–33% (accepted legit
  ceiling; assert a snug window around the measured value AND ≥30%)**; **maniac 3bet% back inside its pinned
  `[12,20]` band** via the tier-2 `3bet:0.45` restore (VERIFY — do NOT edit that band); the limper-rate /
  3bet-pot-rate assertions still hold; `content/` JSON validates; `ruff check .` clean. Report pre/post maniac
  VPIP + 3bet%, the new `vs_rfi-continue` value + the snug band window you set, and which fixtures moved.
- **Depends-on:** T1–T3. No fit-loop (tier-3 freq is a near-dead lever, fixed at 0.9). **If the 3bet% does NOT
  return to `[12,20]` at tier-2 `3bet:0.45`, or VPIP falls below 30%,** STOP and report the measured values.

## Sequencing
T1 → T2 (same file `maniac.json`, serialize) ; T3 independent (`lag.json`) ; T4 last (needs all edits in place).
Single owner / single worker for the whole slice — the two JSON files are one logical change and T4's re-record
must see every edit. No hotspot contention with the `personas_postflop.py` spine (touches no engine code), so
W3R-1 could run parallel to a measurement-only slice, but not split across workers.
