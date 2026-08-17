# Handoff prompt — next session (written 2026-08-05, after N-DRAWLOOSE merged as #168)

Paste everything below the line.

---

Continue the bot-realism flywheel in poker-coach.

⛔ READ BEFORE ACTING — do not answer "what's next" or propose work from context
or memory. A previous session skipped this and recommended a re-measure that had
already been done, from a lane the owner had paused:
  1. docs/ai-dlc/profile.md — confirm `active:` is bot-realism-flywheel
  2. docs/ai-dlc/START-HERE.md — orientation, glossary, hard rules (corrected
     2026-08-05; if it disagrees with the roadmap again, the roadmap wins and
     you fix START-HERE)
  3. docs/ai-dlc/roadmap/bot-realism-flywheel.md — governing plan
  4. docs/ai-dlc/prd/bot-realism-flywheel.md — goal, non-goals, ✅/⚠️/🚫
  5. docs/ai-dlc/contracts/flywheel-working-agreement.md §5 — session protocol
  6. poker-analytics:docs/methods/estimand-contract.md — v2.3, 680 lines, dual-
     review passed. S3–S6 design MUST cite it; changes are amendments, never
     silent edits. I did not read it — nothing below overrides it.
  7. Touching poker-analytics? Read its docs/FLYWHEEL-STATUS.md FIRST; that
     repo's session memory knows nothing about this repo's decisions.

STATE: S1 ✅ · S2a ✅ · **S2b DELIVERED but NOT reviewed, NOT committed, NOT
ticked** · S3–S6 unstarted. The old persona-realism roadmap is PAUSED (history
only); N-DRAWLOOSE merged as #168 and closed that lane. Build no persona-fix or
pack-value change until the phase-3 ceiling verdict — `git diff` on
backend/app/domain/ and content/ must stay clean.

## DO THESE IN ORDER

**(1) Director fan-in on S2b — this is the actual next action, and it is yours,
not a spec or build verb.** Session R delivered four dossiers plus
COMPLETION-NOTE.md into docs/ai-dlc/research/realism-architecture/ (plus `_raw/`
worker outputs). Per working agreement §5, R never commits; the director reviews
and commits accepted dossiers from a worktree. So: read all four, adjudicate
them the way reviewer findings are adjudicated here (verify before accepting,
never auto-fold), decide whether `_raw/` is committed for traceability or
dropped as working material, commit what you accept, and tick S2b on the
roadmap. Headline: the corpus gate brief returns **PARTIAL** — NO-GO on a
licensing-clean corpus of human NLHE *hands* (structural blocker, not lack of
effort), but modern archetype-segmented human *statistics* are freely available,
and that is what the target registry consumes. It says the NO-GO is a
licensing/ethics call rather than a technical one, and that a real answer would
need legal review nobody is buying. **It requires ONE owner ruling to close —
surface it.**

**(2) Check whether S2b amends S2a before speccing S3.** The consumption map
routes 53 conclusions to destinations including the estimand contract. If any
land there, they are amendments to a dual-reviewed doc, not edits — handle them
as such, and expect the corpus ruling to reshape the target registry (the
registry is exactly what a hands-NO-GO / stats-PARTIAL split changes).

**(3) THEN `/ai-org:spec S3` — spec, not build.** S3 has no spec and no tickets;
docs/ai-dlc/{specs,tickets}/ contain flywheel-s1 and flywheel-s2a only.
(`specs/simulate-s3.md` is a different, older epic — do not be misled by the
name.) So the sequence is `/ai-org:spec S3` → it stops at Gate 2 with a spec and
a ticket plan → owner approves → `/ai-org:build`. Never build against a plan
whose gate has not been approved, and never invoke either verb yourself: all
`/ai-org:*` skills are owner-invoked. If the work looks spec-scale, say so and
wait.

## WHAT S3 IS, AND ITS ONE DELICATE PART

A computable per-persona realism score — graded distance over the S2a target
registry — that runs on the sim50k export in under 5 minutes and is
deterministic given a seed. Export (local, gitignored):
research/persona-realism-artifacts/remeasure-2026-08-05/sim50k/ →
hands.parquet, decisions.parquet, seat_outcomes.parquet.

The delicate part is validation, and S2a already pre-registered it: only 13
expert ratings exist, so it is DIRECTIONAL ONLY — report Spearman rho with a CI
and p-value plus a sign-agreement check, at most ONE pre-registered revision,
and if it still fails a STOP-GATE fires: the score stays an "exploratory
surrogate," S5 may not issue a score-only ceiling verdict, and convergent
evidence from the detection pilot becomes required. Record the score's status in
its own output. Follow S2a's plan exactly rather than improvising.

## HARD RULES THAT BITE

· NEVER parse rendered hand text for statistics — replay state_json / Parquet.
  A rendered-text parse already produced a FAIL-grade artifact; the post-mortem
  is in stage0.py's header.
· Targets come from external human evidence only, never the internal theory
  contract.
· Live cells with n<30 defer to the 50k sim.
· Scores are non-authoritative for ANY conclusion until validation passes; S4
  may use them only as reproducibility smoke data.
· Counterfactual configs are EPHEMERAL overrides validated through the real pack
  model — "read-only packs" means nothing is committed, not that overrides are
  banned.

## SCOPE VALVES — appetite is a cap; cut scope, not quality, in this order
S5's confirmatory study is deferred unless the pilot is ambiguous · S2b's
commercial lane is the first research cut (moot, it delivered) · S6's pilot may
shrink judge count but NEVER its blinding.

## TRIPWIRES — STOP and tell the owner, never silently reconcile
A ticket or spec contradicts the active roadmap or PRD, or cites a paused doc as
authority · the two repos disagree about interface, ownership, or priorities ·
research undercuts a planned slice's premise · the work doesn't serve the
roadmap's north star · you are about to re-derive a decision a doc already
records differently.

## PROCESS
Apply GATE.md before any fan-out. Dual review is the standing default — and pair
a gate-based reviewer with a domain reviewer: on the last shipped slice the
refuter verified everything measurable and PASSED it, while the theory reviewer
FAILED it on the one behaviour no gate measured. Reviewers are git-READ-ONLY,
and assume a reviewer with write access will write anyway (Codex edited the
engine despite an explicit review-only brief; it restored correctly, but verify
the tree). Own worktree, immutable-OID push, bare git commands, no pipes where
success matters, absolute paths, PR on feat/*, never merge.

## TOOLING — each of these costs an hour if rediscovered
· Pushes have NEVER worked from this sandbox; hand the push and PR to the owner.
  Reads need the global config nulled, because a global
  `url.git@github.com:.insteadOf` forces SSH and `-c url....insteadOf=` does not
  clear it (insteadOf is multi-valued; -c appends):

      GIT_CONFIG_GLOBAL=/dev/null GIT_TERMINAL_PROMPT=0 \
        git -c credential.helper='!gh auth git-credential' \
        fetch https://github.com/jcabiles/poker-coach main

  The repo squash-merges, so branch commits are never ancestors of main.
· The Bash sandbox deny-list grows with every registered git worktree until it
  exceeds the OS exec limit and kills EVERY command mid-session. /sandbox does
  not fix it — prune from a terminal outside Claude Code, then restart. Ask the
  owner to clean up BEFORE starting.
· A backend suite run is ~4m40s. Redirect to a file and READ the file; never
  read a result from a piped exit code or a `| tail`.
· A Python script run outside a worktree measures the WRONG code — sys.path[0]
  is the script's directory, so imports resolve through the venv's editable
  install to the main checkout, silently. Print `__file__` and check it.
· docs/ai-dlc/ is largely UNCOMMITTED by initiative practice, so it will not
  exist inside a fresh worktree. Read it by absolute path.

## OPEN, FOR THE OWNER
The corpus ruling S2b's gate brief requires · whether pylon-analytics vs
poker-analytics is settled (only poker-analytics exists on disk and every path
points at it) · whether `_raw/` is committed or dropped.
