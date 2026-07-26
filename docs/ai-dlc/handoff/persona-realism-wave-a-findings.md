# Wave A / wave 1 — theory-review findings requiring owner decisions

**Written 2026-07-26 at the wave-1 fan-in.** Companion to `persona-realism-wave-a-w1.md`.

Wave 1 built five instruments. Each was reviewed twice: by the generic `refuter` ("is this code
correct?") and by `persona-realism-theory-reviewer` ("is this good poker, and is the committed theory
right here?"). **All five theory reviews returned NEEDS-WORK.** Every in-scope finding has been fixed.
This file records what could NOT be fixed inside the wave — findings that need files no wave-1 ticket
owns, or that need an owner ruling.

---

## 1. The headline

**The corrected data makes the roster look WORSE than the 3–4/10 it was graded**, and on a different
axis than the grade measured: **archetype distinctness**.

| collapse | measured | contract says |
|---|---|---|
| `maniac` vs `lag` preflop | VPIP 25.4 vs 26.1 — Δ = −0.7 ± 4.6pp, statistically identical; the **maniac is tighter** | ~20pts apart |
| `tag` vs `nit` preflop | 13.0 vs 15.0 — the nit sits in the TAG band, the tag sits in the NIT band | two DISJOINT bands |
| river bluff-catcher fold | `nit` 0.545 == `tag` 0.545 · `lag` 0.570 == `maniac` 0.570 · `passive_fish` **0.683 out-folds the nit** | nit 60–75 > TAG 50–60 > LAG 40–50 > fish 35–50 > maniac 20–35 |
| W$SD ordering | fish 47.7 > tag 44.4 > lag 42.1 > station 41.9 > **nit 36.8** > maniac 22.2 | nit HIGHEST |

The regs are arriving at showdown with a **weaker** range than the recreationals — the exact inverse
of what separates the archetypes. `passive_fish` is now the roster's most internally coherent bot.

The cause is consistently **arrival, not policy**. The `maniac`'s postflop play is correctly maniacal
(top of roster on both aggression cells in `node_trace`); its *preflop entry range* is a TAG's.

---

## 2. Owner decisions needed

### D1 — T-ARR's band ceilings sit below the realistic range

Frozen bands are roster-wide `[0.30, 0.36]` and BTN `[0.05, 0.12]`. The reviewer derives realistic
values of **0.41–0.53** (roster-wide) and **0.20–0.30** (BTN) — so **both ceilings are below the
realistic range**. A Wave B slice that correctly tightens the EP/MP ladders raises arrival and
**fails both assertions**, and the wave's own stop-the-line rule then converts the cure into a halt.

Derivation: `P(BTN unopened) = Π(1 − entry)` over UTG..CO. Three pools — reg-heavy **0.336**, the
contract's stated mixed pool **0.231**, very soft **0.151**. Measured 0.074 is 3.4× below the middle
case and **2.0× below the most pessimistic**. Equivalently `0.074^(1/6) = 0.648`: all six seats ahead
of the button enter unopened pots ~35% of the time — **every one of them plays like a button**.

**Proposed:** convert both to **floor-only**, keeping the owner-frozen floor values byte-identical,
plus an in-file note that the intended direction of travel is UP. Keep monotonicity two-sided
(direction-free) and `UTG == 1.000` HARD (structural).

**Why it needs you:** decision 10 froze the *values*; it is silent on the assertion's *shape*.
Removing a ceiling is a widening, which is a stop-the-line HALT condition.

### D2 — `findings/*.md` carry verdicts graded against bands that do not exist

Seven WWSF pass/fail verdicts were rendered against per-archetype bands (nit 40–46, tag 45–50,
lag 46–52, maniac 42–50, station 38–45, fish 33–40, HERO 45–54) that appear **nowhere in the theory
contract** and carry no `(format, pool/stakes, source)` triple. Five of six quoted WTSD targets also
**disagree with the contract's own numbers**. The evidence base was graded against a private band set.

Owner decision 9 authorized writing only `data/` and `SYNTHESIS.md`, so T-EXPORT flagged rather than
edited. The reviewer judges flagging **insufficient**: the flag lives in `SYNTHESIS.md`, the verdicts
live in `findings/*.md`, that is what a per-persona ticket brief will cite, and there is no
back-pointer. This exact failure mode already propagated one level up — a stale measured row inside
the contract now contradicts the corrected data.

**Proposed:** a narrow scope extension to prepend a 3-line banner to each of the six files, marking
every WWSF verdict and the maniac WTSD verdict **VERDICT WITHDRAWN — target unsourced**, and the
surviving WTSD findings (station, nit, tag, fish) **SURVIVES — value updated**.
**Do NOT refresh the numbers** — re-scoring would launder an unsourced band into a fresh-looking PASS.

### D3 — the maniac WTSD "flip" is not a valid verdict in either direction

Reported as PASS→FAIL (38.5 → 41.9 against a 30–40 band). Four facts make both verdicts invalid:
(a) the contract's per-archetype WTSD edges are **DIRECTIONAL**; no source certifies the per-archetype
spread — the sources give only a pool-level number; (b) no such number is a CI gate before the Wave-4
re-measure; (c) the **binding CI gate is `BANDS["maniac"][2] == (0.34, 0.50)`**, and **41.9 is inside
it** — so nothing actually failed in CI; (d) **n=43, SE 7.5pp, 95% CI ≈ 27–57%** — 41.9 is
statistically **inside** 30–40 as well.

> ⚠️ **Citation correction, worth recording as a process lesson.** The T-EXPORT theory review asserted
> this gate was `(0.47, 0.65)` and "does not even overlap 30–40". **That is wrong.** `(0.47, 0.65)`
> appears only inside a *comment* at `test_personas_postflop.py:2274` describing a **superseded**
> historical value; the live tuple at `:2289` is `(0.34, 0.50)`, and contract §5 C6 (`:136`)
> independently lists `(0.34, 0.50)` as "mostly overlaps". The reviewer read the comment, not the code.
> Caught because the T-EXPORT **worker** re-verified by direct import rather than trusting its
> reviewer — the correct instinct, and the reason the error did not reach the contract.

The archetype is also **bimodal**: an "aggro-give-up" maniac sits ~22–30 WTSD, a "spew-station" maniac
~33–45. This engine builds the second type unambiguously, so 41.9 is *in-archetype*.

**Proposed:** decide and label in the contract **which maniac sub-type this roster builds**, then
derive the cell from that. Fixing the bot to re-pass a band nobody derived is the W3R-1 failure in
reverse.

### D4 — the ±5bb spread deleted short-stack arrival

T-STACK's `[95, 105]` box removes short stacks as well as deep ones. Postflop nodes acted by a ≤40bb
seat: **7.59% → 0.00%**. Small-pot low-SPR nodes: **7.35% → 2.06%**. The diagnosis was exclusively
about the DEEP tail; the short tail was never the complaint and is the more realistic half of a real
9-max buy-in distribution.

Concretely dead: `node_trace.py`'s own `flop_lowspr_commit_overpair` spot is now **structurally
unreachable live** — 15bb behind requires ~85bb invested, impossible when every seat starts 95–105.
The pack still asserts a prescription for a situation the product can no longer produce.

**Proposed follow-up (not a wave-1 blocker):** replace the uniform draw with an asymmetric mixture —
15% U[35,60] · 65% U[90,110] · 20% U[110,160], median ≈ 100.0bb. **Do not widen the symmetric box** —
measured, a fully realistic wide distribution yields 7.0% side-pot hands vs the shipped spread's 6.2%,
so ±5bb already recovers ~89% of achievable side-pot incidence. Side pots are governed by how often
three players get all-in, not by how far apart stacks start.

---

## 3. CONTRACT-DEFECTs to file (no owner decision needed, but they gate Wave B)

- **The contract is blind to arrival by construction.** Its VPIP/PFR keystone is an
  **arrival-weighted aggregate**, so it cannot detect an over-wide or position-flat opening ladder —
  and it *actively rewards widening one*, because widening suppresses downstream arrival, which
  suppresses aggregate VPIP, which invites more widening. **PR #119 is the proof of harm**: it closed
  on "nit … VPIP+PFR now IN band" after widening the wildcard node 8.0 → 29.1, citing the correct
  provenance, and shipped a nit that opens like a LAG. Needs an **RFI-by-seat** row.
- **`occupancy` appears 0 times in the 62KB contract.** The dominant defect class is contract-silent.
- **No lever or row targets limp incidence.** The roster reaches `vs_limpers` on **27.1% of all
  preflop seat-decisions**; `calling_station` open-limps **30.0% of all hands at 0.0% PFR**. The one
  stat that could catch it (`gap ≥ 30`) is an **unbounded floor**, so a bot that never raises preflop
  scores 45.6 and PASSES.
- **§7 says "do NOT edit graders", which read literally forbids T-REJECT.** The slice satisfies the
  invariant's *purpose* (public signatures unchanged, 1.29M-call differential with 0 mismatches,
  `spot_signature()` untouched, `coverage_baseline.json` unchanged and green). Needs a carve-out for
  **behaviour-identical instrumentation** shipping a differential proof. Do not delete the invariant.
- **The contract's reference pool is a scalar (`~100bb`) where the engine needs a distribution.**
  `spr_commit` reads a stack distribution the contract never states, so T-STACK had to invent one in
  a service file — and W4, which *tunes* `spr_commit`, will fit against that invented distribution.
- **No WTSD gate in CI can currently fail a WTSD problem.** For all six personas the binding CI band
  and the grounded target are **disjoint**; every persona passes CI while missing its grounded target
  by 6–28 points. The nit's `(0.37, 0.80)` spans so much of [0,1] it cannot fail.

---

## 4. Claims retracted during this wave

Recorded so they are not re-derived from stale prose.

| claim | status |
|---|---|
| "Zero rejections come from bet sizing or stack depth — sizing recognition is not the bottleneck" | **RETRACTED.** Those gates were **evaluated 0 times**; 82% of rows can never reach a sizing check. `OPEN_SIZE_OFF_BAND` is a tautology (band `[2.0, 4.5]`, every bot opens 3.0–4.5). Now printed as `CENSORED` by the tool. |
| "Side pots restored to 27/150 hands (18%)" | **CORRECTED to 6.2%.** The harness hero never folds; with a persona hero, n=600 → 6.2%. |
| "T-STACK addresses the over-commitment defect" | **FALSE.** ≥60bb-commit is 25.7% carry-over / 24.2% flat-100 / 24.3% shipped. Stack reset removes a **confound**, not the defect. Roster is still ~5× real at exactly 100bb. **W4 is sequenced on this belief.** |
| "Four spots stay context-inert" (my ticket wording) | **CORRECTED to two.** The position multiplier is symmetric, so authored-OOP spots are damped ×0.75, not inert. |
| "The pooling is roster-balanced" (T-ARR docstring) | **CORRECTED.** Real composition 13/9/8/8/8/8; `calling_station` over-weighted 62%. Balanced counterfactual 0.3504. |
| "+0.026 arrival bias" applies per-cell | **CORRECTED.** Roster-wide only. At BTN the correction is **−0.007** — balancing pushes BTN *toward* its floor. |
| "`turn_barrel_toppair` adds turn coverage" | **FALSE.** Byte-identical to `flop_ip_toppair_dry` for all six personas. 8 spots = **7 distinct nodes**; zero turn-barrel coverage. |

---

## 5. Wave B sequencing implied by these findings

1. **Do NOT scope `T-cover` off the limped-family share** (52% of rejections) until arrival is
   adjudicated — it would build grading machinery optimised for a spot distribution persona-realism
   intends to change.
2. **Land the bluff-catcher node FIRST** in the trace pack (`river_facing_bet_bluffcatcher`). It has
   no unit-test substitute for the cross-persona comparison and it gates the two HARD-today stats.
   The `facing_raise` spot ranks below it — those damps have dedicated unit coverage elsewhere.
3. **Fit the maniac/lag arrival ticket against the T-ARR occupancy counters, not aggregate VPIP** —
   aggregate VPIP is the stat that is structurally blind to the defect.
4. **Do not chase the WTSD aggregate with a lever** until the bluff-catcher node is instrumented —
   the aggregate cannot distinguish "folds too little" from "arrives too strong".
