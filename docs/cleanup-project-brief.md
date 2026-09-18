# Poker-coach cleanup project — ready-made brief

**Bottom line:** this repo is the first of the dedicated cleanup projects John approved on 2026-08-25. Feed this file to `/ai-org:roadmap` (or `/ai-org:spec` per slice) in a fresh session inside this repo. The two big jobs are (1) distilling ~750,000 words of committed process docs down to three durable artifacts, and (2) fixing the audit's code findings. John's standing decisions: agents distill, **John approves every deletion before it happens**; hard quality gates get added; the raw paper trail stays recoverable in git history forever.

## Slice 1 — Docs distillation (highest value, do first)

The tree carries 389 tracked files under `docs/ai-dlc/` (104 specs, 80 tickets, 53 contracts, 38 ledgers, 38 reports — ~690k words). Procedure (per org-practice research, sources in the vault session of 2026-08-25):

1. Group the paperwork by finished initiative, not by file type.
2. Per initiative, write a one-page retrospective: what was decided, what was measured, what changed, links to any ADRs it produced.
3. Promote every decision still governing current behavior into `docs/adr/` (one short record each; superseded, never edited).
4. Build `docs/FINDINGS.md` — the measurements log John explicitly asked to preserve: every bot-realism / persona-realism metric ever measured, with date, method, result, and the current value. This must be exhaustive before anything is deleted (no false absence — grep the whole ai-dlc tree).
5. Present the retrospectives + FINDINGS.md to John. **Only after his approval**, `git rm` the raw spec/ticket/ledger/review files.
6. Keep tracked going forward: `docs/adr/`, `ARCHITECTURE.md`, `docs/FINDINGS.md`, retrospectives, and the live profile/spec of any unfinished work. Future agent scratch goes to an untracked scratch dir.

## Slice 2 — Gates (mechanical) — ✅ BUILT 2026-09-18 (branch `chore/quality-gates`; spec `docs/ai-dlc/specs/cleanup-quality-gates.md`)

- Add a backend lockfile (`uv lock`) — currently `>=` floors only.
- Add mypy (or pyright) for the backend; add a linter/formatter for the TypeScript frontend (none exists — Biome recommended); wire both into CI and a root `make check`.
- Add `.pre-commit-config.yaml`.
- Add a `conventions:` entry to the profile naming golden-path files per area.

## Slice 3 — Code findings (from the 2026-08-25 audit)

- `backend/tests/test_personas_postflop.py` is **14,378 lines** (17% of the codebase) with essay-length stale comments ("STALE BUDGET CLAIM, corrected 2026-07-26") — split by scenario family, delete the narrative cruft.
- Oversized domain files to split when next touched (flag, don't big-bang): `backend/app/domain/postflop.py` (2,413), `personas_postflop.py` (2,231), `table/grade_map_postflop.py` (1,773), `services/sim_session.py` (1,718), `tools/detection_corpus.py` (1,452).
- Delete stale root files: `RUN-THESE-COMMANDS.md` (its own text says to delete it after the completed rename), `s3-build-handoff.md` (one-shot handoff prompt).
- `backend/tools/` standalone scripts have zero test coverage; one (`run_s6_dryrun.py`) already shipped broken once. Add smoke tests or an explicit "untested, owner-run only" header.
- README "Status" section is a stale inline changelog (quotes test counts nowhere near the real ~1,575) — replace with a short current-state paragraph; history lives in git.
- Frontend: 4 test files for 16 components; `SimulateView.tsx` (941 lines) untested — add tests for the top 2–3 components when touched.

## Out of scope

- kalshi-cockpit and all other repos (own projects).
- Rewriting working domain logic for style alone.

## Done means

`make check` (format + lint + typecheck + tests) exists and passes; docs tree holds only the durable set; John has approved every deletion; `docs/FINDINGS.md` answers "what did we measure then vs now" without grepping history.
