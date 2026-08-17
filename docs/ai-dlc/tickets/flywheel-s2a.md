# Tickets — flywheel-s2a (spec: ../specs/flywheel-s2a.md rev 2)
status: approved (owner, 2026-08-05 — "approved. /ai-org:build - go")
routing note: T2 runs as general-purpose(model=opus) — heavy-worker lacks WebSearch/WebFetch.

Routing per the model-routing rule. T1 is meticulous read-only extraction over one complex
module → `contract-mapper` (sonnet, pinned medium). T2 is nuanced research + evidence
grading → `heavy-worker` (opus, pinned high). T3 is running existing tools → director
(trivial timing runs). T4 is the initiative's core judgment work → director (this session).
T5 dual review per standing tiering. T6 git ceremony → director.

| # | Ticket | Owns (single owner) | Depends on | Done-condition (runnable) |
|---|---|---|---|---|
| T1 | Config-model inventory (spec P1: full column list) | `docs/ai-dlc/research/flywheel-s2a/config-inventory.md` | — | every field in `models.py`'s pack/persona models appears with all 10 columns; frozen/structural fields have explicit dispositions |
| T2 | Methods + target-evidence research memo (spec P2, both halves, evidence-graded) | `docs/ai-dlc/research/flywheel-s2a/methods-evidence-memo.md` | — | memo has (i) methods and (ii) per-stat evidence sections; every conclusion carries an evidence grade; no academic/commercial/corpus content (session-R lanes) |
| T3 | One-config benchmark (spec (f) protocol) | benchmark section data (lands in the contract) | — | ≥3 reps of export+`make validate`+stub recorded (mean, variance, hardware manifest); N derivation shown under the 8h cap |
| T4 | Draft the contract, sections (a)–(f) | `poker-analytics:docs/methods/estimand-contract.md` | T1, T2, T3 | verify-by 1–7 of the spec pass on the draft |
| T5 | Contract dual review + adjudication (refuter + Codex Sol) | ledger `docs/ai-dlc/ledger/flywheel-s2a.md` (contract section) | T4 | both verdicts recorded; every HIGH closed or owner-adjudicated (PASS per PRD M2) |
| T6 | Land: owner commit (analytics) + worktree commit `feat/flywheel-s2a` (poker-coach: pointer, roadmap `[x]`, ledger, P1/P2 artifacts) | `docs/ai-dlc/START-HERE.md`, roadmap file | T5 | spec verify-by 8–10 pass; OIDs verified; pushes handed to owner |

Parallelizable: {T1, T2, T3} — disjoint outputs, no dependencies. T4 is the fan-in.
