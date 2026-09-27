# Bot Realism at 6-max Roadmap — updated 2026-09-25
status: approved (owner, 2026-09-25)

## Bottom line
- **Goal:** make every bot at the 6-max table play like its type, judged by the owner in a
  200-hand Challenge session. Today the owner flags 2 of the 5 bots (the LAG and the calling
  station). A blind reviewer of the same 200 hands flagged 4 of the 5.
- **The bet:** these problems can be fixed by changing each bot's settings files (the values in
  `content/personas/*.json`) at 6-max only, without rewriting how bots make decisions. There are
  two named exceptions: M1b (settings that can differ by table size) and the board-straight bug
  fix.
- **Testing the bet first:** measure all five bots on thousands of simulated 6-max hands, then
  retune the LAG alone and have the owner play it. Tuning the other bots waits until the owner
  judges the LAG.
- **Running alongside:** research on how poker strategy changes as stacks get deeper, which feeds
  the deep-stack lane.
- **Next action:** `/ai-org:spec` for slice M1 (the 6-max measurement).

## North-star outcome
- **Outcome:** in one 200-hand 6-max Challenge session, the owner rules each bot "plays like its
  type".
  - **Baseline** (session `4b35736f`, 2026-09-25): 3 of 5 pass on the owner's feel. The owner
    flagged the LAG and the calling station.
  - **Target:** 5 of 5.
- **Supporting check, never the verdict:** each bot's stats land inside real 6-max ranges, with a
  cited source for each range. The stats are measured on 5,000 or more simulated hands:
  - VPIP and PFR — how often a bot plays a hand, and how often it raises before the flop;
  - opening rate by seat;
  - c-bet — how often the pre-flop raiser bets the flop;
  - WTSD — how often a bot that sees the flop goes to showdown.
- **Separation guard:** the fixes must not blur the types. It is checked in the owner's verdict:
  the owner must still be able to name each bot's type. The hand-200 guess, if answered, is the
  record.
- **How a round works:** tune → simulate → the owner plays ~200 hands → the owner's verdict. No
  new round starts before the verdict on the last one.

## Evidence this roadmap starts from
- **The owner's notes, 2026-09-25:**
  - The LAG plays like a maniac: aggressive at odd times and too loose, especially from early
    seats.
  - The calling station's pre-flop range feels too wide, and it bets into the last aggressor
    (hand 86).
  - The other bots feel good.
- **The blind review of the same 200 hands, done without the owner's notes:**
  `../reviews/bot-review-200-hands-2026-09-25.md`.
  - It agreed on the LAG.
  - It rated the station the most realistic bot, and missed hand 86.
  - It added three problems: the regular bots play backwards after the flop, every bot plays too
    tight behind a limper, and every bot goes to showdown far too often.
  - Its stats come from 10–34 chances per seat, so they are indicative only.
- **The LAG's early-seat width is authored, not a bug.** At 6-max the first seat is LJ, because
  6-max drops the three UTG seats (`backend/app/domain/table/deck.py:34-38`). The LAG's LJ open
  rate is authored at 37.6% (`content/personas/ladders/lag.unopened.json`), which matches the
  observed 39%. A real 6-max LAG opens about 20–25% there (approximate — the reviewer's estimate;
  M1 sources it).
- **Two facts that shape M2 (blind roadmap review, 2026-09-25):**
  - **There is no 6-max-only settings path today.** Each bot has one settings file, read the same
    way at 6 and 9 seats (`backend/app/domain/personas.py:41-54`, `play.py:234`). So "change 6-max,
    keep 9-max identical" first needs settings that can differ by table size (slice M1b).
  - **Some all-ins are a code bug, not a setting.** A bot treats any straight or better as a
    monster, even when the board alone makes it and the bot's own cards add nothing
    (`backend/app/domain/personas_postflop.py:121-122`). This is the likely cause of the "all-in
    with hands that only tie the board" plays (hands 30 and 134). Retuning cannot fix it.
- **Stacks now carry over** (PR #239, 2026-09-25). The owner's own stack reached 455bb, while the
  bots are tuned for about 100bb (`spr_commit`, the stack-to-pot commitment dial, is authored per
  persona).

## NOW (in order; ICE = impact · confidence · ease, each out of 10)

- [ ] **M1 — Measure the 6-max baseline.** ICE 9·8·6.
  - **Problem:** every number we have comes from 200 hands, which is too few per bot and per seat
    to tune against.
  - **Outcome link:** it provides the stats half of the north star, and it checks that the
    simulator can stand in for the owner's play before any tuning relies on it.
  - **What it delivers:**
    - Teach the bot-vs-bot simulator (`backend/tools/export_analytics.py`, 9-max only today) to
      run the live 6-max lineup: nit, LAG, TAG, TAG and station, with a TAG as the stand-in for
      the hero seat.
    - Run 5,000 or more hands at the existing 95–105bb starting spread. Deep-stack effects belong
      to the deep-stack lane, not here.
    - Source the real 6-max ranges each stat is judged against, cited with the existing
      `(format, pool, source)` provenance rule. Reuse `docs/ai-dlc/research/rfi-seat-provenance.md`
      where it applies. Today's persona bands are 9-max.
    - Produce a per-bot stats table set against those ranges.
  - **Pass/fail:** the report exists at `docs/ai-dlc/research/bot-realism-6max/m1-baseline.md`
    and does all of the following:
    - gives every stat above with its sample size and a 95% confidence interval, per bot;
    - cites a real 6-max range for each stat, or marks the stat unsourced;
    - reports the fidelity check below.
  - **Appetite:** a few days.
  - **No-gos:**
    - no change to any settings file;
    - no change to bot behaviour;
    - 9-max export output stays byte-identical (the existing default-path regression tests pass
      unchanged).
  - **Riskiest assumption:** simulated bot-vs-bot hands reproduce what the owner sees at the
    table.
  - **Cheapest test** (fixed before the run):
    - Compare each bot's VPIP, PFR and flop c-bet rate between the simulation and the 200 real
      hands in session `4b35736f`. That is up to 15 comparisons.
    - **A comparison is eligible only if the real hands gave it 30 or more chances** (owner ruling,
      2026-09-25).
    - **Fewer than 8 eligible comparisons: the result is "can't tell yet".** Tuning does not start.
      The owner plays more Challenge hands, up to the 500–1,000 already offered, and the check
      re-runs on the combined sessions.
    - **Passes** if at most one eligible real rate falls outside the simulated 95% confidence
      interval widened by the real sample's own interval (one miss is a pass: owner ruling,
      2026-09-26). **Fails** if two or more eligible comparisons fall outside it. On a failure M1 stops and reports, and nothing downstream starts.
    - Known limit: the owner, not a stand-in, sat in the real hero seat.
  - **Assumption status:** untested.

- [ ] **M1b — Let bot settings differ by table size.** ICE 6·8·7. Owner ruled it in, 2026-09-25.
  Can run alongside M1; M2 needs both.
  - **What it delivers:** a bot's settings can carry 6-max-specific values, while 9-max keeps
    reading exactly what it reads today.
  - **Pass/fail:**
    - 9-max bot decisions are byte-identical on a fixed seed set;
    - one 6-max override is proved live by a test.
  - **No-gos:** no settings values change in this slice.
  - **Riskiest assumption:** an override layer can be added without making settings hard to
    reason about.
  - **Cheapest test:** the byte-identical 9-max check.
  - **Assumption status:** untested.

- [ ] **M2 — Retune the LAG only, at 6-max only.** ICE 8·5·7. **Starts only after M1 passes and
  M1b is merged.**
  - **Problem:** the owner's top complaint. The LAG is too loose from early seats, and aggressive
    at odd times: 5× raises into bets, bluff-raising the station, and all-ins with hands that only
    tie the board.
  - **Outcome link:** it moves one bot toward the north star. More importantly, it tests the whole
    roadmap's bet.
  - **What it delivers:** 6-max-only LAG settings through M1b, each value cited with the
    `(format, pool, source)` provenance rule.
  - **Also in scope (owner ruling, 2026-09-25):** the board-straight bug fix (see Evidence),
    applied at both table sizes. It is the one sanctioned 9-max change. Land it as a separate
    commit, so the simulation can report its effect apart from the LAG retune.
  - **Pass/fail:**
    - the simulated LAG stats land inside the cited 6-max LAG ranges;
    - 9-max output is byte-identical except for hands the board-straight fix changes;
    - the owner plays about 200 Challenge hands and rules the LAG "plays like a LAG".
  - **Appetite:** one round.
  - **No-gos:**
    - no change to the decision code, apart from the board-straight fix;
    - no other bot is touched.
  - **Riskiest assumption:** settings changes, plus the board-straight fix, can make the LAG feel
    right. The owner judges both together (owner's choice, 2026-09-25), so a pass is not proof
    that settings alone suffice. The separate commit lets the simulation report each part's
    share.
  - **Cheapest test:** this slice itself.
    - If the owner still flags the LAG, the other lanes do **not** proceed.
    - Instead the roadmap returns to framing: are the defects in the decision code rather than
      the values?
  - **Assumption status:** untested.

- [ ] **R1 — Research how strategy changes with stack depth.** ICE 7·8·8. Runs in parallel with
  M1.
  - **Problem:** the bots are tuned for about 100bb, but live stacks now run from 50bb to 455bb.
    No committed source says how real players change strategy as stacks deepen.
  - **What it delivers:** a `/research` pass on expert and academic material:
    - how pre-flop ranges, commitment thresholds (stack-to-pot ratio, SPR) and post-flop
      aggression change from 100bb to 200bb and beyond;
    - any published studies, white papers or population metrics we can reuse, each dated and
      cited.
  - **Pass/fail:** `docs/research/deep-stack-strategy.md` exists and does all of the following:
    - opens with a plain summary;
    - gives numbers that the deep-stack lane can turn into settings, with sources;
    - labels every figure as sourced or approximate.
  - **Appetite:** one research pass.
  - **No-gos:** no solver tables (a global no-go). Sourced heuristics only.
  - **Riskiest assumption:** usable, citable numbers exist for deep-stack adjustments.
  - **Cheapest test:** the research itself.
  - **Assumption status:** untested.

## NEXT (validated problems, not yet spec'd; each waits on M2's verdict)
- **Calling station: pre-flop width and odd leads.**
  - **Evidence:**
    - The owner finds its pre-flop range too wide, and saw it lead into the raiser in hand 86
      (7♥5♥, bottom pair on the turn).
    - The reviewer found it folds strong limping hands like AQo at one flat rate, and sometimes
      calls off its stack with no pair.
  - **Open question:** the owner and the reviewer disagree on its pre-flop width, so M1's numbers
    decide.
- **The regular bots play backwards after the flop (the nit, LAG and TAGs).**
  - **Evidence** (reviewer):
    - the pre-flop raiser bets the flop only 20–50% of the time;
    - big pots are checked down;
    - bets into them are raised 26–29% of the time, at about 5×;
    - WTSD is 48–80%, against roughly 25–30% for real regulars;
    - the nit calls down like a recreational player and lost 238bb.
  - **Open question:** is this one shared cause or several?
- **Everyone plays too tight behind a limper, and the two TAGs are identical.**
  - **Evidence:**
    - The LAG raised the station's limp only 4 times in 24, and folded A4s, JTs and 55 behind it.
      Its limp-raising range is authored tighter than its first-seat open range.
    - Both TAG seats read from one settings file.
- **Deep-stack behaviour.**
  - **Evidence:** live stacks reach 455bb, while the commitment dials assume about 100bb.
  - **Direction (owner, 2026-09-25):** the bots adjust to depth. Stacks keep carrying over, with
    no table maximum.
  - **Waits on R1's numbers.** Its first step is its own measurement: how often deep stacks
    (over 150bb) lead to bad commitments, taken from the owner's real sessions and from a
    simulation run with deep starting stacks.
  - **Open question:** the grader's advice is also about 100bb-based. In scope or not?

## LATER (bets, no dates)
- **Bet:** once 6-max passes, the owner will stop choosing 9-max.
  - **Confidence:** medium.
  - **Test:** which table size the owner picks across the next ten sessions.
  - **Review:** after the north star is hit.
- **Bet:** the hand-200 blind check (guessing each bot's type) is a useful second realism signal.
  - **Confidence:** low. The owner skipped it on 2026-09-25.
  - **Test:** the owner answers it once and says whether it helped.
  - **Review:** after M2.

## Bookkeeping
- **This roadmap is `active:` in `docs/ai-dlc/profile.md`** (owner, 2026-09-25). It replaces
  `phone-and-6max`, whose remaining items are checks the owner owes, not builds.
- **The flywheel roadmap is closed:** the owner's 200-hand Challenge session `4b35736f` met its
  last box.

## Out of scope / no-gos
- **9-max stays byte-identical.** Every change is 6-max-only. The one exception is the board-straight
  bug fix (owner, 2026-09-25).
- **No change to the decision engine unless M2 fails,** and then only after re-framing. There are
  two named exceptions: M1b's table-size settings layer and the board-straight bug fix.
- **The repo's global no-gos still apply:**
  - no solver tables (heuristic EVs only, labelled approximate);
  - no hand-history imports;
  - no auth, accounts or hosting;
  - `spot_signature()` stays frozen.
- **Stack carry-over (#239) stays** (owner, 2026-09-25): no table maximum, no per-hand reset.
- **Not reopened by this roadmap:**
  - the paused persona-realism lane;
  - the flywheel's detection-rate research, i.e. whether a judge can tell bots from humans.
  - This roadmap succeeds the flywheel for the owner-facing goal, and its bot-detection
    machinery is not used here.
