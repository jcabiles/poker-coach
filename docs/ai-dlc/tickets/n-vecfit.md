# Tickets — N-vecfit (doc amendment, spec rev 2)

status: approved (owner, 2026-08-03 — serial single-agent build)
spec: `specs/n-vecfit.md` (rev 2) · ledger: `ledger/n-vecfit.md` · base: docs working tree
(code pin b63dfaa; docs cited by anchor text — see spec citation convention)

All tickets are doc edits. No code, no packs, no tests, no fixtures, no git commits (docs stay
uncommitted per initiative practice unless the owner rules otherwise).

## T1 — amend the fit-loop methodology doc

Add "Multi-lever fitting — measured rules" (Rules 1a mispairing/ρ-screen, 1b conditioning,
2 fresh-slopes-with-levers-held + non-monotone guard, 3 noise budget), instrument facts
(incl. line-blind limitation + ≤3-process note), the D7 procedure-slice reading, and the stale
`:1337-1480` citation fix; retouch steps 2–4 to reference the section; leave D11 untouched.
- Owned file: `docs/ai-dlc/contracts/persona-realism-fit-loop.md`
- Acceptance: every number traces to `reports/n-vecfit-premise.md` (post-corrections values only:
  6v5/7v9, ~1.45×, 1.35 units) or `contracts/n-vecfit.md`; D11 text byte-unchanged.
- Done-condition: `grep -c "Multi-lever fitting" docs/ai-dlc/contracts/persona-realism-fit-loop.md`
  ≥ 1 AND `grep -c "1337-1480" docs/ai-dlc/contracts/persona-realism-fit-loop.md` = 0
  AND traceability sweep clean (T3 verifies).

## T2 — roadmap: N-vecfit entry rewrite + consumer handoff

Rewrite the N-vecfit bullet (anchor "N-vecfit — make the fit loop vector-valued", ~:2001):
premise unsupported-where-tested (scope qualifier verbatim), owner reshape, confirmed facts kept,
**the 4-item R9-LOOSEFIT handoff enumerated** (derived fold/raise-share stats · cross-persona
separation design · own ρ+conditioning check (station 14.3, maniac stickiness surface) · posture
decision incl. `line_aware` passthrough). Update ~:2167 ("Correct order") and ~:2203 (dependency
row) wording; annotate ~:2500 quote with the bracketed refuted-note (no rewrite).
- Owned file: `docs/ai-dlc/roadmap/persona-realism.md`
- Acceptance: all 4 handoff items present, each assigned to R9-LOOSEFIT, none claimed solved;
  chain order string unchanged.
- Done-condition: grep finds all four handoff items AND the annotation at the ~:2500 anchor.

## T3 — peripheral annotations + verify sweep (fan-in)

(a) Annotate `specs/persona-realism-wave-a.md` ~:95-96 (bracketed note, no rewrite);
(b) prepend superseded-note to `contracts/n-vecfit.md` (scan mapped the original tool shape;
§7 tool-need superseded by spec rev 2); (c) run verify-by gates 0–4 from the spec: baseline
snapshot recorded BEFORE T1/T2 start (T3 owner captures it first, then waits), scope check,
traceability sweep over T1+T2 output, stale-promise grep with declared exclusions,
consumer-handoff content check.
- Owned files: `docs/ai-dlc/specs/persona-realism-wave-a.md`, `docs/ai-dlc/contracts/n-vecfit.md`
- Acceptance: gates 0–4 all pass, evidence quoted in the final report.
- Done-condition: gate-by-gate pass list with the grep outputs inline.

## DAG

- T3's baseline snapshot (gate 0) runs FIRST (one command, before any edit).
- T1 ∥ T2 (disjoint files).
- T3 body after T1+T2 (fan-in barrier).
- Gate 5 (dual adversarial review of the final diffs → ledger) at fan-in, after T3.

Parallelizable: T1+T2 only. Total: 3 tickets, all light; a single agent doing T1→T2→T3 serially is
also acceptable at this size.
