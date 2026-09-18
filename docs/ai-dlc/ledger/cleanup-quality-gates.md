# Finding ledger — cleanup slice 2: quality gates

Round 1, 2026-09-18, on spec rev 1. Planned as dual blind review (Claude `refuter` + Codex
`gpt-5.6-sol`). **Codex produced nothing** — its full-access sandbox mode was blocked by Claude
Code's permission classifier and its read-only mode could not initialise a shell (nested
sandbox); record in `../reviews/cleanup-quality-gates-r1-sol.md`. Round 1 is therefore
Claude-only, fail-open per the review policy. Claude refuter (Sonnet, high effort):
APPROVE-WITH-FIXES, report `../reviews/cleanup-quality-gates-r1-claude.md`. Every finding was
checked against the code before adjudication.

| # | Source | Finding | Claimed | Adjudicated | Evidence checked |
|---|---|---|---|---|---|
| 1 | Claude | The `dev` extra never declares mypy or pre-commit, so CI's `uv sync --locked --extra dev` would not install what `make check-backend` runs | blocking | **ACCEPTED** — spec §10 now adds both to the extra before the lock is generated; G4 ticket amended | `pyproject.toml` dev extra = pytest, httpx, ruff. Verified. |
| 2 | Claude | `sim_session.py`, `personas_postflop.py`, `scenarios.py` carry SQLAlchemy/Optional errors, not the two named patterns, yet were listed under "type fixes" — contradicting §8 and risking behaviour change in session code | blocking | **ACCEPTED** — spec §7 and the file list now baseline those three by config; G3 ticket amended | `grep map_fail\|EvaluationResult(` in the three files: zero hits. Verified. |
| 3 | Claude | The `EvaluationResult(**dict)` pattern is 210 errors over 20 call sites, not "~100 from a few sites" | should-fix | **ACCEPTED** — contract map §3 and spec §7 corrected | mypy log: 210 lines in `postflop.py`, dominated by that pattern. Verified. |
| 4 | Claude | The `export_analytics.py` caution is moot: `mypy app` never checks `backend/tools/` | optional | **NOTED, kept** — the sentence costs nothing and `ruff format` does touch that file | `tools/` is outside `app`. Verified. |
| 5 | Claude | `uv lock --python 3.12` was only in the contract map's test, not the spec | optional | **ACCEPTED** — spec §10 pins it | — |

Rejected: none.

## Build record, 2026-09-18

Shape: backend reformat by the Director (own commit, full suite 2239 passed / 2 skipped on an
isolated checkout of that commit); then two workers in parallel — Opus `heavy-worker` for the
mypy gate and lockfile, Sonnet `implementer` for Biome — then the root wiring (Makefile,
pre-commit, CI, docs, profile conventions) by the Director. Fan-in gate: `make check` on the
worktree.

| # | Source | Finding | Adjudicated |
|---|---|---|---|
| B1 | backend worker | `map_fail`'s reason widened to `Optional` is weaker than the runtime truth (every failing gate carries a reason); narrowing at 45 call sites would need asserts or a predicate flip, both behaviour changes | **ACCEPTED as built** — the ticket forbids behaviour change; a later slice may tighten the constructor sites instead |
| B2 | backend worker | `app/domain/postflop.py` is 2,411 lines, past the file-size guidance, and grew by 13 | **RECORDED** — splitting it is cleanup slice 3's "oversized domain files" item |
| B3 | backend worker | `grade_map_reject.py` edited outside the ownership list (one signature, reached by the pattern fix) | **ACCEPTED** — annotation only, named in the return |
| B4 | frontend worker | Two rules not in the spec's table (`useIterableCallbackReturn`, `noAssignInExpressions`, one hit each) fixed by hand rather than downgraded | **ACCEPTED** — mechanical and behaviour-neutral, the spec's stated preference order |
| B5 | frontend worker | `useTemplate` (51 hits) is `info` severity, so it neither blocks nor was auto-fixed | **NOTED** — stays visible as info |
| B6 | Director | Spec §12 asked for the frontend format pass as its own commit; the worker's single pass mixed format and safe-fix output, so it landed as one commit | **NOTED** — the commit message itemises the by-hand fixes; not worth redoing |
| B7 | Director | First pre-commit draft passed filenames from the repo root; Biome rejected that as a nested root config and the whitespace hooks tripped on old docs and a font file | **FIXED** — every tool hook now runs from its own directory over its tree; whitespace hooks scoped to code extensions |

**Baselines shipped (burn-down list).** mypy: ten modules, 76 errors (`sim_session` 33,
`personas_postflop` 17, `scenarios` 12, `stats` 4, `api/v1/drill` 3, `feedback` 2,
`challenge` 2, `review` 1, `table/engine` 1, `equity` 1). Biome: nine rules at `warn`
(`useSemanticElements` 20, `useAriaPropsSupportedByRole` 13, `useFocusableInteractive` 3,
`noAriaHiddenOnFocusable` 3, `noSvgWithoutTitle` 1, `noArrayIndexKey` 26,
`noNonNullAssertion` 15, `noDescendingSpecificity` 18, `useExhaustiveDependencies` 6).
