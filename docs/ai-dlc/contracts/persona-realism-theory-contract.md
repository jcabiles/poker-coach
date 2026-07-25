# Persona-Realism Theory Contract

**Status:** Committed engineering artifact. The single authoritative "theory contract" for the persona-realism rework (the Simulate bot decision engine — `backend/app/domain/personas_postflop.py` + `personas.py`, driven by `table/play.py`).

**Precedence:** where the source docs disagree, `persona-realism-artifacts/RECONCILE.md` (the lead's correction ledger) WINS, and the build spec `persona-realism-audit-2026-07-24.md` §10 applies its corrections. This contract encodes the reconciled result. Every magnitude below traces to a source doc + section; anything I could not confirm is tagged `[UNVERIFIED]`.

---

## 1. Purpose & how to use

This doc is **dual-use**:
- **Worker brief (front-load):** injected into an implementer's brief before a persona-realism slice. Tells them the grounded math, the exact gate/boundary of their mechanic, the target stat, and the HARD-vs-directional status of their acceptance criterion.
- **Reviewer rubric (fan-in):** the theory-reviewer applies §11 to a slice's output to render a pass/fail on adherence to the grounded math/theory/framework.

It is a **rubric, not a re-derivation.** It points to the source docs for depth and does NOT replace them. For any magnitude's derivation open §10.1's cited block; for *why* a correction was made open RECONCILE. Do NOT re-run the research or re-derive numbers — both are DONE and captured (FULL-BUILDOUT §7).

**Reference pool (governs the WHOLE stat table):** online low-mid 9-max ~100bb; idealized-distinct caricatures; baseline + villain-behavior only (audit §9.2 / RECONCILE line 7). The entire keystone stat table is pool-specific — see §10.

---

## 2. The softmax law (NON-NEGOTIABLE — the anti-cosmetic-change rule)

The engine clamps each candidate merit ≥0, **normalizes by the sum**, then draws via `rng.choices`. **A merit multiplier is therefore NOT the observed frequency change.** (audit §10.0 "How to read EVERY number"; RECONCILE cross-package note 1; roadmap "Softmax law").

Concrete re-derivation (RECONCILE RP1-S1 / audit §10.0): a 1.2×/0.75× IP/OOP merit on a TAG mid-pair (base P(bet) ≈ 0.507) yields an **observed** split of only **~1.27×**, NOT the "1.5–1.8×" a naive odds-space read expects. A ×0.50 overcard-damp merit on a TAG mid-pair yields **~34%** observed bet-rate, not 25%; on TOP_PAIR (base 74.6%) → **~59.5%**, barely −15pts (RECONCILE RP2-S2 / audit §10.1-P2c).

Two binding consequences:
1. **Every magnitude is a FIT SEED, tuned to a target measured stat — never a drop-in constant.** State the target as an observed closed-loop stat (a CBet split, an AF, a WTSD), then fit the multiplier to hit it. A quoted factor is a *starting shape/direction*, not the answer.
2. **Strong/saturated buckets barely move.** Normalization means a big multiplier on an already-dominant candidate (top-pair P(bet) ≈ 0.95) shifts the observed rate a few points at most. **The effect lives in the marginal / air / draw region.**

**Failure mode (a reviewer MUST reject this):** dropping `×0.75 / ×0.50` (P2) or a flat `×0.25` fold reduction (P6) into the code *as-is* and closing the slice ships a **cosmetic** change — the observed stat has not been fit. No slice closes on "the constant is in the code"; it closes on "the observed stat hit its target band" (roadmap D7 metric-DoD gate).

---

## 3. Semi-bluff EV identities (`[SOLVED]` — confirmed by independent re-derivation, RECONCILE RP3 / audit §10.1-P3a)

Jam `B` into pot `P`, where **P = pot BEFORE the jam** (see §7 denominator unification), equity-when-called `E`.

- **T1 — value-commit threshold** (zero fold-equity is OK; jam is committable):
  `E ≥ B / (P + 2B)`
- **T2 — required realized fold equity** (when below T1):
  `F* = (B − E·(P+2B)) / (P + B − E·(P+2B))`, collapsing to the classic `B/(P+B)` at `E=0`.
- **T3 — pure-call break-even:** `E ≥ B / (P+B)`. Note **T1 < T3 always** (a jam is committable at lower equity than a call).

**Corrected 3×-pot threshold (RECONCILE RP3 "T1 3×-POT EXAMPLE ARITHMETIC — WRONG" / audit §10.1-P3c):**
B = 3P ⇒ `3P/(P+6P) = 3/7 = ` **42.9%**, NOT 60%. The 60% figure is the α / fold-ceiling for a 1.5× bet, not T1 for a 3× jam. **RECONCILE corrected this — 42.9% is authoritative; never write 60% for the 3×-pot T1.** The F5/F6 illustration survives: a flush draw at E ≈ 0.35 < 0.429 fails T1 ⇒ keeps fold mass — but the number reads 42.9%.

**Bettor bluff-share formula (RECONCILE RP5-S5 — lead OVERRULED Sol / audit §10.1-P5c):** the bettor's optimal bluff share of a value bet is
`s / (1 + 2s)` (where `s` = bet-as-fraction-of-pot).
This gives ½=25%, ⅔=28.6%, pot=33%, 2×=40%. **RECONCILE explicitly overruled Sol's accusation that RP5 used the defender form `s/(1+s)`** (which would give 33/40/50/66.7%). RP5's theory is CORRECT — do NOT "fix" it to the defender form. The only wording correction: the engine's `_BUCKET_BLUFF_SHARE` is 4 coarse representatives (SMALL=.20, MED=.27, LARGE=.32, OVERBET=.375), "directionally consistent with `s/(1+2s)`, coarsened to 4 representatives" — NOT "exact match at every size." No engine table change.

---

## 4. Lever → finding map with boundaries

Each row: the mechanic, the finding(s) it fixes, its EXACT gate/boundary, and HARD-vs-DIRECTIONAL status (per §5/§10.3 measurability). Source: audit §10.1 + FULL-BUILDOUT §2. **Boundaries are load-bearing — a reviewer checks the mechanic's gate against this column.**

| Mechanic (P#) | Fixes | EXACT gate / boundary | Tag |
|---|---|---|---|
| **P1 position** IP/OOP factor | F1, F17 | Applies to the **WHOLE aggressive candidate** = `bluff_mass` + `_AGG_BASE` + `_DRAW_AGG_BONUS` (NOT `_AGG_BASE` alone). `in_position` = "no NOT-folded, NOT-all-in opponent acts after me this street"; exclude FOLDED/ALLIN seats; **BB is IP vs SB**. Distinct from `is_aggressor`. Aggressor-side c-bet/barrel ONLY (OOP continue-realization deferred). | direction HARD, magnitude DIRECTIONAL (`LOW`-conf; IP/OOP split needs metric #5) |
| **P2 vulnerability brake** overcard-count damp | F3 (overcard side), part of F16 | Gates **MIDDLE_PAIR / TOP_PAIR ONLY** — do NOT damp `OVERPAIR_TPTK` (bucket bundles overpairs+TPTK; AA-on-K must not damp). Damp `_AGG_BASE` by count of board ranks strictly above pair rank. Fit-seeds 0→×1.00, 1→×0.75, 2+→×0.50 are DIRECTIONAL, non-linear-in-reality. | DIRECTIONAL (per-overcard bet-rate unmeasured); AF HARD must survive |
| **P2 texture-class damp** | F20 | Made pairs only; monotone-in-wetness ORDERING asserted (dry ×1.00 … monotone ×0.55); magnitudes harness-fit. Combined P2 damps floor **≥0.25** (value never vanishes). | DIRECTIONAL |
| **P3 commit brake** `_commit_factor(c)` | F2, tightens F7 | `c = to_call/stack`. Scope to **facing-fold merit ONLY**. Only *raises* fold merit (a direction, never an asserted floor). No-op where `c ≤ c0` (c0 ≈ 0.25–0.35). Uses **pot-before-bet** as P. `test_clamp_and_jam_edge` is the named non-byte-identical exception. | AF/FtC HARD survive; SPR band edges DIRECTIONAL (continuous `c`) |
| **P4 street schedule** `street_agg_mult` | F4, F8, F19 | On the **bluff/semi-bluff side ONLY** (`bluff_mass`/`bluff_cell`, `_DRAW_AGG_BONUS`); made `_AGG_BASE` does NOT decline. Flop ×1.00 (byte-identical invariant), turn ~0.55–0.70×, river ~0.33× (levels harness-fit). Busted-draw river bluff gated `was_draw_on_turn AND bet_prev_street`, straight>flush provenance. `_DRAW_AGG_BONUS[WEAK]` street-scaled (F19). | turn-barrel% DIRECTIONAL (needs metric #6) |
| **P5 river bet floor** `_RIVER_BET_FLOOR` | F6 | New `_RIVER_BET_FLOOR = (MIDDLE_PAIR,)` — **MIDDLE_PAIR only**, distinct from `_RIVER_RAISE_FLOOR` (3 buckets). Unopened BET + `street is RIVER` + bucket is MIDDLE_PAIR ⇒ `agg_merit = 0.0`. TOP_PAIR/OVERPAIR_TPTK un-floored. Archetype-uniform mechanic. | WTSD/AF re-anchor HARD-today (single Wave-4 re-measure) |
| **P6 draw-jam fold** T1/T2-aware | F5 | Zero fold ONLY inside T1 (`E ≥ B/(P+2B)`); below T1 target normalized fold prob ≈ F* (T2), NOT a flat ×0.25. Made hands (rung ≥ OVERPAIR_TPTK) keep low-SPR commit unchanged. | AF/WTSD HARD survive; if F*-targeting too big, downgrade to DIRECTIONAL explicitly |
| **P6/F7 draw-bonus equity gate** | F7 | A **SEPARATE lever** from the fold-side brake — gate `_DRAW_CALL_BONUS` itself by commitment/equity/nutness at high `c`. The fold brake alone does NOT fix F7 (`_DRAW_CALL_BONUS[WEAK]=0.20` is 2.5× the AIR base 0.08). | DIRECTIONAL |
| **P7 faced_frac fix** | F9 | Denominator = `pot_bb − (latest aggressor's raise increment)`, not full `current_bet_to`. Fresh-aggressor tests are a no-op (increment == current_bet_to); the bug is the **self-re-raise** path only. Comment: over-states → over-folds. | DIRECTIONAL + doc-correctness; additive, no test inverts |
| **P8 elasticity split** `stickiness → call_looseness + size_elasticity` | F10 | station = high `call_looseness` / LOW `size_elasticity` (inelastic); fish = moderate `call_looseness` / HIGH `size_elasticity` (fit-or-fold). | AF HARD; size-bucket FtC HARD-pending (metric #4) |
| **P8-JSON preflop** | F11 | JSON-only: delete maniac/LAG open-limps; replace `vs_rfi` `"*"` catch-all `{call:0.55,fold:0.45}` with 3bet-or-fold. Keep pinned maniac spots green. | VPIP/PFR/gap HARD-pending (metric #3) |
| **P9 multiway made-value tighten** `_MW_VALUE_TIGHTEN` | F13 | ~0.8 on `_AGG_BASE` for MIDDLE_PAIR/TOP_PAIR, `** max(opp−1,0)`. HU byte-identical (exponent 0); recommend base so **3-way stays byte-identical, only 4-way diverges**. Cap at labeled 4-way tier. Bluff collapses faster than value tightens. Monotone in opponents. | DIRECTIONAL-only (never gates a build) |

**Deferred (NOT fixes this pass — do NOT claim built):** F18 opener-position defense (needs schema+plumbing, NOT JSON — §9); the range-favorability "barrel-MORE on scare cards" side of F3 (needs F16 villain-range); blocker-based river/bluff selection (audit §10.5).

---

## 5. Per-archetype target-stat table (the keystone, RP6 — audit §10.3)

The idealized-distinct stat signatures. **HARD-vs-directional is critical — a reviewer that demands a strict numeric match on a directional-only target FAILS good work.**

**Only THREE stats are HARD-gatable today** (the harness measures only these — audit §10.3 harness-measurability caveat): **AF, Fold-to-C-bet aggregate, WTSD.** Everything else is HARD-pending (intended gate, DIRECTIONAL until its harness metric is built) or DIRECTIONAL-only.

**Preflop (VPIP / PFR / gap) — HARD-pending #3 (maniac `MED*` gate-with-headroom; 3-bet & fold-to-3bet extremes DIRECTIONAL):**

<!-- provenance-gate: keystone -->
| | nit | TAG | LAG | maniac | station | fish |
|---|---|---|---|---|---|---|
| VPIP | 10–14 ‡ | 15–20 ‡ | 21–27 ‡ | 45–58 | 42–55 | 40–55 ‡ |
| PFR | 8–12 ‡ | 12–17 ‡ | 17–23 ‡ | 38–48 | 8–14 ⚠ | 10–16 ⚠ |
| gap | 1–4 | 2–5 | 3–6 | ≤10 | ≥30 | ≥24 |
| *live 9-max (VPIP/PFR, 150 hands, indicative only)* | 8.1 / 4.1 | 10.5 / 8.8 | 19.3 / 11.3 | 32.7 / 25.9 | 48.0 / 0.7 | 33.1 / 3.4 |

**‡ 9-max full-ring correction (2026-07-25 — see §9 ledger #14).** The nit/TAG/LAG rows previously carried **6-max** values transferred to 9-max unlabelled (§10); they are corrected down by ~0.7–0.8× VPIP (≈ −5pts), and fish is corrected UP. Confidence `MEDIUM` — practitioner consensus (one strong full-ring specialist source publishing both formats side by side, plus two lower-tier corroborators), not peer-reviewed or solver-derived. **Direction is HIGH-conf; the exact band edges are DIRECTIONAL.**

**Deliberately UNCHANGED:**
- **gap row** — the VPIP−PFR gap is **format-invariant** (~3pts for winners in both 6-max and full ring). It is the strongest cross-format diagnostic in the table; do NOT "correct" it alongside VPIP/PFR.
- **maniac / station VPIP** — the researched 9-max bands (maniac 45–60, station 40–55) already agree with what is written; no edit needed.
- **⚠ station / fish PFR** — sourced 9-max values (station 3–10, fish 5–12) are `LOW`-conf: real recreational examples scatter from 40/2 to 40/30. Flagged UNRESOLVED, not changed. Treat as DIRECTIONAL-only until metric #3 measures it.

**Why only three rows moved (the mechanism confirming itself):** the transfer error lands on **nit / TAG / LAG** — the three *position-aware* archetypes, whose ranges respond to seats-left-to-act and blind frequency (blinds arrive 2/6 ≈ 33% of hands at 6-max vs 2/9 ≈ 22% full ring). It does **not** land on **maniac / station / fish**, because a player who does not adjust to table size has no mechanism by which a 6-max→9-max transfer could bias their stat. The corrections and the non-corrections fall exactly where the mechanism predicts.

3-bet%, still DIRECTIONAL, for the same pool: full ring **4–7%**, 6-max 6–10% — quote the full-ring figure in this contract.

**Postflop:**

<!-- provenance-gate: keystone -->
| Stat [tag] | nit | TAG | LAG | maniac | station | fish |
|---|---|---|---|---|---|---|
| C-bet flop overall [HARD-pending #1] | 40–55 | 55–70 | 60–75 | 80–95 | 25–40 | 35–50 |
| Fold-to-C-bet aggregate [**HARD-today**] | 60–75 | 50–60 | 40–50 | 20–35 | **<30** | 35–50 |
| Turn barrel [DIR, #6] | 30–45 | 45–60 | 55–70 | 70–90 | 15–30 | 20–40 |
| WTSD [**HARD-today**, †re-anchor] | 20–28 | 25–29 ‡ | 26–31 ‡ | 30–40 | 38–48 | 33–42 |
| W$SD [HARD-pending #2] | 55–62 | 52–56 | 48–52 | 40–46 | 40–46 | 44–50 |
| AF [**HARD-today**] | 2–3 | 2.5–3.5 | 3–4 | 4–6 | **<1.5** | 1.5–2.5 |

Also: **C-bet IP/OOP** [DIR, needs #5] · **WWSF** [DIR] · **Check-raise%** [DIR].

**‡ 9-max full-ring correction, postflop (2026-07-25 — W5-a2; see §9 ledger #15).** Only the **TAG and LAG WTSD** cells moved (27–31 → **25–29**, 28–33 → **26–31**; −2pts). They are the only postflop cells for which **two independent sources publish 6-max and full ring side by side** and agree: 6-max ≈ 27–28 vs full ring ≈ 24–25, a consistent **−2 to −3pt** full-ring shift. The move applies the measured delta to exactly the archetypes ledger #14's mechanism predicts — the **position-aware regs** — and to no one else. Confidence `MEDIUM` on the shift's existence and size, `HIGH` on its direction; **band edges remain DIRECTIONAL**. **Documentation only** — no test, band, or content pack was touched (§5/§7: no RP6 number becomes a gate before the Wave-4 re-measure). It **adds** to what W4-b's C6 re-anchor must reconcile.

**Deliberately UNCHANGED postflop (and why) — see §5a for the full audit:**
- **c-bet flop, fold-to-c-bet, turn barrel, AF** — the only side-by-side source reports these as **format-invariant** (6-max = full ring at its resolution). One author, round numbers; enough to *withhold* a correction, **not** enough to certify a level. Kept, `LOW`-conf, DIRECTIONAL. **See §5a's c-bet verdict — the c-bet row's real problem is not table size.**
- **nit / maniac / station / fish WTSD** — nit already sits below the full-ring pool value; the other three are recreational, and a player who does not adjust to table size cannot be biased by a table-size transfer (ledger #14's mechanism, applied consistently).
- **W$SD** — no source found that splits it by table size at all. Left `[UNVERIFIED]`; see §5a.

**Size-bucket Fold-to-C-bet slope [HARD-pending #4 — the F10 elasticity test]** (SMALL→OVERBET): station **INELASTIC/flat** 3–15→18–40; fish **ELASTIC/steep** 20–38→60–80; nit high-all-sizes; maniac low-all-sizes. Station AND maniac both low aggregate FtC but for OPPOSITE reasons — separate by AF and raise-vs-call share, never FtC alone.

**† WTSD downward re-anchor (C6 — DELIBERATE, NOT silent — audit §10.3 C6):** RP6 WTSD targets sit **BELOW** the current P2a-pinned engine bands at `test_personas_postflop.py:1482`. This is an intentional downward re-anchor at re-fit, not a silent pick:

| Persona | RP6 target | Current pinned BAND | Action |
|---|---|---|---|
| calling_station | 38–48 | (0.51, 0.64) | downward re-anchor |
| passive_fish | 33–42 | (0.53, 0.68) | downward re-anchor |
| nit | 20–28 | (0.37, 0.80) | downward re-anchor (below floor) |
| tag | 25–29 ‡ | (0.41, 0.65) | downward re-anchor (deepened by ‡) |
| lag | 26–31 ‡ | (0.37, 0.59) | downward re-anchor (see note) |
| maniac | 30–40 | (0.34, 0.50) | tighten (mostly overlaps) |

**‡ column updated by W5-a2** so this table cannot drift from the keystone above it; tag's and lag's downward re-anchors each get **2pts deeper** for W4-b. Two pre-existing inaccuracies in this table were found while updating it and are flagged, **not** silently rewritten (neither is a provenance defect, and correcting a *pinned band* is W4-b's job, not a doc slice's):
- **lag's "partial overlap" was already wrong on the numbers as written** — 28–33 does not intersect (0.37, 0.59) ≡ 37–59. Only maniac's row genuinely overlaps. lag was a full downward re-anchor before this slice and remains one.
- **the "Current pinned BAND" column is stale for `calling_station` and `passive_fish`** — §7's owner-authorized W3R exception moved them to fish (0.50, 0.57) and station (0.66, 0.72). W4-b must read §7, not this column.

The population is inflated vs RP6 (price-blind defense keeps too many pots to showdown); WTSD should FALL once P3/P8 land. AF and Fold-to-C-bet bands mostly already overlap RP6; only WTSD needs the explicit downward re-anchor. **No RP6 number is written into a test as a gate until this reconcile happens** at the single Wave-4 re-measure.

## 5a. Target provenance registry (W5-a1 — the citing gate)

**Why this exists.** No gate validated a *target*. D7 (§6) validates the *instrument*; §7's anti-laundering rule gives the *measured comparator* immutability and an audit trail. The keystone table had neither — and the softmax law (§2) **consumes** a target, so against a wrong one the engine converges confidently onto wrong behavior and reports success. The project's strictest gate was also its most efficient error-propagator. Ledger #14 is the proof: a 6-max band sat in §5 for the whole preflop program, and the harm channel was never CI (metric #3 is never compared to §5 at all — its only assertion is `0.0 <= pfr <= vpip <= 1.0`) but **human and agent judgement**. So the gate sits where a target is *cited into a ticket*.

**Every row of a `<!-- provenance-gate: keystone -->` table in §5 must appear below**, carrying either a `(format, pool/stakes, source)` triple or the literal `[UNVERIFIED]`. Enforced mechanically by `backend/tests/test_contract_provenance.py`.

**Format-SENSITIVE stats** (a 6-max number may NOT be transferred to 9-max, or vice versa, without restating it): VPIP, PFR, 3-bet%, RFI-by-seat, c-bet, fold-to-c-bet, WTSD, turn barrel, multiway incidence.
**Format-INVARIANT stats** (transfer is safe, state that you relied on it): the VPIP−PFR **gap**, **AF**, and any ordering or monotonicity claim.

**These two lists are themselves claims and must be sourced (W5-a2 remedy — see the CONTRACT-DEFECT note in §10).** Being on the INVARIANT list is a licence to transfer a number across formats; shipping that licence unsourced is the same error as shipping an unsourced number. Current state of the licence:
- **AF → INVARIANT: SOURCED** (S1 publishes AF 3 for 6-max and 3 for full ring side by side). Was an unsourced axiom until W5-a2; it held, but it was not *checked* to hold.
- **gap → INVARIANT: SOURCED** (ledger #14, ~3pts in either format).
- **"any ordering or monotonicity claim" → `[UNVERIFIED]`.** A blanket licence no source was ever asked about. The largest remaining hole in this section; a slice relying on it must say so out loud.
- **The SENSITIVE list is safe-by-default** — it only ever *withholds* a transfer, so an unsourced entry there cannot cause a ledger-#14-class error. Note that **WTSD earned its place empirically** in W5-a2, and that **W$SD is deliberately on neither list**: no source splits it, so neither the licence nor the prohibition is established.

| Row | Format | Pool / stakes | Source | Status |
|---|---|---|---|---|
| VPIP | 9-max full ring | online micro–low NL cash | full-ring specialist publishing both formats side by side + 2 lower-tier corroborators (ledger #14) | VERIFIED · conf MEDIUM · band edges DIRECTIONAL |
| PFR | 9-max full ring | online micro–low NL cash | as VPIP (ledger #14) | VERIFIED for nit/TAG/LAG/fish · ⚠ **station & fish cells are LOW-conf and DIRECTIONAL-only** (§5) |
| gap | format-INVARIANT | both formats | RP6 + ledger #14 (~3pts either format) | VERIFIED · transfer explicitly relied upon |
| C-bet flop overall | 9-max full ring — **level `[UNVERIFIED]`** | online micro–low NL cash (NL2–NL25) | S1 (side-by-side, FR 70 = 6-max 70) — but S1's class is *ideal target*, and the population-class sources S3/S5 read **40–60** at no stated format. Conflict unresolved; see the c-bet verdict below | `[UNVERIFIED]` — **format question answered (no shift found), LEVEL not established.** DIRECTIONAL-only; may not become a HARD gate. **Do not move the band** — see verdict |
| Fold-to-C-bet aggregate | 9-max full ring | online micro–low NL cash (NL2–NL25) | S1 (side-by-side, FR 60 = 6-max 60) + S4 (HM2 official forum, full-ring "normal" 40–70); S3 42–57 & S5 ~40 corroborate the level at unstated format | VERIFIED · conf **LOW** · **CONFIRMED UNCHANGED** · per-archetype band edges DIRECTIONAL · **demotion HARD → no-regression is DEFERRED, see below** |
| Turn barrel | 9-max full ring | online micro–low NL cash (NL2–NL25) | S1 only (side-by-side, turn c-bet FR 50 = 6-max 50); no second source splits turn aggression by format | VERIFIED · conf **LOW** (single source) · **CONFIRMED UNCHANGED** · already DIR-only, keep it DIR-only |
| WTSD | 9-max full ring | online micro–low NL cash (NL2–NL25) | **S1 + S2, two independent authors publishing both formats side by side and agreeing**: 6-max 27 / 27–28 vs full ring 25 / 24–25 | VERIFIED · conf **MEDIUM** · ‡ **TAG & LAG CORRECTED −2pts** (§5) · direction HIGH-conf, band edges DIRECTIONAL · **currently HARD-today; demotion DEFERRED, see below** |
| W$SD | `[UNVERIFIED]` | level only: online low-stakes regs ≈ 49–55 (S3, S6, S7) — **no format stated by any of them** | **no source found that splits W$SD by table size.** The level triangulates well; the format question is genuinely open, and W$SD is on neither §5a list | `[UNVERIFIED]` — level corroborated, **format unresolved**. DIRECTIONAL-only; already HARD-pending #2, must stay pending |
| AF | format-INVARIANT (now **sourced**, not assumed) | online micro–low NL cash (NL2–NL25) | S1 states AF side by side as **3 (6-max) = 3 (full ring)** — the a-priori classification in §5a's own list is now backed by a source instead of an axiom | VERIFIED · conf **MEDIUM** on invariance, **LOW** on level · **CONFIRMED UNCHANGED** · band edges DIRECTIONAL · **demotion HARD → no-regression is DEFERRED, see below** |

**The postflop half was `[UNVERIFIED]` wholesale on purpose.** §10's transfer caveat already said the postflop bands are not table-size verified; this registry made that machine-readable instead of prose. It was a statement about *provenance*, not a claim the numbers were wrong — and W5-a2's audit below bears that out: **five of six rows survive the audit unchanged.**

### W5-a2 — the 9-max postflop audit (2026-07-25)

**Sources, ranked. Tier is about *fitness for a cross-format claim*, not about how well-known the site is.** (Deliberately a list, not a table — §5a's registry parser treats every table row in this section as a registry entry.)

- **S1 — BlackRain79, *What Are The Best Poker HUD Stats?*** (`blackrain79.com/2017/10/what-are-the-best-poker-hud-stats.html`). Tier: **STRONG for format, WEAK for level.** A full-ring micro-stakes specialist publishing a 15-stat list with an explicit **"Ideal for 6max"** and **"Ideal for Full Ring"** value each, scoped to "small stakes games online… NL2, NL5, NL10, NL25", covering 6-max **and** full ring. Relevant values (6max / FR): **Flop CBet 70 / 70 · Fold to Flop CBet 60 / 60 · Turn CBet 50 / 50 · WTSD 27 / 25 · AF 3 / 3** (plus VPIP 20/15, PFR 17/12, 3bet 7/6). *Supports:* the only source found that answers the **table-size** question for c-bet, fold-to-c-bet, turn barrel and AF at once. *Does not support:* a level — its values are **ideal targets for a winning reg**, not population averages, and are round to 5–10pp, so it cannot distinguish genuine invariance from its own rounding.
- **S2 — GipsyTeam, *WTSD in Poker*** (`gipsyteam.com/poker/wtsd-in-poker`). Tier: **STRONG for format, WTSD only.** Independent author, states **6-max 27–28% vs full ring 24–25%** side by side. *Supports:* a genuine second opinion on WTSD, agreeing with S1 within 1pp. Covers no other row.
- **S3 — Poker Copilot stat documentation** (`pokercopilot.com/poker-statistics/continuation-bet`). Tier: **tracking-software vendor — but format-BLIND.** Vendor documentation of its own stat: "many players will have a continuation bet frequency of **40%–60%**"; fold-to-c-bet "**42%–57%**" for good opponents at lower stakes. *Supports:* the best available **population-class** level for c-bet and fold-to-c-bet. *Does not support:* any format claim — it is explicitly scoped to **heads-up flop** pots and states no table size.
- **S4 — Hold'em Manager official forum, full-ring HUD thread** (`forums.holdemmanager.com/…/t-47361`). Tier: **weak (forum), but format-explicit.** Full-ring colour bands, e.g. fold-to-c-bet "0-40 tight / 40-70 normal / 70+". It offers a cross-format conversion — *"VPIP/PFR convert them to full ring by dividing by 1.5"* — **for VPIP/PFR only**, and gives postflop stats a single full-ring band with no conversion at all. *Supports:* the fold-to-c-bet level at a stated full-ring format, and independently reproduces S1's pattern — practitioners convert **preflop** across formats and do not convert **postflop**.
- **S5 — MyPokerCoaching, *Essential Poker Statistics*.** Tier: weak, format-blind. c-bet flop "45%–60%", fold-to-c-bet "around 40%", raise-vs-c-bet 8–12%. *Supports:* a third corroborator for the population-class c-bet level.
- **S6 — Hand2Note, *Essential Postflop Stats*.** Tier: tracking-software vendor, **format-blind and stakes-blind**. W$SD **50–55%** for winning regs; WWSF ~48%; WTSD 27–32% for regs. *Supports:* W$SD/WWSF level only.
- **S7 — Upswing Poker, *What is a HUD…*.** Tier: weak, and **6-max-leaning**. WTSD 27–32 (aim 30); W$SD 49–54; WWSF 45–53; flop c-bet 50–70 IP. *Supports:* level corroboration only. Its VPIP/WTSD framing is 6-handed, which is exactly why its WTSD reads high — treating it as a full-ring source would import the very error ledger #14 corrected.

**Conflicts, stated plainly.**

1. **c-bet level: S1 says 70, S3 says 40–60, S5 says 45–60, S7 says 50–70 (IP).** That is a 10–30pp spread and it is **not** noise — the sources are measuring different things. S1/S7 quote a **winning reg's target in a heads-up flop**; S3/S5 quote an **observed population average over all flop spots**, which folds in multiway and OOP giveups. Multiway c-bet is much lower than heads-up (multiple sources: "the efficacy of c-betting diminishes drastically as the number of opponents increases"). **The population-class reading is the more authoritative comparator for §5**, because §5's row is *C-bet flop **overall*** and the harness metric it is compared against is an aggregate, not a heads-up-only stat — the classes must match. S1's 70 is the better-sourced number and the *wrong instrument*.
2. **WTSD level: S1/S2 say full-ring regs ≈ 24–25, S6/S7 say regs 27–32.** Reconciled by format, not by disagreement: S7 is a 6-max-first site and S6 states no format, while both sources that *split* by table size put full ring below 6-max. **S1/S2 are more authoritative here** for the single reason that matters — they are the only ones who measured the thing in question (the difference between formats) rather than reporting one pooled number.
3. **3-bet% (prose, not a gated row): ledger #14 quotes full ring 4–7 / 6-max 6–10; S1 gives 6-max 7 / full ring 6.** Both agree full ring < 6-max; the magnitudes differ. Recorded, not acted on — 3-bet% is DIRECTIONAL and outside this slice.

**⚠ Single-author dependency — the audit's own biggest weakness.** S1 is a full-ring micro-stakes specialist, which is almost certainly the **same author** as ledger #14's "full-ring specialist source publishing both formats side by side" (its 6-max 20/17 vs full ring 15/12 sits one point from ledger #14's quoted 21/18 vs 15/12). So **most of the keystone's format evidence — preflop *and* postflop — now traces to one practitioner.** S2 is the only genuinely independent format-splitting source found, and it covers WTSD alone. That is precisely why WTSD is **the only row this slice moved**: it is the only row where two independent authors, asked the same question, gave the same answer. Every other row is *confirmed-unchanged at `LOW` confidence*, which is a decision to **withhold a correction**, not a certification. A future slice that finds a second independent full-ring postflop source should re-open c-bet, fold-to-c-bet and turn barrel.

**What the sources do NOT establish, for any row: the per-archetype spread.** Every source gives a single pool-level number. §5's six-cell fan around it (nit … fish) is RP6-derived and stays **DIRECTIONAL** in all rows, exactly as ledger #14 concluded for the preflop half. The `(format, pool, source)` triples above certify the *format question* and the *pool level*; they never certify a band edge.

### The c-bet band verdict (W5-a2's required ruling)

**Verdict: do NOT move the c-bet band in this slice — and the roadmap's stated reason for expecting it to move is not the reason it may eventually need to.**

1. **The table-size hypothesis is unsupported by the only source that could test it.** The expectation was that 9-max's higher multiway incidence pushes the correct c-bet number **down**. The *mechanism* holds — multiway c-bet frequency is clearly and substantially lower than heads-up (S3 and several strategy sources), full ring does produce more multiway pots, and a second, independent mechanism points the same way (6-max post-flop ranges are weaker, so the correct 6-max adjustment is to barrel *more*). But **no source quantifies multiway incidence by table size**, and the one source that publishes flop c-bet for both formats side by side (S1) reports **no shift at all** (70/70). So the direction is plausible-to-likely; the magnitude is unmeasured; and the single format-comparative datum points at zero. That is not enough to move a band.
2. **The row has a larger defect than table size: a class mismatch.** §5's band (TAG 55–70, LAG 60–75, maniac 80–95) is shaped like a **heads-up-flop reg target**. The harness aggregate it is judged against is shaped like an **all-spots population average**, where the observed range is 40–60 (S3, S5). A −20pp "miss" is exactly the size of that class gap. **The measured gap is partly, and possibly wholly, an artifact of comparing two different statistics.**
3. **The instrument is independently known to be broken, and W5-a3-i owns it.** The roadmap already records that metric #1 computes P(bet | first-in flop decision) for *any* tested seat — including cold-callers and blind defenders who check most flops — not aggressor-side c-bet, and that it **under-reads every persona** (tag 0.417 vs 0.488, nit 0.224 vs 0.326, fish 0.196 vs 0.321). The maniac −20pp at n=415 is a reading from that instrument. **A band may not be re-anchored against an instrument its own roadmap has already declared mis-specified** — doing so is the band-laundering §11 item 7 exists to catch.
4. **So the §5a obligation-(2) / W3R-1 test comes out the other way here.** The rule says an unreachable target is evidence about the *target*. It presumes the *measurement* is sound. Here it is not, and two independent confounders (metric denominator, HU-vs-aggregate scope) sit between the bots and the band. **Re-open the target only after both are cleared.**

**Ruling, in order:** (a) c-bet band **unchanged**, `[UNVERIFIED]` on level, DIRECTIONAL-only, **never a HARD gate** while unverified — which also means **W5-a3-i's re-read must not be used to re-anchor it**; (b) sequence **W5-a3-i** (aggressor-side denominator) first, then decide whether §5's row is a heads-up target or an aggregate one and **say so in the row label** — the two cannot share a number; (c) only then, with a population-class 9-max source in hand, re-open the level. **Expected direction if it does move: DOWN, conf MEDIUM. Expected magnitude: unknown — deliberately not guessed.**

### Demotion of the HARD-today gates — DEFERRED, with the reason

W5-a2 was to demote **fold-to-c-bet** and **AF** from HARD to no-regression. The audit's finding is that **neither is the row that most needed it**: both are now sourced at a stated 9-max format and **confirmed unchanged**, whereas the row that moved (WTSD) and the row that stayed `[UNVERIFIED]` on level (c-bet) are the riskier gates.

**The demotion was not executed.** The three HARD-today gates are asserted in `backend/tests/test_personas_postflop.py` (`BANDS`, `test_persona_postflop_bands`), which was **owned by a different concurrent slice** when this audit ran; editing it would have breached §11 item 13 (stay inside the files your ticket names). Recorded here as a **documented follow-up**, not dropped:

- **Follow-up W5-a2-f (owner: whichever slice next legitimately owns `test_personas_postflop.py`; must land before W4-b).** Demote `fold_to_cbet` and `af` in `BANDS` / `test_persona_postflop_bands` from a strict band assertion to **no-regression**, with the in-file reason: *"§5a records these as conf-LOW, single-source (S1) format claims with DIRECTIONAL band edges; a `LOW`-confidence target may bound a regression, it may not define a pass."*
- **Follow-up W5-a2-g (tripwire fragility, found by hitting it).** `test_contract_provenance.py::_registry` treats **every** markdown table row in §5a as a registry entry, so adding any second table to this section fails the gate with spurious "orphan" rows. W5-a2's source list is written as bullets to work around it. Harden `_registry` to bind to the registry table only (e.g. its own HTML marker, mirroring `<!-- provenance-gate: keystone -->`). Not fixed here — `test_contract_provenance.py` is outside this slice's named files.
- **Until then the §5a grandfather clause stands and is now the contract's largest live risk:** three HARD CI gates rest on rows whose per-archetype edges every source in this audit declines to certify. WTSD's gate additionally now disagrees with its own §5 target for tag and lag by 2pts — that is W4-b's to reconcile, and this slice deliberately did **not** touch the test.

**No bot behavior, band fit, lever, content pack, or test was changed by W5-a2. Documentation only.**

### The two obligations

**(1) The citing gate.** A ticket, spec, or slice that cites a §5 target MUST quote its provenance triple. **A bare number FAILs review.** Citing an `[UNVERIFIED]` row is allowed only as DIRECTIONAL evidence — such a row may **never** be made a HARD gate while unverified. (Rows that are HARD *today* and newly marked `[UNVERIFIED]` are grandfathered pending W5-a2's demotion; no slice may add a new one.)

**(2) The W3R-1 rule — infeasibility is evidence about the TARGET.** When a fit cannot reach a target using a legitimate range or lever, the slice **STOPS and re-opens that target's provenance**. It does **not** widen the lever, widen the band, or re-scope the test to dodge the number. Three separate slices hit the α wall and each escaped by node-scoping instead of resolving it; that pattern is what this rule exists to stop.

---

## 6. Harness metrics (the metric-DoD rule)

**Rule (roadmap D7):** a metric must be **live AND showing the expected direction** before the slice that needs it can close. Until a metric exists, its gate is DIRECTIONAL, not HARD (audit §10.3).

Metrics to BUILD (Wave 0) and which mechanic each gates:

| # | Metric | Measures | Gates |
|---|---|---|---|
| 1 | **CBet-flop-overall** rate per persona | aggressor-side c-bet rate (only fold-to-*first*-cbet exists today) | P1, P2 |
| 2 | **W$SD** | won-money-at-showdown | (keystone W$SD row) |
| 3 | **VPIP / PFR / gap** aggregates | preflop tightness/aggression | P8-JSON |
| 4 | **Size-bucketed Fold-to-C-bet** | SMALL/MED/LARGE/OVERBET slope (elasticity) | P8 (F10 elasticity test) |
| 5 | **CBet IP vs OOP** split | per-decision IP/OOP (needs `in_position` logged) | P1 |
| 6 | **Turn-barrel%** by persona | per-street aggressor continuation | P4 |

Already live (the three HARD-today gates): **AF, fold-to-first-cbet, WTSD** (`test_persona_postflop_bands` ~:1546–1612).

---

## 7. Invariants & calibration discipline

Verified against FULL-BUILDOUT §5, roadmap "NO-GOS" + "Cross-cutting discipline", and CLAUDE.md.

- **Domain purity:** `backend/app/domain/` (incl. `personas.py`, `personas_postflop.py`) has NO web/DB imports (test-enforced).
- **StrategyProvider:** grading flows through the ONE async `StrategyProvider` (keep swappable). This rework is **bot-side only** — do NOT edit graders (`grade_map*.py`/`postflop.py`).
- **Results = freq + EV, never boolean.** EVs labeled *approximate* (no solver tables).
- **Strategy lives in versioned `content/` data**, not code (mechanics in code, per-persona identity in JSON).
- **Every schema change ships an Alembic migration.** (Relevant only if F18 is ever built.)
- **`spot_signature()` is FROZEN** (+ `TAXONOMY_VERSION`) — grader's, not the bots'; changing it orphans SRS history.
- **NO solver tables** — heuristic + interim EV only. Villain-range rung (a) static lookup stays inside the line; rung (c) equity-vs-range is the no-go-adjacent one.
- **Action draw stays the FIRST `rng.choices`** — `range_estimate.py:278` replays it via a capture-rng; any new randomness comes *after* the action draw (two-stage bluff-sizing is the template).
- **Default-off byte-identity:** new args default to today's behavior (mirror `is_aggressor=False`/`street`) so `range_estimate` + the population harness stay byte-identical until the live loop deliberately opts in.
- **Estimator parity (Codex-Sol HIGH):** the moment a slice makes the LIVE bot diverge from the streetless policy, `range_estimate.py` MUST be threaded the **same** context and re-tested for **parity with the live policy** — else the villain-range reveal silently lies. Each such slice owns extending the estimator's replay context + a parity test.
- **Stacked-multiplier joint calibration (audit §10.2 note 2):** position × texture+overcard × street × sizing × multiway can over-suppress marginal value/bluffs. Apply to the WHOLE aggressive candidate in this order — base merit → made-value damps (P2, `_AGG_BASE` only, floor ≥0.25) → street mult (P4, bluff side only) → position mult (P1, whole candidate) → multiway (P9, geometric). Calibrate the *combined* product to RP6 targets, not each factor independently. P2 (made cells) and P4 (bluff cells) act on **disjoint** cells; position + multiway are the ones to jointly cap.
- **Denominator unification (audit §10.2 note 3):** P3's commit gate P, the F9 faced_frac fix, and P7's aggressor-increment share ONE definition: **"pot before the current aggression."** Using live `pot_bb` (which already includes the current bet) silently lowers thresholds. Do them together.
- **SINGLE band re-anchor at the CLUSTER END, NOT mid-spine (audit §10.2 note 4 / roadmap W4):** the WTSD+AF bands are moved by P5, P3, P6, AND P8 — re-anchor ONCE after the whole P3/P5/P6/P8 cluster lands (Wave 4). Re-anchor levers-first (tune pack levers before widening test bands). The ONLY early-wave test edit is P5's unit-assertion split (a byte-level assertion, not a band). **Do NOT re-fit bands mid-spine.**
  - **EXCEPTION — W3R fish+station WTSD re-anchor (owner-authorized, 2026-07-24):** W3R-2 (fix hyp-2) proved the grounded arrival-range fold-to-c-bet bands are UNREACHABLE for `passive_fish` + `calling_station` without moving their population WTSD bands (fish 0.53–0.68 → 0.50–0.57; station 0.51–0.64 → 0.66–0.72), because the fit dials (`call_looseness`, station `size_elasticity`) push WTSD out of the frozen bands. The owner formally re-scoped this rule to permit a **per-persona mid-spine re-anchor for these TWO personas only**, using the P2a methodology (re-measure at final dials at both N, band = 3σ CI union rounded outward, all OTHER personas byte-identical). Consequence accepted by owner: station WTSD moves UP, away from its grounded RP6 showdown target, so the Wave-4 cluster re-anchor has more to reconcile. This exception does NOT license any further mid-spine band moves — every other persona's WTSD/AF band stays frozen to Wave 4.
- **Immutable coverage baseline + cumulative delta (anti-laundering):** an immutable initiative-start snapshot (`coverage_baseline.persona-realism-start.json`) exists; each slice re-records the operational fixture for CI green AND reports the CUMULATIVE graded-coverage delta vs the immutable snapshot. Any cumulative loss needs explicit adjudication.
- **Anti-sizing-tell:** value hands must not become size-readable (`test_sizing_spread_no_deterministic_strength_to_size`). This is F14, an INTENTIONAL-LEAVE (§8).
- **Bluff-ordering pin:** `test_bluff_ordering_across_personas_at_fixed_size` pins `station < nit < fish < tag < lag < maniac` — any bluff-path change re-anchors it deliberately.

---

## 8. Intentional-leaves (do NOT "fix")

These findings are correct design — a reviewer who sees a slice "fixing" one should FAIL it (FULL-BUILDOUT §2/§5; roadmap NO-GOS).

- **F12** — the aggression cap (5.6) compresses maniac/lag on *strong* hands. This is a **deliberate RES-D saturation fix**, not a leak. Do NOT "fix."
- **F14** — no strength-correlated sizing (value size ≈ bluff size per persona). This is the **anti-sizing-tell invariant** — sizing is decoupled from hand strength ON PURPOSE. Do NOT "fix." (Sizing overrides are permitted only in the deferred N6 slice, and only *respecting* this no-go.)

---

## 9. Correction ledger (do NOT re-introduce these refuted claims)

Pulled from RECONCILE + the §10 capstone corrections. Any worker or reviewer re-introducing these is WRONG.

1. **60% → 42.9%** — the 3×-pot T1 threshold is **42.9%** (`3/7`), NOT 60%. 60% is the α ceiling for a 1.5× bet. (RECONCILE RP3; §3 above.)
2. **The weak-draw fix needs its OWN gate** — the fold-side commit brake ALONE does NOT fix F7. `_DRAW_CALL_BONUS[WEAK]=0.20` is 2.5× the AIR base (0.08); a ~1.5× fold-merit boost barely dents the inflated call merit. F7 requires a **separate** equity/commitment gate on `_DRAW_CALL_BONUS` itself. (RECONCILE RP3 "F7 AUTO-FIX NOT EARNED".)
3. **faced_frac tests cover fresh-raisers only** — `test_faced_frac_raise_over_bet_lands_medium_not_small` (563) and `test_faced_frac_check_raise_lands_large` (577) use a FRESH aggressor (zero prior street chips), so `increment == current_bet_to` and the increment fix is a **no-op** there — they stay GREEN. The bug is the **self-re-raise** path, which no current test covers ⇒ a NEW self-re-raise test is required. (RECONCILE RP7 correction to BOTH reviewers; the earlier `pot−to_call` fix WOULD have broken 563 — the increment fix does not.)
4. **Delete the "~80% of the benefit" river claim** — this number was unsupported; delete it. Rank-only still misses blocker thin value, blocker bluffs, kicker effects, range caps, texture, line history. No fake precision. (RECONCILE RP5-S6.)
5. **Opener-position defense (F18) is NOT a JSON-only fix** — `sample_preflop_action` receives only the ACTOR's seat + a bare `facing` string; there is NO opener-position discriminator. Defending differently vs a UTG-open vs a BTN-open needs **sampler plumbing + a schema change** (`content/models.py:98–101` new `vs_rfi` opener axis) + re-authoring every pack + new tests. It CANNOT sit in the Wave-1 JSON bucket; it is deferred (owner decision). The F11 maniac-limp / `"*"`-catch-all fix stays JSON and stays in Wave 1 — the two are separate. (RECONCILE capstone #1; audit §10.1-P8 F18 reclassification.)
6. **P2's `×0.75 / ×0.50` are fit-SEEDS, not earned constants** — mark DIRECTIONAL; equity drops are non-linear (mild on 1 overcard, steeper on 2+). Under softmax ×0.50 yields ~34% observed, not 25%. (RECONCILE capstone #6 / RP2-S2.)
7. **P2 overcard damp gates MIDDLE_PAIR / TOP_PAIR ONLY — never OVERPAIR_TPTK** — the bucket bundles overpairs + TPTK; AA-on-K-high must NOT damp. (RECONCILE RP2-S4.)
8. **The made-hand vulnerability brake is NOT a "range-favorability proxy"** — RELABEL it a vulnerability (NPOT) brake, validated by equity-monotonicity (the correct validation for THAT purpose). The range-favorability "barrel-MORE on scare cards" side is UNBUILT / DEFERRED (needs F16 villain-range). Do not claim the equity check earns it. (RECONCILE RP2-S5, "most important call in the research".)
9. **RP5's bluff-share formula is CORRECT — the lead OVERRULED Sol** — RP5 used `s/(1+2s)` (the bettor form), NOT `s/(1+s)` (the defender form Sol accused it of). Do NOT "fix" RP5 to the defender form. Only "exact match at every size" wording is wrong (the code table is 4 coarse representatives). (RECONCILE RP5-S5.)
10. **P6 "toward T2" must be REAL, not slogan-EV** — a fixed `r∈[0.2,0.5]` fold reduction presented as if it targets T2 is cosmetic under softmax (TAG fold 50%→20%, station 36%→12% still force bad low-fold stack-offs). Either target the normalized post-softmax fold prob ≈ F*, or **downgrade P6 to DIRECTIONAL explicitly** — do not fake T2-awareness. (RECONCILE capstone #5 / RP3-P6.)
11. **`is_aggressor` ≠ `in_position`** — `is_aggressor` is the WHOLE-HAND last aggressor; P1's `in_position` is a per-street boolean. Do not conflate. **BB is IP vs SB** (postflop SB acts first — the audit's "BB OOP to SB" was backwards). Exclude ALL-IN/FOLDED seats from "acts after me." (RECONCILE RP1-S3.)
12. **The commit gate's P is pot-BEFORE-bet, not live `pot_bb`** — using live pot silently lowers the threshold. `c = to_call/stack` is an SPR-INTERACTION term (`c = faced_frac · P/stack`), NOT orthogonal to pot price. (RECONCILE RP3.)
13. **The "never semi-bluff-jam a station / value-jam only" line is a HERO exploit, NOT a bot mechanic** — it requires villain-range knowledge the sampler does not have (F16, range-blind). Deferred to the coaching layer. (RECONCILE RP3; audit §10.5.)
14. **The §5 preflop VPIP/PFR keystone was 6-max, mislabelled 9-max** — corrected 2026-07-25.
    - **Defect:** §5 declares its pool "online low-mid **9-max** ~100bb", but §10 already admitted anchors were "derived from 6-max solver outputs and transferred to 9-max." That admission was scoped only to the IP/OOP gap; it also silently governed the VPIP/PFR keystone, which was therefore carrying 6-max numbers under a 9-max label.
    - **Evidence:** a full-ring specialist source publishing BOTH formats side by side (6-max optimal 21/18 vs full ring 15/12), corroborated in direction and magnitude by two lower-tier sources (6max 18–25 → FR 14–20; 6max 22–28 → FR 15–20). Consistent shift ≈ **−5 to −7 VPIP points (×0.7–0.8)**. Mechanism: blinds arrive 2/6 ≈ 33% of hands at 6-max vs 2/9 ≈ 22% full ring, and fewer players left to act per seat widens 6-max opens. Live 9-max play over 150 recent hands (row in §5) sits at or below the corrected bands — consistent with the direction of the correction, indicative only at that n.
    - **Sourcing quality:** practitioner consensus. **Not peer-reviewed, not solver-derived.** Confidence `MEDIUM` on the split's existence and size, `HIGH` on its direction, DIRECTIONAL on exact band edges.
    - **CHANGED:** nit VPIP/PFR 13–16 / 10–13 → **10–14 / 8–12**; TAG 19–23 / 16–19 → **15–20 / 12–17**; LAG 26–31 / 21–26 → **21–27 / 17–23**; fish VPIP 36–48 → **40–55**. 3-bet% quoted at the full-ring **4–7%**.
    - **Deliberately NOT changed:** (a) the **gap row** — the VPIP−PFR gap does not shift between formats (~3pts for winners in either), making it a format-invariant diagnostic that needs no correction; (b) **maniac/station VPIP** — the researched 9-max bands already agree with what was written (concordance, not a miss); (c) **station/fish PFR** — sources scatter far too widely (recreational examples run 40/2 to 40/30) to justify a move; flagged UNRESOLVED and left in place.
    - **Confirming pattern:** exactly the three *position-aware* archetypes (nit/TAG/LAG) carried the error and the three *recreational* ones (maniac/station/fish) did not — because players who don't adjust to table size cannot be biased by a table-size transfer. The distribution of the error matches its proposed mechanism.
    - **Scope:** documentation only. **No test, no band in `backend/tests/`, no content pack was touched** — per §5/§7, no RP6 number becomes a test gate until the single Wave-4 re-measure, and these corrected numbers inherit that rule.
15. **The §5 postflop keystone was audited for table size (W5-a2) — five of six rows survive; only WTSD moved.** 2026-07-25. Full working, sources and conflicts in **§5a**; this is the ledger summary.
    - **CHANGED:** WTSD **tag 27–31 → 25–29 ‡**, **lag 28–33 → 26–31 ‡** (−2pts). The only postflop cells with **two independent sources publishing 6-max and full ring side by side** (6-max 27 / 27–28 vs full ring 25 / 24–25). Applied to exactly the position-aware regs, per ledger #14's mechanism. Conf `MEDIUM` on size, `HIGH` on direction, edges DIRECTIONAL. The §5 C6 re-anchor table was updated in step so it cannot drift from the keystone.
    - **CONFIRMED UNCHANGED (do not "re-correct" these):** **c-bet flop, fold-to-c-bet, turn barrel, AF.** The one side-by-side source reports them as format-invariant at its resolution. This is a decision to **withhold a correction at `LOW` confidence**, *not* a certification of the levels — do not cite these rows as "verified numbers".
    - **AF's format-invariance is now sourced, not assumed.** §5a's own list had classified AF as format-INVARIANT *a priori*, with no citation — the same unsourced-transfer move that produced ledger #14, applied to the classification rather than to the number. A side-by-side source now agrees (AF 3 = 3). **It survived by luck, not by process**; see the CONTRACT-DEFECT note in §10.
    - **STILL `[UNVERIFIED]`:** **W$SD** — its *level* triangulates well (≈49–55 across three sources) but **no source found splits it by table size**, and it appears on neither of §5a's format lists. Format genuinely open. **C-bet flop overall** — the format question came back "no shift found", but its *level* is unresolved by a real class conflict (ideal-reg-target ~70 vs observed-population 40–60), so the row stays `[UNVERIFIED]` and DIRECTIONAL-only.
    - **The c-bet band did NOT move, and the roadmap's stated reason is not the operative one.** The multiway mechanism is sound but unquantified, and the measured "−20pp" comes from metric #1, which the roadmap itself records as mis-specified (it under-reads every persona). Re-opening the c-bet target is gated on **W5-a3-i** plus a decision about whether the row is a heads-up or an aggregate statistic. Full ruling in §5a.
    - **⚠ Single-author dependency.** Most of the keystone's format evidence — preflop *and* postflop — now traces to **one** full-ring practitioner. Only WTSD has a genuinely independent second opinion, which is why only WTSD moved. A second independent full-ring postflop source should re-open c-bet, fold-to-c-bet and turn barrel.
    - **Demotion of the fold-to-c-bet and AF HARD gates: DEFERRED, not dropped** — the gating file was owned by a concurrent slice. Logged as follow-up **W5-a2-f** in §5a, and must land before W4-b.
    - **Scope:** documentation only. **No bot behavior, band fit, lever, test, or content pack was touched.**

---

## 10. Reference pool

Everything is calibrated to **online low-mid 9-max ~100bb** (audit §9.2 / RECONCILE line 7). The whole §5 stat table is pool-specific. If the target audience/pool differs, the entire keystone needs recalibration (FULL-BUILDOUT §6 #7).

**The 6-max→9-max transfer caveat applies to the WHOLE keystone, not just IP/OOP.** Anchors were mostly derived from 6-max solver outputs and transferred to 9-max. Two consequences, both live:

1. **IP/OOP gap (RECONCILE RP1-S6):** the exact *gap* magnitude is `LOW`-conf (9-max changes opening ranges / caller composition / multiway incidence); the *direction* (IP>OOP) is `HIGH`-conf.
2. **VPIP/PFR keystone (§5, corrected 2026-07-25 — ledger #14):** the same transfer left the nit/TAG/LAG preflop rows carrying **6-max** values under a 9-max label. Corrected down ~0.7–0.8× VPIP (fish corrected up). The correction rests on **practitioner consensus, not peer-reviewed or solver data** — one strong full-ring specialist source publishing both formats side by side (6-max 21/18 vs full ring 15/12), corroborated in direction and magnitude by two lower-tier sources. Confidence `MEDIUM`; band **edges** stay DIRECTIONAL.

3. **Postflop keystone (§5, audited 2026-07-25 — ledger #15 / §5a):** the transfer was checked and **mostly holds**. c-bet, fold-to-c-bet, turn barrel and AF come back format-invariant from the one side-by-side source (`LOW` conf — a withheld correction, not a certification); **WTSD does not** and was corrected down 2pts for tag and lag on two independent sources; W$SD and the c-bet *level* remain `[UNVERIFIED]`. The transfer caveat is therefore now **narrowed, not lifted** — it stands in full for the c-bet level and for W$SD, and it stands as a `LOW`-confidence "probably fine" everywhere else postflop.

**Standing rule:** any *other* magnitude in this contract that traces to a 6-max solver output and is quoted at 9-max is suspect by default and must be re-checked against a full-ring source before it is written into a test as a gate. Recreational-archetype anchors are the exception — they are table-size-insensitive, so the transfer is harmless there (§5).

**Standing rule, second limb (added by W5-a2, ledger #15):** a **format-comparative** source — one that publishes both formats side by side and can therefore be asked the difference — outranks a better-known source that reports a single pooled number, *for the format question only*. For the **level**, the ranking inverts: prefer a population-class measurement over an ideal-target one, and **match the class of the source to the class of the harness metric** before comparing them at all. Most of the −20pp c-bet "miss" is a class mismatch, not a behavior deficit.

> **CONTRACT-DEFECT (HIGH) — logged against this contract by W5-a2 under §11 item 15, which states the contract is not immune.**
> §5a shipped its **Format-SENSITIVE / Format-INVARIANT lists as unsourced assertions.** Placing **AF** on the INVARIANT list is a cross-format transfer claim, and it was made with no citation — structurally the *same* move that caused ledger #14, one level up: ledger #14 transferred an unsourced *number*, §5a transferred an unsourced *licence to transfer numbers*. It mattered, because AF is a **HARD-today CI gate** that the list authorised to sit unchecked. W5-a2 has now sourced AF's invariance and it holds — **the classification survived on luck, not on process.**
> **Remedy, now in force:** every entry on either §5a list must carry a source or be marked `[UNVERIFIED]`, exactly as the registry rows do. Current state: **AF — sourced (S1, side by side). gap — sourced (ledger #14). "any ordering or monotonicity claim" — `[UNVERIFIED]`, an untested blanket licence and the largest remaining hole. W$SD — on neither list, correctly, because no source splits it.**

---

## 11. Reviewer checklist (apply to a slice's output — each item is pass/fail)

The most important section. For a persona-realism slice under review:

1. **[Softmax law]** Are ALL new magnitudes justified by a MEASURED (observed closed-loop) stat hitting its target, or are any dropped-in constants closing the slice on "the constant is in the code"? Any un-fit constant → **FAIL**.
2. **[Metric-DoD]** If the slice needs a NEW harness metric to prove its effect, is that metric live AND showing the expected direction? If not, the slice cannot close on a HARD gate → **FAIL** (unless correctly self-labeled DIRECTIONAL).
3. **[Gate boundary — §4]** Does the mechanic's gate exactly match §4? Specifically: P2 damp gates MIDDLE_PAIR/TOP_PAIR only (NOT OVERPAIR_TPTK)? P5 floor is MIDDLE_PAIR only? P1 factor hits the WHOLE aggressive candidate (`bluff_mass`+`_AGG_BASE`+`_DRAW_AGG_BONUS`)? P4 street mult on the bluff side only (made `_AGG_BASE` does NOT decline)? P3 commit brake scoped to facing-fold merit only? Any boundary mismatch → **FAIL**.
4. **[EV numbers — §3]** If the slice cites a threshold: is the 3×-pot T1 read as **42.9%** (not 60%)? Are T1/T2/T3 the exact forms? Is the bettor bluff share `s/(1+2s)` (not `s/(1+s)`)? Any wrong number → **FAIL**.
5. **[Correction ledger — §9]** Does the slice re-introduce any refuted claim in §9 (F7 auto-fix without a separate gate; F18 as JSON-only; "~80% benefit"; range-favorability claimed as earned; P6 flat-r faked as T2-aware; `is_aggressor` used as `in_position`; live `pot_bb` as the gate denominator)? Any → **FAIL**.
6. **[HARD-vs-directional — §5]** Does the slice's acceptance criterion demand a strict numeric match on a DIRECTIONAL-only target (e.g. per-overcard bet-rate, IP/OOP split, turn-barrel%, multiway value)? Demanding a hard match on a directional target FAILS good work → **FAIL the criterion**. Conversely, are the three HARD-today gates (AF, Fold-to-C-bet, WTSD) actually checked where applicable?
7. **[Band re-anchor — §7]** Was any band re-anchored **mid-spine**? The only legitimate band re-anchor is the SINGLE Wave-4 cluster re-measure; the only early-wave test edit is P5's unit-assertion split. Any mid-spine band widening (outside the P5 assertion split) → **FAIL**.
8. **[Intentional-leave — §8]** Did the slice "fix" F12 (aggression-cap compression) or F14 (no strength-correlated sizing)? Either → **FAIL**.
9. **[Estimator parity — §7]** Does the slice make the LIVE bot diverge from the streetless policy? If so, did it thread `range_estimate.py` the SAME context and add a parity test? Divergence without parity → **FAIL**.
10. **[Default-off byte-identity]** Do new args default to today's behavior so `range_estimate` + the population harness stay byte-identical for un-opted-in callers? Is the action draw still the FIRST `rng.choices` (new randomness only after)? If not → **FAIL**.
11. **[Denominator unification — §7]** If the slice touches faced_frac / commit-gate / T1, does it use ONE "pot before current aggression" denominator (not live `pot_bb`)? If not → **FAIL**.
12. **[Stacked-multiplier order — §7]** If the slice adds a multiplier, is it applied to the whole aggressive candidate in the §10.2 order, and is the *combined* product calibrated (not each factor independently)? If not → **FAIL**.
13. **[Domain purity + scope]** Does the slice keep `personas*.py` pure (no web/DB), leave the grader / `spot_signature()` untouched, and stay inside the files its ticket names? Any breach → **FAIL**.
14. **[Coverage delta]** Did the slice report the cumulative graded-coverage delta vs the immutable snapshot, and is any loss adjudicated? Silent loss → **FAIL**.
15. **[Target provenance — §5a]** Does the slice cite a §5 target as a **bare number**, with no `(format, pool/stakes, source)` triple? → **FAIL**. Does it transfer a format-SENSITIVE stat across table sizes without restating it, or gate HARD on an `[UNVERIFIED]` row? → **FAIL**. And the W3R-1 rule: did the slice fail to reach a target and respond by widening a lever, widening a band, or re-scoping the test — instead of stopping and re-opening that target's provenance? → **FAIL**. **This contract is not immune:** a format/pool mismatch found here is a **CONTRACT-DEFECT at HIGH**, and the slice may not pass on the contract's authority alone.

---

## 12. Source pointers

- **Grounded magnitudes / engine mapping / acceptance criteria (P1–P9):** `docs/ai-dlc/research/persona-realism-audit-2026-07-24.md` §10.1 (per-P blocks), §10.2 (cross-package interactions), §10.2a (context-plumbing contract), §10.3 (keystone stat table + C6 re-anchor), §10.4 (sequencing/waves), §10.5 (deferred gaps), §10.6 (owner decisions).
- **Corrections / what was refuted (AUTHORITATIVE):** `docs/ai-dlc/research/persona-realism-artifacts/RECONCILE.md` — per-package (RP1–RP8) verdicts + the capstone 8 corrections.
- **Lever→finding map, invariants §5, findings coverage F1–F20 §2, glossary §8:** `docs/ai-dlc/research/persona-realism-FULL-BUILDOUT.md`.
- **Wave plan, cross-cutting discipline (softmax/D7/D8/D9/parity/baseline), no-gos:** `docs/ai-dlc/roadmap/persona-realism.md`.
- **Findings F1–F20 (root cause, evidence, class):** audit §3, §6b.
- **Depth on any single package:** `persona-realism-artifacts/RP1_findings.md … RP8_findings.md` + `RP*_sol.md` (adversarial reviews).
