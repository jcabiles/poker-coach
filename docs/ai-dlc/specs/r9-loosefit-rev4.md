# Spec — R9-LOOSEFIT rev 4: nit-only, gated at correctly-priced nodes AND across the cell population

status: draft-rev4 (awaiting delta dual review)
slice: r9-loosefit · initiative: persona-realism · code pin: `origin/main` = b63dfaa
supersedes: `specs/r9-loosefit.md` (rev 2, build halted at T1) and `specs/r9-loosefit-rev3.md`
(⛔ WITHDRAWN, dual FAIL — its feasibility table was mispriced)
contracts: `contracts/r9-loosefit.md` — **the REV-2 SCAN block only; §1–§8 are the older,
partly-refuted scan** · ledger: `ledger/r9-loosefit.md` (B-1…B-15, S-1…S-8, verification tables)
citation convention: code @ b63dfaa; ai-dlc docs @ working tree, anchors authoritative.
**Branch from `origin/main` WITHOUT commit `7736156`** — the halted build's shares accessor is not
part of this slice, which makes ledger row B-15 inapplicable here (S-6).

## One-line goal

Move **nit's `call_looseness` 0.6 → 0.45 and nothing else**, and prove — at correctly-priced
constructed nodes *and* across the whole canonical cell population — that the nit now folds
materially more than it did, and more often than tag, everywhere the lever can reach.

### ⚠️ The claim is PAIRWISE, and that narrowing is deliberate (S-3 resolution, sharpened by S-10)

Rev 3 was titled "make the nit measurably the tightest defender." **That claim is NOT made here and
is NOT supported by these gates.** Every gate in this spec compares nit against **tag only**. All
of them can pass while nit still folds less than lag, passive_fish, maniac or the calling station
at some nodes — nothing here measures that, and the roadmap's own scoped ask is a pairwise
nit-versus-tag separation gate, not an all-persona ranking.

**Binding on the build:** the roadmap "mark built" note (files-to-touch 5) must say *"nit folds
more than tag"* and must **not** use "tightest defender" or any all-persona ranking language. An
all-persona ordering claim would need the existing fold-ordering test's coverage extended, which is
out of scope. This is written down because the phrase has been used loosely in this initiative
before and would ride on gates that do not support it.

## The structural result this spec is built on (measured, then verified analytically)

nit authors `call_looseness = continue_ref = 0.6`. At a facing node the engine scales the CALL
merit by `looseness` and the RAISE merit by `rscale = looseness/continue_ref`
(`personas_postflop.py:1241-1249`). Both defend merits therefore move by the **same** factor
`s = 0.45/0.6 = 0.75`, so the whole continue mass scales by `s` and the move is a **pure shift of
the continue/fold log-odds by ln(0.75) = −0.2877**. Consequently the self-difference depends on the
base fold probability *alone*:

```
self(p₀) = p₀ / (p₀ + 0.75·(1 − p₀)) − p₀        max |predicted − measured| = 1.11e-16 over 25 nodes
```

> **Hard ceiling: the self-difference can never exceed (1−√0.75)/(1+√0.75) = 0.071797**, attained
> at base fold probability 0.4641. Director-verified analytically and numerically. No board, price,
> street, headcount or legal shape beats it; the maximum observed across 2,600+ measured cells is
> 0.071795. **Any self threshold ≥ 0.072 is unsatisfiable by construction** — rev 3's 0.05 was
> already 70 % of a physical ceiling nobody had computed.

**Why identity separation is structurally narrow.** nit and tag share *every lever that reaches a
facing node's FOLD and CALL merits* — `call_looseness` 0.6, `stickiness` 0.6, `continue_ref` 0.6,
`size_elasticity` None, `position_sensitivity` 1.0. They differ only in `aggression` (0.6 vs 2.4),
`bluff_freq`, `multiway_bluff_damp`, `spr_commit` and `line_sensitivity` — all of which reach only
the RAISE leg, the commit gate, or the line damp. Therefore:

- **On a FOLD/CALL-only node the two personas are byte-identical**, and the identity leg collapses
  into the self leg (S-2). On the re-priced canonical grid, **560 of 970 non-degenerate cells
  (57.7 %) have nit@0.60's fold probability exactly equal to tag's.**
- Identity difference = self difference **+ the pre-existing HEAD gap** created by tag's
  `aggression: 2.4` diluting tag's fold share. At panel node P1 that is 0.0697 + 0.0533. **The
  identity leg is a real gate — red at HEAD — but it is not a pure measure of defensive
  discipline, and this spec says so rather than implying otherwise.**

## Premise (restated, unchanged from rev 3 and independently verified)

Rev 2 claimed the nit "measurably folds LESS than tag — backwards." False at stable sample: the
independent estimate is **+0.0087 ± 0.0063** (56 seeds + a second large draw; ledger B-12). The nit
already folds marginally *more*. **This slice converts a statistical tie into a visible identity
difference — a magnitude problem, not a sign problem.**

## Binding constraint (acknowledged, not resolved here)

`test_r9d_s5_fold_rate_rise_follows_the_defensible_ladder` (`:9452`) floors this lever: measured
**0.38 FAIL · 0.40 FAIL · 0.42 pass · 0.45 pass**, deterministic, verified twice by independent
agents. The floor is **not constant** — tightening tag raises it (contract scan) — which this slice
guarantees against by not touching tag. **0.45 is chosen for margin, not maximum effect.** Whether
that gate's premise is defensible is filed as `N-LADDER-PREMISE`, deliberately out of scope.

## Measured feasibility — CORRECTLY PRICED

Method: `sample_postflop_decision` called directly with `latest_aggressor_contribution_bb` always
supplied; `_dist_for_pack` **never used** (it has no such parameter — naming it is what would have
propagated rev 3's bug). Every node asserts, before its numbers are kept, that the engine's own
computed faced fraction equals both `to_call / (pot_bb − contribution)` (to 1e-12) and the fraction
the row is labelled with (to 1e-9). The instrument was first proved to catch the documented bug:
rev 3's `pot_bb=6, to_call=3, no contribution` reads as faced_frac **1.00**, not 0.50. All nodes
below are built as `pot_bb = pre_bet_pot + to_call`, `contribution = to_call`.

### The panel — 4 gated nodes + 1 declared control

All at SPR 20, `aggressor_bet_prev_street=False`, `noise` default.

| id | hole | board | street | legal | raise bounds | pot | to_call | stack | opp | f | self | identity | HEAD gap | min legal prob |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **P1** | 9h 4c | Kc 9s 3h | flop | F/C/R | 36–480 | 24 | 12 | 480 | 1 | 1.000 | +0.0697 | +0.1230 | 0.0533 | 0.0483 |
| **P2** | 9h 4c | Kc 9s 3h 2d | turn | F/C/R | 36–480 | 24 | 12 | 480 | 3 | 1.000 | +0.0717 | +0.1285 | 0.0568 | 0.0422 |
| **P3** | Ah 8d | Kc 9s 3h | flop | F/C/R | 18–360 | 18 | 6 | 360 | 1 | 0.500 | +0.0718 | +0.1185 | 0.0467 | 0.0250 |
| **P4** | 9h 4c | Kc 9s 3h 2d | turn | F/C/R | 18–360 | 18 | 6 | 360 | 1 | 0.500 | +0.0595 | +0.1023 | 0.0428 | 0.0594 |
| **C5** control | 9h 4c | Kc 9s 3h 2d | turn | **F/C** | — | 24 | 12 | 480 | 1 | 1.000 | +0.0707 | ≡ self | 0.0000 | 0.4017 |

**C5 carries the SELF leg only. Its identity difference is identically its self difference** (the
personas are byte-identical without a raise), so asserting identity there would be one gate wearing
two hats. C5 exists to prove the lever still moves the bot when the raise branch is absent.

### Node classes deliberately EXCLUDED, each with its reason

| class | why excluded |
|---|---|
| top pair (+0.0614 identity), overpair (+0.0369) | below any threshold that is also red at HEAD |
| pot-sized bet on a weak holding | **rounded**-degenerate, not forced: folds 0.9999942860 / 0.9999957145 / 0.9999927823, self movement 1.4e-6 (S-8) |
| river bluff-catcher | `_RIVER_RAISE_FLOOR` zeroes the value-raise ⇒ P(raise) exactly 0, identity collapses to self |
| river air / ace-high | `bluff_cell and street is RIVER` ⇒ CALL merit 0.0, P(call) exactly 0 |
| MONSTER any node | `_FOLD_BASE[MONSTER] = 0.0` ⇒ P(fold) exactly 0 at every price/SPR/headcount; all 192 canonical monster cells degenerate |
| **SPR between 1.2 and 2.5** | ⚠️ **the trap that looks like a win.** nit's `spr_commit` is 1.2, tag's is 2.5, so in that band *tag* commits (fold → 0.0000) and nit does not, manufacturing an identity difference of +0.0654 **that the lever did not produce.** Any node in this band is forbidden |
| multiway with the bluff damp firing | `multiway_bluff_damp` 0.3² crushes the raise leg to 0.0014 |

## Pre-registered thresholds (from the table above; NOT to be re-chosen)

- **Self leg ≥ 0.040** at P1–P4 and C5. Binding node **P4 at +0.0595 → 1.49× margin**.
- **NO identity leg on the panel.** ⚠️ **An earlier draft of this spec gated identity ≥ 0.075 at
  P1–P4. That gate was VACUOUS and is removed (finding S-9).** The decomposition
  `identity = self + HEAD_gap` is an exact telescoping identity, not an approximation, and
  `HEAD_gap` is fixed at HEAD and untouched by this slice (tag is out of scope). So a build that
  merely clears the self floor already forces identity to 0.0828–0.0968 at the four panel nodes —
  **above the 0.075 floor before that floor is ever reached.** The gate could not fail while the
  self gate passed, i.e. it added zero verification power while presenting as an independent leg.
  Raising the floor to bind would leave 1.02× margin at P4, which is noise-thin on a gate whose
  whole point is determinism. **The cross-persona claim is carried by G-SWEEP instead**, which is a
  genuine population comparison and is red at HEAD by 2.08× — it is not subsumed by anything.
- **Non-degeneracy** at every panel node, both personas, both lever values: every *legal* action's
  probability in [0.01, 0.99]. Tightest observed is P3's raise leg at 0.0250.
- **Robustness (measured, not asserted):** over a ±15 % price band and ±1 opponent around each
  panel node, worst self = +0.0595 and worst identity = +0.1023 — both still at P4.

## The sweep gate — the strongest evidence in the slice

Four hand-picked nodes cannot support a general claim (S-3). The canonical enumeration
`_nlogit_cells()` (`:7010`, 1,728 cells) answers the general question — **but its own prices are
wrong**, and that is a repo defect, not a spec choice:

> `_NLOGIT_PRICES = (2.0, 4.0, 6.0, 12.0)` at `pot_bb = 6.0` with `contribution = to_call` yields
> engine faced fractions **0.50, 2.00, 600.00, 1200.00** — while the source comment at `:7005`
> claims "1/3 pot … 2x pot". Director-verified. **Half that grid tests bets of 600× and 1200× the
> pot**, where the R10-TAIL unbounded term drives P(fold) to 0.999994. Filed as `N-NLOGITPRICE`.

This slice therefore builds its sweep on a **re-priced** construction — `pot_bb = pre_bet_pot +
to_call`, `contribution = to_call`, faced fractions {⅓, ⅔, 1, 2} (the grid's own *intended*
labels), SPR held at the grid's intent — and pins that construction in the gate, or the gate
silently reverts to measuring 600×-pot bets.

| | at HEAD (nit@0.60) | after the move (nit@0.45) |
|---|---|---|
| non-degenerate cells | 970 of 1,728 | 970 of 1,728 |
| cells where nit folds strictly more than tag | **384 (39.6 %)** | **970 (100.0 %)** |
| … by more than 0.02 | 300 (30.9 %) | 826 (85.2 %) |
| cells where nit folds LESS than tag | — | **0** |
| reversals anywhere (panel + sweep + 3,456 cells) | — | **0** |

- **G-SWEEP-a: at least 800 of the 970 non-degenerate cells show nit@0.45 folding strictly more
  than tag.** Measured 970 → 1.21× green; at HEAD 384 → **red by 2.08×**.
- **G-SWEEP-b: at least 650 of 970 by more than 0.02.** Measured 826 → 1.27×; HEAD 300 → red 2.17×.
- The gate must **enumerate** its denominator, not assert 970 — the count depends on the
  [0.01, 0.99] degeneracy constant, which is arbitrary and to which the count is sensitive.

## Files to touch (complete)

1. `content/personas/nit.json` — `call_looseness` 0.6 → **0.45**; add a `_doc` version array (nit
   lacks one; `_doc` is a schema-ignored extra key); bump `version` (1.5.0).
   **`continue_ref: 0.6` and `stickiness: 0.6` byte-untouched.**
2. `backend/tests/test_personas_postflop.py` —
   a. **G-NODE panel** — P1–P4 + C5 as complete tuples, built on a contribution-aware helper (NOT
      `_dist_for_pack`) that asserts each node's engine-computed faced fraction equals its label.
      Each node records its measured baseline in a comment so a later reader can distinguish a
      re-measurement from a re-pin. Docstring states the identity leg's composition (self + HEAD
      aggression gap) and the 0.071797 ceiling.
   b. **G-SWEEP** — the re-priced cell sweep, both legs, denominator enumerated, re-pricing pinned.
   c. **Correct the five statements that this slice makes false (S-4):** `:6899`, `:6925`, `:7208`,
      `:8468`, `:8610` — "authored value" → "calibration anchor". Assertions unchanged.
   d. `_GOLDEN_STATS_N200` re-record per the protocol at `:3316-3448`, attribution proven by revert
      per `:3530-3535`.
3. `backend/tests/test_limper_coverage_belt.py` — `_PRE_M3_FIRES` re-record per `:44-287`,
   attribution proven by revert per `:277-287`.
4. `docs/ai-dlc/reports/r9-loosefit-rev4-measurement.md` — **new**: the panel table, the sweep
   distribution and histograms, the ceiling derivation. This is where the population evidence
   lives; rev 3's print-only "report test" is **dropped** (S-5 — `pytest -q` does not emit passing
   tests' stdout, so it would have been a test that asserts nothing and shows nothing).
5. `docs/ai-dlc/roadmap/persona-realism.md` — mark built; record the five filings below.

## Filings (recorded, NOT built here)

- **`N-LADDER-PREMISE`** — is R9-DEFENCE-a's "the nit must show the largest fold-rate rise" premise
  defensible when the nit is genuinely tight? Sole constraint floring this lever. Theory reviewer +
  owner ruling. If it falls, the window opens to ≈0.31.
- **`N-NLOGITPRICE`** (new) — `_NLOGIT_PRICES` produces 600× and 1200× pot bets while its comment
  claims ⅓-pot to 2×-pot. Half the N-LOGIT canonical grid tests prices that cannot occur.
- **`N-ANCHORSTALE`** (narrowed by S-4) — the five known-stale statements are fixed *in this slice*;
  what remains filed is the broader audit of 41 `model_copy(update=` sites for the same
  "author the value on the probe copy, so the shipped value is never read" idiom.
- **`N-TAGPIN`** — tag's lever is immovable until `test_elasticity_split_...` (`:1321`) is re-scoped
  onto a **fully synthetic** pack (repointing at another shipped pack only moves the pin), which is
  a prerequisite of ever authoring `size_elasticity` on tag. Carries the four `_W3R6_RAISE_DROP`
  pins (`:6260`), which have **no documented re-record protocol**.
- **`N-SIMFLAKE`** (new) — `test_sim_session_buyin_cap.py::test_every_hand_starts_every_seat_inside_the_buyin_band`
  is genuinely flaky: `app/services/sim_session.py:16-18` uses unseeded `secrets.randbits`. Failed
  once and passed on re-run and standalone during review. A non-deterministic test in a suite whose
  entire discipline is determinism.

## Out of scope

tag and lag `call_looseness` (see `N-TAGPIN`) · `continue_ref` and `stickiness` on any pack ·
BANDS values (frozen to W4-b) · re-opening R9-DEFENCE-a's ladder (`N-LADDER-PREMISE`) · fixing
`_NLOGIT_PRICES` itself (`N-NLOGITPRICE` — this slice re-prices only its OWN sweep) · the 41-site
staleness audit · `line_aware` passthrough · engine code (`personas_postflop.py` untouched) ·
`_persona_stats` · `spot_signature()` · the halted build's shares accessor (`7736156`, not branched
from).

## Constraints (repo + initiative law)

Strategy lives in versioned `content/` data — one pack value, tests and docs only, zero engine
code. Domain core `backend/app/domain/` has no web/DB imports. **Every gate asserts that something
MOVED or kills a named mutant — never merely that two things agree, and never a collected test that
asserts nothing.** Thresholds derive from the measurements recorded above and are never re-chosen
after seeing a result. **Any node's price is what the engine computes, not what the label says —
assert the derived faced fraction inside the test.** Only `_GOLDEN_STATS_N200`, `_PRE_M3_FIRES` and
the coverage baseline may be re-recorded, each under its own protocol with attribution proven by
revert; any other fixture that moves is a defect to investigate. Git: own worktree, immutable-OID
push, bare git, no pipes, absolute paths; PR on `feat/*`; never merge. **Suite results read from a
file, never a piped exit code.**

## Verify-by

1. Base green from a file, unpiped (`1416 passed, 1 skipped` at b63dfaa) → branch from
   `origin/main`, **not** from `7736156`.
2. `./scripts/verify.sh` → `BACKEND VERIFY OK` · `ruff check .` clean · full suite green unpiped.
3. **Exactly two pre-existing tests fail under the 0.45 pack** — `_GOLDEN_STATS_N200` and
   `_PRE_M3_FIRES` — and both are re-recorded under protocol. Independently confirmed twice
   in review (`2 failed, 1414 passed, 1 skipped`), with the ladder, bands, price-tail, node-trace,
   arrival-range and coverage baseline all green. **Anything else that moves is a finding to
   report, not a re-record to perform.**
4. `test_price_tail.py`, `test_node_trace.py`, `test_mw_catch_toppair.py`,
   `test_arrival_range_ftc.py` green **without edit**.
5. **Sensitivity by revert:** restore nit to 0.6 → every G-NODE self leg red (measured: exactly
   0.000000 on all five), G-SWEEP-a red. **There is no identity leg** — S-9 removed it; earlier
   wording here said "every identity leg red" and was stale. G-SWEEP-a's revert reading is
   **396 of 982**, not 384 of 970: under the revert the shipped and pre-slice packs coincide, so
   the three-pack validity mask enumerates 12 more cells. The gate reports its own denominator —
   read what it says rather than matching a number here.
6. **Mutant check by an agent that did not write the gates.** Required kills: a `call_looseness`
   no-op (lever read, result discarded) must die on the self leg AND G-SWEEP-a.
   **Disclosed non-kill, with a caveat this slice created (S-11):** a mutant scaling CALL but not
   RAISE survives *all* G-NODE legs and G-SWEEP. Ownership is delegated to the existing N-LOGIT G1
   invariance gate — **but G1 runs on the mispriced canonical construction** (faced fractions 600
   and 1200), a regime this very spec excludes from its own panel as degenerate. **The build must
   therefore demonstrate that G1 actually kills that mutant, and must do so on BOTH the shipped
   construction and a correctly-priced one**; asserting the ownership is not sufficient. If G1
   discriminates only at the broken prices, say so — that is a finding about G1, and it escalates
   `N-NLOGITPRICE` from filed to blocking.
   **Correction from the build (T6 measurement):** the claim that G-NODE "accepts ≈0.42–0.48" is
   right at the top and **wrong at the bottom — the new gates impose NO lower bound.** Both pass at
   0.20, 0.30, 0.35, 0.40, 0.42, 0.45 and 0.48, and only redden at 0.50. The floor on this lever
   comes from elsewhere in the suite (at 0.20 `test_fold_to_bet_respects_alpha_ceiling[nit]` fails,
   and the R9-DEFENCE-a ladder binds at ≈0.42). Neither gate this slice ships is a value pin, and
   neither should be cited as one.
7. Dual adversarial review of the diff (`refuter` + Codex Sol) + `persona-realism-theory-reviewer`
   at fan-in; every finding adjudicated into `ledger/r9-loosefit.md`.

## Known limits of this evidence (carried from the measurement, not hidden)

- The re-derivation **did not run the test suite**; the blast radius comes from the two independent
  review runs at nit 0.45 (verify-by 3).
- Every headline number is `aggressor_bet_prev_street=False`. With the line signal on, the panel
  measured *better* (self 0.0665–0.0707, identity 0.1379–0.1538); the sweep was not re-run that way.
- The sweep holds SPR at the grid's intent and lets absolute stacks move. Fixing stacks instead is
  a defensible alternative that would yield a different degeneracy count.
- The [0.01, 0.99] degeneracy rule is an arbitrary constant to which the 970 count is sensitive —
  which is why G-SWEEP enumerates its denominator instead of asserting it.
- The sweep's four fractions are the grid's intended labels, not the prices the packs' own `sizing`
  ladders actually produce; ⅔ and ½ collapse into one price bucket.
