# Finding ledger — S1, the 6-max table option

## Bottom line

One blind reviewer read spec rev 1 against the code and returned **FAIL** with thirteen findings.
**Eleven were accepted, one was narrowed, one was rejected.** Four of them needed the owner, who
ruled on all four the same day.

The review earned its cost twice over. Rev 1's headline argument was simply false — it claimed the
expensive hazard was the spaced-repetition key, which Simulate does not use — and rev 1 had no way
for the owner to choose a six-seat table at all, so the slice would have shipped unreachable.

Round 1 · reviewer: blind Claude `refuter`, Opus, high effort · 2026-09-18
Codex second opinion: **not run.** Codex cannot execute in this sandbox (its nested sandbox cannot
spawn a shell). Recorded as a gap, per the fail-open rule; no Claude agent was substituted under
the Codex name.

| # | Claim | Severity | Verdict | What I checked |
|---|---|---|---|---|
| 1 | §4's rationale is false: `table_size` on a Spot changes nothing on the Simulate path, so D1 is not delivered and Verify-by #10 passes vacuously | blocking | **ACCEPTED** | `grep -rn "\.table_size" backend/app` returns exactly one reader, `srs.py:63`. `spot_signature` callers are `drill.py:334,446` and `review.py:57` — Practice and review only. Simulate uses `_sim_signature` (`sim_session.py:1022,1051-1058`), parts `["sim", node_context, hero_position, facing]`, no table size, with a docstring saying the omission is deliberate. **Owner ruling: put the seat count in `_sim_signature`.** |
| 2 | The only Simulate preflop spot-construction call site, `grade_map_preflop.py:63-70`, is missing from the file list | blocking | **ACCEPTED** | Read it. `_preflop_spot` calls `build_spot` with no seat count and is the funnel for all five preflop call sites (`:99,128,158,192,227`). `scenarios.py:275` sits inside `build_spot`, which has no state, so the value can only arrive from here. Without this file §5 is unreachable. |
| 3 | There is no way to choose six seats, and the Definition of Done forbids adding one | blocking | **ACCEPTED** | `client.ts:108-116` sends `{ mode }` alone; `SimModeChoice.tsx` is a two-card chooser typed `(mode: SimMode) => void`. Rev 1 named none of the three files. **Owner ruling D3: four cards on the sit-down screen.** |
| 4 | Button *seeding* is a fourth hardcoded site and the roadmap named it | blocking | **ACCEPTED** | `sim_session.py:931` is `button_seat=secrets.randbelow(9)`. At six seats it lands out of range about a third of the time and persists onto the session row. Rev 1 said "three sites"; the contract map dropped it too. Both corrected. |
| 5 | Seven of the twelve `table_size=9` sites are Practice-only, so §4 contradicted the spec's own out-of-scope line and would orphan real review history | should-fix | **ACCEPTED** | Traced every caller of the seven builders: all reach `drill.py` only. `grade_map_postflop.py` mentions them in comments at `:33-34,104,375,422,531` but imports only `_combos_for` and `_find_entry`. Practice genuinely calls `spot_signature()`, which genuinely hashes `table_size`, so a non-9 value there orphans SM-2 history. **Scope cut from twelve sites to five.** |
| 6 | A 6-max Challenge blind check displays a provably false roster | should-fix | **ACCEPTED** | `blindCheck.ts:46-56` hardcodes the 9-max eight as `HOUSE_LINEUP`/`HOUSE_SEATS`, rendered at `SimBlindCheck.tsx:204`. The file's own comment warns it "goes on asserting a false lineup under a heading that says it is the truth". **Owner ruling D4: make it table-size aware.** |
| 7 | The slice's riskiest-assumption test lives in the roadmap and was absent from the spec | should-fix | **ACCEPTED** | Roadmap names "a headless run asserting a set of 6-max hands grade *identically* to the equivalent 9-max hands". Rev 1's nearest step was "hero decisions grade at every 6-max position" — presence, not equality. Restored as Verify-by #4. |
| 8 | D2 contradicts the approved roadmap's pass/fail, which is a CLAUDE.md tripwire | should-fix | **ACCEPTED** | Roadmap says "five **distinct** personas"; D2 is nit, TAG, TAG, LAG, station — four distinct across five seats. Escalated rather than reconciled. **Owner ruling D2: keep the lineup, amend the roadmap wording.** |
| 9 | §2 as written breaks Verify-by #2, because ~150 call sites pass no seat count | should-fix | **ACCEPTED** | `test_table.py:53` calls `positions_for_button(0)` bare. A required parameter breaks them all, and criterion 2 forbids editing a 9-max test. Rev 2 states that every new domain parameter defaults to 9, and names the silent-miss cost that default creates. |
| 10 | Verify-by #3 is unfalsifiable — no mechanism named for obtaining "before the change" | should-fix | **ACCEPTED** | A test written after the fact comparing the new code to itself would pass. Rev 2 requires capturing the fixture from `origin/main` first and committing it. |
| 11 | `sim_session.py:262`'s `deal_hand` call is missing; with a default of 9 it fails silently | optional | **ACCEPTED** — promoted to blocking | A six-seat table would pop eighteen hole cards before the board, drawing it from a different deck offset. No crash, no test failure. Given finding 9's default-to-9 rule, this is precisely the silent miss that rule creates. Raised above the reviewer's own severity. |
| 12 | Two citations are wrong | optional | **ACCEPTED** | `SimTable.tsx:19-24` is the constant and a comment; the geometry is `slotStyle(i, n)` at `:42-49`, called with `ordered.length` at `:188`. And rev 1 claimed every `_SEATS` use in `engine.py` can read from state, but `:81-82,88,122` are inside `start_hand`, which has none. Both fixed. |
| 13 | Stale nine-seat claims beyond the two named | optional | **ACCEPTED** | Spot-checked `types.ts:221,585`, `models.py:68,79-81`, `engine.py:38,57,74`. Rev 2 adds a docstring sweep. This repo already has one stale docstring that cost a session. |

## The one narrowed finding, from the earlier contract scan

The contract scan (not this review) claimed 6-max hands would be graded against wrong ranges,
because a 6-max LJ is first to act where a 9-max LJ is seventh. **Narrowed, not accepted.** The
lookup is `_find_entry(NodeContext.RFI, hero.position, None)` at `grade_map_preflop.py:96` — keyed
on position, not player count — and the six 6-max seats are the six *latest* 9-max seats, so
players-behind is identical: LJ has five behind it at both sizes. Opening width is governed by
players-behind, so the ranges transfer. The roadmap's central bet survives.

The reviewer independently agreed, listing it under "verified clean".

## Verified clean by the reviewer, recorded so it is not re-checked

The 6-max rotation slice preserves the 9-max worked example at `test_table.py:52-63`;
`(button+3) % 6` lands on LJ preflop and `_close_street`'s SB-first walk is correct at six;
`grade_map_postflop.py`'s four sites all have a `HandState` in scope; `range_estimate.py` is
accurately described and `history.starting_stacks_bb` already carries the right length; migration
0015's additive-nullable pattern is the right model and SQLite backfills the `server_default`, so
pre-migration rows read 9 rather than NULL; `PokerTable.tsx:11,47` is genuinely a separate copy, so
Practice and Quiz do not bleed.

## What this round changed about the slice

- **Shrunk:** grading scope from twelve sites to five, because seven were Practice-only.
- **Widened:** a sit-down control (three frontend files), a table-size-aware blind check (two more),
  a fourth and fifth session-service site, and a docstring sweep.
- **Redirected:** D1 moves from `spot_signature` to `_sim_signature`, which is where Simulate's key
  actually lives.
- **Hardened:** the byte-identical claim gets a captured fixture instead of an assertion, and the
  roadmap's grade-equality test is restored as the slice's central check.
