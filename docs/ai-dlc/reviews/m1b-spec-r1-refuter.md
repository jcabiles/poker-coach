# M1b spec review, round 1 — Claude `refuter` (Opus), raw report

Blind: the reviewer received the spec, the contracts file, the invariants and the verify commands, and
not the interview record. Captured verbatim from the agent's final message on 2026-09-27; adjudication
is in `../ledger/m1b-table-size-settings.md`.

verdict: approve-with-fixes (under my standard rubric this is a `fail` until the four major issues below are fixed)

**Bottom line:** The M1b plan is safe for 9-max. M1b is the slice that lets a bot carry 6-max-only
settings in separate override files. At 9 seats the loader path really is unchanged, and the golden
fingerprint (a hash of every hand's action history) is deterministic and fast. The plan's weak points
are elsewhere:
- The merge cannot remove a key, so some single post-flop dials cannot be overridden at all.
- 6-max override files skip most of the existing settings-file safety checks.
- Three of the "proved live" tests can pass without testing anything.

None of this harms 9-max. All of it lands on M2 (the LAG retune), the only user of this mechanism.

**What I ran (read-only, in the worktree `…/scratchpad/wt-m1b`, commit 9d20026 on top of 7d9f575):**
- **Existing tests:** `pytest -p no:cacheprovider tests/test_persona_pack_invariants.py
  tests/test_export_analytics_table_size.py tests/test_preflop_size_mix.py tests/test_domain_purity.py`
  gave 70 passed. `git status` stayed clean.
- **Test-weakening check:** `check_test_weakening.py --base 7d9f575` exited 0. The diff is docs only.
- **Golden feasibility probe** (script in `$TMPDIR/golden_probe.py`): 360 hands at 9-max via
  `play_one_hand` with `DEFAULT_LINEUP`, plus `run_baseline(360, 1234)` at 6-max. It ran in three
  processes with `PYTHONHASHSEED` set to 0, 1 and 12345. All three gave identical digests (9-max
  `194f95d773aee1ce…`, 6-max `10c40e6ebd3b539b…`) in about 0.9 s + 0.5 s. So the §4 golden plan works
  and fits the 15 s budget.
- **Round trip:** `model_dump(mode="json", exclude_unset=True)` then `PersonaPack.model_validate` gives
  an equal object for all six shipped packs.
- **Unknown keys:** confirmed that `PersonaPostflop` silently ignores them (a misspelled `agression`
  validates to an equal object).
- **Spec claims checked against the code, all accurate:**
  - call sites `sim_session.py:275, :1089, :1516`;
  - `_table_size` at `:212`;
  - `models.py` is 558 lines;
  - the golden-path line ranges;
  - no app code outside `sim_session` loads packs;
  - no cache in `app/` is keyed on pack id or version, so keeping the base `id`/`version` on the merged
    pack is safe;
  - `LINEUP_6MAX` always seats the LAG.

issues:
  - severity: major
    where: spec §2 "The merge" ("Update sizing and postflop key by key") and the owner decision "any
      single sizing or post-flop dial"
    problem: The merge can only set keys, never remove them, and the spec does not say what `null`
      means. Because of that, some single dials cannot be overridden. Adding `size_elasticity` to the
      LAG, TAG or NIT always fails validation. Each of those packs authors `stickiness`, and the
      `_stickiness_authorship` rule rejects `stickiness` whenever both split levers (`call_looseness`
      and `size_elasticity`) are set. That rule checks whether the key is present, so writing
      `"stickiness": null` does not help. By contrast, the sizing mutual-exclusion case only works
      through an undocumented `null` (`open_bb_mix` plus `"open_bb_mix_by_position": null` loads).
    evidence: |
      Probe merging into the LAG's dump, then PersonaPack.model_validate:
      add size_elasticity            ERR: postflop | stickiness must be absent when both call_looseness and size_elasticity are authored
      add size_elasticity+stick null ERR: postflop | stickiness must be absent ...
      flat open_bb_mix               ERR: sizing | open_bb_mix and open_bb_mix_by_position are both set
      flat open_bb_mix + by_pos null OK
      continue_ref null              ERR: postflop | continue_ref must be ABSENT rather than null
      Split levers per pack: lag/tag/nit have call_looseness but no size_elasticity, and stickiness is set.
    reproducer: from backend/, run PYTHONPATH=. …/.venv/bin/python -c "from app.domain.personas import
      load_persona_packs; from app.domain.content.models import PersonaPack;
      d=load_persona_packs()['lag'].model_dump(mode='json',exclude_unset=True);
      d['postflop'].update(size_elasticity=1.0, stickiness=None); PersonaPack.model_validate(d)"
    fix: State in §2 that an override value of `null` deletes that key from the merged dict before
      re-validation, for both `sizing` and `postflop`. Document this in the override schema description.
      Add one test (LAG `{size_elasticity: 1.0, stickiness: null}` loads and drops `stickiness`) and one
      error test (deleting a required dial such as `aggression` fails, naming the file). Gain: the
      owner's "any single dial" becomes true, and the `open_bb_mix` switch stops relying on unwritten
      behaviour. Cost: one branch in the merge function, two tests, and a meaning of `null` that authors
      must learn. The alternative is to record "cannot add `size_elasticity` at 6-max" as an
      owner-accepted limit. That costs nothing now, but M2 may hit it mid-retune.

  - severity: major
    where: spec §2 "6-max coverage" and §1 row `test_persona_pack_invariants.py`
    problem: Only the position-coverage check is extended to merged 6-max packs. The other checks in the
      same file still run on 9-max packs only, because the fixture calls `load_persona_packs()` with no
      arguments at `test_persona_pack_invariants.py:34-36`. Those checks are:
      - postflop sizes stay on the grader's recognised grid (`_check_grid`);
      - preflop sizes stay gradeable (`_check_preflop_sizes`);
      - a regular's open never exceeds the hero's 3-bet-line cap;
      - no seat table plays as one size;
      - no mix is shadowed dead.
      The owner explicitly allows overriding "any single sizing dial". So an M2 override with an off-grid
      pot fraction, or an open above the 4.5bb `_OVERSIZE_OPEN_CAP`, would pass every gate. It would
      then silently make hero spots against the 6-max LAG ungradeable ("No baseline yet") or leave dead
      mixes. These are exactly the silent failures the file exists to catch.
    evidence: test_persona_pack_invariants.py sections 1, 1b and 2 (lines 39-268) all take the `packs`
      fixture, which is `load_persona_packs()`. `grade_map_postflop.py:159-230` recognises persona bets
      only against `RECOGNIZED_BET_FRACS` and `_OVERSIZE_OPEN_CAP`.
    reproducer: none needed; this is a spec gap. Confirm with grep -n "def test_\|def packs"
      backend/tests/test_persona_pack_invariants.py
    fix: Run every `_check_*` in that file (not just coverage) over
      `load_persona_packs(table_size=6).values()` and over the merged test fixture, with coverage limited
      to the six seated positions. Gain: 6-max overrides get the same authoring guards as base packs.
      Cost: parametrising about six existing tests by table size (tens of lines, well under 1 s runtime).

  - severity: major
    where: spec §4 "Merge and liveness", third bullet (play_one_hand), and §4 "Live session", second
      bullet
    problem: Both play-level checks of the override are conditional: "the LAG's first action *in an
      unopened pot*" and "LAG unopened decisions obey the override". Neither is required to show that
      the condition actually happened.
      - A single `play_one_hand` hand may never put the LAG first-in. It may be the big blind, or someone
        may open ahead of it. The loop then asserts nothing and passes.
      - The live session draws from `secrets` (`_fresh_rng()` and `secrets.randbits` in
        `_deal_and_advance`, `sim_session.py:257, :274`) and cannot be seeded. So whether any LAG
        unopened decision occurs varies from run to run.
      - Bots act at two separate call sites: `:275` (at the deal, before the hero) and `:1089` (after the
        hero acts). If one site were mis-wired to the 9-max packs, the test would only notice when a LAG
        unopened decision happened to occur at that site.
    evidence: the lookup at `personas.py:95-111` makes the outcome independent of the random draw (a
      non-AA hand hits `break` and folds; AA raises at weight 1.0), so only whether the case occurs is
      random. In `sixmax_baseline.SEATS` the LAG sits at seat 2 with the button rotating `i % 6`.
      `create_session` uses `assign_lineup(_fresh_rng(), 6)`.
    reproducer: none yet (the tests are unwritten). The acceptance criteria should pin non-vacuity.
    fix:
      - play_one_hand test: choose the button so the LAG sits in LJ, which acts first preflop at 6-max
        and is always unopened. Assert that its decision row exists and is a fold (or a raise when it
        holds AA).
      - Live session: run a bounded loop of hands (for example up to 60) until at least one LAG unopened
        decision is seen after a deal and at least one after a hero action (the hero folds or checks).
        Fail if the cap is reached. Read hole cards and history from `SimHand.state_json`.
      Gain: each test turns red when either call site is wired to 9. Cost: a longer live-session test
      (tens of hands, still seconds) and slightly more setup code.

  - severity: major
    where: spec §4 "Live session", third bullet ("The villain-range endpoint serves a 6-max session
      without error")
    problem: The contracts doc's integration risk #2 is that the range the endpoint shows must come from
      the same pack the bot plays. The planned check only asserts "no error". That stays green if
      `:1516` is wired to `_packs(9)` or to `_seat_personas(seats, 9)`: the endpoint would serve the
      9-max range with no error, while the bot plays the override.
    evidence: `sim_session.py:1516` currently reads `_packs()[VillainType(persona_type)]`. Under the
      fixture, `estimate_range` for a LAG that raised first-in from LJ gives exactly `{AA}` with the
      override and a wide range without it. The two are easy to tell apart, but the spec never asserts
      either.
    reproducer: after implementation, plant `_packs(9)` at the endpoint. The spec's test as written stays
      green.
    fix: Store a SimHand whose state has the LAG raising first-in from LJ, using direct DB setup in the
      style of `test_two_mode_simulate_gate._renumber`. Call `villain_range` and assert its `weights`
      keys == {"AA"}. Optionally assert that the 9-max session's range differs. Gain: guards the one
      drift the contracts doc ranks second-most severe. Cost: about 30 lines of test setup.

  - severity: minor
    where: spec §2 "A `_doc` list of strings is accepted … (`extra="forbid"`)"
    problem: A pydantic v2 field literally named `_doc` becomes a private attribute, not a field. With
      `extra="forbid"`, a file containing `_doc` is then rejected. The spec names no mechanism, and no
      test requires `_doc` to be accepted, so a naive build passes every planned test and fails on M2's
      first cited override.
    evidence: probe `class M(BaseModel): model_config=ConfigDict(extra='forbid'); _doc: list[str]=[];
      x:int` gives `model_fields == ['x']`, and `M.model_validate({'x':1,'_doc':['a']})` raises "_doc
      Extra inputs are not permitted".
    reproducer: see the evidence probe (pydantic 2.13.4).
    fix: Specify `doc: list[str] = Field(default_factory=list, alias="_doc")`, give the fixture
      `six_max/lag.json` a `_doc`, and assert it loads. Cost: one line and one assertion.

  - severity: minor
    where: spec §2 "The merge"; `models.py:499` (`postflop: PersonaPostflop | None = None`)
    problem: `PersonaPack.postflop` may be `None`. An override with `postflop` keys applied to such a
      base pack would crash with a TypeError or AttributeError that does not name the file. That breaks
      the §7 rule "every override problem raises with the file name". All shipped packs have a postflop
      block, so this only bites third-party or test packs.
    evidence: `models.py:499`
    reproducer: none (edge case)
    fix: Add "override has postflop keys but the base pack has no postflop block" to the §4 error list.
      Cost: one check and one test.

  - severity: minor
    where: spec §4 "Golden fingerprint" and roadmap M2 pass/fail ("9-max output byte-identical except
      for hands the board-straight fix changes")
    problem: optional. A single SHA over 360 hands cannot show which hands changed. M2 must change both
      constants: 9-max because of the board-straight bug fix, 6-max because of the LAG override. The
      spec says only that the constants are frozen "for the rest of the slice".
    evidence: roadmap `bot-realism-6max.md:146-147`
    reproducer: none
    fix: Either store per-hand digests, or add one line saying M2 re-pins both constants with a reported
      hand-level diff. Gain: M2's check becomes checkable, and re-pinning does not read as weakening a
      test. Cost: a slightly larger constant, or one sentence.

  - severity: minor
    where: spec §3 grep check `grep -n "_packs()\|_seat_personas("`; spec §1 `sim_session.py`
    problem: optional.
      - The grep cannot tell a zero-size `_seat_personas(seats)` call from a correct one. mypy and
        pytest would catch it anyway, because the argument has no default.
      - `sim_session.py` is 2021 lines, and the spec grows it without flagging, which the engineering
        standard requires.
      - A second `Literal[6, 9]` would duplicate `app/schemas/simulate.py:28`.
      - M1's spec (`docs/ai-dlc/specs/m1-6max-baseline.md:66`) still pins "raw as-loaded
        `load_persona_packs()`".
    evidence: see the listed lines
    reproducer: none
    fix: Replace the grep with "mypy passes, since the size argument is required". Add one sentence
      flagging the file size. Optionally have `schemas/simulate.TableSize` re-export the domain alias;
      that touches one file outside §1.
