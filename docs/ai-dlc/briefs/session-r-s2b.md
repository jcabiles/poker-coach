# Session-R launch brief — S2b research wave (bot-realism flywheel)

**INERT until the owner launches it.** Launch precondition (working agreement §6): S1 is
merged in BOTH repos (poker-coach + poker-analytics) and the owner has confirmed both.
The owner starts session R by pasting the PROMPT block below into a fresh Claude Code
session in the poker-coach repo.

---

## PROMPT (paste from here down)

You are **session R** — the research session for slice S2b of the bot-realism-flywheel
roadmap. Read first, in order: `docs/ai-dlc/START-HERE.md` →
`docs/ai-dlc/roadmap/bot-realism-flywheel.md` (the S2b entry is your payload) →
`docs/ai-dlc/prd/bot-realism-flywheel.md` §R5 →
`docs/ai-dlc/contracts/flywheel-working-agreement.md` §5 (your protocol).

**Your slice — S2b (verbatim from the roadmap):** problem: architecture bet needs evidence;
prior planning missed known prior art (Alberta CPRG); NLHE-corpus existence unknown ·
outcome-link: phase-3 gate quality + corpus bet · pass/fail: 3 dossiers in
`docs/ai-dlc/research/realism-architecture/` (academic incl. Alberta lineage · commercial
practice · NLHE-corpus gate brief ending GO/PARTIAL/NO-GO with licensing assessment; on
PARTIAL/NO-GO the brief must evaluate the owner-agreed fallback ladder: (i) limit-era data
for era-stable shape parameters only, each with explicit justification, (ii) modern
tracker-site population statistics (aggregates, not hands), (iii) spot-level expert/LLM
elicitation panels, (iv) literature bands as the floor) PLUS a **consumption map** (each
conclusion → scorer / sweep / detection / architecture option / corpus decision /
explicitly-rejected, with evidence grade) · appetite: ~1 week part-time, parallel to
S2a–S4 · no-gos: docs-only session; no data downloads without licensing review.

**Hard protocol (working agreement §5 — binding):**
- Docs-only. Write ONLY under `docs/ai-dlc/research/realism-architecture/`.
- NO git commands, no code, no sims, no edits anywhere else in either repo.
- No downloading any external dataset — licensing review first (ask the owner).
- On any conflict between your findings and the roadmap/PRD: STOP and surface it to the
  owner (tripwires in `.claude/CLAUDE.md`) — do not silently reconcile.
- Finish by writing a **completion note** in your output dir: file list + one-line summary
  each. The director session reviews and commits accepted dossiers — you never commit.

**Context that will save you time:** the DS-methodology lane was moved OUT of S2b into S2a
(don't research it here). The evidence base for why this initiative exists is
`docs/ai-dlc/research/persona-realism-artifacts/remeasure-2026-08-05/SYNTHESIS.md` (local;
§1 adjudicated scores are authoritative). The real-time constraint that kills
per-decision-LLM policies (but NOT small learned models) is ~500 hands/sec sim throughput.
The IRC Poker Database is limit-era — that is exactly why the NLHE gate brief exists.
