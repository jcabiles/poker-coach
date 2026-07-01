# Preflop Content Validation: Ranges vs Solved 9-Max Baselines

**Scope:** Validate `content/preflop/*.json` range *membership* against authoritative solved
9-max/full-ring ranges. Tag each deviation `[LEAK]` (real EV error worth fixing),
`[OK-SIMPLIFICATION]` (deviates from GTO, costs ~nothing live — keep), or add a
`[$5/$10: tighten →]` one-liner where cheap and obvious. Then recommend gap-fills.

**Boundary:** Range membership only. Does **not** touch `hand_rank`/equity ordering or EV models
(owned elsewhere). No content JSON was edited — this is a research doc.

**Last updated:** 2026-07-01
**Research agent:** preflop-validation v1

---

## 1. Methodology, Handedness & Live Caveat

- **Baseline built from:** RangeConverter 9-max 100bb solver grids (RFI by seat, incl. UTG+1/UTG+2),
  GTO Wizard's squeeze-construction and 3-bet-pot articles, FreeBetRange/PokerCoaching full-ring
  chart hubs, and Upswing's cash-vs-MTT BB-defense guidance. Reconciled with the app's own cited
  baseline, `docs/research/01-preflop-strategy.md` (referred to below as **doc 01**).
- **Handedness:** the content is **9-handed**. Where only a 6-max chart existed it was **not** diffed
  as equivalent — the primary numeric baseline (RangeConverter) is genuinely 9-max, so most rows
  below are apples-to-apples. GTO Wizard's squeeze numbers come from a shallower spot and are used
  only for *shape* (linear/value-heavy), not exact combos — flagged inline.
- **Doctrine applied:** simplified-but-winning, not perfect GTO. The solver is a **measuring stick**.
  The app is deliberately **tighter than the solver in most seats** (rake + live realization +
  memorizability) — those tighter deviations fold near-0-EV hands and are almost all
  `[OK-SIMPLIFICATION]`. `[LEAK]` is reserved for spots where the app is **wider than both the solver
  and doc 01**, or **continues wider than the nutted live population warrants** — i.e. deviations
  that actually lose money at $1/$2–$2/$3.
- **Net finding:** the packs are well-built. Only **3 mild `[LEAK]`s** (all low-cost), and the bigger
  EV story is **missing coverage** (empty `squeeze`, no UTG1/UTG2 RFI, thin `vs_RFI` hero pool).
- **Methodology caveat — external solver corroboration:** WebFetch/WebSearch for preflop solver data proved unreliable for this doc — public chart pages render as images (no fetchable text), and AI search-summaries returned contradictory answers on hands like KQo and QJo. Therefore the `[LEAK]` verdicts rest primarily on **internal consistency with the app's own cited baseline doc 01**, not fresh external solver data. **Recommend manual GTO Wizard / Preflop chart cross-check** before applying any JSON changes derived from this doc.

---

## 2. Errata by Node

### 2.1 RFI (`rfi.json`)

Baseline = RangeConverter 9-max 100bb. App is tighter than solver in most seats (expected). Only the
rows that matter are shown.

| Seat | App deviation vs solver + doc 01 | Tag |
|---|---|---|
| UTG | Opens **KQo**. Solver UTG is `AQo+` only; doc 01 §3A explicitly lists KQo/KJo under "EXCLUDE from EP." Dominated + multiway-prone + raked. | **[LEAK]** — drop KQo from UTG. |
| UTG | Opens A7s/A8s (solver opens A9s+) and AJo (solver AQo+). Doc 01 supports both; marginal. Skips A6s while keeping A5s — matches the solver's own wheel-blocker pattern (`A9s+, A5s`). | [OK-SIMPLIFICATION] `[$5/$10: drop AJo, A8s]` |
| UTG | Folds 66, KTs, QTs, T9s, 98s that the solver opens. Near-0-EV EP opens; folding simplifies. | [OK-SIMPLIFICATION] |
| HJ | Opens **QJo**. Solver HJ offsuit is `ATo+, KJo+` (no QJo); doc 01 introduces QJo only at **CO** (§3C), one seat later. | **[LEAK]** (mild) — defer QJo to CO+. |
| HJ | Folds 22-44 and the low suited connectors (87s-54s) the solver opens from HJ. | [OK-SIMPLIFICATION] |
| CO | Opens offsuit **KTo/QTo/JTo**; strict solver CO offsuit is `A9o+, KJo+`. Doc 01 §3C adds these; live CO with 3 seats behind + high blind-fold rates makes them ~break-even, not money-losers. | [OK-SIMPLIFICATION] `[$5/$10: cut QTo/JTo]` |
| BTN | ~43-45% open vs the solver's loose 51.3% (drops K2s-K4s, Q2s-Q6s, offsuit connectors). Matches doc 01 §3D (~40-45%) and live norms. | [OK-SIMPLIFICATION] |
| SB | Pure raise-or-fold, no limp/complete range (solver SB mixes in limps). Intentional per doc 01 §3E. | [OK-SIMPLIFICATION] |

**Verified non-issues:** the UTG "A6s gap" is correct (deliberate wheel-blocker convention, mirrors
the solver's `A9s+, A5s`). No leaks of omission — every hand the app folds vs the solver is a
near-0-EV open.

### 2.2 vs_RFI (`vs_rfi.json`)

The pack is **value-only merged** (no polarized 3-bet bluffs beyond A5s/A4s), which is the
intentional low-stakes approach (doc 01 §5, §12). Solver would add A2s-A5s/suited-connector bluffs
and 3-bet ~7-8% from BTN vs CO; the app trades that balance for exploit-simplicity. All existing
entries (HJ/CO/BTN vs earlier seats) are consistent — value ranges are appropriately tight and the
flats are reasonable.

| Spot | Note | Tag |
|---|---|---|
| All entries | Value-only, bluffs stripped (except wheel aces). | [OK-SIMPLIFICATION] |
| HJ/CO flat vs UTG | Cold-calls with live players still behind (squeeze exposure). Fine at these stakes. | [OK-SIMPLIFICATION] `[$5/$10: tighten cold-calls with seats left to act; add polarized bluff-3bets vs regs]` |
| BTN vs CO | Continues ~30% (flat 22-99 + broadways/SCs, 3-bet TT+/AQs/A5s/A4s). Folds some suited aces (A6s-A8s) that are strong IP flats. | [OK-SIMPLIFICATION] (slightly tight IP) |

Coverage gaps (LJ-as-hero, CO/BTN vs LJ) → §3.3. **No `[LEAK]`s.**

### 2.3 vs_3bet (`vs_3bet.json`)

Value-heavy 4-bet-or-fold with wheel-ace 4-bet-bluffs (BTN vs BB/SB). Correct for a live population
that under-bluffs 3-bets. All entries `[OK-SIMPLIFICATION]`. Coverage is thin (UTG/CO/BTN only; no
HJ/LJ hero, no SB-as-opener) — noted as an aside, **not** in the requested gap-fill scope.

### 2.4 vs_4bet (`vs_4bet.json`)

Continue only the top vs a 4-bet — correct, because live 4-bets are nutted (doc 01 §7).

| Spot | Note | Tag |
|---|---|---|
| CO vs UTG | Calls **QQ** vs an early-position 4-bet. Doc 01 §7 says fold QQ-JJ to nutted live 4-bets; UTG is the tightest 4-bettor. | **[LEAK]** (mild/exploitative) — trim CO-vs-UTG continue to AA/KK/AK; defensible only vs a known 4-bet-bluffer. |
| BB vs BTN | Calls QQ, JJ. BTN 4-bets a wider range, so continuing QQ/JJ is fine here. | [OK-SIMPLIFICATION] |
| BTN vs CO | Jam AA/KK/AKs, call QQ/AKo. Reasonable vs a CO 4-bet. | [OK-SIMPLIFICATION] |

### 2.5 blind_defense (`blind_defense.json`)

| Spot | Note | Tag |
|---|---|---|
| BB vs BTN | Wide flat + narrow value 3-bet + the one mixed spot in the whole content set (A5s/A4s 50/50 raise/call) — solver-consistent wheel-ace treatment. Defends ~48-52%; solver ~55%. | [OK-SIMPLIFICATION] (see below) |
| BB vs BTN | Flat **omits** the weak-suited region (K5s-K8s, Q8s, J8s, T7s, 96s-53s). These are the *last* hands to fold from the BB (best equity + playability). Slightly under-defends. | [OK-SIMPLIFICATION] — cheapest defense width to reclaim; low cost. `[$5/$10: leave as-is; regs open tighter]` |
| BB vs UTG | Call string ends `...JTs, TT` — **TT is already inside `99-JJ`**, so it's a redundant token. Parsed membership is unchanged (TT included either way). | Content-hygiene, **not** a leak — remove the trailing `TT`. |
| BB vs UTG / CO | Tight, value-3-bet, fold small pairs & gappers vs strong EP range — matches doc 01 §8. | [OK-SIMPLIFICATION] |
| SB vs BTN / CO | 3-bet-or-fold, merged (55+, KTs, QTs, J9s as 3-bets). Intentional — SB can't profitably flat OOP. | [OK-SIMPLIFICATION] |

### 2.6 vs_limpers (`vs_limpers.json`)

Live-specific iso/over-limp heuristic with no clean GTO baseline. Iso ranges are value-skewed,
over-limps reserved for speculative multiway hands — consistent with doc 01 §11 and standard
punish-limpers logic. All `[OK-SIMPLIFICATION]`. Coverage is thin (CO/BTN only) — not in scope.
`[$5/$10: fewer limpers → fewer iso spots; don't force isolation]`.

### 2.7 exploit.json

Villain-archetype overlays, out of scope for baseline-membership validation (they are intentional
deviations *from* the baselines, which this doc validates). Spot-checked as internally consistent
with their rationales; no action.

---

## 3. Gap-Fill Recommendations (concrete range strings)

Ready to hand to whoever edits the JSON. Strings use the pack's existing notation.

### 3.1 `squeeze` node — currently EMPTY (enum-declared, zero entries)

**Assumption (stated explicitly):** the schema has no caller-count field, so **each entry assumes
exactly one cold-caller between the opener and hero.** Put that in each entry's `rationale`.
Cash squeeze is **linear + value-heavy** (GTO Wizard: cash ranges are more linear and lower-frequency
than MTT because of rake). Size ~4-4.5x the open (doc 01 §11). Recommended entries:

| position | facing | raise (value) | raise (bluff) | call (set-mine, IP only) | sizing_bb |
|---|---|---|---|---|---|
| BB | CO | `TT+, AQs, AKs, AKo` | `A5s, A4s` | — (squeeze-or-fold OOP) | 14 |
| BB | BTN | `99+, AJs, AQs, AKs, AKo, KQs` | `A5s, A4s, A3s` | — | 14 |
| SB | CO | `JJ+, AQs, AKs, AKo` | `A5s, A4s` | — | 14 |
| BTN | CO | `QQ+, AQs, AKs, AKo, AJs` | `A5s, KQs` | `22-JJ, ATs+, KJs+, QJs, JTs` | 12 |

Notes: BB/SB squeeze-or-fold (avoid bloated multiway OOP pots). BTN squeezes IP so it can add a flat
range and one extra bluff (KQs). Widen vs a BTN opener (weakest range), tighten vs CO. A 5th entry
(CO squeezing an LJ/HJ open) can mirror the SB-vs-CO row if desired.

### 3.2 RFI UTG1 / UTG2 — currently MISSING (positions exist in the schema enum)

Interpolate between the app's UTG (~10%) and LJ (~12.8%, actual authored LJ), keeping the app's tier morphology and its
"skip A6s, keep A5s" convention. Doc 01 treats UTG+1 as EP (no offsuit KQ); offsuit broadways
legitimately enter as you approach LJ (this is *why* KQo is a leak at UTG but fine at UTG2/LJ).

| position | raise combos | sizing_bb |
|---|---|---|
| UTG1 | `66+, A7s+, A5s, KTs+, QJs, JTs, T9s, AJo+` | 3.0 |
| UTG2 | `55+, A4s+, KTs+, QTs+, J9s+, ATo+, KJo+` | 3.0 |

(UTG1 stays EP-tight, no offsuit KQ/KJ. UTG2 is the EP→MP transition seat where `ATo+, KJo+` enter,
matching the solver's LJ shape one seat early. UTG2 must sit tighter than LJ per seat order.)

### 3.3 Thin vs_RFI hero seats — add the 3 identified gaps

`LJ` never appears as hero; `CO`/`BTN` never face `LJ`. These mirror existing analogous entries,
adjusted for LJ sitting between UTG and HJ.

| position | facing | raise | call | sizing_bb |
|---|---|---|---|---|
| LJ | UTG | `QQ+, AKs, AKo, A5s` | `88-JJ, AQs, AJs, ATs, KQs, KJs, QJs, JTs` | 10.0 |
| CO | LJ | `JJ+, AQs, AKs, AKo, A5s` | `66-TT, AJs, ATs, KQs, KJs, QJs, JTs, T9s, AQo` | 9.0 |
| BTN | LJ | `JJ+, AQs, AKs, AKo, A5s` | `22-TT, AJs, ATs, KQs, KJs, QJs, JTs, T9s, AQo` | 9.0 |

(Optional 4th: `HJ` facing `LJ` — mirror `CO vs LJ` a touch tighter. Not required.)

### 3.4 Mixed-frequency spots worth authoring (2-3)

The content is ~all-pure with a single mixed spot today. Per doctrine, add mixing only where a pure
line clearly leaves EV on the table — the canonical case is **wheel-ace blockers** and one **IP
suited-broadway 3-bet-or-flat**. Recommended:

1. **`blind_defense` BB vs CO — A5s/A4s → 50% raise / 50% call.** Mirrors the existing BB-vs-BTN
   mixed treatment; currently A5s is a pure 3-bet. Wheel aces realize equity fine as flats too.
2. **`vs_RFI` BTN vs CO — KQs → 50% raise / 50% call.** The textbook IP 3-bet-or-flat combo; adds a
   balanced bluff without over-committing the merged value range.
3. **`squeeze` BB vs BTN — KQs → ~50% squeeze / 50% fold** (built into the new node). GTO Wizard
   shows suited broadways squeezing at partial frequency in multiway pots; a natural place to author
   one deliberate mixed bluff rather than retrofitting the pure packs.

---

## 4. Sources (fetched / used)

- [RangeConverter — 9-Max 100bb NLHE Charts](https://rangeconverter.com/articles/poker-charts-9-max-100bb-no-limit-texas-holdem) — primary 9-max RFI grids incl. UTG+1/UTG+2.
- [GTO Wizard — How To Construct a Squeezing Range](https://blog.gtowizard.com/how-to-construct-a-squeezing-range/) — cash squeeze shape (linear, value-heavy, ~10% freq).
- [GTO Wizard — Crush 3-Bet Pots OOP in Cash Games](https://blog.gtowizard.com/crush-3-bet-pots-oop-in-cash-games/) — 3-bet frequency/composition vs opens.
- [FreeBetRange — 9-Max Preflop Charts](https://blog.freebetrange.com/article/9-max-poker-preflop-charts-for-texas-holdem) — full-ring chart structure (grids are images).
- [PokerCoaching — Free Preflop Charts (GTO & Exploitative)](https://pokercoaching.com/preflop-charts/) — full-ring RFI + 3-bet/defense framing.
- [Upswing Poker — Big Blind Defense: Tournaments vs Cash](https://upswingpoker.com/big-blind-defend-strategy-mtt-vs-cash/) — BB defend-width (~52-58% vs BTN) and cash tightening.
- Reconciled with the app's own baseline: `docs/research/01-preflop-strategy.md`.
