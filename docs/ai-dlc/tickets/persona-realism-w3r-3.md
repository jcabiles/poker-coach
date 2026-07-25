# W3R-3 tickets — spr_commit ladder + ace-high call base + call_looseness tidy (#4, #5, #12)

Spec: `docs/ai-dlc/specs/persona-realism-w3r-3.md`. Single owner/worker — the ace-high base constant is GLOBAL, so
#4/#5 share one roster-wide AF re-measure + fixture re-record; #12 rides the same re-record (byte-identical).
Behavior change IS intended for #4/#5 → seeded fixtures re-record (P1/P2a). Dial + base-constant magnitudes are FIT
SEEDS — measured to target, never dropped in. NO merit-table structural change, no new lever/bucket, grader frozen.

Owned files: `content/personas/passive_fish.json`, `content/personas/maniac.json`, `content/personas/tag.json`,
`content/personas/nit.json`, `content/personas/lag.json`, `backend/app/domain/personas_postflop.py` (the
`_CALL_BASE[ACE_HIGH]` constant at line 256 ONLY — no other engine edit), `backend/tests/test_personas_postflop.py`
(new ace-high-float test + any assertion the base change re-pins), the re-recorded fixture data files.

## T1 — spr_commit ladder (#4)
Set `passive_fish` `spr_commit 2.0 → 1.4` and `maniac` `spr_commit 4.0 → 3.3`. These are FIT SEEDS. Confirm the
commit-order fix: fish (1.4) now reaches commitment at a LOWER SPR than the station (1.5) — i.e. the fish commits
LATER, not earlier. If a behavioral commit-order test is derivable (a spot where the old fish 2.0 committed and the
new 1.4 does not, vs the station), add it; otherwise the dial order + the T4 AF-in-band check is the gate.
- **Done-condition:** fish `spr_commit` < station `spr_commit`; both packs validate; report any behavioral assertion added.
- **Owned:** the two JSONs.

## T2 — ace-high call base (#5), the GLOBAL constant — ⚠️ DROPPED / RE-ROUTED (owner, 2026-07-24)
**NOT BUILT in W3R-3.** Building it hard-stopped: the global `_CALL_BASE[ACE_HIGH] 0.40→0.22` cut folds the fish
past its α exploitability ceiling (fish range is ~⅓ ace-high, already on the ceiling from W3R-2). Re-routed to a
facing-a-raise-scoped ace-high fold damp in W3R-6 (the H117 float is a facing-action bug, not a global-calling bug).
The original T2 text is retained below for the record only.

### (SUPERSEDED) T2 — ace-high call base (#5), the GLOBAL constant
Lower `_CALL_BASE[ACE_HIGH]` `0.40 → ≈0.22` (`personas_postflop.py:256`), mirroring the A1 `_CALL_BASE[AIR]
0.25→0.08` precedent. FIT SEED — measure and tune the exact value so (a) the new ace-high-float test passes and
(b) NO persona's AF/WTSD/fold-to-cbet band busts (this constant scales EVERY persona's ace-high call merit). Add a
NEW test: naked ace-high (no pair, no draw) facing a RAISE on flop/turn folds at a materially higher normalized
prob than at the old 0.40 base — exact capture-weights path (no sampling noise), `test_size_elasticity_steeper_*`
style; cite H117.
- **Done-condition:** the ace-high-float test passes at the fitted constant; report the value + the per-persona
  re-measured AF. **HARD-STOP:** if no value in a sane range (≈0.15–0.30) both fixes the float AND keeps every
  persona in band, STOP and report — a further band re-anchor is an owner decision (§7: the W3R-2 exception was
  fish+station ONLY; all others frozen to W4-b).
- **Owned:** `personas_postflop.py` (line 256 only), `test_personas_postflop.py` (new test).
- **Depends-on:** none structurally, but co-measured with T1/T3 on the shared fixture.

## T3 — call_looseness tidy (#12), BYTE-IDENTICAL
Author explicit `call_looseness` on `tag`, `nit`, `lag` = each pack's CURRENT `stickiness` (tag 0.6, nit 0.6, lag
0.55) so behavior is byte-identical (the lever already defaults to `stickiness` when unset). This is a documentation
tidy, NOT a behavior target — do NOT use the roadmap's "tag≈0.55" (tag stickiness is 0.6; the 0.55 is a slip). Maniac
stays inheriting (roadmap lists only tag/nit/lag).
- **Done-condition:** the three packs carry explicit `call_looseness` == their prior inherited `stickiness`; the
  seeded fixtures show ZERO behavioral drift attributable to #12 (only #4/#5 move stats); `call_looseness↑`
  monotonicity holds.
- **Owned:** the three JSONs.

## T4 — Fixture re-record + verify green
Re-record the seeded fixtures the #4/#5 change moves (golden / coverage_baseline / limper belt). Report the
per-persona re-measured AF and confirm each is IN its existing (frozen) band — NO re-anchor. Verify green end-to-end.
- **Done-condition:** `./scripts/verify.sh` green; every persona's AF/WTSD/ftc band passes (in-band, not re-anchored);
  `content/` JSON validates; `ruff check .` clean. Report fitted `_CALL_BASE[ACE_HIGH]`, per-persona AF, which
  fixtures moved, and confirm #12 is byte-identical. **HARD-STOP** as in T2 if any band busts.
- **Depends-on:** T1–T3.

## Sequencing
{T1 spr_commit, T2 ace-high, T3 tidy} co-measured (shared global constant + shared fixture re-record) → T4
(re-record + verify). Single owner/worker. One engine-constant edit (line 256) — no structural merit-table change,
so no hotspot contention. The GLOBAL ace-high constant is the risk surface: T2's hard-stop guards a band bust.
