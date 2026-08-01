# RFI-by-Seat Provenance — 9-max Full-Ring Opening-Raise Frequency

- **Date:** 2026-07-31
- **Slice:** R9-SEATPROV (persona-realism)
- **Status:** **PARTIAL** — solver-chart provenance **ESTABLISHED** for 9-max at coarse seat granularity; **measured-population provenance NOT ESTABLISHED** (no verifiable pool study found via web; population cells below are [UNVERIFIED] internal recall).
- **Method note:** Web search + fetch performed 2026-07-31. Fetches verified page content directly (not search-snippet hearsay) for sources T1, T3, T4, T5. No PokerTracker/H2N/HM population study with per-seat full-ring RFI numbers is publicly retrievable; the UAlberta corpora are predominantly limit hold'em and were not pursued.

## Provenance triples

| ID | (format, pool, source) | Verification | Applicability |
|----|------------------------|--------------|---------------|
| T1 | (9-max full-ring cash, 100bb, **solver-derived simplified charts** — Preflop Wizard blog "Preflop Charts: Free GTO Poker Range Charts for Every Position (2026)", preflopwizard.app/blog/preflop-charts) | VERIFIED by direct fetch 2026-07-31 | **APPLICABLE** — this is the strongest triple found. Caveat: "simplified solver" charts, exact solver/config unstated; seats coarser than 9 (uses one "MP" bucket). |
| T2 | (6-max cash, 100bb, solver-derived — GTO Gecko blog + Preflop Wizard 6-max table) | VERIFIED by direct fetch | **NOT-APPLICABLE (6-max)** — recorded only as a flagged cross-check; never import. GTO Gecko's prose adds one full-ring datum: "full-ring UTG ≈ 12–13%". |
| T3 | (9-seat labels UTG..SB, **80bb**, unspecified provenance — pokerskill.com RFI glossary) | VERIFIED by direct fetch, but the page itself does not state solver vs population vs illustrative | WEAK — 80bb not 100bb, provenance unstated. Numbers look GTO-Wizard-MTT-shaped. Use for shape only. |
| T4 | (9-max **early-stage MTT**, deep, "good benchmarks" — funfarm.pro RFI article) | VERIFIED by direct fetch | WEAK — MTT recommendation bands, not cash, not population. Shape only. |
| T5 | (9-max low/mid-stakes cash **population**, — , —) | **NO SOURCE FOUND.** Cells below are [UNVERIFIED] recalled-from-training. | Never gate on these. |

## Per-seat RFI tables per source

Seat vocabulary in this project: UTG, UTG1, UTG2, LJ, HJ, CO, BTN, SB, BB (BB has no RFI — everyone folding to BB is a walk).

### T1 — Preflop Wizard, 9-max full-ring cash, 100bb, solver-derived (VERIFIED fetch)

| Seat | RFI % | Note |
|------|-------|------|
| UTG | ~11 | source's own "~" — simplified chart |
| "MP" bucket | ~13 | source collapses UTG1/UTG2/LJ into one bucket; per-seat split is NOT given |
| HJ | ~17 | |
| CO | ~24 | |
| BTN | ~40 | |
| SB | ~30 | raise-or-fold model |
| BB | n/a | |

Source's caveat: early-position 9-max tightening vs 6-max; late-position ranges ≈ format-invariant (same players left to act).

### T2 — 6-max 100bb solver tables (NOT-APPLICABLE, recorded to prevent silent import)

Preflop Wizard 6-max: UTG ~15, HJ ~19, CO ~27, BTN ~43, SB ~36. GTO Gecko 6-max: UTG ~18, HJ ~22, CO ~28, BTN ~43, SB ~40–48 (with limps). ⛔ These are the numbers most likely to be accidentally imported into a full-ring bot — the format-confusion failure mode that already caused one correction in this project. GTO Gecko's full-ring aside: UTG ≈ 12–13.

### T3 — pokerskill.com, 9-seat labels, 80bb, provenance unstated (VERIFIED fetch of the page, NOT of the numbers' origin)

| Seat | RFI % |
|------|-------|
| UTG | 13 |
| UTG+1 | 14 |
| MP | 18 |
| LJ | 22 |
| HJ | 26 |
| CO | 28 |
| BTN | 55 |
| SB | 35 |

Caveat: 80bb; page never says solver vs population; BTN 55 is far above T1's 40 (80bb + likely MTT-chart origin). Shape use only.

### T4 — funfarm.pro, 9-max early MTT "good benchmarks" (VERIFIED fetch)

UTG 15–18, MP 18–24, HJ 24–28, CO 32–38, BTN 50–65. All cells wider than T1 (MTT antes widen everything). Shape use only.

### T5 — low-stakes full-ring population (NO SOURCE FOUND — every cell [UNVERIFIED], recalled from training)

Typical micro/low-stakes online full-ring pools are tighter and more passive than solver baselines; classic tracker-era folklore puts pool averages roughly:

| Seat | RFI % [UNVERIFIED] | Confidence |
|------|--------------------|------------|
| UTG | 8–11 | low |
| UTG1 | 9–12 | low |
| UTG2 | 10–13 | low |
| LJ | 11–14 | low |
| HJ | 13–17 | low |
| CO | 17–22 | low |
| BTN | 24–34 | low (steal stats historically ~25–33 at micro FR) |
| SB | 15–28 | very low (huge spread: limp-heavy pools crater SB RFI) |

These may inform DIRECTION and sanity only. They must not become bands, gates, or fixture targets.

## Synthesis row — recommended per-seat bands, low-stakes 9-max full-ring pool

Construction: T1 anchors the verified skeleton (UTG, HJ, CO, BTN, SB); UTG1/UTG2/LJ are monotone interpolation inside T1's "MP ~13" bucket (DERIVED, not sourced); population shading from T5 widens each band downward.

| Seat | Band (RFI %) | Label |
|------|--------------|-------|
| UTG | 9–13 | anchor 11 VERIFIED(T1, solver); low edge [UNVERIFIED] pop shading |
| UTG1 | 10–14 | [DERIVED] interpolation — no source gives this seat alone at 100bb cash |
| UTG2 | 11–15 | [DERIVED] interpolation |
| LJ | 12–17 | [DERIVED] interpolation (T3's LJ 22 is 80bb/unknown-provenance — excluded from band) |
| HJ | 14–19 | anchor 17 VERIFIED(T1); low edge [UNVERIFIED] |
| CO | 20–27 | anchor 24 VERIFIED(T1); low edge [UNVERIFIED] |
| BTN | 30–45 | anchor 40 VERIFIED(T1); pop low edge [UNVERIFIED] |
| SB | 15–36 | anchor 30 VERIFIED(T1, raise-or-fold model); band deliberately wide — SB RFI is model-dependent (limping pools) — weakest row |
| BB | n/a | walk only |

Only the five T1 anchors are verified-with-citation. Every band EDGE is at best derived; **no full row is gate-grade yet.**

## Derived shape stats — cliff ratios (BTN ÷ UTG)

| Source | Cliff BTN/UTG | Basis |
|--------|---------------|-------|
| T1 (9-max 100bb cash, solver) | 40/11 ≈ **3.64** | VERIFIED anchors |
| T3 (9-seat 80bb, unknown) | 55/13 ≈ **4.23** | weak |
| T4 (9-max MTT) | 50–65 / 15–18 ≈ **2.8–4.3** | weak, MTT |
| T2 (6-max — NOT-APPLICABLE) | 43/15 ≈ 2.9 (PW) / 43/18 ≈ 2.4 (Gecko) | flagged for contrast only |
| T5 population [UNVERIFIED] | ~24–34 / 8–11 ≈ **2.4–3.9** | recall |

Adjacent-seat ordering: every source strictly increases UTG→BTN; every 9-max source with an SB row puts **SB between CO and BTN** (T1: 24 < 30 < 40; T3: 28 < 35 < 55).

### Verdicts on the circulating numbers

- **Shipped nit ladder cliff 2.84 (21.42/7.54): NOT CONTRADICTED, NOT YET SUPPORTED — UNRESOLVED.** As a *pool/GTO baseline* cliff it is low (baselines cluster 3.6–4.2). As a *nit-archetype* cliff it is directionally plausible — a nit compresses positional widening ("tight everywhere") — but that compression claim is itself [UNVERIFIED]; no archetype-stratified source was found. The ladder's SHAPE (strict increase; SB 16.59 sitting between CO 15.99 and BTN 21.42) matches every source's ordering. Its absolute BTN level 21.42 sits inside the [UNVERIFIED] population BTN band's low half, consistent with "nit ≈ tighter than pool average" — again direction only.
- **Candidate ratio band 3.2–5.25: SUPPORTED as a baseline-pool bracket** — it contains every verified/weak 9-max cliff found (3.64, 4.23, and most of T4's 2.8–4.3). It is NOT established as an archetype-invariant band: nit-side cliffs may legitimately fall below 3.2 (see above), and nothing found supports the upper half above ~4.3.
- **~6.5 UTG→BTN derivation: UNSUPPORTED.** No source of any quality produced a 9-max cliff above ≈4.3. 6.5 exceeds even the 80bb/MTT-shaped T3 (4.23). If that derivation came from mixing a 6-max BTN with a full-ring UTG (43/6.5≈6.6-style arithmetic), that is exactly the cross-format import this doc exists to block. Retire it unless a source materializes.

## DO-NOT list (gate hygiene)

1. **Do NOT gate on any T5 population cell** — every one is [UNVERIFIED] recall.
2. **Do NOT gate on UTG1/UTG2/LJ levels** — no source resolves these seats individually at 9-max 100bb cash; the synthesis cells are interpolation.
3. **Do NOT import any T2 (6-max) number into full-ring targets** — NOT-APPLICABLE by prior project correction; this includes the 15/19/27/43 and 18/22/28/43 ladders.
4. **Do NOT gate on T3 or T4 levels** — 80bb/unknown-provenance and MTT respectively.
5. **Do NOT promote the ~6.5 cliff derivation anywhere** — unsupported, likely cross-format arithmetic.
6. **Do NOT promote the 3.2–5.25 band to an archetype gate** — it is a baseline-pool bracket; nit-side ladders may sit below it.
7. **Do NOT treat SB RFI as settled** — weakest row; solver raise-or-fold (≈30) vs limpy pools (≪) diverge wildly.
8. Safe to gate TODAY (shape only, already shipped policy): strict seat-by-seat increase UTG→BTN; SB strictly between CO and BTN; BTN is the max non-blind seat. These hold in every source examined.

## Archetype implications (direction-level; provenance weak everywhere below archetype granularity)

- **Nit:** Ladder LEVEL (UTG 7.54 … BTN 21.42) is plausibly below-pool at every seat, as intended; cliff 2.84 stays a shape-only assertion until archetype-stratified data exists. No change forced by this doc; the ceiling stays SHAPE-gated.
- **TAG:** Should track the T1 solver skeleton most closely of the roster (that is roughly what "TAG" means): UTG near ~11, BTN near ~35–40, cliff ~3.5. Direction: TAG's cliff should EXCEED the nit's.
- **LAG:** Above-pool at every seat with the widening concentrated LATE (LJ→BTN), not early — a LAG UTG ≈ 15–18 and BTN ≈ 50+ is the recalled folklore [UNVERIFIED]; the R9-SEATMETRIC finding (25% UTG-always vs 66% BTN-rarely) is the inversion of exactly this and would fail even a shape-only "cliff ≥ TAG's cliff" check. Direction: cliff(LAG) ≥ cliff(TAG) > cliff(NIT).
- **Maniac:** High everywhere with a COMPRESSED cliff from the top (opening 40% UTG leaves little room to triple by BTN) — the one archetype whose cliff may legitimately fall below the nit's, for the opposite reason. Do not apply a single monotone-cliff-ordering gate across the whole roster.
- Cross-cutting: because only cliff *ordering* between archetypes is directionally defensible (nit-compressed < TAG-solver-like ≤ LAG-steep; maniac excluded), the first safe seat-axis instrument is an ordinal cross-persona comparison, not per-seat bands — consistent with R9-SEATMETRIC's "instrument definition only" scoping.

## Sources

- https://www.preflopwizard.app/blog/preflop-charts (T1, T2 — fetched)
- https://gtogecko.com/blog/preflop-charts-opening-ranges (T2 + full-ring UTG aside — fetched)
- https://www.pokerskill.com/poker-glossary/rfi/ (T3 — fetched)
- https://funfarm.pro/en/poker/rfi-in-poker (T4 — fetched)
- Searched without usable result: PokerTracker/Hand2Note/HM population studies, blackrain79 (gives global 15/12 full-ring VPIP/PFR guidance, no per-seat RFI), rangeconverter (charts behind PDF/403), poker-coaching.s3 100bb PDF (403), gipsyteam (no numbers).
