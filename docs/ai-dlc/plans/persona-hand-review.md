# Team plan: persona-hand-review (756-hand realism + hero-play review)

- initiative: persona-hand-review
- status: approved   # owner 2026-07-28, with amendments: graders = Codex Sol (high), Sonnet only for simple lanes, cross-checker = Opus (since Codex authors the gradings)

## 1. Objective
Run the review REVIEW-HANDOFF.md defines over the pinned 756 complete hands of session
`8c04aa55...`: (Report 1) bot-persona realism graded two-layer (arrival + policy) against the
hardened rubric set, with the owner's three named defects specifically investigated (no fear of
draws · absurd call-downs · general unrealism); (Report 2) hero-play review — re-examine all 1102
app-graded hero decisions (632 graded / 470 unmappable) against baseline-good-play and compare
with the app grader's verdicts. Both reports in the owner's per-concept simple-then-technical format.

## 2. Risk level
medium — read-only analysis, no code changes; cost is the main exposure.

## 3. Roster
- Wave 0 (done/ongoing, Director in-session): data pinned (756 complete hands), `hands_756.txt`
  export, `compute_stats.py` aggregate stats, deterministic spot-extractors for themed lanes.
- Wave 1 — bot grading: **8 × Codex Sol, model_reasoning_effort=high, concurrent** (fires the
  >5/wave gate; owner-amended from Sonnet). Sealed briefs; each lane grades ~95 hands (contiguous
  chunk of hands_756.txt) using rubrics/grading-protocol.md + persona rubrics + baseline; writes a
  structured report with the evidence rule (rubric file+item AND hand facts) + headline candidates.
- Wave 2 — themed + hero: **4 × Codex Sol (high) + 1 × Sonnet, concurrent.**
  Codex: 2 themed analysts (draw-fear lane; call-down lane — each fed Director-extracted spot
  lists) + 2 hero postflop lanes (flop 154 decisions / turn+river 173 — deep judgment).
  Sonnet: hero preflop lane (775 decisions, chart-comparison work — the simple lane).
- Wave 3 — verification, **3 × Opus high effort, max 2 concurrent** (Opus rule respected):
  3a concurrent pair — auditor A spot-audits bot-grading lanes (random sample per lane + EVERY
  headline finding); auditor B spot-audits hero + themed lanes. 3b after drafts exist — ONE blind
  Opus cross-family cross-checker over both draft findings docs, locked checklist (misread hand
  facts · rubric misattribution · unsupported leaps · precedence-ladder violations · missing
  counter-evidence). Cross-family holds: Codex authored the gradings, Claude checks.
- Wave 4 (Director in-session, Fable = session model): ledger adjudication, both reports, log.
- **No Fable subagents anywhere** (GATE.md floor; Director's own session context is the only Fable use).

## 4. Cost line
16 workers total ≈ 8 medium-input Sonnet lanes + 5 smaller Sonnet lanes + 3 review agents — the
hand chunks are genuinely parallel and separable; one strong model reading 23.6k lines serially
would blow context and lose per-lane blindness.

## 5. Mechanism
Sealed briefs; lanes never see each other's output. Grading lanes write nothing — findings return
inline; Director owns all files. Review agents are git-READ-ONLY (standing lesson). Artifacts stay
in the gitignored playstyle-research dir. Evidence rule mandatory in every lane contract.

## 6. Review approach
Tier 2 (no executable oracle for realism judgments): Opus spot-audits (maker ≠ checker) + one
blind Codex cross-family pass; all findings → ledger/persona-hand-review.md; Director adjudicates
with pushback, nothing auto-folded.

## 7. Stop condition
Both reports delivered with every headline claim spot-verified; further passes only on a new
question/method/counterexample.

## 8. Usage estimate
high — 16 workers, large inputs (rubrics ~1.2k lines per lane + hand chunks).

## 9. Assumptions
- Pinned set = 756 complete hands (the 757th was in-progress; excluded).
- Sample-level checks use the Director-computed measured stats (stats_756.txt), not pack-derived
  predictions, where the two disagree (they do: e.g. measured nit VPIP 11.2 vs pack-predicted ~28).
- Hero W$SD/winnings not computable from state_json (no payouts recorded) — P/L stays session-level.

## 10. Gate evaluation
Shape rule fired: wave 1 schedules 8 concurrent workers (>5). Model rules: Opus 2 concurrent at
high effort within an approved plan = compliant; Fable never spawned. Verdict: GATED — owner
approval required before execution.
