# Bot Realism at 6-max Roadmap — updated 2026-10-03
status: approved (owner, 2026-09-25); amendment of 2026-10-03 approved (owner, 2026-10-03)

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
- **Target changed (owner, 2026-10-03): the bots aim at a live $1/$2 card room, not online
  6-max.** An audit found the 6-max table plays like an online game. It has one recreational
  player out of five, 85% heads-up flops and 2.5bb opens, and its stat ranges come from online
  tracking-software guides. The live retarget starts with sourced live numbers (L1) and a
  measured gap (L2), both of which change no bot behaviour.
- **Next action:** the owner plays about 200 Challenge hands and gives the M2 verdict on the
  retuned LAG. L1 and L2 can run meanwhile. M1, M1b and R1 are done (archived in
  `bot-realism-6max-archive.md`).

## North-star outcome
- **Outcome:** in one 200-hand 6-max Challenge session, the owner rules each bot "plays like its
  type".
  - **Baseline** (session `4b35736f`, 2026-09-25): 3 of 5 pass on the owner's feel. The owner
    flagged the LAG and the calling station.
  - **Target:** 5 of 5.
- **Supporting check, never the verdict:** each bot's stats land inside **live $1/$2 ranges**
  (re-anchored by the owner on 2026-10-03; M1 and M2 used online 6-max ranges, which stay as
  their record). Each range has a cited source and comes from L1. The stats are measured on 5,000
  or more simulated hands:
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
- **The 2026-10-03 audit** (`../reviews/coach-math-audit-2026-10-03.md`, findings 12–17) was
  checked by nine independent reviewers. It found:
  - the 6-max lineup is nit, TAG, TAG, LAG, station;
  - 84.7% of flops are heads-up, and the station starts 99% of limped pots;
  - median opens are 2.5bb, and the repo's two research docs disagree on live open size;
  - 57% of seat-hands start above 150bb;
  - no rake.

  It refuted river over-bluffing: bots already under-bluff, as live players do.
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
  - **Built (2026-10-01) on `feat/m2-lag-retune`:** the board-made-hand fix at both table sizes
    (its own commit), then the LAG's 6-max override (opening ranges by seat, smaller raises, fewer
    raises when bet into). Spec `specs/m2-lag-6max-retune.md`; results report
    `research/bot-realism-6max/m2-lag-retune.md`. **The box stays unticked:** the project owner's
    200-hand verdict is this slice's check.
  - **Measured result (seed 20260926, 6,000 hands, simulated):**
    - opening rates: LJ, HJ, BTN and SB inside their sourced figures; CO misses on the judged seed
      (28.5% against 33), waived by the project owner on 2026-10-01 because held-out seeds 1-5 and
      6-10 give 33.5%;
    - raise rate when bet into 18.1% (band 10-20%, approximate); raises at 4x or more 5.9% (at most
      10%, approximate), median 2.66x;
    - 9-max unchanged apart from the fix's hands: 13 of 4,000 changed, all attributed;
    - no other bot's settings touched;
    - known gaps: PFR 18.5% is under the 20 floor; the LAG opens less than the TAG at LJ and HJ
      (accepted) and on the judged seed also at CO; flop c-bet and showdown rate have no sourced
      range, so the full supporting check is not claimed.
    - post-flop overlap: the LAG raises into bets 18.1% of the time against the TAG's 23.6% and the nit's
      18.2%, and only 5.9% of its raises are 4x or more (TAG 25.9%); accepted for now by the project
      owner on 2026-10-01. The 200-hand verdict records it; the remedy if needed is a second LAG settings change.
  - **Assumption status:** untested. The simulation passing does not prove settings alone suffice:
    the project owner judges the fix and the settings together, and the matched replays report each
    part's share.

> **Lanes added 2026-10-03 follow the six-phase template** in `coach-math.md` ("How every lane
> runs"): research, evaluate, ideate, plan, build, verify. Builds stay locked until the lane's
> riskiest assumption holds. L1 and L2 change no bot behaviour, so they may run before the M2
> verdict. **Phases they skip, and why:** L1 is the research phase of the live retarget, and L2
> is its evaluate phase. Neither changes code, so neither has its own ideate, plan or build;
> those phases belong to "Make the 6-max table live-shaped" in NEXT, which consumes both.

- [ ] **L1 — Source live $1/$2 benchmarks.** ICE 9·5·7.
  - **Problem:** every stat range the bots are judged against comes from online
    tracking-software guides. No committed source describes a live $1/$2 table.
  - **Outcome link:** this supplies the supporting check's live ranges, and it sets the target
    for the live-table build.
  - **Research, first principles** (`docs/research/live-low-stakes-benchmarks.md`):
    - **What each stat measures**, and how seat count, rake and straddles move it. The stats
      are:
      - VPIP and PFR;
      - open-limp rate and over-limp rate;
      - players to the flop;
      - open size by seat and by number of limpers;
      - 3-bet rate;
      - c-bet;
      - WTSD and W$SD (won money at showdown);
      - river bet and raise rates.
    - **Table make-up:** the share of recreational players versus regulars at live $1/$2, and
      the usual seat count.
    - **The open-size conflict:** settle the disagreement between `01-preflop-strategy.md` (4–6bb
      live) and `10-bet-sizing-by-node-persona.md` §3 (3bb).
    - **Labels:** every figure is labelled sourced or approximate. R1 found no public population
      data by stack depth, so gaps are expected and are stated, not filled.
  - **Pass/fail:** the report exists and does all of the following:
    - opens with a plain summary;
    - gives a range plus a source and a label for each stat;
    - settles the open-size conflict;
    - describes the table make-up.
  - **Appetite:** one `/research` pass, blind-verified.
  - **No-gos:** no hand-history imports (a global no-go); online ranges are never presented as
    live.
  - **Riskiest assumption:** sourced live numbers exist for the core stats, which are VPIP,
    players to the flop and open size.
  - **Cheapest test:** the research itself. If fewer than three core stats are sourced, the
    supporting check becomes direction-only, and the owner's feel carries the verdict alone.
  - **Assumption status:** untested.

- [ ] **L2 — Measure the gap to a live table.** ICE 8·7·8. It needs L1.
  - **Problem:** nobody knows how far each bot, and the table as a whole, sits from live play.
  - **Evaluate:**
    - run the existing tooling (`backend/tools/sixmax_baseline.py`, `table_stats.py`) on
      5,000 or more seeded hands at 6 seats;
    - build a gap table per bot and per stat, plus table-level gaps: players to the flop, limp
      rate, open size and the stack-depth spread.
  - **Pass/fail:** `docs/ai-dlc/research/bot-realism-6max/l2-live-gap.md` holds the gap table,
    the seeds and the commands that re-run it.
  - **Appetite:** about 1 day.
  - **No-gos:** no bot setting changes.
  - **Riskiest assumption:** the live gap is closable through settings and the lineup, not
    through decision code. The audit found one counterexample: the TAG has no over-limp option
    at all.
  - **Cheapest test:** tag every gap in the table "a setting reaches it" or "needs code". If most
    gaps need code, this roadmap's bet ("settings, not decision code") fails for the live
    retarget, and the roadmap returns to framing.
  - **Assumption status:** untested.

## NEXT (validated problems, not yet spec'd; each waits on M2's verdict)
- **Make the 6-max table live-shaped** (the owner set the direction on 2026-10-03; it needs L1,
  L2 and the M2 verdict).
  - **Problem today** (audit findings 13–16, 6,000 simulated hands): one recreational player in
    five seats; 84.7% of flops heads-up; the station starts 1,432 of 1,452 limped pots; TAG and
    LAG open to a median 2.5bb; 57% of seat-hands start above 150bb after 500 hands.
  - **Research and evaluate:** L1 supplies the live targets, and L2 the measured gap per stat.
  - **Ideate:** lineup options. More recreational seats can reuse the passive fish and maniac
    that 9-max already has, which reverses the 2026-09 lineup choice. Other options:
    - over-limping and wider calls behind limpers;
    - live open sizes;
    - a spread of buy-ins.
  - **Sub-slices:** the lineup; limps and multiway pots; open sizes. Each is followed by a
    simulation re-measure, and the round ends with the owner's 200-hand verdict.
  - **Known collision:** more multiway pots mean fewer graded hero decisions. That is the
    grading-coverage item (lane 7) in `coach-math.md`.
- **Rake** (the owner approved it on 2026-10-03, at both table sizes).
  - **The default to build:** about 10% of the pot, capped at $5 plus a $1 promo drop, with no
    flop no drop (a pot that ends preflop pays nothing). At $1/$2 the cap is 3bb. Other rules
    (a flat drop, other caps) are configuration, not the target.
  - **Research:** mostly done (`docs/research/rake-and-adjustments.md`). Top-up: the per-player
    cost is unsourced. The "35–60 bb/100" figure is the whole table's drop; one player's share
    is roughly 4–10 bb/100, an estimate (audit finding 17). Also cover split pots, side pots
    and uncalled bets.
  - **Evaluate:** the ledger before and after on seeded hands; the hero's net result with and
    without rake; how often the cap binds.
  - **Ideate:** where rake is taken (engine settlement versus the ledger), how it is shown at
    the table, and how it is configured.
  - **Sub-slices:** engine settlement and the ledger; the table display; then rake in the
    coach's pricing (lane 8 of `coach-math.md`).
  - **Byte-identity note:** rake changes settlement directly, and later bot decisions only
    through the smaller stacks it leaves (stacks carry over, and the commitment dial reads
    stack ÷ pot). The 9-max check therefore confirms that hands are identical up to the first
    raked pot, and that every later divergence traces to a stack difference.
- **Bots judge commitment from their own stack, not the effective stack** (audit finding 12).
  - **Evidence:** `table/play.py:300` and `personas_postflop.py:1889` use the bot's own stack.
    In 1–4% of bot postflop decisions, the own and effective stack-to-pot ratios point opposite
    ways (12 × 500 seeded hands).
  - **Research:** effective stack and SPR from first principles (shared with `coach-math`
    lane 4's research).
  - **Evaluate:** count the affected decisions per bot at 6 seats, and list hands where the
    wrong commitment cost or won chips.
  - **Ideate:** pass the effective stack into the existing dial; or a separate effective-SPR
    input; or a clamp only where the two disagree.
  - **Sub-slices:** 6-max first (owner, 2026-10-03), then 9-max only with an owner ruling.
  - **The cost:** it changes decision code, so it needs a named exception like the
    board-straight fix.
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
    - WTSD is 48–80%, against roughly 25–30% for real regulars (an online figure; L1 replaces it);
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
  - **R1's research is in** (`docs/research/deep-stack-strategy.md`; SPR cutoffs sourced,
    direction only elsewhere). The first step is its own measurement: how often deep stacks
    (over 150bb) lead to bad commitments, taken from the owner's real sessions and from a
    simulation run with deep starting stacks.
  - **The grader's 100bb assumption** is now `coach-math.md` lane 4 (stack depth), not here.

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
- **This roadmap and `coach-math.md` are both active** in `docs/ai-dlc/profile.md` (owner,
  2026-10-03). A session asks the owner which one to work on. This roadmap replaced
  `phone-and-6max`, whose remaining items are checks the owner owes, not builds.
- **Finished slices** M1, M1b and R1 are in `bot-realism-6max-archive.md`.
- **The flywheel roadmap is closed:** the owner's 200-hand Challenge session `4b35736f` met its
  last box.

## Out of scope / no-gos
- **9-max stays byte-identical.** Every change is 6-max-only, with two exceptions:
  - the board-straight bug fix (owner, 2026-09-25);
  - rake (owner, 2026-10-03). It changes how pots are settled, and later bot decisions only
    through the resulting stacks; see the rake item in NEXT for the check.
- **Not planned** (owner, 2026-10-03): bet-sizing tells, bots adapting to the hero, and bb/100 with
  a confidence interval.
- **The coach's grading** belongs to `coach-math.md`, not here.
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
