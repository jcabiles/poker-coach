# Build review record — Two-mode Simulate (Training / Challenge)

One entry per hand-off barrier between the eight tickets of this slice. The plan is
`../plans/two-mode-simulate.md`; the tickets are `../tickets/two-mode-simulate.md`. Every entry
records which deterministic checks ran, who reviewed, and what the verdict was — because a
barrier that leaves no record is indistinguishable from a barrier that was skipped.

## The worktree's test baseline is not the main checkout's

Measured 2026-08-26 on this branch's base commit. The main checkout runs `2 failed, 2189
passed`; this worktree runs **`2189 passed, 2 skipped, 0 failed`**. The difference is entirely
benign and worth stating once so nobody reads it as a masked regression: the two
`test_detection_probe.py` tests that fail in the main checkout **skip** here, because they read
a machine-local data file that is deliberately not tracked by git and so was never copied into
the worktree. Their own skip message says so: `local S6 deck / owner DB not present`.

The practical consequence is good: inside this worktree, **any failure at all is ours**.

---

## Barrier after ticket T1 — the two session columns and migration `0015`

**Ticket in plain terms.** T1 is the database groundwork: it adds two columns to the Simulate
session table — `mode`, which records whether the player chose Training or Challenge, and
`blind_check_json`, which will later hold the result of the hand-200 opponent-identification
quiz — plus the Alembic migration that adds them to an existing database. It builds no
behaviour.

**Worker:** `implementer`, Sonnet, medium effort (the agent's pinned effort).
**Reviewer:** `refuter`, Sonnet, high effort (pinned). Fresh context; did not see the
implementer's reasoning.
**Verdict: APPROVE.** No blocking issues.

**Deterministic checks — re-run independently by the reviewer, not taken from the worker's
report:**

| Check | Result |
|---|---|
| Full backend suite (`pytest -q`) | `2190 passed, 2 skipped`, zero failures |
| `tests/test_db.py` | 1 passed |
| The new migration test | 1 passed |
| Selection `-k "db or migrat or sim_session or sim_replay or sim_grading"` | 94 passed |
| `ruff check .` | clean |

The passing count rose by exactly one, which is the one test T1 added. Nothing was lost.

**The new test was proved non-vacuous rather than assumed to be.** The reviewer moved the
migration file out of the versions directory, cleared the compiled-bytecode cache, and re-ran:
the test failed with `OperationalError: no such column: mode`. Restoring the file made it pass
again. So the test genuinely exercises the migration and does not merely re-assert its own
setup.

**The one design question, adjudicated.** The specification says both columns are nullable with
`NULL` read as Training, but the implementation types the Python field as a plain non-optional
string. The reviewer settled it: SQLite's `ALTER TABLE ... ADD COLUMN ... DEFAULT 'training'`
writes the literal default into every pre-existing row at migration time rather than leaving
them null, and the only place that constructs a session row in Python never omits the field, so
no null can reach a reader through any path that exists. The type annotation is therefore
truthful, and the absence of a read-time fallback is correctly unnecessary rather than a defect.
This matches the golden path it was told to copy, `DrillAttempt.source`, which also carries no
per-instance guard.

**One thing carried forward to T2, which is the ticket that adds the first reader.** If a null
ever did reach the column, the schema field T2 is about to add — a literal union of exactly
`"training"` and `"challenge"` — would raise a validation error rather than quietly fall back to
Training. T2's brief therefore instructs it to normalise at the read boundary. The gain is that
a hand-rolled or future write path cannot turn a missing mode into a 500 error; the cost is one
extra line in the view assembly.

---

## Barrier after ticket T2 — the mode accepted at creation and carried on every response

**Ticket in plain terms.** T2 makes session creation accept the player's Training-or-Challenge
choice and makes every response carry it back, together with whatever hand-200 quiz result is
stored. It builds no gate, no scoring and no user interface.

**Worker:** `implementer`, Sonnet, medium effort (pinned).
**Reviewer:** `refuter`, Sonnet, high effort (pinned). Fresh context.
**Verdict: APPROVE WITH FINDINGS**, two of them Major. Both were fixed by the original
implementer before this barrier closed, and the fixes were verified by the Director.

**Deterministic checks — re-run by the reviewer independently, then again by the Director after
the fixes:**

| Check | Result |
|---|---|
| Full backend suite | `2195 passed, 2 skipped`, zero failures — exactly the five tests T2 added |
| Selection `-k "sim or simulate"` after the fixes | 148 passed (146 plus the two regression tests) |
| The ticket's own test module after the fixes | 7 passed |
| `ruff check .` | clean |

**All five original tests were proved load-bearing**, not merely present. The reviewer broke the
specific code each one guards and confirmed the test failed, then restored every file and checked
it byte-for-byte against the original. The test that matters most — that villain archetypes
survive in the database in Challenge mode, the one constraint in this slice that must not bend —
was attacked twice, including a version that nulls the archetype *after* the session is dealt so
that the assertion itself has to catch it rather than an incidental engine crash. It did.

**The two Major findings, both reproduced as real HTTP 500 responses.** They share one shape:
`_view()` is the single point where every Simulate response is assembled, so anything that raises
inside it takes down not one field but the whole session — restore, dealing, and acting alike,
with no recovery short of hand-written SQL.

1. **An unrecognised stored mode.** The normalisation guarded only null and empty values, so a
   non-empty junk string passed into the two-value literal union and failed response validation.
   The reasoning that justified handling null applies identically to an unrecognised value: both
   are reachable by exactly the same hand-rolled write. Fixed by validating against the permitted
   values rather than testing truthiness.

2. **A malformed stored blind check.** The stored-result parse was unguarded. Fixed with a
   commented fallback that drops the field and lets play continue — the case the engineering
   standard carves out when it allows "a deliberate fallback [that] states its reason in a
   comment". The specification's own framing settles it: the blind check is "a keepsake for the
   player, not a measurement", so core play must not depend on it parsing. The finding was latent,
   because nothing writes that column until T4, but T2 owns the read path that will inherit
   whatever T4 writes.

A third, minor finding: the `# type: ignore` comment suppressed nothing, because this repository
runs no static type checker in any of its gate commands. It was removed.

**Why no second review round.** The two fixes were specified by the reviewer, not invented by the
implementer; the implementer proved each new regression test fails against a mechanically
reverted copy of the file; and the Director read the final diff and re-ran the checks. A third
agent re-reviewing two reviewer-designed edits would have cost another full review pass to
re-confirm what two parties had already established. Recorded here so the decision is visible
rather than implied.
