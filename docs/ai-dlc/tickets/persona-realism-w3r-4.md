# W3R-4 tickets — multiway busted-bluff decay + middle-pair call base (#7, #11)

Spec: `docs/ai-dlc/specs/persona-realism-w3r-4.md`. Single owner/worker — both are small `personas_postflop.py`
edits sharing one AF re-measure + fixture re-record. **#14 SPLIT OUT** (its own taxonomy slice — do NOT touch
`_made_bucket`). Behavior change intended for #7 (multiway) + #11 → seeded fixtures re-record (P1/P2a). The
`_CALL_BASE[MIDDLE_PAIR]` value is a FIT SEED — measured to target, never dropped in. NO new lever/bucket, grader
frozen.

Owned files: `backend/app/domain/personas_postflop.py` (line 675 + line 266 ONLY), `backend/tests/test_personas_postflop.py`
(new multiway-busted-decay test + any assertion #11 legitimately re-pins), the re-recorded fixture data files.

## T1 — #7 multiway busted-river-bluff decay
At `personas_postflop.py:675`, scale the busted-draw river bluff add-on by the multiway factor already applied to the
generic bluff mass at line 650: `bluff_mass += _BUSTED_RIVER_BLUFF.get(context.busted_draw, 0.0) *
pf.multiway_bluff_damp ** max(opponents - 1, 0)`. Apply ONLY the multiway factor — the busted bluff must STILL be
added AFTER the `_STREET_AGG_MULT` decay (line 673) so it survives the street decay (its W3-c purpose). Add a NEW
test: for a persona with `multiway_bluff_damp < 1`, the river busted bluff mass strictly DECREASES from 1 opponent
to 3 opponents; heads-up (opponents=1) is BYTE-IDENTICAL (factor `**0 = 1.0`).
- **Done-condition:** the multiway-decay test passes; heads-up busted bluff byte-identical; the existing busted-bluff
  / W3-c tests stay green.
- **Owned:** `personas_postflop.py:675`, the new test.

## T2 — #11 middle-pair call base trim
Lower `_CALL_BASE[MIDDLE_PAIR] 0.60 → ≈0.52` (`personas_postflop.py:266`). FIT SEED — tune so naked middle pair calls
marginally less AND no persona's AF/WTSD/fold-to-cbet band busts.
- **Done-condition:** value set; report the per-persona re-measured AF. **HARD-STOP:** if no value in ≈0.48–0.56 keeps
  every persona in band, STOP and report (band re-anchor is an owner decision — §7, W3R-2 exception was fish+station
  only).
- **Owned:** `personas_postflop.py:266`.

## T3 — Fixture re-record + verify green
Re-record the seeded fixtures the #7/#11 change moves (golden / coverage_baseline / limper belt). Report per-persona
re-measured AF, confirm each IN its existing frozen band (NO re-anchor). Verify green.
- **Done-condition:** `./scripts/verify.sh` green; every persona's AF/WTSD/ftc band passes IN-BAND; `content/` JSON
  validates; `ruff check .` clean. Report fitted `_CALL_BASE[MIDDLE_PAIR]`, per-persona AF, which fixtures moved.
  **HARD-STOP** as in T2 if any band busts.
- **Depends-on:** T1, T2.

## Sequencing
{T1 busted-decay, T2 middle-pair} co-measured (shared file + fixture re-record) → T3 (re-record + verify). Single
owner/worker. Two localized engine edits (lines 675 + 266) — no `_made_bucket`/taxonomy edit, so no hotspot
contention with the split-out #14 slice or W3R-7.
