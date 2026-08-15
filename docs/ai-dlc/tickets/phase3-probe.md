# Tickets — judge-bias probe (spec: specs/phase3-probe.md)

Sequential except where noted; single implementer (main session, post-setup).

1. **P1 — rule-breaking policy.** `backend/tools/probe_policies.py` (tools/, NOT
   app/domain — keeps experiment code out of the product core; purity test untouched):
   engine-legal illogical action policy. Done when: legality test passes 500 simulated
   hands (no CanonicalHandError at render). Owns: `backend/tools/probe_policies.py`.
2. **P2 — stimulus builders.** Self-play stimuli (rule-breaker / T1 / production) +
   pinned-snapshot human-window re-derivation per spec Behavior §1 (assert session_id,
   filter `hand_no <= pins.human.n_pinned`, assert candidate-table match, choose
   deterministically from valid-minus-selected), phase-set focus seats. Done when: each
   returns a 30-hand renderable window; T1 hash assertion fires on tamper; candidate
   re-derivation reproduces the deck's recorded table exactly. Owns:
   `backend/tools/detection_probe.py` (builders section).
3. **P3 — probe pipeline + stub dry-run.** Fail-closed path guard (spec §1b, tested) +
   render + leak audit + stub-vendor judging + verdict report + ledger writer;
   separate `probe/` output tree. Done when: stub end-to-end test green and
   deterministic; path-guard tests refuse live-tree paths and deck==out. Owns: rest of
   `detection_probe.py`, `backend/tests/test_detection_probe.py`. Depends: P1, P2.
4. **P4 — paid probe episode.** Run against `claude-sonnet-5`, ≤40¢ total including
   iteration; log every call; report verdicts against matrix §3's preregistered
   interpretation. Done when: 4 verdicts recorded + interpretation stated, or budget
   exhausted with a written stop report. Depends: P3 + owner's one-time setup script.
5. **P5 — ledger + hand-off.** Findings ledger complete; results folded into the
   decision-matrix ruling section for owner ratification. Depends: P4.
