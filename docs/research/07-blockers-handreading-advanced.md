# Blockers & Combinatorics, Hand-Reading, and Advanced Postflop Lines

**Scope:** Live NLHE cash games. Fills the gap between `01-preflop-strategy.md` and `02-postflop-strategy.md` — three intermediate skills that move a player from "winning by cards" to "winning by reads." Practical over academic; usable at the table.
**Player profile:** Winning $1/$2 player (~200bb effective), targeting $2/$3, with a lean toward $5/$10 in mind.

---

## Table of Contents
1. [Blockers & Combinatorics](#1-blockers--combinatorics)
2. [Hand-Reading / Range Construction](#2-hand-reading--range-construction)
3. [Advanced Lines: Overbet, Probe Bet, Delayed C-Bet](#3-advanced-lines-overbet-probe-bet-delayed-c-bet)
4. [Sources](#4-sources)

---

## 1. Blockers & Combinatorics

### 1.1 What a Blocker Is
A **blocker** is a card in your hand (or visible on board) that removes combinations of a specific holding from an opponent's range, simply because that card can no longer be part of any card they hold. Holding the A♠ means villain cannot hold any A♠-containing hand — full stop. Blockers are the mechanism that lets you pick better bluffs, better bluff-catchers, and safer thin value bets, using *arithmetic* instead of vibes.

### 1.2 Combo Counting Basics
There are 1,326 possible two-card starting hands from a 52-card deck, split three ways:

| Hand type | Combos per specific hand | Total combos | Why |
|---|---|---|---|
| Pocket pair (e.g., AA) | **6** | 78 (13 ranks × 6) | Choose 2 of the 4 cards of that rank: C(4,2) = 6 |
| Suited (e.g., AK♠) | **4** | 312 (78 rank-pairs × 4) | One combo per suit |
| Offsuit (e.g., AK not matching) | **12** | 936 (78 rank-pairs × 12) | 4 suits for the first card × 3 remaining suits for the second |
| **Total** | 16 per unpaired rank-pair (4 suited + 12 offsuit) | **1,326** | 78 + 312 + 936 |

**Memorize:** pairs = 6, suited = 4, offsuit = 12. Everything else follows from these three numbers.

### 1.3 Card-Removal Math (How Blockers Reduce Combos)
When cards of a given rank disappear from play (in your hand or on the board), the remaining combos shrink predictably.

**Pocket-pair combos remaining, by how many cards of that rank are still unseen:**

| Unseen cards of that rank | Pair combos remaining | Formula |
|---|---|---|
| 4 (none removed) | 6 | C(4,2) |
| 3 (one removed — your hand or the board) | 3 | C(3,2) |
| 2 (two removed) | 1 | C(2,2) |
| 1 (three removed) | 0 | — |

**Unpaired-hand combos (e.g., AK) when you hold one specific card of the pair:** holding one King removes every AK combo built on *that* King — 1 suited match + 3 offsuit matches (one per remaining Ace) = **4 combos removed**, taking AK from 16 combos down to **12**. This exact removal count (4) is the one worth memorizing — it recurs constantly (blocking any specific "one overcard" hand).

### 1.4 Practical Uses

**Bluff selection:** bluff with hands that block villain's *continuing* (calling/raising) combos — this maximizes the fraction of their range that folds.
**Bluff-catching:** call with hands that do NOT block villain's bluffing combos (so their bluffs stay in their range) — ideally while blocking some of their value combos too.
**Thin value betting:** bet with hands that block villain's *raising* range while leaving their *calling* range (worse hands) untouched.

### 1.5 Worked Example 1 — Bluff Selection (Blocking the Nuts)
**Board:** Q♠ J♠ 3♠ (flop) → 6♦ (turn) → 8♥ (river, brick). Three spades are out; a fourth never comes, so anyone holding two spades has a made flush.
**You hold:** A♠ 5♦.

- Spades unseen to villain if you *don't* hold one: 13 − 3 (board) = 10 → flush combos villain could hold = C(10,2) = **45**.
- Spades unseen with your A♠ removed from the pool: 13 − 3 − 1 = 9 → flush combos = C(9,2) = **36**.
- The 9-combo difference (45 − 36) is exactly the set of combos that pair A♠ with each of the other 9 live spades — i.e., **every nut-flush combo villain could have held is gone.**

**Why it matters:** you didn't just "block a flush" in the abstract — you specifically removed the combos that would never fold and would often raise you. The remaining 36 spade combos are all non-nut flushes, which are more foldable/less likely to raise. This is the single highest-leverage blocker in poker: the A-high blocker on a completed flush board.

### 1.6 Worked Example 2 — Bluff-Catching (Unblocking Villain's Bluffs)
**Board:** Q♥ 8♣ 4♦ 2♠ 5♥ (dry, no flush/straight possible). Villain (a 3-bettor) fires three streets.
**Villain's realistic range:** value = QQ/88 (sets), AQ/KQ (top pair+); bluffs = missed overcard hands like AK, AJ, KJ that whiffed and are now barreling on "ace-high equity."
**Your decision:** call with J♦T♦ or K♦J♣? Both have identical showdown value (beat only bluffs).

- Total AK combos in the deck: 16.
- If you hold **K♦J♣**, you remove one specific King from the pool → 4 of villain's 16 AK combos die (same math as §1.3) → only 12 AK bluff combos remain possible.
- If you hold **J♦T♦** instead, you block none of villain's AK combos → all 16 stay live.

**Conclusion:** with equal showdown value, **prefer J♦T♦** — it keeps villain's bluffing combos intact, which is what makes the call profitable relative to pot odds. Holding a card that blocks their *bluffs* (not their value) is the classic bluff-catching mistake.

### 1.7 Worked Example 3 — Thin Value Betting (Blocking the Raise, Not the Call)
**Board:** A♠ K♦ 7♣ 7♥ 3♦ (paired sevens). Villain could raise your thin value bet with AK (two pair) or A7/K7 (trips); villain's *calling* range with worse includes hands like A2, A5, K9, K5 — hands you want to keep alive.
**You hold:** A♣9♣ (top pair, weak kicker — a thin value bet).

- Your A♣ removes 4 of villain's 16 AK combos (same math again: holding one Ace kills 1 suited + 3 offsuit AK combos built on that Ace) → villain's two-pair/raising combos drop from 16 to 12.
- Your 9♣ doesn't touch any of villain's worse Ax/Kx *calling* combos.

**Conclusion:** the Ace in your hand quietly de-risks a thin value bet by cutting the number of hands that could raise you off it, without removing any of the worse hands you're targeting for value.

### 1.8 Blocker/Combo Checklist (Use at the Table)
- [ ] Count the raw combos first: pairs = 6, suited = 4, offsuit = 12.
- [ ] Ask: "Does the board pair/suit/connect in a way that changes these baseline counts?" (paired boards crush set/pair combos toward 1 or 3; monotone boards make flush combos countable directly from unseen suit cards.)
- [ ] For bluffing: pick the hand that blocks villain's **best, least-foldable** hands (nut flush blockers > random middle-pair blockers).
- [ ] For bluff-catching: pick the hand that blocks the **least** of villain's likely bluffs, and ideally some of their value.
- [ ] For thin value: pick the kicker/side-card combo that blocks their **raises**, not their **calls**.
- [ ] Target ratio for a balanced river betting range (if you care to balance rather than pure-exploit): roughly **2–2.5 value combos per 1 bluff combo**.

---

## 2. Hand-Reading / Range Construction

### 2.1 The Core Method
Hand-reading is not "guessing a hand" — it's **narrowing a population of combos street by street** until only a small, decision-relevant range survives. Repeat this loop on every street:

1. **State the action and sizing.** What did villain actually do (check/bet/raise, and how much)?
2. **Filter by fit.** Given villain's known profile (position, preflop action, player type), which hand-classes from their *current* range plausibly take this exact action at this exact size?
3. **Remove what doesn't fit.** Discard combos that are inconsistent with the action — e.g., a set-heavy, straightforward player checking back a flop after raising preflop is unlikely to be slow-playing top set; more likely his continuing range there is capped at one-pair-or-worse.
4. **Carry the survivors forward** as the new starting range for the next street.
5. **At the river**, the surviving range IS your decision input — compare your specific hand (plus blockers, see §1) against it.

**Where it starts:** preflop range by position + action (open/3-bet/call/limp) — see `01-preflop-strategy.md` for baseline RFI/3-bet ranges to seed step 1.

### 2.2 Live-Specific Reads
Combine the range-narrowing logic above with these live-table signals — they refine *which* combos in the theoretical range are actually plausible for *this* opponent:

**Bet-sizing tells:**
- Small/uniform sizing → merged range (some value, some protection, some weak made hands) — don't over-narrow.
- Large/unusual sizing (especially a sudden jump in size vs. their own pattern) → more polarized. At $1/$2–$2/$3, population **under-bluffs**, so trust big bets toward value more than solver-optimal frequencies would suggest.

**Timing tells:**
- Instant bet/raise → often a pre-made decision: strong value for weak/inexperienced players, or a well-rehearsed bluff for thinking regs. Context (player type) decides which.
- Long tank before a big bet → more often a marginal/tough decision (thin value or a bluff they're talking themselves into) — more common at $5/10+ where opponents actually deliberate; rarer as a meaningful signal at $1/$2 where many tanks are just distraction/phone-related, not hand-strength-related.
- Long tank then check/fold → range-defining weakness; narrow hard toward air or a hand that gave up.

**Player-type profiling (reuse the archetypes from `02-postflop-strategy.md` §10):**
- **Calling stations:** their *calling* range is wide — don't narrow much off a call. Their *betting/raising* range is narrow and trustworthy — when a station bets or raises unprompted, believe it.
- **Under-bluffers / straightforward regs:** river aggression, especially after a checked street, skews heavily toward value. Fold bluff-catchers more freely against this profile than raw pot odds alone would suggest.
- **Nits:** narrow every aggressive action hard; they rarely have anything but real hands.
- **Thinking regs (more common approaching $5/10):** balance more genuinely — range construction needs to lean on game-theoretic logic (blockers, sizing tells, line coherence), not just "they wouldn't do that."

### 2.3 Worked Hand: Full Range Narrowing, Preflop → River

**Setup:** $2/3 live, ~100bb effective. Villain = CO, a straightforward regular (bets real hands, rarely multi-street bluffs, semi-observant). Hero in BB.

**Preflop.** CO opens to $10. Hero calls in the BB with 9♠8♠.
- *Range assigned to CO:* a realistic straightforward-reg CO open — pairs 22+, broadways AT+/KQ+, suited connectors 98s–T9s down to ~76s, a few suited aces. (~18–22% of hands; see `01-preflop-strategy.md` CO RFI range for the baseline.)

**Flop: J♥ 8♦ 4♣ ($23 pot).** Hero checks. CO bets $12 (~50% pot).
- *Board read:* high-card, semi-dynamic texture that favors CO's broadway-heavy range (range/nut advantage to the preflop raiser).
- *Range narrowing:* a straightforward player's half-pot c-bet here still covers a fairly wide slice of his range (J-x, pairs, backdoor-equity overcards) *because the board favors him* — but because he's not a habitual multi-street bluffer, we discount hands that are pure air with zero going-forward equity (e.g., KQ or QT with no draw) — a player of this profile more often checks those back rather than betting them.
- Hero calls with second pair (pair of 8s), pricing in the range described above.

**Turn: 6♣ ($47 pot).** CO checks.
- *Range narrowing:* a blank turn relative to CO's range. For a straightforward, non-multi-barrel villain, checking back here removes the top of his continuing range (sets, two pair, strong Jx are usually bet again for value/protection by this profile — straightforward players don't often slow-play into a brick). What survives: marginal made hands (weak pairs, including some worse than hero's) and missed overcard/draw hands that are giving up.

**River: 2♦ ($47 pot, unchanged). CO bets $35 (~75% pot)** — a bet-check-bet(big) line.
- *Range narrowing:* this sizing, after checking back the turn, is a "picked up value / feels good now" signal for this archetype rather than a bluff — straightforward players rarely execute a delayed, sized-up bluff after showing weakness; that requires a level of multi-street planning this profile doesn't usually do.
- *Live tell layering:* if CO fired quickly and without hesitation, weight this further toward value (confident action from a non-bluff-heavy player). If CO tanked visibly before betting big, shift some weight toward a marginal value bet he's unsure about, or (rarely for this profile) a bluff — but still don't move all the way to "mostly bluffs," because the archetype caps how much bluff-weight is realistic.
- *Final range:* mostly real value (a Jack he now feels fine betting, two pair, a rivered set) with very few bluffs.
- *Decision:* hero's pair of 8s loses to essentially this entire final range → **fold.** The value of the exercise isn't the fold itself — it's that the fold is now grounded in a street-by-street narrowing chain, not a guess.

### 2.4 Range-Narrowing Checklist
- [ ] Seed the range from position + preflop action before the flop is even dealt.
- [ ] On every street, ask: "What does THIS action, at THIS size, from a player of THIS type, tell me about which combos survive?"
- [ ] Explicitly discard combos that don't fit the action (don't just mentally note it — actually narrow).
- [ ] Weight bet-sizing and timing tells by player archetype — the same bet size means different things from a station vs. a nit vs. a thinking reg.
- [ ] At the river, compare your specific combo (with its blockers, §1) against the final narrowed range to make the call/raise/fold decision.
- [ ] Remember: "ranging is never definitive" — treat the output as a weighted lean, not a certainty, especially against unpredictable or mixed-strategy opponents.

---

## 3. Advanced Lines: Overbet, Probe Bet, Delayed C-Bet

These three lines share one theme: **they all fire when villain's range is capped or you have an unusually skewed advantage** — they are tools for exploiting exactly the range-narrowing work in Section 2.

### 3.1 Overbet (bet sizing > pot)

**What it is:** a bet larger than the current pot, typically 125–200%+ pot.

**Simple $2/3 triggers — overbet when:**
- [ ] You hold a hand that beats almost everything in villain's range (rivered near-nuts/nuts) **and**
- [ ] Villain's range is capped — they checked back an earlier street as the aggressor, or called down multiple streets without ever raising **and**
- [ ] It's heads-up, not multiway (see `02-postflop-strategy.md` §9 — multiway kills big bluffs, not big value)

**Keep it simple:** at $2/3, default overbetting to **value-heavy**. Most opponents are calling stations who don't fold correctly to a big bet regardless of your range construction — the overbet works because they call too much with worse, not because you've built a perfectly balanced bluff mix.

`[$5/$10: tighten →]` Higher-stakes opponents defend overbets better (fold more accurately, raise back more) — overbet *bluffs* there need real blockers and a genuinely capped read on villain, not just "I have air and the pot is big." Value-overbetting stays simple at both levels; bluff-overbetting needs to tighten as stakes rise.

### 3.2 Probe Bet (leading into a player who checked back)

**What it is:** the out-of-position player bets a street *after* the in-position player checked back the previous street (most commonly: PFR checks flop, BB/caller leads turn).

**Simple $2/3 trigger:** villain (the preflop aggressor) checked back → their range is now capped/weakened → **lead with any pair-or-better, or a real draw, at 50–75% pot.**
- [ ] PFR checked flop, you have a pair+ or a strong draw on the turn → probe.
- [ ] PFR checked flop, you have complete air → probing is fine occasionally against known weak/passive villains, but skip it against calling stations who call regardless of your range.

**Why it works:** a checked-back street removes villain's strong hands from their range (they'd have bet those) — you're betting into a range that's already been filtered down to medium/weak holdings, so a merged, wider-than-usual betting range is profitable.

`[$5/$10: tighten →]` Thinking regs at higher stakes occasionally check back strong hands specifically to induce a probe (trapping) — at $2/3, this induce-and-trap pattern is rare enough to keep probing simple and value-heavy by default; at $5/10, be more selective about probing into players who've shown this trap tendency before.

### 3.3 Delayed C-Bet (check flop as the preflop aggressor, bet turn)

**What it is:** the preflop raiser checks back the flop, then bets the turn (or later) instead of c-betting immediately.

**Simple $2/3 triggers — delay the c-bet when:**
- [ ] Your hand is medium-strength (weak top pair, middle pair) and doesn't want to bloat the pot across three streets, **or**
- [ ] You whiffed but have backdoor equity and the flop doesn't favor your range enough to profitably bluff yet, **or**
- [ ] You have a monster that blocks villain's continuing range on the flop (so betting now gets little value anyway) — check once, bet turn once the board develops.

**Why it works (mechanically):** checking the flop once gives you a free look at villain's turn action. If they check back too (or call small), their range is now twice-filtered/capped — you gain "a lot more leeway to make thin value bets, to bluff into a twice-weakened range, and to keep the pot small" when your hand prefers that (GTO Wizard).

`[$5/$10: tighten →]` Thinking regs notice a check-flop/bet-turn pattern as a "gave up, now trying again" tell and will attack it more (float wider, raise more) — at $5/10, mixing in genuine air behind a delayed c-bet needs real balance. At $2/3, population under-attacks checked-back flops, so delayed c-bets can lean a bit more liberally into weaker hands without getting punished.

### 3.4 How the Three Lines Connect
Overbet sizing shows up naturally *inside* probe bets and delayed c-bets: once a villain checks back a street as the aggressor, their range is capped — which is exactly the condition that makes an overbet size profitable. Practical shortcut: **"villain checked back → their range is capped → I can go wider (probe/delay) AND bigger (overbet) than usual, if my own hand/story supports it."**

### 3.5 Advanced-Lines Checklist
- [ ] Before any of these three lines: has villain's range actually been capped by a check, or am I assuming it?
- [ ] Overbet: nut/near-nut advantage + capped villain + heads-up → size big, value-heavy at $2/3.
- [ ] Probe: PFR checked → lead with pair+/draws at 50–75% pot; keep air-probes rare and player-dependent.
- [ ] Delayed c-bet: medium hands, missed-backdoor hands, or blocker-heavy monsters → check flop, bet turn once you have more information.
- [ ] At $5/10, tighten the bluff/air component of all three lines — value-heavy versions of each stay simple and correct at every level.

---

## 4. Sources

**GTO Wizard Blog:**
- [A Beginner's Guide to Poker Combinatorics](https://blog.gtowizard.com/a-beginners-guide-to-poker-combinatorics/)
- [Delayed C-Betting](https://blog.gtowizard.com/delayed-c-betting/)

**Upswing Poker:**
- [How To Range Your Poker Opponents With Accuracy](https://upswingpoker.com/poker-range-technique/)
- [What is Overbetting in Poker & When Should You Overbet?](https://upswingpoker.com/overbetting-poker-when-should-you-overbet/)
- [Outplaying the Reckless Player: Mastering Turn Probes After Missed C-Bets](https://upswingpoker.com/reckless-player-mastering-turn-probes/)

**PokerCoaching.com:**
- [How to Count Poker Combinations (and Use Them to Win More)](https://pokercoaching.com/blog/poker-combinations/)

**SplitSuit Poker:**
- [Poker Combos & Blockers 101](https://www.splitsuit.com/poker-combos-blockers)
