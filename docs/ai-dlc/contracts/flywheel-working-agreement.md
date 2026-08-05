# Flywheel Working Agreement — poker-coach ⇄ poker-analytics

Slice S1 of `../roadmap/bot-realism-flywheel.md` (spec: `../specs/flywheel-s1.md` rev 2).
Canonical copy: this file (poker-coach). Mirror: `poker-analytics:docs/WORKING-AGREEMENT.md`.
On conflict the canonical wins. Owner-approved initiative, 2026-08-05.

## 1. Ownership manifest

| Asset | Owner |
|---|---|
| Sim engine + bot policy (`backend/app/domain/`, `content/`) | poker-coach (FROZEN until phase-3 gate) |
| Export producer `backend/tools/export_analytics.py` | poker-coach |
| Vendored ODCS copy `backend/tools/poker_events.odcs.yaml` | poker-coach — whoever changes the export schema updates the vendored copy IN THE SAME CHANGE; sync check: `diff` against the canonical below |
| Counterfactual-config execution (S4) | poker-coach |
| ODCS contract canonical `contracts/poker_events.odcs.yaml` | poker-analytics |
| Ingestion gate `ingest/validate.py` (+ `make validate`) | poker-analytics |
| Scorer (`scorer/`), target registry, stat models | poker-analytics |
| Human-hand corpus (future, post S2b gate) | poker-analytics |
| Methodology docs / portfolio surface | poker-analytics |
| Roadmap, PRD, START-HERE, this agreement's canonical, status/bridge docs | poker-coach director session (single-owner — see §5) |

One file = one owner. Cross-repo edits happen only where a row above says so.

## 2. Interface contract

- **Data contract:** ODCS `poker_events.odcs.yaml` v1.0.0 (canonical in poker-analytics,
  vendored in poker-coach per §1). Batch layout: `hands.parquet`, `seat_outcomes.parquet`,
  `decisions.parquet` + JSON `_SUCCESS` manifest written LAST (fields as of
  run-s20260805-n50000: `run_id`, `seed`, `n_hands`, `lineup` (seat→persona, string keys),
  `stacks_bb`, `git_sha`, `engine`, `generator`, `contract_version`, `schema_path_version`,
  `exported_at`, `row_counts`).
- **Planned, NOT built (S4):** batch-manifest extension — config hash · scorer version ·
  target-registry version · dependency lockfile · artifact checksums. Until S4, scorer
  outputs pin what exists today (§4); the missing pins are a **declared gap**, not an
  oversight.
- **Ingestion-gate rule:** the authoritative batch gate is `make validate`
  (`ingest/validate.py` — manifest integrity, row counts, 150 ODCS checks). The S1 stub
  performs only cheap integrity checks (manifest keys, per-table row counts, seat⊆lineup).
  From S3 on, any real scorer run must be preceded by (or embed) the full gate.

## 3. Repo bridge

`poker-coach:scripts/score_realism.sh` → resolves the analytics checkout via
`POKER_ANALYTICS_DIR` (absolute path recommended; empty string = unset), else the sibling
`../poker-analytics` of the poker-coach repo root. One command, exit code passes through.

## 4. Versioning rules

- `contract_version`: semver; breaking schema change = major bump (both copies, same change).
- `schema_path_version`: data-path major (`v1`); bumps only on a breaking change.
- Scorer outputs embed: the producing run's full `_SUCCESS` manifest verbatim
  (`producer_manifest`), `scorer_version` (stub = `0.0-stub`), `analytics_git_sha`,
  `duckdb_version`. Lockfile + checksum pins arrive with S4 (§2).
- Every cross-repo artifact must be traceable to (engine sha, seed, config) through these
  pins — an artifact that can't name its producing run is invalid.

## 5. Session protocol

**Session F (flywheel build — code):**
- Owns code + git in both repos. Commits from git worktrees only; never stages or commits in
  a shared primary tree; commits ONLY files its slice owns; never sweeps foreign
  working-tree edits. Local commits with verified OIDs; push per §8.
- **Concurrent code sessions** (the roadmap schedules S6 ∥ S5): allowed ONLY with disjoint
  declared file ownership per slice and separate worktrees. The roadmap checklist,
  START-HERE, this agreement, and status/bridge docs are single-owner (director session) —
  a parallel session never edits them; it reports state for the director to record.

**Session R (research — S2b):**
- Launches ONLY after S1 lands (§6). Docs-only: writes ONLY under
  `poker-coach:docs/ai-dlc/research/realism-architecture/`. No git commands, no code, no
  sims, no data downloads without a licensing review.
- **Handoff:** R ends by writing a completion note in its output dir (file list + one-line
  summary each). The director reviews at fan-in and commits accepted dossiers from a
  worktree — R never commits its own work.

**Conflict rule (both sessions):** on any conflict between docs, repos, tickets, or research
findings and the governing plan — STOP and surface to the owner (tripwires in
`poker-coach:.claude/CLAUDE.md`). Never silently reconcile.

## 6. "S1 lands" — definition

S1 is complete only when BOTH repos' S1 commits are merged and the owner has confirmed both.
The session-R launch brief (`docs/ai-dlc/briefs/session-r-s2b.md`) carries this as its
launch precondition.

## 7. Scheduling note

S6 (detection pilot) runs parallel to S5 (reachability) after S2a + S3, under the
concurrent-session rule in §5. S2b (session R) runs parallel to S2a–S4.

## 8. Standing boundaries

- **No bot-policy or committed pack changes before the phase-3 gate.** Verification is
  two-sided: merge-base range diff on the branch AND working-tree diff, both empty over
  `backend/app/domain/` + `content/`. S4's counterfactual configs are ephemeral by
  definition — never committed.
- **Never parse rendered hand text for statistics** — replay `state_json`/Parquet only.
- **Targets come from external human evidence only** — never the internal theory contract.
- Everything under `poker-coach:docs/ai-dlc/research/persona-realism-artifacts/` is
  LOCAL/never-push (holds owner hand data; gitignored — referenced by path, never committed).
- **Push protocol:** autonomous pushes on `feat/*|fix/*|chore/*` remain AUTHORIZED
  (`.claude/CLAUDE.md` — no conflict with this doc). The Claude sandbox currently cannot
  push; operational fallback: commit locally in the worktree, verify the OID, hand the push
  to the owner. Never push `main`, never force-push, never merge without explicit owner
  confirmation — both repos.
