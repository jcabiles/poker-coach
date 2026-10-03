# Coach Math Roadmap — updated 2026-10-03
status: approved (owner, 2026-10-03)

## Bottom line
- **Goal:** the coach's advice is correct No-Limit Hold'em (NLHE). It reads hands right, prices
  calls right, and follows real betting rules, so the owner never learns a wrong lesson from it.
- **The bet:** most wrong answers come from a few faulty *inputs*, namely how the coach labels a
  hand and how it prices a call, rather than from its whole scoring design. If fixing the
  inputs still leaves answers wrong, the scoring design itself needs rework.
- **How we will know:** a fixed set of 25 textbook spots, each with a sourced answer, runs as a
  test. About half are expected to fail today; lane 0 measures the real number.
- **Next action:** lane 0, which builds the textbook spot set and records the baseline.
- **Runs alongside** `bot-realism-6max.md` and changes no bot behaviour. The evidence for every
  lane is `docs/ai-dlc/reviews/coach-math-audit-2026-10-03.md`.

## North-star outcome
- **Outcome:** the share of textbook spots the coach answers correctly.
  - **Baseline:** TBD, measured in lane 0. The estimate is about 13 of 25 passing.
  - **Target:** 0 failing. Every spot with one right answer passes; a spot where sources differ
    passes when the coach's answer is inside its sourced set of acceptable answers.
  - **What it does not prove:** 25 spots show the coach is right on *those* spots, not on every
    street, bet size, stack depth and board. Two things widen it: the spots are spread on
    purpose across those dimensions (lane 0), and every lane's verify phase regrades a seeded
    sample of real graded decisions and explains every verdict that flips.
- **Guards (must not regress):**
  - the bots are unchanged: a bot-only simulation is byte-identical at 6 and 9 seats (lane 6
    asks the owner if its rules fix changes any bot decision);
  - the share of hero decisions that get a grade does not fall (seeded sweep, 2026-10-03:
    57.7% preflop, 3.5% postflop);
  - `make check` stays green.

## How every lane runs (owner-approved template, 2026-10-03)
Each lane passes through six phases in order. A phase is skipped only with a written reason in
the lane itself. **Build phases stay locked until the lane's riskiest assumption has been tested
and holds.**
1. **Research, from first principles.** For every concept the lane touches, write down the
   definition, the derivation (why the formula is what it is), its sub-components, worked
   examples with numbers, and where sources disagree. Output goes to `docs/research/`. Every
   figure is labelled *sourced*, *derived* or *approximate*, and a blind reviewer checks the math.
2. **Evaluate, before changing anything.** Record the baseline number the lane must move, the
   spots that fail and why, and the blast radius: which tests, fixtures and live verdicts would
   change. Pass/fail is fixed as a number here, not after the build.
3. **Ideate deeply.** At least three genuinely different designs, generated with
   `propose-ideas`. Each states its gain, its cost, and what it would still get wrong. Where the
   owner already agreed a design, that design is the default, and the others must beat it with
   recorded evidence. The owner picks.
4. **Plan.** Run `/ai-org:spec` on the chosen design to get the spec, the tickets and a
   contract scan. Hand it the lane's problem, outcome link, pass/fail, appetite and no-gos.
5. **Build in small sub-slices.** Each sub-slice is one PR with a test that fails before it and
   passes after. Each one names the textbook spots it flips (their `xfail` markers come off).
6. **Verify.** Re-run the spot set, the guards and the seeded regrade sample. Results go to a
   lane report under `docs/ai-dlc/research/coach-math/`.

## NOW (2-week appetite, in order; ICE = impact · confidence · ease, each out of 10)
The four lanes total about 8 working days, which leaves about 2 days for owner decisions and
slippage. **If time runs short, defer in this order:** 2c (implied odds, which pairs naturally
with the stack-depth lane in NEXT), then 1c (the draw taxonomy beyond flush and straight draws).

- [ ] **Lane 0 — The textbook spot set (the measuring stick).** ICE 9·8·8.
  - **Problem:** there is no objective way to say whether the coach is right. Each audit
    re-derives the answers by hand.
  - **Outcome link:** this lane *is* the north-star measurement.
  - **Research:** for each spot, the textbook answer and why. The topics are:
    - hand-ranking rules: best five of seven, the ace-low straight, the board plays,
      counterfeiting;
    - price math: pot odds, alpha and MDF (minimum defense frequency), each derived;
    - draw odds: outs, one card versus two to come, and the rule of 2 and 4 with its error;
    - effective stack and SPR (stack-to-pot ratio);
    - card-room betting rules for short all-ins.
  - **Classify every spot:**
    - **math-determined:** one right answer (a wheel is a straight; a call price is arithmetic);
    - **judgment:** sources differ (K2o folding in the big blind; 55 opening under the gun
      live). A judgment spot gets a set of acceptable answers, each with a source.
  - **Evaluate:** run each spot through the same path the Simulate table uses (mapper →
    provider → grader) and record pass or fail. That count is the baseline.
  - **Ideate:** the spot list, not designs (a test file has one shape; reason for skipping the
    three-designs step). 25 spots, spread on purpose:
    - hand reading, about 8: the wheel; a board straight; a board flush with no card of the
      suit; counterfeited two pair; underpair plus a board pair; gutshot plus overcards;
      double gutshot; a set on a paired board;
    - call pricing, about 6: a 50%-pot river bet (25% needed, not 33%); a flush draw facing a
      1.5×-pot turn bet; a combo draw facing a pot-size flop bet; a gutshot facing a small
      bet; a bluff-catcher facing an overbet; a draw facing an all-in;
    - stack depth, about 4: an overpair facing a check-raise at SPR about 1, 4 and 13; a set
      mine at 10× versus 20× the call;
    - preflop, about 5: A6o and 55 opened under the gun; K2o in the big blind against a
      button open; big-blind defence against 2.5bb versus 4.5bb;
    - betting rules, about 2: the short all-in minimum re-raise; cumulative short all-ins
      reopening the betting.

    Spread the spots across streets, bet sizes, SPR bands and board textures. The owner
    reviews the list.
  - **Plan:** skipped (one test file, one sub-slice; reason recorded here).
  - **Build (1 sub-slice):** `backend/tests/test_textbook_spots.py`, one parametrized case per
    spot. Each known failure is marked `xfail(strict=True)` naming the lane that fixes it, so the
    gate stays green and every fix flips a marker.
  - **Pass/fail:**
    - the file runs inside `make check`;
    - it has 25 spots, each citing its source and its category (math or judgment);
    - the baseline count is recorded in `docs/ai-dlc/research/coach-math/baseline.md`.
  - **Appetite:** about 1 day. **No-gos:** no grader changes; no spot without a source.
  - **Riskiest assumption:** most spots have one defensible answer.
  - **Cheapest test:** the research classification. If more than a third of the spots are
    judgment calls, the north star splits into two numbers: math spots must all pass, and
    judgment spots report their agreement rate.
  - **Assumption status:** untested.

- [ ] **Lane 1 — Hand reading: the coach labels hands correctly.** ICE 9·7·5.
  - **Problem:** the coach mislabels several hand types (audit findings 1–3 and 5):
    - the wheel is a "draw", and on the river "draw" becomes "air";
    - board-made straights and flushes are "strong";
    - counterfeited and underpair two pair are "strong";
    - gutshots plus overcards and double gutshots are mislabelled ("draw" or "air").
  - **Research, first principles** (`docs/research/hand-reading-fundamentals.md`):
    - **Hand ranking and best-five selection.** On the river, the test is whether the hero's
      best five *outranks* the board's own five, not how many hole cards it uses: a hole card
      can replace a board card and still only tie the board. On the flop and turn there is no
      five-card board hand, so write separate rules for those streets (for example, trips on a
      trips board are not the hero's trips).
    - **Absolute versus relative strength:** nut versus non-nut flushes and straights;
      one-card straights on four-straight boards; full houses on paired boards; how a board
      pair counterfeits a lower two pair; why an underpair plus a board pair plays like one pair.
    - **Draw taxonomy, with outs:**
      - flush draw 9; open-ended straight draw 8; double gutshot 8; gutshot 4;
      - combo draws 12–15 (flush draw plus straight draw, or plus a pair);
      - overcards about 6, discounted because some outs make a second-best hand;
      - backdoor draws about 1–1.5 each.
    - **Dirty outs and draw quality.** A dirty out pairs the board or completes a better hand
      for the opponent. Also cover nut versus non-nut draws.
    - **Blockers.** For example, holding the A♥ on a three-heart board.
  - **Evaluate:**
    - measure label disagreement on 20,000 random deals per street among three readers:
      today's coach classifier (`_hand_category`, `postflop.py`); the bots' classifier
      (`strength_bucket`, `personas_postflop.py`); and an exact reference built on the repo's
      7-card evaluator (`domain/equity.py`), using the river and flop/turn rules from research;
    - run the riskiest-assumption test below;
    - list the blast radius: about 25 tests assert labels, and over 100 assert grader output.
  - **Ideate (at least 3 designs):**
    - **(a) default, agreed 2026-10-03:** a grader-side adapter over the bots' classifier, with
      overrides for the cases it also gets wrong (counterfeits, underpairs);
    - **(b)** a new coach classifier built on the exact evaluator;
    - **(c)** relative-strength reading: where the hand ranks among all hands possible on this
      board.

    (b) or (c) replaces (a) only if the evaluate numbers show (a) still mislabels a hand-reading
    spot. Also decide the label vocabulary: keeping the 4 labels leaves feedback text, content
    tables and the frontend untouched; more labels give more precise advice but touch more files.
  - **Plan:** `/ai-org:spec` on the chosen design.
  - **Build sub-slices (locked until the assumption holds):**
    - **1a** made-hand correctness: the wheel, the board plays, board flushes and straights;
    - **1b** counterfeited and underpair two pair;
    - **1c** the draw taxonomy: gutshot, double gutshot, combo draws and backdoors;
    - **1d** (only if the assumption test finds residual failures) the scoring fix.
  - **Pass/fail:** the hand-reading textbook spots pass; `strength_bucket` is unchanged;
    `fixtures/ninemax_parity.json` is unchanged.
  - **Appetite:** about 3 days.
  - **No-gos:** never edit the bots' classifier, because it changes 9-max bot play;
    `spot_signature()` stays frozen.
  - **Riskiest assumption:** correct labels alone make the graders give textbook answers. This
    could be false: the river grader prefers RAISE for every "strong" hand, whatever the label.
  - **Cheapest test:** in the evaluate phase, patch correct labels into the hand-reading spots
    (test-only, never committed) and re-run the graders. **Any** spot still wrong adds
    sub-slice 1d. **More than 2 of the 8** still wrong means the roadmap's bet (inputs, not
    scoring design) is false for hand reading: stop and take it to the owner before any build.
  - **Assumption status:** untested.

- [ ] **Lane 2 — Call pricing: the coach compares equity to the price.** ICE 9·7·5.
  - **Problem:** the coach's "price" is wrong, and draws are never compared to it (audit
    findings 4–5):
    - "price" is bet ÷ (pot including the bet), which is alpha, labelled as pot odds
      (`postflop.py:826`); pot odds is call ÷ (pot + call), so a 50-into-100 river bet needs
      25%, not 33%;
    - draw equity is never compared to that price, so a flush draw (about 19.6% on one card)
      facing a 1.5×-pot turn bet, which needs 37.5%, grades "call".
  - **Research, first principles** (`docs/research/call-pricing-fundamentals.md`, extending
    `06-postflop-reference-tables.md` and `equity-realization.md`):
    - **Pot odds, alpha and MDF.** Derive each from break-even expected value. Say when each
      applies (the caller's decision, the bluffer's, the defender's whole range) and why they
      are not interchangeable. Worked numbers for 33%, 50%, 75%, 100% and 150% of pot.
    - **One card versus two to come.** An all-in guarantees both cards at today's price.
      Otherwise the river card is not free: a later bet must be modelled through implied odds
      and realization, not by quoting two-card equity against a one-street price.
    - **The rule of 2 and 4.** Cover its error at 8 or more outs.
    - **Equity realization.** Why a hand in position realizes more than its raw equity; reuse
      the repo's existing realization factor (R) values.
    - **Implied odds.** Required extra winnings W = call ÷ equity − (pot + call). Three things
      cap W: the effective stack behind; the villain type's willingness to pay off; how
      disguised the draw is. Reverse implied odds come from dominated draws and non-nut flushes.
    - **Multiway pots.** More dead money but lower realization, and why heads-up MDF does not
      apply per player.
    - **Rake.** Its effect on required equity, as a formula only (a $15 call into $30 needs 25%
      raked-free and about 27.8% when a $6 rake comes off the $60 pot). Real rake lands in
      `bot-realism-6max`.
  - **Evaluate:** list every place the code computes a price, and which formula each one uses;
    run the riskiest-assumption test below; record the pricing-spot baseline.
  - **Ideate (at least 3 designs):**
    - **(a) default, agreed 2026-10-03:** counted outs, correct pot odds, and an implied-odds
      cap from the stack behind;
    - **(b)** Monte Carlo equity against a range narrowed by the betting;
    - **(c)** a hybrid: outs for draws, and a sourced bluff-catching rule for made hands.

    Also decide where the implied-odds constants live: versioned `content/` data, later per
    villain type.
  - **Plan:** `/ai-org:spec` on the chosen design.
  - **Build sub-slices (locked until the assumption holds):**
    - **2a** the correct price formula everywhere a faced bet is graded, made hands and draws
      alike;
    - **2b** draws priced against the call, using lane 1's outs;
    - **2c** implied odds capped by the stack behind (first to defer if time runs short).
  - **Pass/fail:** the pricing textbook spots pass, and a regrade-drift report says which live
    verdicts flip and why.
  - **Appetite:** about 3 days.
  - **No-gos:** no solver; EVs stay labelled approximate; no rake inside grading yet (lane 8).
  - **Riskiest assumption:** the graders' score thresholds were hand-tuned around the wrong
    number, so correcting the formula may break spots that pass today.
  - **Cheapest test:** swap the formula in a scratch run (never committed) and count verdict
    flips on the seeded coverage sweep (`tests/test_coverage_baseline.py`) and on the spot set.
    Every flip toward a wrong answer means a threshold must be re-derived inside 2a.
  - **Assumption status:** untested.

- [ ] **Lane 6 — Betting rules and honest labels.** ICE 6·9·9.
  - **Problem:** two rule bugs and a mislabelled score (audit findings 9 and 11):
    - after a short all-in, the engine lets BTN raise to 19 where 24 is legal (LJ raises to
      10, CO goes all-in for 15: the minimum is 15 + the last full raise of 9)
      (`table/engine.py:297-301`);
    - several short all-ins that together make a full raise never reopen the betting
      (`engine.py:159-160`);
    - a penalty score is shown and summed as "−X bb", as if it were chips (`grading.py`,
      `feedback.py`, `services/stats.py`).
  - **Research** (`docs/research/betting-rules.md`): the standard no-limit rules for short
    all-ins (the full-raise rule, cumulative short raises, who may re-raise), where card rooms
    differ, and what a grading score means versus chip expected value.
  - **Evaluate:** engine tests reproduce both bugs (the audit's commands); a bot-only simulation
    at 6 and 9 seats, run before and after, counts changed bot decisions.
  - **Ideate:** for 6a, three designs are skipped because the rule has one correct form (reason
    recorded here). For 6b, the label options are "points", "grade score", or approximate chip
    EV scaled by the pot; the last is a bigger model and goes to LATER.
  - **Plan:** `/ai-org:spec` covering both sub-slices.
  - **Build sub-slices:**
    - **6a** the min-raise and reopen rules;
    - **6b** penalties relabelled as points in the UI, the feedback text and the stats.
  - **Pass/fail:** the betting-rule textbook spots pass; no penalty score carries a "bb" label
    anywhere in the UI (checked with grep); the stats page says points.
  - **Appetite:** about 1 day. **No-gos:** no change to how penalties are computed.
  - **Riskiest assumption:** the engine fix changes only what is legal, and no 9-max bot
    decision.
  - **Cheapest test:** the before-and-after bot simulation. If any 9-max bot decision changes,
    the owner rules before merge, because of the 9-max byte-identity rule in
    `bot-realism-6max`.
  - **Assumption status:** untested.

## NEXT (validated problems, not yet spec'd; each runs the six phases when promoted)
Lanes 3–5 are the agreed fixes 3–5, moved here by the owner's "cut to fit 2 weeks" (2026-10-03).
- **Lane 3 — A price check on every faced bet.** Depends on lane 2.
  - **Problem:** where the coach cannot grade (about 96% of postflop decisions), the player sees
    no price at all, so the call-pricing lesson only lands in the 4% that are graded.
  - **Research:** what learners act on (`03-ux-learning-workflow.md`); how training tools show
    pot odds and MDF.
  - **Evaluate:** is an estimated-range equity honest? Compare it with real showdown outcomes
    *before* showing it. If it is not honest, show only the price (equity needed and MDF).
  - **Ideate:** price only; price plus a hand-class equity band; price plus estimated equity.
  - **Sub-slices:** an API field on every faced bet; a panel plus design review; a rule for
    ungraded spots (show the price, give no verdict).
- **Lane 4 — Stack depth is ignored.** QQ facing a check-raise grades the same at SPR 1.2, 3.9
  and 13.0 (audit finding 6).
  - **Research:** top up `deep-stack-strategy.md` with sourced commitment guidance.
  - **Hypotheses to test, not rules to teach:** one pair is usually committed at SPR 3 or below
    and usually not above about 6; implied odds are capped by the stack behind; set-mining needs
    about 15–20 times the call. SPR is one input alongside bet size, ranges, board, position and
    raise legality; each hypothesis needs sources and counterexample spots before it grades.
  - **Sub-slices:** postflop commitment rules; preflop set-mining.
  - **Open question:** the preflop grader is stack-blind by design, so set-mining needs an owner
    ruling.
- **Lane 5 — Preflop grading is too soft, and open sizes are mispriced.**
  - **Evidence:** A6o and K9o opened under the gun, and K2o called in the big blind, grade
    ACCEPTABLE; a 4.5bb open is priced as 2.5bb (27.3% needed versus 36.8%;
    `grade_map_preflop.py:115`, `scenarios.py:201`).
  - **Research:** are these plays mistakes *live*? 55 under the gun may be fine in deep,
    multiway games. Uses `bot-realism-6max` L1's live benchmarks.
  - **Evaluate:** regrade the owner's real sessions and count verdict flips.
  - **Sub-slices:** a range-edge penalty; open-size pricing.
- **Lane 7 — Grading coverage is thin.** Postflop 3.5% graded; turn 0.3%; river 0.1%.
  - **Cause:** 80% of postflop rejections are "pot shape not covered" (5+-way pots 24%,
    heads-up 3-bet pots 21%, limped 3-way+ 20%, 3-way 18%, multiway 3-bet 12%).
  - **Order:** heads-up 3-bet pots first. A live-shaped bot table (more multiway pots) lowers
    coverage further.
  - **Open question:** this overlaps `T-cover` (a parked coverage item in
    `professional-teacher-rework.md`). Merge it there, or move it here?
- **Lane 8 — Rake in the coach's pricing.** Waits on the rake lane in `bot-realism-6max`.
- **Lane 9 — Training surfaces.** Each depends on lanes 1–2 being correct:
  - turn and river drills: the spot builders exist, but no drill mode does;
  - a river-decision review after each session;
  - the hero's VPIP, PFR and WTSD against live ranges (needs `bot-realism-6max` L1);
  - coaching by villain type (`T-oppo` in `professional-teacher-rework.md`).

## LATER (bets, no dates)
- **Bet:** correct advice changes how the owner plays.
  - **Confidence:** medium.
  - **Test:** the owner's VPIP, WTSD and river-call rate in Simulate before versus after lanes
    1–2 (`backend/tools/table_stats.py`).
  - **Review:** after lane 2.
- **Bet:** an approximate chip-EV model, scaled by the pot, is worth replacing points.
  - **Confidence:** low.
  - **Test:** does the owner act on the number once it is shown?
  - **Review:** after lane 3 ships.

## Bookkeeping
- **Both this roadmap and `bot-realism-6max` are active** (owner, 2026-10-03). A session must
  ask the owner which one to work on before picking up a slice.
- **Owner rulings, 2026-10-03:** see the last section of the audit record.
- **Review record:** `docs/ai-dlc/ledger/coach-math-roadmap.md`.

## Out of scope / no-gos
- **No change to bot behaviour.** That means the bots' classifier, persona content and bot
  decision code. `bot-realism-6max` owns the bots. Lane 6's engine fix is the one place this
  roadmap could touch bot play, and it stops for an owner ruling if it does.
- **Rake settlement** belongs to `bot-realism-6max`.
- **Not planned** (owner, 2026-10-03): sizing tells, bot adaptation to the hero, and bb/100
  with a confidence interval.
- **The repo invariants hold:** `spot_signature()` stays frozen; no solver tables; EVs are
  labelled approximate; grading stays behind the one `StrategyProvider`; strategy lives in
  versioned `content/` data; the domain core has no web or database imports; results are
  frequency + EV, never boolean.
