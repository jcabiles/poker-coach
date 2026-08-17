# Handoff — S3 build phase (bot-realism flywheel), poker-coach + poker-analytics

You are taking over immediately AFTER a completed `/ai-org:spec S3` run. The spec phase is
DONE: contract defect verified and ruled on, requirements interviewed, delta spec written,
dual adversarial review run and adjudicated, ticket plan decomposed. The run is parked at
**Gate 2 (the plan gate)** — the owner has NOT yet said "go". Your first job is to take
the owner's approval (or amendments), then implement ticket-by-ticket. Do not write any
feature code before an explicit affirmative ("go", "approved", "build it"). "Looks good"
or a question is not approval.

## 0. READ THESE FIRST, in this order — do not work from this prompt alone

1. `docs/ai-dlc/profile.md` — confirm `active: bot-realism-flywheel`.
2. `docs/ai-dlc/START-HERE.md` — orientation; current position = first unchecked roadmap box.
3. `docs/ai-dlc/roadmap/bot-realism-flywheel.md` — governing plan (committed, now accurate:
   S1 ✅ S2a ✅, S2b `[ ]` with a fan-in-pending note, S3 is the live slice).
4. `docs/ai-dlc/prd/bot-realism-flywheel.md` — goal, non-goals, 🚫 list.
5. **`docs/ai-dlc/specs/flywheel-s3.md` — the delta spec, rev 2. This is your build order.**
   Every A1-item number and pin in it is review-forced; do not water any of them down.
6. **`docs/ai-dlc/tickets/flywheel-s3.md` — the 8-ticket DAG you execute.**
7. `docs/ai-dlc/ledger/flywheel-s3.md` — the 24 adjudicated review findings behind rev 2
   (why each spec clause exists; 22 accepted, 2 narrowed, 0 rejected).
8. `docs/ai-dlc/ledger/flywheel-s3-contract-defect.md` — the defect + owner ruling the
   whole slice implements.
9. `poker-analytics:docs/methods/estimand-contract.md` — v2.3, the binding methods
   contract, COMMITTED (PR #11). Read §a.1, §a.3, §a.5, §b, §e, §f, §g in full. S3
   implements this contract AS AMENDED by ticket T1.
10. `poker-analytics:docs/FLYWHEEL-STATUS.md` + `docs/WORKING-AGREEMENT.md` (§1–§4) —
    read BEFORE touching that repo. `poker-analytics:scorer/score_stub.py` — the stub the
    real scorer replaces (shows manifest gating + output shape).
11. Context if needed: `docs/ai-dlc/research/realism-architecture/` (S2b dossiers —
    consumption map §2.7 lists 12 REJECTED options, do not re-propose) and
    `docs/ai-dlc/ledger/flywheel-s2a.md` (how the contract survived 4 review rounds).

## 1. WHAT WAS DECIDED (owner rulings — do not re-ask, do not re-derive)

- **The contract defect is real and ruled on (2026-08-06).** Contract v2.3 validates a
  per-persona score it never defines (§a.1 pool-only vs §e.2's 12 persona-points).
  Ruling: **two-tier fix** — pool-level D(x) stays the verdict's primary anchor;
  a per-persona score is ADDED, targets anchored on the GGPoker regulars-vs-recreationals
  strata with a constructed+justified mapping; per-persona reported as **average (trend)
  AND floor = worst persona (gate)**; §e.2's validation legs test the per-persona score.
  Recorded as a §g amendment noting "no analyses had run".
- **Guard checkers (§a.5) are IN scope for S3** — owner explicitly chose the larger scope.
- **One combined amendment PR** (defect fix + registry upgrade together), as ticket T1.
- **July-campaign data:** timeboxed half-day feasibility spike first (ticket T6); if the
  July-era engine can't produce a clean export, STOP and bring the owner the
  one-campaign-amendment fallback decision.
- **Export gap:** the determinism guard's context fields don't exist in the export —
  fixed by extending the export tool (T2), NOT by approximating.
- **Mapping content:** drafted by you, attacked by dual review, owner adjudicates at the
  T1 PR — he does NOT want to co-design it in chat first.
- **Dual review = ON** (Claude refuter + Codex `gpt-5.6-sol`; both verified working).
- **OWNER-1 provenance ruling (standing):** GGPoker aggregates MAY be used; four binding
  conditions — every value recorded with exact filter combo (stake·segment·statistic) +
  retrieval date; low-confidence grades; constructed+justified strata→persona mapping;
  limitation disclosed in registry and any public write-up.
- **Metric philosophy (owner discussion, folded into the spec):** north star stays blind
  detection rate; per-bot average = progress metric, per-bot floor = gate (detection is
  weakest-link); community/pool realism is NOT derivative of individual realism (mix
  realism + bot-farm cross-similarity are group-level-only phenomena) and is the
  better-externally-anchored tier.

## 2. WHERE THE RUN IS PARKED — Gate 2, three open flags for the owner

Present these with (or before) the go/no-go; all three were flagged at Gate 2 already:

1. **Appetite re-costed 5–7 days** (roadmap still says 3–4; predates the scope-doubling
   ruling; both reviewers flagged it). Owner yes/no; roadmap wording sync rides T1.
2. **Floor = hard executable constraint** (spec A1.2 makes "worst bot individually under
   its cutoff" a new §a.5 rule — the review showed "floor as reporting" nullified the
   owner's gate intent). Owner confirms or softens.
3. **Owner to-dos:** add `bluffaces.com` to `sandbox.network.allowedDomains` in
   poker-coach `.claude/settings.json` + restart (BLOCKS T1's data fetch — currently the
   sandbox cannot reach it); owner pushes the T1 amendment PR and all poker-analytics
   landings; S2b's branch `feat/s2b-research-wave` (local-only, tip `59184c8`) still
   needs its fan-in + push — separate from S3, don't lose it.

On explicit approval: execute T1 ∥ T2 ∥ T3 (disjoint, parallel-safe), then T4→T5, T6
after T2, T7 last, T8 fan-in. Ticket-by-ticket solo is fine; if fanning out, apply
GATE.md + orchestration-discipline (4-element sealed briefs, one file one owner,
maker ≠ checker; reviewers are git-READ-ONLY — a past reviewer ran `git stash` mid-review
and destroyed work; Codex once edited despite a review-only brief — verify the tree after
every review).

## 3. REVIEW FINDINGS YOU MUST NOT RE-LEARN THE HARD WAY (verified facts)

- **`make validate` hardcodes the sample dir and `datacontract test` reads a fixed
  path** — the "authoritative gate" does NOT check the batch you point it at. T3 fixes
  this (parameterize; bind ODCS model paths to `--dir`; negative test with a corrupted
  batch; never hardcode "150/150" — the count grows with T2's new columns).
- **GGPoker publishes per-street aggression FREQUENCY, not the contract's pinned
  AF=(bets+raises)/calls**, and no c-bet denominator methodology. Per-persona stat
  vectors use definition-compatible subsets only (k_p ≤ 10, χ² df adjusted). NEVER
  translate between statistic definitions.
- **Score orientation is pinned:** S_p = −D_p; validation PASS requires correct sign AND
  p < .05 — a reversed ordering must not pass on |statistic|.
- **Formula identity:** F0 = λ0.8 initial; F1 = the §e.3 pinned revision. Validation
  status is keyed to (formula ID, registry content hash, stat-def version).
- **Anti-leakage:** the 12 expert ratings are public in the contract. Mapping + σ recipes
  must be authored mechanically (no reference to which personas rated high/low), then the
  registry frozen + content-hashed BEFORE any campaign score is computed; breach ⇒ §e
  results relabeled retrospective.
- **decisions.parquet today lacks `engine_node_key`/`hand_class_bucket`** (verified by
  schema read). T2 adds them: nullable; `action='post'` NULL + excluded from determinism
  contexts; preflop node key = an export-side facing-state derivation (only
  `postflop_node_key` exists in domain code — do NOT add domain logic).
- **Output identity:** embed the producer's `_SUCCESS` manifest VERBATIM
  (`producer_manifest`, WORKING-AGREEMENT §4) + registry hash + formula ID + covariance
  artifact ID; byte-identity is over a canonical payload EXCLUDING volatile fields like
  `exported_at`.
- **Seat pooling stays ratified** (9 seats, 3 personas duplicated ⇒ ~2× observations for
  some) — disclosed limitation, NOT a lineup redesign; Σ_sim,p absorbs the precision
  asymmetry.
- **Σ_sim:** per-campaign ≥5-replicate estimates (or shared with preregistered
  justification — the amendment decides, not run time). Never estimate Σ_target/Σ_disc
  from bot runs.

## 4. GIT + SANDBOX STATE (verified this session, 2026-08-06)

- **Both S2a PRs are MERGED:** poker-coach #171 (ledger, research artifacts, roadmap
  S2a-tick, START-HERE fix) and poker-analytics #11 (the contract). Working-tree copies
  verified byte-identical to merged main. The old handoff warnings ("roadmap wrong about
  S2b", "contract untracked") are OBSOLETE.
- poker-coach local `main` = `529b582`, one behind remote `e0a1441` (#171) — content
  already matches; fast-forward when convenient. poker-analytics checkout is on
  `feat/flywheel-s2a`, clean, = the merged content.
- **Pushes have NEVER worked from this sandbox** — owner pushes everything. Reads work
  via: `GIT_CONFIG_GLOBAL=/dev/null GIT_TERMINAL_PROMPT=0 git -c credential.helper='!gh
  auth git-credential' fetch https://github.com/jcabiles/<repo> main` (a global SSH
  insteadOf breaks plain fetch; repo is `jcabiles/...` not `johncabiles`).
- **The sandbox cannot WRITE inside poker-analytics** (fetch there fails on
  `.git/FETCH_HEAD`; file writes blocked). Draft poker-analytics changes in `$TMPDIR` or
  a poker-coach staging area and hand the owner an apply/push path, or have the owner
  widen the write allowlist. VERIFY write access before promising a ticket plan that
  assumes it.
- `gh api`/`gh pr` calls intermittently die with `tls: failed to verify certificate:
  x509: OSStatus -26276` — transient; retry after a few seconds.
- Shared working tree: all branch work in your OWN worktree (`git -C` everywhere, no
  pipes where success matters, push immutable OIDs `${oid}:refs/heads/branch` — zsh
  mangles unbraced `$SHA:r`). Never stage/commit in the shared checkout.
- Codex recipe (Claude's OS sandbox breaks nested Seatbelt — do NOT prompt for login on
  `sandbox_apply` errors): copy `~/.codex/auth.json` + `config.toml` into
  `$TMPDIR/codex-home`, then `CODEX_HOME="$TMPDIR/codex-home" codex exec
  --skip-git-repo-check --sandbox danger-full-access -m gpt-5.6-sol
  -c model_reasoning_effort=high "<prompt>" </dev/null`. Run as background Bash,
  redirect stdout to a file; rmcp/chatgpt.com transport errors in stderr are harmless.
- Backend suite ≈ 4m40s — redirect to a file and READ it. Scripts run outside a worktree
  import the MAIN checkout via the venv (print `__file__` to prove which code ran).
  Scratch files in `$TMPDIR`, never `/tmp`. The 50k export takes ~121 s.
- `docs/ai-dlc/` is partly uncommitted — read by absolute path, not from a worktree.

## 5. HARD RULES THAT BITE

- 🚫 No persona-fix code, no committed pack changes before the phase-3 gate:
  `git diff backend/app/domain/ content/` must stay EMPTY through this entire slice
  (T2 touches `backend/tools/` only).
- 🚫 Never parse rendered hand text for statistics — Parquet/state replay only.
- 🚫 Targets from external evidence only; versioned data file, never hardcoded; scores
  non-authoritative for ANY conclusion until validation passes.
- 🚫 `/ai-org:*` skills are owner-invoked only. Tripwires (STOP and tell the owner,
  never silently reconcile): doc/repo conflicts, research undercutting a slice premise,
  re-deriving a recorded decision. This slice exists because that tripwire fired.
- Owner communication: plain language ALWAYS; never a bare synthetic ID (`S3`, `T1`,
  `§e.2`, `D_p`) without saying in the same breath what it is; every decision through
  AskUserQuestion with situation, options with gain AND cost, engine impact per option,
  and a stated recommendation. Owner = expert in data work, newcomer to poker-engine
  internals. Fable model is opt-in only (ask first); route subagents by task complexity
  per `~/.claude/rules/model-routing.md`.

## 6. RESIDUAL RISKS / HONESTY NOTES FROM ME

- I read the estimand contract, ledgers, corpus brief, completion note, consumption map
  §1–2.4/§2.7, roadmap, PRD, START-HERE, working agreement §2, stub scorer, and the
  parquet schemas MYSELF. I did NOT fully read dossiers 01/02 (headings + routed
  conclusions only) or FLYWHEEL-STATUS.md this session, nor GATE.md.
- The spec's A1 item list is dense because every item answers a specific review finding —
  the ledger maps finding→clause. If you're tempted to simplify a clause, read its
  finding first.
- The July spike (T6) may reveal the export tool can't backport cleanly — that decision
  path (one-campaign amendment) goes to the owner, not to your judgment.
- Session memory (auto-loaded) has entries for the defect ruling, S2b outcomes, and the
  flywheel direction — trust them as pointers, but the ledgers are the record.
