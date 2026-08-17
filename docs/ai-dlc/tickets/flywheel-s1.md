# Tickets — flywheel-s1 (spec: ../specs/flywheel-s1.md rev 2)
status: approved (owner, 2026-08-05 — "I approve. /ai-org:build")

Routing per the model-routing rule: T1–T3 are judgment/protocol writing → director (this
session) authors directly, no spawn. T4–T5 are well-scoped single-ticket implementation →
`implementer` (sonnet). T6 is verification + git ceremony → director. Dual fan-in review
(refuter + Codex Sol) over the T4+T5 diff before T6 commits.

| # | Ticket | Owns (single owner) | Depends on | Done-condition (runnable) |
|---|---|---|---|---|
| T1 | Author the working agreement (spec D1, all 8 sections) | poker-coach `docs/ai-dlc/contracts/flywheel-working-agreement.md` | — | file exists; contains §1–§8 headings incl. "S1 lands" definition + concurrent-code-session rule |
| T2 | Mirror + status bridge (spec D1 mirror, D5) | poker-analytics `docs/WORKING-AGREEMENT.md`, `docs/FLYWHEEL-STATUS.md` | T1 | `diff` mirror vs canonical = header line only; FLYWHEEL-STATUS has both D5 corrections |
| T3 | Session-R launch brief (spec D2) | poker-coach `docs/ai-dlc/briefs/session-r-s2b.md` | T1 (needs §5/§6 text) | file exists; contains S2b payload, docs-only/no-git rules, handoff clause, launch precondition |
| T4 | Stub scorer + Makefile (spec D3) | poker-analytics `scorer/score_stub.py`, `Makefile` | — (interface fixed by spec) | `make score` on 5k sample exits 0; gate checks exit 1 with clear messages; JSON/stderr contract per D3 |
| T5 | Bridge script (spec D4) | poker-coach `scripts/score_realism.sh` | — (interface fixed by spec) | `test -x`; resolution + error cases per D4 |
| T6 | End-to-end verify, fan-in review, worktree commits (spec Verify-by 1–6; roadmap rider deltas + S1 `[x]`) | poker-coach `docs/ai-dlc/roadmap/bot-realism-flywheel.md` (+ commits in both repos) | T1–T5 + fan-in review | all six Verify-by steps pass; two local commits with verified OIDs; owner handed the pushes |

Parallelizable: {T1, T4, T5} then {T2, T3} — but the whole slice is ≤1 session of work;
sequential single-agent execution is acceptable and simpler. T4 and T5 may go to one
`implementer` each (different repos, disjoint files) or sequentially to one.
