# Team plan: persona-playstyle-research

- initiative: persona-playstyle-research
- status: approved

## 1. Objective
Ground-truth audit of the 6 bot personas (nit, TAG, LAG, calling station, passive fish, maniac). Three phases: (A) engine behavior review — code that decides how bots play; (B) independent research of each persona's real-life counterpart, one sealed agent per persona, 20-item template; (C) refutation + Director synthesis → plain-language verdict on what the poker engine has right/wrong. Precursor to the user's 500-hand analysis (explicitly OUT of scope — awaits separate command).

## 2. Risk level
medium — read-only analysis + research; no code changes, no pushes.

## 3. Roster
- **Wave A — engine analysis (2 Claude workers, sonnet, concurrent with Wave B):**
  - A1 `general-purpose` (sonnet): extract preflop behavior per persona from `content/personas/*.json` packs + `personas.py` sampler — ranges, frequencies, limp/raise/3bet mixes, position coverage, per persona.
  - A2 `general-purpose` (sonnet): extract postflop decision model from `personas_postflop.py` + `postflop.py` + `table/sizing.py` + `table/postflop_context.py` — levers per persona, merit assembly, softmax law, sizing, context modifiers.
  - Director reads hotspots inline in parallel (persona packs, merit table) — synthesis is mine, extraction is theirs.
- **Wave B — persona research (6 Codex gpt-5.6-sol workers, `model_reasoning_effort=high`, `tools.web_search=true`, concurrent):** one sealed lane per persona; 20-item template; anchored to low-stakes live ($1/$2–$1/$3) + online (micro/low), differences flagged; BLIND to app implementation (gets only archetype one-liner + app context: 9-handed 100bb NLHE cash trainer).
- **Wave C — refutation (3 Claude `refuter` workers, sonnet, concurrent):** 2 reports each, locked checklist. READ-ONLY on git (standing lesson).
- Peak concurrency if A and B overlap: 8 workers. No Opus, no Fable, no foreman.

## 4. Cost line
6 × Codex-high ≈ heavy but the lanes are genuinely parallel and separable (one archetype each, zero shared state); one strong model sweeping 6 archetypes serially costs similar tokens, 6× wall-clock, and cross-contaminates the per-persona takes that item 12 (distinction from adjacent personas) and the sealed-independence design require.

## 5. Mechanism
- Wave A workers return inline; Director folds into synthesis.
- Wave B via REGISTRY.md Codex recipe (`CODEX_HOME` copy per lane, `--sandbox danger-full-access`, background Bash). Each lane's stdout captured to `docs/ai-dlc/research/persona-realism-artifacts/playstyle-research/<persona>.md` (gitignored artifacts dir — research stays local per standing owner decision).
- Sealed briefs: persona one-liner + app context + anchor + 20-item template + anti-yap contract (claims carry source URL + as-of date; "no info found" over invention). Lanes never see each other or the engine.
- Wave C refuters get the report files only; findings → ledger.
- Phase D (Director): reconcile per research skill §5 → read all existing persona docs + engine → findings report + noobify breakdown.

## 6. Review approach
Tier 2 (no executable oracle): cross-family — Codex-authored reports reviewed by Claude refuters with locked checklist (fabricated/misread sources · unsupported leaps · missing counter-evidence · staleness · template completeness · internal contradictions). Findings adjudicated by Director into `ledger/persona-playstyle-research.md`, never auto-folded.

## 7. Stop condition
6 reports refuted + adjudicated; synthesis findings report delivered at `docs/ai-dlc/reports/persona-playstyle-research--findings.md` + noobify verdict in-session. 500-hand analysis NOT started.

## 8. Usage estimate
high

## 9. Assumptions
- Codex CLI logged in; nested-Seatbelt recipe works (proven in this repo).
- Persona roster is exactly the 6 in `archetypes.py`.
- Research artifacts stay local/uncommitted (standing owner decision on research docs).

## 10. Gate evaluation
- Shape rule fired: Wave B = 6 concurrent workers (>5/wave). Peak 8 if A overlaps B.
- Model rules: Codex never gated; no Opus; no Fable in any worker.
- No external side effects (web search is read-only), no irreversible actions, no foreman.
- Verdict: GATED → this plan file; execution only on explicit approval.
