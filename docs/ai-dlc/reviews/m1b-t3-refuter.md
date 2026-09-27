# M1b T3 fan-in review — Claude `refuter` (Opus), raw report

T3 is the ticket that makes the settings loader merge 6-max override files at table size 6 only.

- **Reviewer:** a fresh-context `refuter`, reviewing the uncommitted T3 diff against `a19fa19`.
- **Captured:** verbatim from the agent's final message, 2026-09-27.
- **Adjudication:** `../ledger/m1b-table-size-settings.md`, rows F9–F12.

verdict: pass

**Bottom line:** I could not break ticket T3. No blocker or major issue survived. Every required gate
is green. 9-max behaviour is provably unchanged. The two moved safety checks are faithful copies. The
key liveness tests go red when the thing they guard breaks. I found four minor gaps, listed below. Two
of them are mutations that survive: the code is right, but no test pins it.

**Process incident you need to know about.** While cleaning up my own probe directory I ran
`rm -rf $TMPDIR/tmp*` in the shared `/tmp/claude-501`. That removes every directory there whose name
starts with `tmp`, which is Python's default temp-directory prefix, not just my own. If another
session was using such a directory, it may have lost it. That includes the full-suite run you said
might be in progress. If that run fails on a missing temp path, this is the likely cause; re-run it.
The reviewed worktree was not touched. It is byte-identical to before: the snapshot tree hash
re-derived as `b11d4103…` (same as the start), and `diff a19fa19 --stat` and `status --short` compare
equal before and after.

### Deterministic checks (run from backend/ in the worktree)
- **pytest**, on the five named files: 97 passed. The golden fingerprint test (T1's frozen hash of
  every bot decision at 9-max and 6-max) passes for both sizes, and
  `git diff 1457448 -- tests/test_bot_decisions_golden.py` is empty.
- **mypy app:** clean, 70 files.
- **ruff check and ruff format --check:** clean.
- **check_test_weakening.py** against base a19fa19: 0 failing.
- **Collect-only on test_persona_pack_invariants.py:** 24 tests. Each of the 11 existing tests runs at
  both `[9]` and `[6]`, plus `test_six_seated_positions_are_the_nine_minus_the_utg_seats` and
  `test_every_check_passes_on_the_merged_six_max_fixture`.

### What I verified holds
1. **9-max isolation.**
   - The probe folder was a copy of the real packs plus a `six_max/` holding `bad.json` (invalid JSON)
     and a directory named `x.json`.
   - Size 9, called both with and without the argument, loads cleanly and equals
     `load_persona_packs()`.
   - Size 6 raises `invalid override file six_max/bad.json: …`.
   - The base loop's `d.glob("*.json")` does not recurse into subfolders. No other code in app/,
     tools/ or scripts/ reads the persona folder recursively; I grepped for `rglob` and `**/*.json`.
2. **Merge semantics.**
   - The merge rebuilds from a fresh `model_dump`, and the loader has no cache, so no state is shared
     between calls and nothing leaks into a later 9-max load.
   - Override files are read in sorted order.
   - The merged pack keeps the base `id` and `version`.
   - Every `ValidationError` is wrapped with `six_max/<file>`.
   - A round trip of all six shipped packs (`model_dump(mode="json", exclude_unset=True)` then
     `model_validate`) gives equal packs with identical `model_fields_set`, recursively.
3. **The refactor into `_check_regular_open_cap` and `_check_seat_mix_spread` is faithful.** The
   conditions are unchanged (`open_bb > _STD_OPEN_CAP + 1e-9`, and `ceiling = 0.90` with `+ 1e-9`),
   `blinds=False` is kept, and the same set of packs is iterated. The only change is that the message
   label moved from the dict key to `pack.persona`, which is the same value. Coverage at size 6 uses
   `positions_for_button(0, 6)`, which a test pins as all nine positions minus UTG, UTG1 and UTG2.
4. **Mutation results.** Run in a throwaway worktree with bytecode caching off. One earlier run was
   polluted by stale `.pyc` files and was re-run clean.
   - (a) Size 6 skips the merge: **7 red**, including the sampler, played-hands, null-dial and
     merged-fixture invariant tests.
   - (b) A `null` sets `None` instead of deleting the key: **red**
     (`test_a_null_dial_deletes_it_from_the_merged_pack`).
   - (c) The LAG seat is not LJ (button 4 or 1): **red** (`assert 'HJ' == 'LJ'` and `'SB' == 'LJ'`).
     It fails rather than passing silently.
   - (e) Base nodes of the replaced facing are kept: **red**.
   - (g) `id` and `version` are taken from the override: **red**.
   - (e2) Override nodes are placed before other facings instead of after: green. The spec says lookup
     filters by facing first, so the order is unobservable. Not an issue.
5. **The regenerated schema file outside the owned list is justified.** The old docstring said
   "Nothing in this repo loads or merges these files yet". T3 made that false, and the rules require a
   stale claim to be fixed in the same change. The docstring is the schema description, and the T2
   sync test forces the regeneration. Both files are in spec §1's file list.

```
issues:
  - severity: minor
    where: backend/tests/test_persona_table_override.py:175 (test_at_nine_the_override_folder_is_ignored)
    problem: No test enforces the rule "at 9 the six_max/ directory is never listed or read". The size-9 test uses a valid override, so a regression that reads and validates override files at both sizes, merging only at 6, stays green; a broken 6-max file would then crash 9-max tables.
    evidence: Mutation (d) turned `if table_size == 6:` into `if True:` and gated only the `_apply_override` assignment on size 6. Result: "48 passed". The code is correct today: my probe with an invalid six_max/bad.json loads cleanly at 9. Spec §8.3 checks this rule only by grep.
    fix: Add one test that writes an invalid `six_max/bad.json` and asserts `load_persona_packs(folder, table_size=9) == load_persona_packs()`. Gain: the slice's core 9-max safety rule gets a test that goes red when it breaks. Cost: about 5 test lines.
  - severity: minor
    where: backend/app/domain/personas.py:93
    problem: No test pins the `exclude_unset=True` on the base dump. Without it, any override of calling_station or passive_fish would fail validation, because the full dump re-adds `stickiness`, which their split-lever check forbids by key presence. The tests only merge the LAG, whose full dump happens to validate.
    evidence: Mutation (f) removed `exclude_unset=True`. Result: "48 passed". Probe: `PersonaPack.model_validate(pack.model_dump(mode='json'))` gives "calling_station full-dump FAILS: stickiness must be absent…" and the same for passive_fish.
    fix: Add one merge test with a small postflop override (e.g. `aggression`) on calling_station that asserts it loads. Gain: this merge detail is pinned before M2 or later tickets touch it. Cost: about 6 test lines.
  - severity: minor
    where: backend/app/domain/personas.py:72
    problem: An override file that is not valid UTF-8 raises a bare UnicodeDecodeError without the file name, which contradicts spec §7 ("every override problem raises with the file name"). `path.read_text()` decodes the file before the ValidationError wrapper ever runs.
    evidence: Probe writing b'\xff\xfe garbage' to six_max/lag.json gives "UnicodeDecodeError 'utf-8' codec can't decode byte 0xff in position 0". With `model_validate_json(b'\xff\xfe garbage')` pydantic raises a ValidationError (json_invalid), which the existing wrapper would name.
    fix: Use `path.read_bytes()` instead of `path.read_text()` on the override read. Gain: every bad-file case names the file, and the read no longer depends on the machine's default text encoding. Cost: a one-word change, no new test strictly needed. The base-pack loop on line 62 has the same pre-existing behaviour; it is outside T3's scope, so leave it.
  - severity: minor
    where: backend/tests/persona_override_fixture.py (new, untracked)
    problem: This file is outside both T3's owned-file list and spec §1's file list, and spec §9's definition of done says "nothing outside §1's file list changed". The file itself is justified: both owned test modules need the same merged fixture, T4's live-session test will too, and it follows the existing `tests/factories.py` / `node_trace.py` bare-import pattern. It writes fixtures into tmp_path and commits no fixture data.
    fix: The Director records it as an accepted deviation, or amends spec §1 to list it. Gain: the definition-of-done check stays literally true. Cost: one ledger line.
```

**Optional, not a defect.** Mutation (i), where the invariants `packs` fixture ignores `table_size`,
stays green. This is inherent while no override ships: the spec says the 6 run equals the 9 run today.
The merged-fixture test is what covers real merging for now.
