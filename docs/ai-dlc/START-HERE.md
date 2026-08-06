# START HERE — poker-coach AI-DLC orientation (updated 2026-08-05)

One page for a fresh session (any model tier). Read top to bottom; follow links only as needed.

## Current state in five sentences

The villain bots were re-measured 2026-08-05 at **4.8/10 realism** (up from 4.2) after an
expensive hand-tuning program; the owner halted all further persona-fix work. The governing
initiative is now the **bot-realism flywheel** (`roadmap/bot-realism-flywheel.md`, PRD in
`prd/`): build a cheap measurement loop (computable realism score + seeded sim sweeps +
detection protocol), answer whether the current dial architecture can EVER reach human-band
behavior (the "ceiling question"), and only then decide fix-vs-overhaul (phase-3 gate). The
old `persona-realism.md` roadmap is **PAUSED** — history only. Everything doubles as the
owner's analytics/DS portfolio via the **poker-analytics** repo (poker-coach produces data;
poker-analytics produces judgment). The roadmap is drafted and dual-reviewed but **awaits the
owner's explicit approval**; on approval the next action is `/ai-org:spec S1` (owner-invoked).

## Reading order

1. `profile.md` — stack, verify commands, invariants, `active:` initiative.
2. `roadmap/bot-realism-flywheel.md` — the governing plan; resume from the first `[ ]`.
3. `prd/bot-realism-flywheel.md` — goal, non-goals, hard boundaries (✅/⚠️/🚫).
3b. `poker-analytics:docs/methods/estimand-contract.md` — the S2a methods & estimand
   contract (v2.3, dual-review PASSED 2026-08-05). **S3–S6 design MUST cite it**; changes
   to it are amendments, never silent edits.
4. `research/persona-realism-artifacts/remeasure-2026-08-05/SYNTHESIS.md` — the evidence base.
   §1's **adjudicated** scores are authoritative; the seven `report_*.md` files carry banners
   because Sol reviews corrected parts of them.
5. `ledger/bot-realism-flywheel-roadmap-review.md` — why the roadmap says what it says.
6. Working in poker-analytics too? Read `poker-analytics:docs/FLYWHEEL-STATUS.md` FIRST —
   that repo's session memory knows nothing about these decisions.

## Glossary (plain language for the roadmap/PRD jargon)

- **Flywheel** — the sim→score→tweak loop that replaces token-expensive agent measurement.
- **Realism score** — computed distance between a bot's ~20 stats and human target bands;
  an *exploratory surrogate* until its validation plan passes (only 13 expert ratings exist).
- **Detection rate (north star)** — blind judges label seats human vs bot; perfect realism =
  coin-flip. v0 is a single-player *pilot* (owner's own hands), NOT the real baseline.
- **Operational ceiling** — the best realism reachable by tuning dials *within a declared
  search space and compute budget* — deliberately NOT a claim about the architecture in total.
- **Estimand contract (S2a)** — the doc that pins, before building: what's swept, what
  "reachable" means, the REACHABLE/NOT-REACHABLE/INCONCLUSIVE rule.
- **Winner's curse guard** — best-of-sweep configs must be re-run on fresh seeds before any
  "reachable" claim (the best of N noisy tries is biased upward).
- **DoE probes** — designed experiments (vary one dial / pairs) to say WHICH mechanism blocks
  a failing stat, not just that it fails.
- **Goodhart guard** — detection may not be improved by making bots bland; archetype
  separation and coaching value are floors.
- **Counterfactual config** — a validated, EPHEMERAL pack override used for sweeps;
  "read-only packs" means nothing is ever COMMITTED.

## Hard rules that bite

- **No persona-fix code or committed pack changes** until the phase-3 gate (`git diff` on
  `backend/app/domain/` + `content/` must stay clean).
- **Never parse rendered hand text for statistics** — replay `state_json` / Parquet
  (a rendered-text parse produced a FAIL-grade artifact; see `stage0.py` header).
- **Targets from external human evidence only** — never the internal theory contract.
- **Live cells with n<30 defer to the 50k sim.**
- Tripwires (when to STOP and tell the owner) live in `.claude/CLAUDE.md` — conflicts between
  docs, repos, tickets, or research and this plan are surfaced, never silently reconciled.

## Cleanup obligation (owner ruling 2026-08-05)

When the flywheel roadmap completes: sweep and delete/banner everything no longer needed —
superseded reports and spot lists, sim exports, interim status docs, stale memory entries.
Do not let this repo accumulate misleading history.
