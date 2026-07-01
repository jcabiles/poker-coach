# 06 — Postflop Reference Tables (Solver-Grounded)

**Purpose:** A reality-check layer for the postflop grader (`backend/app/domain/postflop.py`), which currently uses hand-tuned merit scores with **zero equity/frequency backing**. This doc pulls real solver-cited numbers (GTOWizard blog + aggregate-report write-ups) and translates them into **simple, memorizable rules** — not frequency grids. Doctrine: simplified-but-winning for a live $1/$2 → $2/$3 9-handed cash player, not perfect GTO. Scope: flop/turn/river **frequencies and sizings only** — no equity/EV math, no blockers/hand-reading, no preflop ranges (owned elsewhere).

Tags used throughout:
- `[LEAK]` — the grader (`postflop.py`) or `docs/research/02-postflop-strategy.md` is materially wrong vs. solver data.
- `[OK-SIMPLIFICATION]` — a simplification that's fine to keep at these stakes.
- `[$5/$10: tighten →]` — cheap adjustment to make once the player moves up.

## 1. Methodology + Sources
Solver figures below come from GTOWizard blog aggregate-report write-ups (100bb, single-raised pot, BTN vs BB unless noted) and one 888poker board-texture explainer. These are **illustrative example boards**, not universal constants — solver strategy is board-specific; the point is the *direction and magnitude* of the swing between textures, which is what a simplified rule should track. Full source list in §7.

## 2. Flop C-Bet: Frequency + Sizing by Texture

| Example board | Texture (this app's classifier) | IP c-bet behavior | Defender fold / call / raise |
|---|---|---|---|
| K♦K♠5♣ | dry, paired, high, rainbow | ~96% c-bet freq, small size | — |
| Q♥Q♣6♦ | dry, paired, rainbow | bets most of range, ~33% pot | 37% / 39% / **24%** |
| A♠9♥3♣ | dry-ish, unpaired, monotone | only ~26.6% c-bet freq (mostly checks) | — |
| K♥J♥7♦ | wet, two-tone, semi-connected | bets often but polarized: 75–125% pot (overbet common) | 62% / 32% / 5% |
| Q♦J♦T♦ | wet, monotone, connected | only ~50% c-bet freq (checks the other half), small size (~33%) when betting | 37% / 53% / 9% |

Position note (not independently re-verified this pass, inherited from doc-02 + GTOWizard's IP-c-betting article): **OOP c-bets 15–25% less often than IP on an identical board, and sizes down a tier.** `[OK-SIMPLIFICATION]` — treat as directionally correct; don't build a separate OOP frequency table, just discount IP numbers.

**Findings vs. current baseline:**
- `[LEAK]` **Monotone ≠ generic "wet."** `postflop.py`'s `Texture.wetness` scoring lumps monotone boards into "wet" (suitedness contributes +2 to the wetness score) alongside wet two-tone boards, and `_merits()` only branches on `wetness` (dry vs. not-dry) — it never reads `texture.suitedness`. Solver reality: wet two-tone boards (K♥J♥7♦) get bet *often* with *big/overbet* sizing; monotone boards (A93 mono, QJT mono) get bet at roughly **half the frequency**, with **small** sizing when betting at all. The grader currently gives both the same "polarize big with strong+draws, check more otherwise" treatment — it's missing a distinct low-frequency, small-size monotone dial.
- `[LEAK]` **Ace-high exception is undocumented in code.** `docs/research/02-postflop-strategy.md` §2 itself calls out ace-high boards as a documented exception (bet *less* than other high-card boards — BB defends more Ax, check-raises more). `range_advantage()`'s `texture.high_board` flag treats all T+-high boards identically; it doesn't discount ace-high. This is a leak against the project's own cited doctrine, not just external solver data.
- `[OK-SIMPLIFICATION]` Paired boards being folded toward "dry" in the wetness score happens to roughly match solver c-bet *frequency* (paired boards do get bet often, small) — fine to keep for frequency purposes. But see §4 for the check-raise-side gap this same choice creates.
- `[OK-SIMPLIFICATION]` The 3-tier size model in doc-02 (25–33% dry / 40–55% semi-connected / 55–75% wet) undersells how large solvers go on the *wettest, most polarized* boards (KJ7 two-tone hit 75–125% including overbets). For a memorizable rule this is fine — add a 4th tier only for "very wet + you have the nuts."
- `[$5/$10: tighten →]` None needed here — c-bet frequency/sizing by texture is a fundamental that holds across stakes; what changes at $5/$10 is opponents' *defense* quality (see §4), not your own sizing menu.

**SIMPLIFIED RULE:** Dry & paired boards → bet small (33%), bet most of your range. Wet two-tone boards → bet big (66–100%+) but only with strong hands + real draws, check the rest. **Monotone boards → check most of the time; when you do bet, go small and only for real value/nut draws** (this is the one texture the current grader treats identically to regular wet boards and shouldn't).

## 3. Turn Barreling (forward reference — no turn grader exists yet)

| Spot | Stack depth | Barrel size | Barrel frequency |
|---|---|---|---|
| Blank paired flop (5♠5♥2♣), generic turn | 100bb | 50–75% pot (≈67% optimal) | Aggressive — virtually all Q9+ bets again for value; overcards are the best bluff candidates |
| Blank paired flop, generic turn | 40bb (shallow) | 25–50% pot, virtually never shoves | Geometric-lite, still frequent |
| Connected flop (8♦7♦6♣), turn | 100bb | Smaller on turns that help villain's range | "Not much lower" than the blank-flop barrel rate, despite a lower flop c-bet rate to start |
| Wet turn card (K♦7♥5♥→8♦) | 30bb | 67% pot | High — but villain (defender) can profitably check-raise ~11% back |
| Wet turn card, same line | 100bb (deep) | 67% pot | Only ~39% of range barrels (SPR/geometric considerations cut frequency vs. shallow) |
| Brick turn card (K♦7♥5♥→2♣) | 30bb | Pot-size | Barrel range is 85% no-draw / merged made-hands — a "give up with air" spot |

**Findings vs. current baseline:** No `[LEAK]` tag applies — `postflop.py` has no turn grader (`grade_cbet`/`grade_vs_cbet`/`grade_vs_check_raise` cover only the flop). Doc-02 §5.1–5.2's qualitative "fire on scare cards, give up on bricks" framing matches this data directionally; the new information is *magnitude*: barrel frequency should **drop with stack depth** (100bb barrels less than 30bb on the same wet turn, counter to the naive "deep stacks can afford to keep firing" intuition — it's an SPR/geometric-sizing effect) and **brick turns should see barrel frequency collapse to mostly-value** (85% no-draw), not a 50/50 mix.

`[$5/$10: tighten →]` Barrel frequency into an opponent's checked range should come down slightly — $5/$10 regs check-raise turns with real semi-bluffs more often than $1/$2 stations (doc-02 §11.2.3), so blind "keep firing scare cards" needs a floor of actual equity, not just fold-equity assumption.

**SIMPLIFIED RULE:** Barrel ~⅔ pot on scare-card turns with your value hands and best draws; give up on bricks unless you had real equity already. Deeper stacks barrel *less* often than shallow (geometric sizing, not "more room = fire more").

## 4. Check-Raise (Flop)

Using the same three cited boards as §2, defender (BB) response to the c-bet breaks down:

| Board | Bet size | Fold | Call | **Raise (check-raise)** |
|---|---|---|---|---|
| Q♥Q♣6♦ (dry, **paired**) | 33% pot | 37% | 39% | **24%** |
| K♥J♥7♦ (wet, two-tone) | 75–125% pot | 62% | 32% | **5%** |
| Q♦J♦T♦ (wet, monotone) | 33% pot | 37% | 53% | **9%** |

A dedicated GTOWizard article title ("Defending vs BB Check-Raise on Paired Flops") confirms qualitatively: **BB check-raises paired flops more than the average flop** — consistent with the 24% figure above vs. 5–9% on the other two textures. A separate generic reference point: across all boards/depths, a bettor facing a check-raise folds ≈40% (≈ MDF for a typical sizing), i.e. check-raises get respected roughly at the rate math says they should — this app's live-player exploit (fold-heavy vs. check-raise, see below) is a deliberate deviation *below* solver-optimal continuing frequency, justified by live read, not solver equilibrium.

**Findings vs. current baseline:**
- `[LEAK]` **Paired-board check-raise bump is missing.** `_merits_vs_cbet()` and `_merits_vs_check_raise()` (raise_ merit) never read `texture.pairing` — the only texture-conditioned raise bonus is for "connected + wet" boards (semi-bluff check-raise spot). Paired boards, which the solver data above shows get check-raised at ~2.5–5x the rate of other textures, get no bump at all. Confirmed by reading the full file: the string `pairing` does not appear anywhere in `postflop.py`.
- `[OK-SIMPLIFICATION]` `grade_vs_check_raise`'s fold-heavy baseline (`fold = 1.6`, vs. `0.6` for facing a plain c-bet) is an intentional, well-documented live-exploit: at $1/$2, a check-raise is rarely a bluff (doc-02 §4.4, §10.3). This is sound for the stated player pool and shouldn't be "fixed" toward solver-equilibrium continuing frequencies.
- `[$5/$10: tighten →]` The same fold-heavy prior should loosen at $2/$3+/$5/$10 — doc-02 §11.2.3 explicitly notes regs check-raise more dynamically (including semi-bluffs) at higher stakes. The code has no stake dial at all today; when a stakes parameter exists, this is the first constant to soften.

**SIMPLIFIED RULE:** As defender, check-raise paired boards meaningfully more often than other textures (they're a two-pair-and-trips-heavy spot for both ranges, cheap to represent). As the original bettor facing a check-raise from a live $1/$2 opponent, default to folding anything less than a strong made hand or real draw — but loosen that default as stakes rise.

## 5. River: Value:Bluff Ratio by Sizing (forward reference — no river grader exists yet)

Derived from the standard river-indifference formula (bluff-combo share of betting range = α/(1+α), where α = bet/(pot+bet) — this is Alpha from §6). **For a pot-size bet, bluffs should be ~33% of the betting range (2:1 value:bluff)** — this 33% figure is computed directly from the formula above, not stated independently in the cited article.

| Bet size (% pot) | Bluff share of betting range | Value : Bluff |
|---|---|---|
| 33% | ~20% | 4 : 1 |
| 50% | ~25% | 3 : 1 |
| 66% | ~29% | ~2.5 : 1 |
| 75% | ~30% | ~2.3 : 1 |
| 100% (pot) | ~33% | 2 : 1 |
| 150% (overbet) | ~38% | ~1.6 : 1 |

**Findings vs. current baseline:** No `[LEAK]` tag — no river grader exists in `postflop.py` yet, so this is a forward reference. Doc-02 §6.3 already states "larger bet = more bluffs" directionally and cites the 33%-bluffs-at-pot-size figure; this table just fills in the missing sizes with the same formula so a future river grader has a lookup instead of one anchor point.

`[OK-SIMPLIFICATION]` doc-02's "live $1/$2 opponents under-bluff, so mostly just value bet" advice (§6.2) is sound as a player-facing heuristic — it doesn't contradict the table above, it just says "don't try to hit these ratios yourself against stations; do expect villains to under-bluff relative to them."

`[$5/$10: tighten →]` Once opponents include semi-bluffs and this table's ratios more, hero's own bluff-catching needs to move toward it too — pure "they never bluff, always fold" stops being safe.

**SIMPLIFIED RULE:** Small river bets (≤50% pot) ≈ mostly value, one bluff per 3–4 value bets. Big/polarized bets (75%+) ≈ one bluff per ~2 value bets. Overbets need even more bluffs proportionally, but at $1/$2 you can skip the bluffs and still print — villains don't defend enough to punish a pure-value river.

## 6. MDF & Pot-Odds Cheat Lines

Confirmed directly (GTOWizard's MDF & Alpha article, worked example: $60 bet into $100 pot → Alpha = 60/160 = 37.5%, MDF = 62.5% — matches the formulas below exactly):

`MDF = Pot / (Pot + Bet)`   `Alpha = Bet / (Bet + Pot)`   (MDF + Alpha = 100%)

| Bet size (% pot) | MDF (defend at least this much) | Alpha (bluff needs this much fold to break even) | Pot odds (equity needed to call) |
|---|---|---|---|
| 25% | 80% | 20% | ~17% |
| 33% | 75% | 25% | ~20% |
| 50% | 67% | 33% | ~25% |
| 66% | 60% | 40% | ~29% |
| 75% | 57% | 43% | ~30% |
| 100% | 50% | 50% | ~33% |
| 150% | 40% | 60% | ~38% |

Reference point from live solver data: across all boards/stack-depths cited in the fetched turn-check-raise article, **the bettor's actual fold frequency versus a raise hovers right around 40%** — i.e., real solved play sits almost exactly at the MDF/Alpha equilibrium for a common sizing, which is a nice sanity check that the formula above isn't just theoretical.

**Findings vs. current baseline:** No `[LEAK]` — doc-02 §8.1/§8.3 already has this exact table (confirmed independently, not contradicted). Reproduced here so the postflop reference doc is self-contained and the numbers are pinned to a freshly-fetched worked example, not just carried over.

**SIMPLIFIED RULE:** Bigger bet → lower MDF you must defend, but higher Alpha (fold%) the bettor needs for a bluff to break even. Use the pot-odds column directly for "do I have enough equity to call" and the MDF column only as a range-wide sanity check, never as a per-hand rule (doc-02's caveat still holds: MDF assumes zero-equity bluffs, which live villains rarely play).

## 7. Sources

- [The Mechanics of C-Bet Sizing](https://blog.gtowizard.com/the-mechanics-of-c-bet-sizing/) — GTOWizard
- [Flop Heuristics: IP C-Betting in Cash Games](https://blog.gtowizard.com/flop-heuristics-ip-c-betting-in-cash-games/) — GTOWizard
- [Turn Check-Raise Heuristics](https://blog.gtowizard.com/turn-check-raise-heuristics/) — GTOWizard
- [Defending vs BB Check-Raise on Paired Flops](https://blog.gtowizard.com/defending-vs-bb-check-raise-on-paired-flops/) — GTOWizard
- [Principles of River Play](https://blog.gtowizard.com/principles-of-river-play/) — GTOWizard
- [MDF & Alpha](https://blog.gtowizard.com/mdf-alpha/) — GTOWizard
- [Turn Barreling in 3-Bet Pots](https://blog.gtowizard.com/turn-barreling-in-3-bet-pots/) — GTOWizard
- [Flop C-Betting: Board Textural Theory for Beginner Poker Players](https://www.888poker.com/magazine/flop-cbetting-textual-beginner-theory) — 888poker (KK5-rainbow 96% / A93-monotone 26.6% c-bet-frequency figures)
