> **Note (2026-09-25):** the `hands.txt` listing and the analysis scripts this review mentions sat
> in a temporary scratch folder and are not kept. The hands can be rebuilt from
> `backend/data/poker_coach.db`, session `4b35736fa8c7438eb57ca9d09874f8dc` (table `sim_hand`,
> `state_json`).

# Bot review: 200-hand 6-max Challenge session `4b35736f…`

## Bottom line

**Only the calling station reads as a convincing version of its type. The nit, the LAG and both TAGs each have at least one habit a competent 6-max player would notice within about 50 hands.** The station is realistic. Before the flop the TAGs look plausible, but after the flop they play in a way no real TAG does. The LAG's overall numbers are right, but it plays as a mechanical over-raiser. The nit is the least realistic: it opens like a nit, then calls down and moves all-in like a recreational player, and it lost 238 big blinds in 200 hands.

**The three biggest problems:**

1. **The regulars (nit, TAG, LAG) are passive when they have the betting lead and hyper-aggressive when someone bets into them.** They skip continuation bets (the follow-up bet on the flop by the preflop raiser) far too often, including with overpairs such as QQ, KK and AA. They check about a fifth of their raised pots all the way to showdown. Yet when they face a bet, they raise 26–29% of the time, usually to 4–5× the bet. Real players work the other way round, and this inversion is the most noticeable tell in the session.
2. **Every bot plays a limper far tighter than an open pot.** The station limps into roughly a quarter of all hands. Behind that limp, the LAG folds A4s, JTs, KTo and 55 on the button, even though it opens Q3s and T2s when nobody has entered. No bot ever calls behind a limper. A real LAG or TAG raises a known station's limps with a wide range.
3. **The bots make large bets and all-ins that ignore what their hand actually is.** Examples: the nit check-raises all-in on the river with QQ on a board of K-J-J against two opponents (#23). The LAG re-raises all-in holding AQ when the five board cards already make a straight, so AQ adds nothing (#134). The LAG shoves the river with king-high on a straight board (#30). A thinking human never plays hands like these.

Smaller issues are listed per bot below. All of these numbers come from 200 hands, so most per-position and postflop counts are small. Where a sample is too thin to trust, the text says so.

---

## Method and caveats

- **Data.** The data covers 201 completed hands (hand 202 was still in progress). It was read read-only from `sim_hand.state_json`. Positions come from the stored `seats[].position` field, which `positions_for_button` in `backend/app/domain/table/deck.py` produces. In 6-max play, "LJ" (lojack) is the first to act, which makes it effectively UTG (under the gun).
- **How the stats are defined.** VPIP (voluntarily put money in the pot) and PFR (preflop raise) are the usual definitions. RFI (raise first in) counts an open when every player before has folded, and a hand opened with a limp counts as not raised. The 3-bet rate uses the first decision after facing a single raise. A c-bet (continuation bet) is a flop bet by the last preflop raiser when nobody has bet before it. AF (aggression factor) is postflop bets and raises divided by calls. WTSD (went to showdown) is the share of flops seen that reached showdown. Winnings are recomputed from each hand's pot with side pots included.
- **Sample sizes.** Each bot has 10–34 RFI chances per position, 9–30 c-bet chances, and fewer than 5 fold-to-c-bet chances, except the station, which has 27. Treat single-digit counts as anecdotes rather than statistics.
- **Scripts.** All scripts are in the scratchpad (`analyze.py`, `net.py`, `extra.py`, `chk.py`, `donk.py`, `sd.py`). A readable history of every hand is in `hands.txt`.
- **Result by seat (bb):** hero +354, station +123, tag3 −9, tag4 −21, lag −208, nit −238.

## Summary table

"n/a" means the bot had no chances in this session.

| | nit | lag | tag3 | tag4 | station |
|---|---|---|---|---|---|
| VPIP / PFR | 11 / 9 | 36 / 29 | 18 / 13 | 18 / 13 | 53 / 1.5 |
| 6-max realistic VPIP / PFR | 12–16 / 10–13 | 28–35 / 22–28 | 20–25 / 16–20 | same | 45–60 / 0–8 |
| RFI LJ / HJ / CO / BTN / SB (%) | 12 / 10 / 20 / **0** / 40 | **39** / 48 / 52 / 50 / 40 | 21 / 25 / 27 / 31 / 33 | 18 / 19 / 13 / 27 / 33 | limps 15/17/14/4/3 times |
| RFI chances per position | 33 / 30 / 15 / 10 / 5 | 33 / 29 / 27 / 12 / 10 | 34 / 20 / 15 / 13 / 6 | 34 / 27 / 15 / 11 / 9 | — |
| 3-bet vs one open | 2% (1/54) | 8% (4/51) | 4% (3/84) | 6% (5/85) | 0% (0/82) |
| Flat call vs one open | 7% | 25% | 11% | 12% | **61%** |
| Fold to 3-bet | 2/2 | 7/8 | 4/4 | 2/2 | n/a |
| Raise vs a limper (iso) | 10% (4/40) | **17% (4/24)** | 0% (0/11) | n/a | — |
| Flop c-bet | **20% (2/10)** | 50% (15/30) | **22% (2/9)** | 46% (6/13) | n/a |
| Fold to c-bet | n/a | 1/1 | 0/1 | 0/2 | **11% (3/27)** |
| Facing a postflop bet: fold / call / raise | 2 / 9 / 2 | 12 / 15 / **11** | 9 / 5 / **5** | 8 / 8 / 4 | 18 / 104 / 2 |
| Postflop AF | 1.1 | 5.0 | 5.4 | 3.8 | 0.3 |
| WTSD | **80% (12/15)** | **62% (37/60)** | 48% (14/29) | **61% (19/31)** | 70% (70/100) |
| Won at showdown | 42% | 32% | 50% | 53% | 56% |
| Net bb | −238 | −208 | −9 | −21 | +123 |

Realistic 6-max WTSD is about 25–30% for regulars and 40–50% for a station. **Every bot sits far above that.** Across the session, 48% of flops, 46% of turns and 48% of rivers were checked through. That rate would be high even at a passive low-stakes table.

---

## Nit (seat 1)

### Stats
VPIP 11 and PFR 9 are right for a 6-max nit. The preflop range is clean. It opened QQ, KK, AQo, AJo and 99 from early position, TT, KJo and Q9s from the cutoff, and 99 and QTs from the small blind, and it never limped. BTN RFI of 0/10 comes from the cards dealt, not the range: the folded hands were K9o, J9o, A7o, JTo and trash, and the pack's button range (`nit.json`, `BTN`) is reasonable. The postflop numbers are what break the archetype. The nit c-bets 20% (2/10), calls 9 of 13 postflop bets and folds only 2, has a WTSD of 80% (12/15), and lost 238bb, the worst result at the table.

### Patterns, most damaging first

1. **It moves all-in on the river with a medium hand into a multiway pot.** In **#23** the nit holds LJ QQ on a board of J♦8♦2♠ K♦ J♥. It checks the flop three-way, checks and calls the turn, then check-raises the river all-in for 86.5bb after the LAG bets and the station calls. A nit's river check-raise means a full house or better, every time. With QQ on a paired king-high board against two players, a real nit checks and folds, or at most checks and calls. This single hand cost 87.5bb. The pack's `spr_commit: 1.2` is probably the cause: once the stack-to-pot ratio drops below the commit threshold, the bot jams whatever its hand. That is a hypothesis, not verified in code.
2. **It calls down multiway with second pair.** In **#57** the nit holds CO AQs on K♦8♠Q♦ 8♥ 5♦. It calls a lead on the flop, the turn and the river (5.5, 13.75, then 34.4bb) in a three-way pot against a TAG leading from the big blind and a station calling behind. That is second pair with a king and a pair of eights on board. A nit folds the turn at the latest. In **#90** it calls a river bet from the passive station with QJs top pair on a four-straight board (Q-5-7-4-3), even though the station almost never bets rivers without a strong hand. The pack's `stickiness 0.6` and `continue_ref 0.6` match the TAG's values, so the nit's postflop continuing range is barely tighter than the TAG's.
3. **It gives up c-bets with overpairs and premium hands.** It checked the flop with KK in #95 (A♣4♣9♣, heads-up, then called two barrels), 99 in #101 (Q-7-5, checked all three streets heads-up against the station), QQ in #23, AA four-way in #158 (Q♥J♣3♥), QQ in #36, and AQo in #10 (8-2-6, checked down). Real nits are the most straightforward value bettors at the table. They bet overpairs on dry flops almost every time. A 20% c-bet rate combined with "checks KK" reads as broken, not tricky.

### Verdict
**Preflop it is a convincing nit; postflop it is a sticky recreational player.** Anyone who has played against nits knows that a nit check-raise is the nuts. #23 breaks that expectation in a way a human would remember. Problems in order of severity: (1) the river check-raise jam with a medium hand, (2) multiway call-downs with second pair, (3) checking premium hands on the flop.

---

## LAG (seat 2)

### Stats
VPIP 36 and PFR 29 are loose for a 6-max LAG, but a human would accept them. The VPIP-to-PFR gap is 7. Nothing else in the preflop numbers is realistic.

### Patterns, most damaging first

1. **It opens almost the same share of hands from every position, and far too wide from early position.** RFI is LJ 39% (13/33), HJ 48%, CO 52% and BTN 50%. From the first seat to act it opened Q8s (twice), 74s, K7s, JTo, 65s and 22. From the second it opened Q3s, J3s, 98o, J8o and Q9o. A 6-max LAG opens about 20–25% from the first seat and 45–55% from the button, so the first-seat opens are about 1.7× too wide. The cause is in the pack: `lag.json` "unopened LJ" is `22+, A2s+, K2s+, Q4s+, J4s+ …, A7o+, K9o+, Q9o+` plus a 40% mix. LJ in 9-max has the same five players behind it as UTG in 6-max, so seat mapping is not the problem. This range was simply authored far too wide.
2. **It folds hands behind a limp that it opens without one.** Behind the station's limp it isolated only 4 of 24 times, with A5s, KQo, 44 and A9s. It folded **A4s (#129, BTN), JTs (#200, SB), KTo (#15, BTN), 55 (#122, SB), Q8s (#141, BTN)** and A3o. All of these are hands it opens routinely, and most of them it opens from the first seat. Isolating a limping fish is the core play of a real LAG. The pack's `vs_limpers CO/BTN` range (`66+, A9s+, KJs+, ATo+, KQo` + a 20% mix) is **tighter than its first-seat open range**.
3. **It raises big with a hand that only plays the board.** In **#134** (SB AQo, board 9♠8♣6♠ 5♣ 7♠, which already makes a straight) the LAG bets, gets raised by the TAG, then re-raises all-in for 69.7bb. AQ adds nothing to the board straight, so the best it can do is split the pot, and the TAG's KTo made a ten-high straight. In **#30** (LJ KJo, board 5♠6♥7♣ 9♣ 8♠) it check-raises the station's turn lead from 6.2 to 29.5bb with king-high, then shoves 58bb on the river when the board makes a straight. That is a pure bluff against a calling station into a board that plays. Both hands look like the engine fails to recognise when the board plays and when a hand has showdown value.
4. **It raises to about 5× the bet, over and over, and mostly into the station.** It raised in 7 of the 14 spots where the station bet into it, at multiples of 2.7–4.8×. Hands **#71 and #119** show the same exact line: the station leads 1.98bb, the LAG raises to 9.45bb (4.8×), the station calls 7.47bb, and the turn is checked through. The amounts match to the cent. Separately, the LAG raised 11 of the 38 postflop bets it faced (29%). Humans raise a small lead to about 3×, and a competent LAG does not bluff-raise a player who never folds.
5. **It leads into the preflop raiser from the big blind.** It led 4 of 10 times when it had the chance: **#55** 86s (gutshot), **#169** 65s (gutshot), **#187** T9o (straight draw, three barrels into the station's AA), and #14. Regulars lead into the raiser rarely, at most 10%. Treat this as indicative only, because the sample is 10 hands.
6. **Its c-bet rate is fine but it never follows through.** It c-bet 50% overall and 56% heads-up. After checking the flop, it declined to bet the turn 7 of 11 times, and it checked four raised pots all the way down (#84, #118, #124, #137). This is minor.

### Verdict
**Its overall numbers are about right, but it plays like a random aggression generator rather than a thinking LAG.** Its opens are the same in every seat, it plays tight against a limper, it bluff-raises the station, and it shoves hands that only play the board. A real LAG builds its aggression around position and around who will fold. Problems in order of severity: (1) big bets with board-playing or no-showdown hands, (2) reflexive 5× raises into the station, (3) folding strong hands behind a limp, (4) the flat position curve.

---

## TAGs (seats 3 and 4, same pack)

### Stats
Both TAGs play **VPIP 18 and PFR 13**, which is tight for 6-max; a realistic TAG is about 20–25 and 16–20. The gap of 5 means they flat-call more than a 6-max TAG usually does. Their RFI curves are flat and noisy. Tag3 opens 21% from LJ and 31% from BTN; tag4 opens 18% from LJ, 13% from CO and 27% from BTN. The BTN and CO counts are only 11–15 hands, so the flat shape is partly noise. The early-position opens are too loose for a 6-max TAG, though: J6s, T7s, 87s and A6s from LJ (tag3), and 97s, Q9s and QTo from LJ (tag4). The pack's LJ range (`tag.json`: `33+, A2s+, K4s+, Q6s+, J7s+, T7s+, 97s+, 86s+ …` + 50% extras, about 25%) is a 6-max hijack range placed in the first seat. They 3-bet 4–6%, never 4-bet, and folded 6 of 6 times to a 3-bet. Every hand they folded (K4s, QTo, T7s, KJo, 97s, AJo) is a reasonable fold, so the 3-bet response is not a defect in this sample.

### Patterns, most damaging first

1. **They raise or fold facing bets, and when they raise, it is often a bluff.** Facing a bet, tag3 raised 5 times, called 5 times and folded 9 times, which is a 26% raise rate; a real TAG raises about 10%. In **#8** tag4 has KQo on K♥T♥3♥ 3♣ J♥, top pair on a monotone paired board. It check-raises the station's turn lead of 4.1bb to 19.6bb, then check-calls the river. In **#122** tag3 in the BB check-raises the flop with 42s, no pair and no draw, on K♠8♣J♥ into the station, then bets the turn. In **#134** tag3 check-raises the flop with KTo holding only a gutshot and ends up in a river raise war. In **#154** tag3 cold-calls a turn bet *and* a raise with 99 on K-2-4-5 before folding to a shove, which costs 60bb.
2. **Tag3 rarely c-bets and gives up pots.** Tag3 c-bet 2 of 9 times. It checked AJo on A-9-6 heads-up in #145, only to bet small on later streets. It checked QQ from the BB on K-7-4 in #170. It checked all three streets in raised pots #66, #151 and #180. In **#98** tag4 with 99 on 5-3-7-A-2 against tag3 in the BB checks all three streets, so neither bot bets once. Tag4's c-bet rate (46%) is closer to normal. Both packs are identical, so the gap between them is variance. A TAG c-bets heads-up in position around 60–70%.
3. **They lead from the big blind with air.** Tag4 led 3 of 5 times when it had the chance: **#117** A3s with no pair on K♥9♣4♣ against the LAG's button open, **#57** KQs leading three streets multiway, and #63. Tag3 led once in 3 chances, in #92. The sample is small.
4. **They almost never raise a limper.** Tag3 folded 11 of 11 times from the SB behind a limp, including 22, 33, KTo and A8o, and never completed. The pack's `vs_limpers` range (`88+, ATs+, KJs+, AJo+` + mixes) is too tight for isolating a known station from late position.
5. **The two TAGs play identically.** They have the same VPIP and PFR (36 and 26 in both cases), the same 2.5/3.0/3.5 open sizes and the same bet menus. That is expected because they share one pack. At a 6-max table, a human who sees two regulars with no individual style will notice. Different opening sizes or c-bet habits would be enough to tell them apart.

### Verdict
**Preflop they are a believable, slightly tight TAG. Postflop they are not.** A TAG that rarely continuation-bets, check-raises air into a calling station and leads from the big blind reads as a scripted player. Problems in order of severity: (1) check-raise bluffs and raise-or-fold responses, (2) skipped c-bets and checked-down raised pots, (3) leading from the big blind, (4) no individual style between the two seats.

---

## Calling station (seat 5)

### Stats
VPIP 53 and PFR 1.5 are right. It limped 53 times, flat-called 61% of opens, never 3-bet, raised only with AA, KK and AKs, and limped AKo, JJ and KQo. It folded 11% of the time to a c-bet (3/27, a real sample) and called 104 of the 124 postflop bets it faced. AF is 0.3, WTSD 70% and it won 56% at showdown. It made +123bb, largely because the other bots bluffed into it.

### Patterns
1. **Most of its play is realistic.** It limp-calls, floats with gutshots and ace-high, and makes small 33–50% leads on the turn and river with weak made hands (#86 75s bottom pair leads the turn and calls off 110bb). This looks like a real low-stakes calling station.
2. **Now and then it folds a strong hand preflop.** In **#63** it folds AQo unopened from LJ, and in #87 it folds KJo from LJ. Meanwhile it limps T6s, J4s, T7o and 52s from similar seats. The cause is in the pack: `calling_station.json` gives its whole "limp" block, `22+ … A5o+ …`, which covers AQo, a flat `{limp 0.88, fold 0.12}`. So strong hands get folded 12% of the time, the same rate as the weakest hands in the block. A real station never folds AQo when nobody has entered, so this rare fold is jarring.
3. **It sometimes calls off a stack with no pair.** In **#25** it calls a 44bb all-in on the turn with KJo, no pair and no draw, in a three-way raising war. It won with king-high. Even an extreme station needs some pair or draw to call that. **#164** (called 20bb with K9o, no pair) is milder. This is borderline, because extreme stations do make these calls, but a three-way all-in with king-high is past what a human would find plausible.
4. **It check-raises now and then with draws.** In **#113** it check-raises the flop from 3bb to 12bb with QJo holding an open-ended straight draw (4×). That is uncharacteristically aggressive for its AF of 0.3, and it happened 2 times in 200 hands, so it is a minor point.

### Verdict
**It is the most realistic bot at the table.** The problems are small: the flat 12% fold on premium hands, and occasional stack-off calls with no pair.

---

## Across all bots

1. **The regulars are passive when they have the lead and aggressive when they face a bet.** Nit, tag3 and the LAG c-bet 20–50%, and about 12 of 58 raised pots that reached the river were checked through by the preflop raiser. Yet the LAG and TAGs raise 26–29% of the bets they face, and the LAG raised 7 of the station's 14 bets into it. Real regulars do the reverse. They bet when they have the betting lead and mostly call or fold when bet into. This is the strongest pattern-level tell, and it applies to every regular.
2. **Nobody takes advantage of the station.** The station is the obvious target: it limps a quarter of hands, folds 11% to c-bets and has AF 0.3. Every regular isolates it rarely and folds good hands behind its limp. They also bluff-raise it and fire bluffs at it, which is exactly backwards: against a station, a human bets strong hands for value and gives up bluffs. As a result the station is the only bot that wins money, and a human will notice that the four "good" players all play into the fish's strength.
3. **The engine appears not to recognise when the board plays.** In #134, #30 and #23 bots put large amounts in with hands that only tie the board or have no showdown value. On a board that already makes a straight, a human knows AQ is worth only a split.
4. **Raise sizes repeat exactly and are too large.** Postflop raises cluster at 4.8× (for example 1.98 to 9.45, seen twice to the cent in #71 and #119). Postflop bets always use one of the same pot fractions: 0.33, 0.4, 0.5, 0.75 or 1.0. Players who track bet sizes would notice the repeats.
5. **Nearly everything goes to showdown.** WTSD is 48–80% for every bot. Half of all flops and rivers are checked through, so the table plays like a very passive home game rather than a 6-max game with three regulars.
6. **Preflop the bots are much better than postflop.** VPIP, PFR and the gap between them are close to realistic for every type, and folding to 3-bets looks fine on this sample. The preflop defects are limited to how the bots play against limps and how wide the LAG and TAG open from the first seat, both of which are in the packs. Most of what breaks realism happens after the flop.
