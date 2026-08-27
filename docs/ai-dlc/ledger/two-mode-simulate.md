# Finding ledger — Two-mode Simulate

Round 1, 2026-08-26. Two blind reviewers, neither shown the requirements interview: the Claude
`refuter` (Opus, high effort) and Codex `gpt-5.6-sol`. **Both returned REJECT.** Raw reports:
`../reviews/two-mode-simulate-r1-claude.md`, `../reviews/two-mode-simulate-r1-sol.md`.

Every finding below was checked against the code before it was accepted. Reviewer output is a
report, not a verdict.

## Process failure worth recording

The first two Codex invocations produced nothing usable and the first one was actively
misleading. `CODEX-REVIEW.md` §5 prescribes `CODEX_HOME="$HOME/.codex-ai-org"`, a **fixed shared
path**. That directory is outside this repo's sandbox write allowlist, so `mkdir`/`cp` were
denied — but the directory already existed, created by a concurrent Claude session reviewing a
different repository. Codex ran against that session's state and returned a review of
`purposeful-youtube-feed` (Node/Fastify/better-sqlite3) into an empty report file. The second
attempt used a unique home under the same denied parent and died at `mkdir`. Only the third,
with `CODEX_HOME="$HOME/.codex/ai-org-2mode"` (inside the writable `~/.codex`) and `--cd` pinned
to the repo root, reviewed this repository. The log header was checked for `workdir:` before a
word of its findings was read.

**Gain of fixing the shared recipe: reviews stop silently reviewing the wrong repo. Cost: one
line changed in a reference file.** Not done here — it is outside this slice.

## Findings

| # | Source | Finding | Claimed | Adjudicated | Evidence checked |
|---|---|---|---|---|---|
| 1 | both | Completed hands are not `hand_no - 1` between hands; the gate fires only after hand 201 is dealt | blocking | **ACCEPTED** — spec §11 rewritten to `hand_no - (0 if hand_over else 1)` | `sim_session.py:1398-1412` early-returns on `in_progress` and increments only after settle. Verified. |
| 2 | both | The pause cannot be enforced in the browser: with Watch off a fold posts action and next-deal in one handler | blocking | **ACCEPTED** — spec §12 moves the barrier into `deal_next_hand()` | `SimulateView.tsx:492-508`. Verified. |
| 3 | Claude | Skipping the dialog stores nothing, so the gate re-fires forever and the unlock un-does itself | blocking | **ACCEPTED** — spec §15 stores `{"skipped": true}` | Spec-internal gap between old §13 and §14. Verified by reading. |
| 4 | Claude | The ledger's Player column cannot fall back to `position` — it duplicates the Seat column and position rotates every hand | blocking | **ACCEPTED** — spec §9 now uses a stable `seat_index` identity | `SimLedger.tsx:59` renders `seat.position`; `:60` the archetype; `sim_session.py:1407` rotates the button. Verified. |
| 5 | both | `frontend/src/api/client.ts` is unavoidable and was not in the file list, so the definition of done was unsatisfiable | blocking | **ACCEPTED** — added, along with `backend/tests/`, the roadmap, and this ledger | `client.ts:105-107`, `postSimulateSession()` takes no argument. Verified. |
| 6 | Codex | An already-open villain-range panel stays visible when labels are re-hidden after the unlock | blocking (Codex) / near-miss (Claude) | **ACCEPTED at Codex's severity** — spec §21. The two reviewers differ only on severity, not fact; the panel mounts independently of its button, so this is a live leak | `SimulateView.tsx:839-847`. Verified. |
| 7 | both | The new route used plural `/sessions/` against a singular-only router | should-fix | **ACCEPTED** — now `/session/{id}/blind-check` | All 16 routes in `simulate.py:71-246` are singular. Verified. |
| 8 | both | Deterministic seat pick guarantees neither distinctness nor stability; Python's `hash()` is salted per process | should-fix | **ACCEPTED** — spec §14 requires `hashlib.sha256` and sampling without replacement | Salted `hash()` is standard CPython behaviour. Verified by inspection. |
| 9 | both | `mode` as NOT NULL contradicts the repo's documented nullable add-column pattern and risks failing on populated SQLite | should-fix | **ACCEPTED** — both columns nullable, `NULL` read as Training | `models.py:38-42` documents the pattern for `DrillAttempt.source` (migration 0010). Verified. |
| 10 | both | The blind-check endpoint had no idempotency, error, or validation contract | blocking (Codex) / should-fix (Claude) | **ACCEPTED** — a Wire contract section now specifies first-write-wins, `409`, `400` | Neighbouring routes are explicitly idempotent (`deal_next_hand`'s no-op return). Verified. |
| 11 | both | The 404 recovery path and Leave Table both create eagerly, silently downgrading Challenge to Training | should-fix | **ACCEPTED** — spec §4 routes all three creation paths through the choice screen | `SimulateView.tsx:462-470` and `:549-566`. Verified. |
| 12 | Codex | The migration claim is untested against a populated database with an active session | should-fix | **ACCEPTED** — added to Verify-by | `backend/tests/test_db.py` upgrades a clean database only. Accepted on the reviewer's reading; not independently re-read. |
| 13 | Codex | Second-tab semantics undefined for both the toggle and a stale dialog | should-fix | **ACCEPTED** — spec §23 declares the toggle tab-local and the check server-authoritative | Existing localStorage controls read once into state, `SimulateView.tsx:94-104`. Verified. |
| 14 | Codex | The contract map's prose counts are wrong: seven archetype-naming leads in `exploit.json`, not three, plus four more in `content/cards/preflop.json` | optional | **ACCEPTED** — contract map §F corrected 2026-08-26 | Counted directly: 7 matching leads; `content/cards/preflop.json:106` names four archetypes. The card pack is not a Simulate render site — `sim_session.py` never loads it. Verified. |
| 15 | Claude | The fixed `LINEUP` multiset makes the six guess options non-equiprobable, so the check is a closed-set task | should-fix | **ACCEPTED** — spec §17 records it and bars citing the score as a measurement | `domain/table/play.py:44-54`: two passive fish, two TAGs, one each of the rest. Verified. |
| 16 | both | `./scripts/verify.sh` is already red on `main`, so the spec's own gate was unachievable | optional | **ACCEPTED** — baseline recorded as 2 failed / 2189 passed; the definition of done now permits exactly those two | Ran `tests/test_detection_probe.py` directly: 2 failed, 6 passed, `CorpusBuildError: no complete hands`. Pre-existing and unrelated. Verified. |
| 17 | Claude | No fifth archetype leak site exists | — | **NOTED, no action** — the grader's exploit prose is gated on `spot.villain_type is not None`, which Simulate never sets | `domain/providers/heuristic.py:44`. Accepted on the reviewer's reading. |

**Rejected: none.** Every finding survived checking, which is itself worth noting — the spec's
first draft asserted four things about the code that were not true.

## Reviewer disagreements

One, and only on severity: the open range panel (#6). Claude filed it as a near-miss, Codex as
blocking. Resolved in Codex's favour because the panel's mount site is independent of the button
it was assumed to follow. No disagreement of fact between the two reviewers.
