# M1b whole-branch review — Claude `refuter` (Sonnet, `mode: standards`), raw report

This reviewer checked the finished M1b branch only against the written rules no tool checks. M1b is
the slice that lets bot settings carry 6-max-only values.

- **Reviewer:** a fresh-context `refuter` on Sonnet.
- **Scope:** `git diff 7d9f575`, plus the then-uncommitted T4 files.
- **Captured:** verbatim from the agent's final message, 2026-09-27.
- **Adjudication:** `../ledger/m1b-table-size-settings.md`, rows B1–B2.

Verdict: fail (one major, one minor). The M1b implementation itself is clean. It has real
domain-purity boundaries, no error swallowing, no duplicated merge logic, and tests that use real
objects with seeded randomness. The one already-oversized file (`sim_session.py`) grew by only about
4 lines, exactly as the spec flags. The gate is reported green and I did not re-run it, per the
brief. The problem I found is a written-rule breach in a brand-new file's opening comment.

```
issues:
  - severity: major
    where: backend/tests/test_sim_session_table_size_packs.py:1
    problem: The repo's comment rule (quoted in my brief) bans "references to tickets/tasks/slices (`M1b`, `T3`, `added for X`) in code or comments." This new file's module docstring opens with the bare initiative label and ticket ID, exactly the pattern the rule names as forbidden.
    evidence: |
      Line 1: `"""M1b T4: the live table reads bot settings for its own table size.`
      Confirmed via `git diff 7d9f575 -- backend/tests/test_sim_session_table_size_packs.py` (a new, untracked file, so every line is new) and a grep of every in-scope file's added lines (`git diff 7d9f575 <files> | grep -E "^\+" | grep -iE "M1b|\bT[0-9]\b"`), which turned up exactly two hits: this one and the minor item below. The pre-existing `N-3BSTRATA`/`T-STICKY` style tags elsewhere predate this diff and are out of scope.
    fix: Rewrite the opening line to describe the behaviour under test without the ticket label, e.g. "The live table reads bot settings for its own table size."

  - severity: minor
    where: backend/tests/test_bot_decisions_golden.py:14 (comment above NINE_MAX_DIGEST/SIX_MAX_DIGEST)
    problem: Same rule, weaker case — "A later slice re-pins these when a bot decision intentionally changes" uses "slice" generically (a future unit of work), not a specific ticket ID. Borderline against the letter of the rule.
    evidence: `+# Pinned 2026-09-27. A later slice re-pins these when a bot decision` / `+# intentionally changes; diff \`per_hand_digests()\` between commits to see` / `+# exactly which hands moved.`
    fix (optional): reword to "A future change to bot behavior re-pins these constants".
```

**Other rule checks I ran, all clean:**
- **Domain purity:**
  - `personas.py`, `persona_override.py` and `table/deck.py` import only `pydantic`, `app.domain.*`
    and the standard library.
  - `TableSize` moved to `app.domain.table.deck`, and `app.schemas.simulate` imports it from there.
- **No error swallowing:** both new `except ValidationError` blocks re-raise as `ValueError(...) from e`.
- **No duplication:** the villain-range line now uses the same `_seat_personas` helper as the bot call
  sites.
- **No new dependency.**
- **File size:** `sim_session.py` grew by about 4 lines, and the spec flags it; every other file is
  under 500 lines.
- **Tests:** they use real objects and seeded randomness, and never assert on a mock.
  `check_test_weakening` reported 0 failing.
- **`spot_signature()`:** untouched.
