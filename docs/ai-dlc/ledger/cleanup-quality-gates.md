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
