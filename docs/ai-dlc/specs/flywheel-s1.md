# Spec — flywheel-s1: cross-repo working agreement + walking skeleton (rev 2)

Slice S1 of `../roadmap/bot-realism-flywheel.md` (owner-approved 2026-08-05). PRD requirement
R6. **Rev 2 folds the dual spec review** (refuter NEEDS-WORK + Codex Sol FAIL; adjudication:
`../ledger/flywheel-s1.md`). Provenance: core payload (agreement + walking skeleton, pass/fail,
appetite 1–2 days, no-gos) from the roadmap entry; D2 (session-R brief) and D5
(FLYWHEEL-STATUS commit) are owner-mandated additions from the 2026-08-05 handoff instruction;
owner interview settled dual review ON and the `POKER_ANALYTICS_DIR` + sibling-default bridge.

## Goal (one line)

Two repos can work as one flywheel without collisions: a committed working agreement in BOTH
repos, and a stub scorer in poker-analytics that runs end-to-end from ONE poker-coach command
against the local sim50k export — proving the pipe, with zero real scoring logic.

## Problem & outcome-link (from the roadmap)

Two repos + parallel sessions, no collision protocol; the measurement loop must span repos in
one command. Outcome-link: enables everything downstream (S2a–S6 assume this plumbing).

## Deliverables

### D1 — Working agreement doc (canonical + mirror)

Canonical: poker-coach `docs/ai-dlc/contracts/flywheel-working-agreement.md`.
Mirror: poker-analytics `docs/WORKING-AGREEMENT.md`, headed
"MIRROR — canonical copy lives in poker-coach:docs/ai-dlc/contracts/flywheel-working-agreement.md;
on conflict the canonical wins." Mirror = canonical byte-for-byte below that header line.

Required sections:
1. **Ownership manifest** — poker-coach owns: sim engine, bot policy, export producer
   (`backend/tools/export_analytics.py`), counterfactual-config execution (S4), **and the
   vendored ODCS copy `backend/tools/poker_events.odcs.yaml`** (whoever changes the export
   schema updates the vendored copy in the same change; sync check = `diff` against
   `poker-analytics:contracts/poker_events.odcs.yaml`). poker-analytics owns: scorer, target
   registry, ingestion gate, corpus (future), methodology docs (portfolio surface). One file =
   one owner; cross-repo edits require the agreement to say so.
2. **Interface contract** — the ODCS contract v1.0.0 (canonical in poker-analytics, vendored
   in poker-coach per §1) + the `_SUCCESS` manifest fields as of run-s20260805-n50000. The S4
   batch-manifest EXTENSION (config hash · scorer version · registry version · dependency
   lockfile · artifact checksums) is named planned-not-built; **until S4, scorer outputs pin
   what exists today** (see D3) and the missing pins are a declared gap, not an oversight.
   **Ingestion-gate rule:** the authoritative batch gate is `make validate`
   (`ingest/validate.py`); the S1 stub performs only cheap integrity checks (D3) — from S3 on,
   any real scorer run must be preceded by (or embed) the full gate.
3. **Repo bridge** — `POKER_ANALYTICS_DIR` env var (absolute path recommended; empty string =
   unset), else `../poker-analytics` sibling of the poker-coach repo root. Documented here,
   implemented in D4.
4. **Versioning rules** — `contract_version` (semver, breaking = major),
   `schema_path_version` (v1; bumps only on breaking change), scorer emits `scorer_version`
   (stub = `0.0-stub`) + the analytics repo's own git SHA; every cross-repo artifact embeds
   the producing run's full `_SUCCESS` manifest.
5. **Session protocol** —
   *Session F (flywheel build):* owns code + git in both repos; commits from worktrees only;
   never sweeps foreign edits. **Concurrent code sessions** (the roadmap schedules S6 ∥ S5)
   are allowed ONLY with disjoint declared file ownership per slice and separate worktrees;
   the roadmap checklist, START-HERE, and status/bridge docs are single-owner (the director
   session) — a parallel session never edits them.
   *Session R (research, S2b):* launches ONLY after S1 lands (definition below); docs-only —
   writes ONLY under `poker-coach:docs/ai-dlc/research/realism-architecture/`; no git, no
   code, no sims, no downloads without licensing review.
   *Session-R handoff:* R ends by writing a completion note (file list + one-line summary
   each) in its output dir; the director reviews at fan-in and commits accepted dossiers from
   a worktree — R never commits its own work.
   *Conflict rule:* STOP and surface to the owner (tripwires in `.claude/CLAUDE.md`).
6. **"S1 lands" definition** — S1 is complete only when BOTH repos' S1 commits are merged
   (owner-confirmed); the session-R brief carries this as its launch precondition.
7. **Scheduling note** — S6 parallel to S5 (after S2a + S3, under the concurrent-session rule
   in §5); S2b parallel to S2a–S4.
8. **Standing boundaries restated** — no bot-policy/committed-pack changes before the phase-3
   gate (verification per this spec's Verify-by step 4: range diff AND working-tree diff);
   never parse rendered hand text; targets from external human evidence only; everything
   under `persona-realism-artifacts/` is LOCAL/never-push. **Push protocol:** autonomous
   pushes on `feat/*|fix/*|chore/*` remain AUTHORIZED (`.claude/CLAUDE.md` — no conflict);
   the sandbox currently cannot push, so the operational fallback is: commit locally in the
   worktree, verify the OID, hand the push to the owner.

### D2 — Session-R launch brief

Poker-coach `docs/ai-dlc/briefs/session-r-s2b.md`: paste-ready prompt for the owner to start
session R. Contents: the S2b payload verbatim from the roadmap (3 dossiers + fallback ladder +
consumption map + GO/PARTIAL/NO-GO), the D1 §5 docs-only/no-git protocol + handoff clause,
output dir, reading order (START-HERE → roadmap → PRD §R5), the no-download rule, and the
launch precondition from D1 §6. States it is inert until the owner launches it.

### D3 — Walking-skeleton stub scorer (poker-analytics)

`scorer/score_stub.py` (new top-level dir, sibling of `ingest/`):
- CLI: `--dir <batch dir>` (+ `--out <json path>`, optional; **omitted = no file written**).
- **Gate checks (all exit 1 with a one-line clear message):** `_SUCCESS` missing · manifest
  not valid JSON or missing any of `run_id`/`seed`/`git_sha`/`lineup`/`row_counts` · any of
  the three Parquet files missing · actual row count of each Parquet ≠ manifest `row_counts`
  (via duckdb `count(*)`) · any decisions seat not present in `lineup`. This is deliberately
  LESS than `ingest/validate.py` (no ODCS run) — the reduced bar is stated in the module
  docstring and the agreement (D1 §2); an unhandled traceback on inputs outside these checks
  (e.g. mid-file Parquet corruption) is accepted stub behavior.
- Stat: decision-row count per persona, seats pooled by manifest `lineup` (labeled
  `"stat": "decision_count", "note": "walking-skeleton stub — not a realism score"`).
- **Output contract:** human-readable table → stderr; JSON → stdout (machine-parseable);
  `--out` additionally writes the same JSON to a file. JSON fields: the full producer
  `_SUCCESS` manifest embedded verbatim under `producer_manifest`, plus `scorer_version:
  "0.0-stub"`, `analytics_git_sha` (repo HEAD, `unknown` fallback), `duckdb_version`,
  `per_persona: {persona: count}`. Lockfile/checksum pins deferred to S4 per D1 §2.
- Makefile: `score` target — `$(PY) scorer/score_stub.py --dir $(DIR)`, `DIR ?= $(SAMPLE_DIR)`;
  `score` added to `.PHONY`.
- No new dependencies (duckdb 1.5.5 already pinned and importable in the venv).

### D4 — One-command bridge (poker-coach)

`scripts/score_realism.sh` (executable):
- Resolves analytics root: `$POKER_ANALYTICS_DIR` if set and non-empty, else
  `<poker-coach repo root>/../poker-analytics`. Errors (exit 1, readable message) if: the dir
  is missing · `.venv/bin/python` is missing or not executable (message points at
  `make venv`) · `scorer/score_stub.py` is missing.
- Batch dir = `$1` if given (normal cwd-relative shell resolution), else the local sim50k
  export `docs/ai-dlc/research/persona-realism-artifacts/remeasure-2026-08-05/sim50k`
  resolved against the poker-coach **primary checkout** (path string only; data stays
  local/gitignored — a worktree won't contain it, hence the pre-merge test procedure below).
- Remaining args passed through to the stub (`--out` reachable from the bridge); stub's exit
  code passes through.

### D5 — FLYWHEEL-STATUS.md update + first commit (poker-analytics)

- "Interim rules until S1 lands" → pointer to `docs/WORKING-AGREEMENT.md`.
- Corrections: "awaits the owner's approval gate" → approved (PR #169); "extended with a
  batch manifest in slice S1" → the extension is S4 (S1 builds only the stub pipe).
- Ticket-adjudication section stays. Committed as part of S1 (currently untracked).

## Files touched (exhaustive)

| Repo | File | Action |
|---|---|---|
| poker-coach | `docs/ai-dlc/contracts/flywheel-working-agreement.md` | new |
| poker-coach | `docs/ai-dlc/briefs/session-r-s2b.md` | new |
| poker-coach | `scripts/score_realism.sh` | new, chmod +x |
| poker-coach | `docs/ai-dlc/roadmap/bot-realism-flywheel.md` | commit the EXISTING owner-ratified working-tree deltas (status→approved · publication-strategy paragraph · durability-header fix — committed HEAD still says `draft`) + S1 `[x]` after pass/fail verified. The S1 worktree branch starts from the working-tree content of THIS FILE ONLY; all other riders (CLAUDE.md, profile.md, pause banner, other sessions' docs) stay uncommitted. |
| poker-analytics | `docs/WORKING-AGREEMENT.md` | new (mirror) |
| poker-analytics | `scorer/score_stub.py` | new |
| poker-analytics | `Makefile` | add `score` target + `.PHONY` entry |
| poker-analytics | `docs/FLYWHEEL-STATUS.md` | edit per D5 + first commit |

## Out of scope (explicit)

No real scoring logic, target registry, or graded distance (S3, gated on S2a). No batch-
manifest extension or counterfactual-config schema (S2a/S4). No export-producer changes. No
edits under `backend/app/domain/` or `content/`. No new dependencies. No S2b research content
(D2 is the brief only). No pushes (owner performs — D1 §8). **Flag carried to S2a:** personas
occupy multiple seats (3× tag, 2× passive_fish in sim50k) — the estimand contract must state
pooled-vs-per-seat treatment; S1's pooling is stub-only precedent, not a decision.

## Constraints (from profile + PRD §5)

- No backend/frontend code changes — shell + poker-analytics files + docs only; all profile
  invariants untouched by construction.
- Manifest-pinned: stub output embeds the full producer manifest + its own provenance (D3).
- Parquet/state_json only — never rendered text.
- Git: separate worktree per repo, branch `feat/flywheel-s1` in each; commit ONLY the files
  in the table above; never sweep foreign riders; local commits, OID verified, owner pushes.

## Verify-by (end-to-end)

**Pre-merge procedure** (branches live in worktrees; sim50k + venv live in the primary
checkouts): run the WORKTREE copy of `scripts/score_realism.sh` with explicit args —
`POKER_ANALYTICS_DIR=<analytics worktree> <coach worktree>/scripts/score_realism.sh
<primary poker-coach>/docs/.../sim50k` — steps 1–3 below must pass that way; step 1's
no-arg/no-env form is re-run from the primary checkout post-merge.

1. Bridge run → exit 0; stdout JSON parses; `per_persona` equals EXACTLY
   tag=244555 · calling_station=138263 · passive_fish=230849 · lag=89439 · nit=71878 ·
   maniac=109761 (sum 884745); JSON embeds `producer_manifest.run_id=run-s20260805-n50000`,
   `seed`, `git_sha`, plus `scorer_version`, `analytics_git_sha`, `duckdb_version`.
2. Failure modes: missing dir / missing `_SUCCESS` → exit 1 with the clear message; unset
   `POKER_ANALYTICS_DIR` with a bogus sibling → readable bridge error (not a traceback).
3. In poker-analytics: `make score` (no DIR) → runs against the committed 5k sample, exit 0.
4. No-go boundary, both forms: `git diff --stat <merge-base>..HEAD -- backend/app/domain/
   content/` on the S1 branch is EMPTY, and the working-tree diff over the same paths is
   unchanged from pre-S1.
5. Deliverable completeness: agreement committed in BOTH repos, mirror = canonical modulo
   the header line (`diff` check); D2 brief exists with the launch precondition; D5
   corrections present in the committed FLYWHEEL-STATUS; `scripts/score_realism.sh` is
   executable (`test -x`).
6. Roadmap S1 `[x]` only after 1–5 pass; ledger `../ledger/flywheel-s1.md` records the
   spec review (done) and the build fan-in review.
