# Findings — M1b, bot settings that can differ by table size
scheme: 2026-09-26

**Bottom line:** one blind review round of the spec approved it with fixes. All eight findings
were checked against the code before being accepted, and seven are folded into spec rev 2. None
touched 9-max safety. The four major ones would each have let M2 (the LAG retune) hit a silent
failure:
- a dial it could not override;
- an override the settings-file safety checks never saw;
- tests that pass without testing anything.

The one rejection is a historical M1 document that stays as written.

- **Pass 1 (spec rev 1), 2026-09-27:**
  - **Reviewer:** Claude `refuter` on Opus, blind. It received the spec, contracts, invariants
    and verify commands, and not the interview record.
  - **Checklist:** contract breaks, regressions, missed edge cases, and vacuous pass/fail checks.
  - **Why this pass:** it was the first review.
  - **Same-family only:** Codex (`gpt-6-sol`) could not reach its service from the sandbox
    ("workspace routing discovery failed"). The Gemini fallback's login timed out.
- Raw report: `../reviews/m1b-spec-r1-refuter.md`.
- **Director re-checks:**
  - **F1:** on the LAG, adding `size_elasticity` fails, and loads once `stickiness` is removed.
    The TAG and nit behave the same.
  - **F2:** all 11 checks in `test_persona_pack_invariants.py` take the 9-max-only `packs` fixture.
  - **F5:** a `doc` field with `alias="_doc"` under `extra="forbid"` accepts `_doc`.
- whole-branch review: not yet run.

| ID | Target | Severity | Finding | Evidence | Status | Resolution test |
|----|--------|----------|---------|----------|--------|-----------------|
| F1 | spec §2 merge | major | The merge could only set keys, so presence-checked validators made some single dials impossible to override (adding `size_elasticity` to LAG/TAG/nit always fails while `stickiness` is present). | Director probe: add `size_elasticity` gives ERR; after popping `stickiness` it loads. `models.py` `_stickiness_authorship`. | fixed: rev 2 §2, an override `null` deletes the key; §4 tests | `{size_elasticity: 1.0, stickiness: null}` loads with no `stickiness`; `{aggression: null}` fails naming the file |
| F2 | spec §2 coverage; `test_persona_pack_invariants.py` | major | Only position coverage was extended to 6-max. The grid, gradeable-size, 3-bet-cap, one-size and shadowing checks would never see an override. | `test_persona_pack_invariants.py:34-35` fixture is `load_persona_packs()`; 11 tests take it | fixed: rev 2 §2, fixture parametrised over 9 and 6, plus a merged-fixture run | each check runs at `table_size=6` and on the merged fixture |
| F3 | spec §4 liveness and live session | major | Play-level override tests were conditional on situations they never forced, so they could pass vacuously, and a mis-wired second bot call site could go unnoticed. | `sim_session.py:257,274` draw from `secrets`; bot sites at `:275` and `:1089` | fixed: rev 2 §4, LAG pinned to LJ in `play_one_hand`; live test rewrites every villain to LAG and must see each call site within a cap | the test fails if either site is wired to 9 or never fires |
| F4 | spec §4 villain range | major | "Serves without error" stays green if the range endpoint reads 9-max packs while the bot plays the override. | `sim_session.py:1516`; contracts risk #2 | fixed: rev 2 §4, asserts range classes == `{"AA"}` at 6 and wider at 9 | planting `_packs(9)` at the endpoint turns the test red |
| F5 | spec §2 `_doc` | minor | A pydantic field named `_doc` is private, so `extra="forbid"` would reject M2's cited override files. | Reviewer probe (pydantic 2.13.4); Director probe of the alias fix | fixed: rev 2 §2, `doc` with `alias="_doc"`; fixture carries `_doc` | the fixture with `_doc` loads |
| F6 | spec §2 merge; `models.py:499` | minor | Postflop keys against a base pack with `postflop: None` would crash without naming the file. | `models.py:499` | fixed: rev 2 §2 and §4 error list | the error test names the file |
| F7 | spec §4 golden | minor | A single hash cannot show which hands changed, so M2's "identical except the board-straight hands" check would be uncheckable. | roadmap M2 pass/fail | fixed: rev 2 §4, per-hand digest helper plus a re-pin-with-report rule for M2 | the helper returns per-hand digests |
| F8 | spec §3 grep; `sim_session.py` size; `TableSize`; M1 spec line 66 | minor | The grep check was weak (mypy catches omissions anyway); the growth of the oversized `sim_session.py` was unflagged; a second `Literal[6, 9]` would duplicate `schemas/simulate.py:28`; the M1 spec still says "raw as-loaded". | the cited lines | fixed: rev 2 §3 swaps the grep for mypy; §1 flags the file size; `TableSize` moves to `deck.py` and `schemas` imports it. The M1 spec part is rejected: that spec is the closed record of M1, and the live contract (the `sixmax_baseline.py` docstring) is updated in this slice | mypy green; one `TableSize = ` definition |
