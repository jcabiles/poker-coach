# START HERE — poker-coach AI-DLC orientation (updated 2026-10-03)

One page for a fresh session (any model tier). Read top to bottom; follow links only as needed.

## What this initiative is (durable — for live status, see below)

**Two roadmaps are active as of 2026-10-03. Ask the owner which one to work on before picking
up any slice.**
- **`roadmap/bot-realism-6max.md`** — bots at the 6-max table play like live $1/$2 players.
  Ledger: `ledger/bot-realism-6max.md`.
- **`roadmap/coach-math.md`** — the coach's poker math is correct, measured by a 25-spot
  textbook test. Ledger: `ledger/coach-math-roadmap.md`. Evidence:
  `reviews/coach-math-audit-2026-10-03.md`.

The **phone access + 6-max** roadmap (`roadmap/phone-and-6max.md`, approved 2026-09-18) is
built; its remaining items are checks the owner owes, not builds.

The **bot-realism flywheel** (`roadmap/bot-realism-flywheel.md`, PRD in `prd/`) governed the
repository through 2026-09-18 and is not closed, only superseded as the lead initiative: it has
exactly one unticked box, two-mode Simulate (Training vs Challenge), which stays open until the
owner plays a Challenge-mode session and reaches its hand-200 threshold. The phase-3
fix-vs-overhaul question it raised was decided 2026-08-15 (ruling A: fix the current bots). The
persona-realism roadmap that preceded the flywheel remains **PAUSED** — history only, its two
NEXT items (`T-cover`, `T-agentcoach`) blocked until the flywheel's finale play session closes.
Everything doubles as the owner's analytics/DS portfolio via the **poker-analytics** repo
(poker-coach produces data; poker-analytics produces judgment).

## Where are we right now — read the ROADMAP, not this file

**Current position = the first unchecked `[ ]` box in whichever active roadmap the owner
names** (each box
carries a dated progress note when work is in flight). Checkboxes and their notes are updated
INSIDE each slice's landing commit, so the committed roadmap is exactly as current as the last
merge. This file deliberately does NOT narrate slice-by-slice status — a committed narrative goes
stale between merges and misleads fresh sessions (it did, repeatedly, before this rule).
**Working tree beats committed copy:** in-flight work exists as deliberate uncommitted
riders; when the checkout disagrees with `git show HEAD`, trust the checkout and STOP
before "cleaning" anything. `/ai-org:*` skills are owner-invoked only.

## Reading order

1. `profile.md` — stack, verify commands, invariants, `active:` initiative.
2. The active roadmap the owner names (`roadmap/bot-realism-6max.md` or
   `roadmap/coach-math.md`); resume from its first `[ ]`.
3. That roadmap's ledger — review rounds and the findings behind the roadmap.
4. Still touching bot-realism-flywheel work (its one open box, or the paused persona-realism
   items behind it)? Read `roadmap/bot-realism-flywheel.md`, `prd/bot-realism-flywheel.md`, and
   `poker-analytics:docs/methods/estimand-contract.md` (the S2a methods & estimand contract,
   v2.3, dual-review PASSED 2026-08-05 — S3–S6 design MUST cite it; changes are amendments, never
   silent edits) first.
5. Working in poker-analytics too? Read `poker-analytics:docs/FLYWHEEL-STATUS.md` FIRST —
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
