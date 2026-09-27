# M1b whole-branch review — Claude `refuter` (Opus, `mode: whole-branch`), raw report

This reviewer checked how M1b's four tickets interact, and reviewed ticket T4 (wiring the live table and
the 6-max measurement tool) for the first time. M1b is the slice that lets bot settings carry
6-max-only values.

- **Reviewer:** a fresh-context `refuter` on Opus.
- **Scope:** `git diff 7d9f575`, including the then-uncommitted T4 files.
- **Captured:** verbatim from the agent's final message, 2026-09-27.
- **Adjudication:** `../ledger/m1b-table-size-settings.md`, rows B3–B6.

verdict: fail

**Bottom line:** I found no wrong behaviour today. Every bot at 9-max and 6-max still plays exactly as
before, and all three live-session call sites read the correct table size's settings. The one blocking
gap is in T4 (the ticket that wires the live table and the 6-max measurement tool). The measurement
tool's new `table_size=6` load has no test. Reverting it leaves every test green, and M2 (the LAG
retune at 6-max) depends on that tool to judge its results. There are three minor findings besides
that.

**Checks I ran on this exact working tree:**
- **Targeted tests:** 69 passed across `test_sim_session_table_size_packs`, `test_bot_decisions_golden`,
  `test_sixmax_baseline`, `test_persona_table_override` and `test_persona_pack_invariants`.
- **Type check, lint and format:** `mypy app` is clean. `ruff check` and `ruff format --check` are clean.
- **Test-weakening check:** `check_test_weakening.py --base 7d9f575` reports 0 failing (exit 0).
- **Golden fingerprint:** `git diff 1457448 -- backend/tests/test_bot_decisions_golden.py` is empty, so
  the constants T1 pinned are unchanged.
- **Spec §8.3 greps:** `six_max` is read only inside the table-size-6 branch of `personas.py` (the other
  hits are docstrings). There is exactly one `TableSize = Literal`, in `deck.py:20`.

**Mutation tests (step 3c):** I planted breaks in a private rsync copy of the worktree, not in a git
worktree, because the brief forbids state-changing git. I deleted the copy afterwards.

| Planted break | Result |
|---|---|
| `sim_session.py:276` (deal site) forced to 9 | red 5/5, then 200/200 over repeated runs |
| `sim_session.py:1092` (after-hero site) forced to 9 | red 5/5, then 200/200 |
| `sim_session.py:1520` (villain-range endpoint) forced to 9 | red 5/5 |
| `_packs` ignores its size argument | red |
| `sixmax_baseline.py:70` reverted to `load_persona_packs()` | **green**, 18 passed |
| Both bot call sites forced to 6 | **green**, 111 passed |

- **The maker's plant claim holds.** Forcing 9 at each of the three sim_session sites turns T4's tests
  red, as the maker reported.
- **The call-site test is not flaky in practice.** Over 200 runs on correct code, it reached 30
  decisions per site in 16 to 22 hands (120 of the 200 runs took exactly 18), well under the 80-hand
  cap.

**Consumer sweep:** I grepped `_packs`, `_seat_personas`, `load_persona_packs`, `estimate_range`,
`bot_decision`, `advance_to_hero` and `play_one_hand` across `backend/app` and `backend/tools`. The only
code that reads bot settings at 6 seats is the three sim_session sites and `sixmax_baseline.run_baseline`.
`export_analytics`, `counterfactual`, `detection_corpus` and the probes are all 9-max (`i % 9`).
`coach.py`, `review.py` and `sim_current.py` never load settings. The per-size `@cache` is keyed
correctly; `_table_size` returns only 6 or 9, and the call order 9, 6, 9 is tested. The villain-range
change fails the same way as before on a bad persona value (an unhandled error, a 500, either way).

**Boot-probe flake:** its code path is confirmed unrelated. The probe (`scripts/verify.sh:40-44`) calls
`/api/v1/drill/next`, which uses the preflop content packs, not the bot settings. The branch diff
touches nothing under `scripts/`, `app/api`, `registry.py` or `scenarios.py`. I could not measure the
2.8% rate, because running `verify.sh` was off limits.

```
issues:
  - severity: major
    where: backend/tools/sixmax_baseline.py:70
    problem: The switch to `load_persona_packs(table_size=6)` is new behaviour with no test that fails without it. This breaks the rule "New behavior ships with a test that fails before the change" in `~/.claude/rules/engineering-standards.md`; spec §4 also never asked for such a test. If the line regresses, M2's measurement tool silently measures the 9-max LAG while the live table plays the 6-max one. The golden 6-max fingerprint cannot catch this, because no override file ships.
    evidence: With line 70 changed to `packs = load_persona_packs()`, running `pytest tests/test_sim_session_table_size_packs.py tests/test_bot_decisions_golden.py tests/test_sixmax_baseline.py` gives "18 passed in 2.45s". No test under `backend/tests` points `run_baseline` at the override fixture (checked with grep for `sixmax_baseline|run_baseline`).
    fix: Add one test, for example in `test_sim_session_table_size_packs.py`. It points `personas.PERSONA_DIR` at `write_fixture_content(tmp_path)` with monkeypatch, runs `sixmax_baseline.run_baseline(60, 1)`, and asserts two things. First, the LAG at seat 2 makes an unopened decision at least once. Second, every such decision is a fold, or a raise holding AA; this reuses `_unopened_bot_decisions`' logic. It gains a red test for the regression above. It costs about 20 lines and about 0.1 s, and it adds a file outside T4's test list only if it goes into `test_sixmax_baseline.py`.
  - severity: minor
    where: backend/app/services/sim_session.py:276 and :1092
    problem: The reverse direction is unguarded. A hard-coded 6 at both bot call sites would make every live 9-max table play 6-max settings, and no test catches it. This is harmless today because no override ships. Once M2 ships `six_max/lag.json`, it would break the "9-max byte-identical" goal. The 9-max golden fingerprint drives `export_analytics.play_one_hand`, not the live session, so it would not see this either.
    evidence: With both sites planted as `_seat_personas(seats, 6)`, running `pytest tests/test_sim_session_table_size_packs.py tests/test_sim_session.py tests/test_simulate_6max.py tests/test_two_mode_simulate_gate.py` gives "111 passed in 4.11s". The villain-range test does cover both directions (its 9-max leg asserts classes strictly wider than `{"AA"}`), but the bot call sites have only a 6-max leg.
    fix: Add a 9-max leg to `test_both_bot_call_sites_use_the_six_max_pack`. It creates a 9-max session, rewrites every villain to the LAG with the fixture folder active, and requires at least one non-AA unopened open from each site within a cap; the base LAG opens many hands, so this fills quickly. It gains protection for the 9-max-identical rule once M2 ships an override. It costs about 15 lines and under 0.5 s.
  - severity: minor
    where: backend/tests/test_pack_range_lint.py:99, backend/tests/test_persona_range_edges.py:59, backend/tests/test_persona_size_ecology.py:187
    problem: This is the same kind of bug as ledger F2 (a settings-file safety check that never sees a 6-max override), nearby. The branch runs `test_persona_pack_invariants.py` at both sizes, but three other checks over every settings file still load at 9 only. They are the RR-LINT lint (gaps in a hand-class row, dead range tokens, out-of-order weights), the "range boundaries must be ramps" rule, and the "bet size must not name the bettor" rule. Override nodes that M2 writes for 6-max would bypass all three.
    evidence: Each file's fixture or scan helper is `load_persona_packs()` with no table size, found with grep. Spec §2 lists only `test_persona_pack_invariants.py` checks for the 6-max run.
    fix: Ledger it for M2's spec rather than widening this slice, because these files are outside spec §1's file list. Parametrise each fixture over table sizes 9 and 6, as `test_persona_pack_invariants.py` now does. That gains safety checks on M2's authored 6-max nodes, at the cost of three fixture edits and roughly doubling those files' runtime.
  - severity: minor (optional)
    where: backend/tests/test_sim_session_table_size_packs.py:127-150
    problem: The call-site test drives the service's unseeded random source (`secrets`), so a red run cannot be replayed from a seed. Its pass or fail result does not depend on the draw in practice, but a precedent for seeding exists at `backend/tests/test_grade_map.py:768-769`, which monkeypatches `_fresh_rng` and `secrets.randbits`.
    evidence: Across 200 runs on correct code, it passed 200/200 using 16 to 22 hands out of the 80 allowed. Across 400 runs with a mutated site, it went red 400/400.
    fix: Optional. Seed `_fresh_rng` and `secrets.randbits` the way `test_grade_map.py` does. That gains a replayable red run, at the cost of about 3 lines and slightly less realistic play-through.
```

**Notes that are not issues:**
- **Not verifiable at review time:** Spec §8.4 (the live-app check) and the roadmap tick in spec §9 are
  the Director's close-out ticket (T5), so a reviewer cannot verify them.
- **Stale line numbers:** The spec and ticket cite call sites at `:275`, `:1089` and `:1516`; they are
  now `:276`, `:1092` and `:1520`. This is optional to fix.
- **New untracked file during my review:** `docs/ai-dlc/reviews/m1b-branch-standards.md` appeared in the
  worktree while I was working. I did not create it; it is probably the parallel standards review's
  output. Apart from that file, `git -C <worktree> status --short` and `git diff --stat` match my
  starting snapshot (diff-stat hash `a5709967…` both times).
