# Finding ledger — parallel wave 3: N-LAGLADDER (+lag AQo row) · nit CO/BTN pair opens + maniac vs_4bet pairs (2026-07-31)

> Orchestration: two parallel isolated-worktree lanes, serial landings (single fixture-recorder law —
> orchestrator re-records at each landing; wave-wide re-record authorization given by owner 2026-07-31).
>
> **LANDING (owner decision, 2026-07-31): ONE COMBINED PR** — GitHub unreachable from the owner's
> location, so both lanes were merged locally into `feat/persona-realism-wave3` (lane B commits +
> lane A cherry-picked; two test-file conflicts union-resolved; one stale index-addressed validator
> probe dropped in favor of lane B's kind-addressed version) and the fixtures re-recorded ONCE on the
> combined tip `e25abde`: coverage **1314/322 = 24.5% cumulative vs the immutable 28.3% start
> (−3.8pp — LARGEST dip yet; attribution readings: lane B alone 27.8%, lane A alone 26.4%, so the
> extra loss is cross-lane rng displacement, adjudicated mapper-track class, T-cover owns the
> ratio)**; graded ratchet 331→322 disclosed. All six golden rows + all nine limper fires moved
> (compound displacement). Full suite **1322 passed / 2 skipped**, ruff clean. Push + PR pending
> network recovery.
> Lane grouping (orchestrator decision, one file = one owner): Lane A = everything touching `lag.json`
> (N-LAGLADDER ladder tighten via RR-EMIT first production run + opener-band re-check + flagged AQo
> vs_rfi row); Lane B = `nit.json` + `maniac.json` (T-M2 nit CO/BTN pair opens through the RR-EMIT
> proving spec + T-F3 maniac vs_4bet 99/88/77 continue mass). End-game (N-logit / R9-DEFENCE-a / W4-b)
> explicitly NOT started.

## Lane A — N-LAGLADDER + lag AQo flagged row

Build: lag `unopened` ladder re-authored via RR-EMIT curve spec (FIRST production authoring run —
smooth-curve model expressed it cleanly), substitution style: early-seat offsuit cut hard, suited
raised; per-seat RFI −3–7pp (UTG 25.10→22.11 … BTN 66.09→62.90). Production opener fold-to-3bet
stayed in [0.43,0.53] with ZERO vs_3bet edit (byte-identical, Codex-verified); component pin
re-derived 0.6034→0.5771. AQo vs_rfi carved {3bet .6, fold .4}→{3bet .6, call .4}, width-neutral.
Authored-width BANDS re-anchor confirmed on the DIRECTIONAL dict (test_personas.py, W5-b1/W5-b3/
R10-PRE2 precedent verified via git history by Codex); frozen population BANDS untouched.
Theory verified T-H1's complaint materially fixed: dominated-tier 3-bet-flat mass 20.9%→14.9%
(−29% rel.), arrival-weighted offsuit RFI 16.43→10.66 — the cut landed in high-arrival seats.

Reviews: refuter PASS-WITH-ISSUES (1 HIGH + 1 MED + 3 LOW) · theory GO-WITH-ISSUES (1 HIGH + 4 MED
+ 2 LOW) · Codex PASS-WITH-ISSUES (1 MED). Convergent HIGH (refuter+theory) and 3-way convergent
MED (emits path, also lane B's C-3).

| ID | Sev | Finding | Adjudication |
|---|---|---|---|
| L1+T-H1 | HIGH (convergent) | tighten OVERSHOT: population PFR 17.32→15.77 (n=4000), ~3.7σ BELOW the §5 LAG floor 17 (band 17-23); slice's report-only docstring disclosed VPIP only | **RESOLVED — WIDTH TIGHTEN ABANDONED, COMPOSITION SWAP SHIPPED.** The retune prescription was measured infeasible on two counts the builder proved: (a) unopened arrival is EP-dominated (UTG 0.846 vs BTN 0.033) so LP width restoration moves PFR ~0.13pp; (b) pre-slice PFR sits ON the §5 floor (17.32, 10-seed sweep), so NO width reduction has headroom. Shipped: constant-width composition swap (offsuit cut hard, suited raised, seat-avg RFI 43.15→43.04), PFR preserved 17.32 ±0.30 ≡ pre-slice, VPIP 23.88 ∈ [21,27]. The vacuous per-seat RFI-ceiling gate DELETED (gate-design rule — cannot fail); red-first burden now on offsuit ceilings + suited floors + AQo, all re-proven red at pre-slice content. **N-LAGLADDER's width premise REFUTED** — see roadmap update; any genuine lag width tighten is BLOCKED on a §5 PFR decision (T-M1's filing) |
| (new) A-F1 | MED | carried fix, post-review content change: the composition swap alone dropped the production opener blend to 0.4242 @n=12000 (under the 0.43 floor — suited-heavier opens get 3-bet-continued less… i.e. meet a table that folds them less), so the lag `vs_3bet` OPENER node's two middle call tiers were re-tuned 0.60→0.55 / 0.50→0.46 (4-bet legs untouched, share stays 4.00%); component pin 0.6034→0.6166. Sanctioned lever (opener-role node, per the wave brief) but unreviewed at fan-in | **DELTA RE-REVIEWED → PASS-WITH-ISSUES (3 LOW).** Refuter reproduced everything independently: re-tune scope exactly two call weights (cold node + 4-bet legs byte-identical), blend 0.4622 @n=4000 / 0.4452 @n=12000 reproduced to 4 dp, motivation replicated on two fresh seeds (pre-fold 0.4223/0.4299 under floor; shipped 0.4778/0.4551), PFR Δ −0.04 ≪ 1 sd on a 10-seed sweep, all red-first gates re-verified, zero orphaned refs to the deleted ceiling gate, frozen bands byte-identical |
| dr-L1 | LOW | re-tune leaves a 1pp cross-tier defense inversion in the opener node (stronger suited-broadway tier folds 0.45 vs weaker speculative tier 0.44; was tied 0.40/0.40 at main); RR-LINT's fold-exclusion can't see it | **ACCEPTED-RECORDED** — behaviorally negligible; joins `N-M4BET`-class future vs_3bet passes (shape artifact of band-targeted tuning, the known failure mode) |
| dr-L2 | LOW | ceiling-block comment claims SB "covered by the ≥TAG gate" — SB is in neither mechanism (ungated) | **FIXED** at landing (a8cd962) — comment corrected to state SB ungated-by-scope |
| dr-L3 | LOW | blend gate left underpowered: Wilson half-width at n=4000 (±0.045) exceeds the shipped margin above the 0.43 floor — the gate that was meant to catch this regression cannot (0.4366-green while truly 0.4242) | **ACCEPTED-FILED** — merged into the L4/estimator-instrument ticket: raise the gate's n (or assert at n=12000) when that ticket runs; docstring warning ships now |
| (new) A-F2 | LOW | §5 gap row [3,6] was never met, incl. pre-slice (6.19 ±0.36); AQo fold→call adds +0.36 arithmetically (0.905% of hands × 0.40) → 6.55. NOT compensated elsewhere (correct — compensating would be the lever trap) | **RECORDED** — joins T-M1's §5 joint-consistency filing (gap row's format-invariance is part of the same contract defect) |
| T-M1 | MED→filed | CONTRACT-DEFECT (§11 item 15 family): §5's LAG VPIP/PFR/gap trio is NOT jointly satisfiable across full band edges post-ledger-#14 (gap row deliberately left format-invariant while VPIP/PFR scaled ~0.75×); no §5 text rules which rows dominate — a mislead-later-slice channel | **FILED FORWARD** — contract edit belongs to the contract owner (W5-a2 lineage), not a content slice; recommendation on file: VPIP+gap primary, PFR derived/DIRECTIONAL, or restate LAG PFR 16-23 |
| T-M2 | MED | offsuit inversion: lag per-seat OFFSUIT width ≤ tag's at 6 of 9 seats (CO 25.70 vs 29.41; arrival-weighted 10.66 vs 10.82) — the loose persona reads offsuit-tighter than the TAG; ordering gate was total-width-only | **FIXED** in the retune (offsuit premium restored at LJ-BTN + new per-seat offsuit≥tag gate there); tag's own suited/offsuit composition filed → `N-TAGCOMP` (tag BTN plays 70% suited / 62% offsuit — the genuinely wrong shape; outside this ticket per §11 item 13) |
| C-1+T-M4 | MED (3-way convergent w/ lane B C-3) | lag proving gate derives pack path from the spec's own `emits`, unpinned | **FIXED** — asserts resolution to `content/personas/lag.json` |
| T-M3 | MED | metric #3 instrument bias unruled-out: lineup = 3×persona+fillers, roster-wide §5 readings miss one-sidedly LOW (nit 0.067 vs 10-14, maniac 0.390 vs 45-58, fish 0.354 vs 40-55) — VPIP readings not pool-comparable | **FIXED (disclosure)** in-docstring; instrument investigation belongs to W4-b/metric-#3, filed on the W4-b watch list |
| T-M5 | MED | bare "21-27" cited ×4 with no §5a provenance triple (item-15 FAIL) | **FIXED** — triple stated once in spec `_doc`, tests point at it |
| L2 | MED | coverage re-record is NOT a pure refresh: graded ratchet moves DOWN 331→328 (total 1252→1242; ratio ~flat −0.03pp); first-assert short-circuit masked it | **DISCLOSED** — recorded here for the owner; cumulative delta vs immutable snapshot reported at landing (T-R6/L-precedent), any loss adjudicated there |
| L3 | LOW | stale blend provenance: docstring's pre value 0.4735 is the N-3BSTRATA-era figure; true origin/main value 0.4667 (n=480) — intervening drift | **FIXED** — corrected + post-retune value re-measured |
| L4 | LOW | production-blend gate asserts a point estimate whose Wilson lower bound (0.417) sits below the 0.43 floor; margin inside sampling error (deterministic seed, won't flake today, won't survive a reseed) — PRE-EXISTING instrument, unweakened by this slice (verified) | **ACCEPTED-RECORDED** — instrument hardening rides with the deferred estimator/instrument tickets; do not fix ad hoc mid-wave |
| L5 | LOW | `_doc` key now in a RUNTIME-loaded pack for the first time; pydantic ignores extras, nothing validates persona.schema.json (no jsonschema consumer in backend) — schema under-describes shipped pack | **ACCEPTED-RECORDED** — harmless at runtime; schema catch-up note filed with RR-NORM scope |
| T-L1 | LOW | AQo zero-fold applies uniformly incl. vs UTG opens and from SB (node is opener/position-blind by construction — F18 deferred plumbing) | **FILED** — AQo-vs-EP added to F18's motivating-examples list (see roadmap E1-b/F18 entry) |

## Lane B — nit CO/BTN pair opens (T-M2) + maniac vs_4bet pairs (T-F3)

Build: nit opens 55-77 @CO, 22-77 @BTN at raise 0.3 (converted from FOLD mass; limp 0.4 byte-preserved
at all nine seats — verified independently by refuter AND Codex); authored through the RR-EMIT nit spec
(tail tier demoted to two per-seat slope tiers — a real expressiveness limit, documented in-spec; seven
untouched seats emit byte-identically). Maniac vs_4bet 99/88/77 dead → continue mass. Nit 1.2.0→1.3.0,
maniac 1.2.0→1.3.0, spec 1.0.0→1.1.0. Red-first proven for all three defect gates.

Reviews: refuter PASS-WITH-ISSUES (2 MED + 4 LOW) · theory GO-WITH-ISSUES (2 HIGH filed + 3 MED + 1 LOW)
· Codex PASS-WITH-ISSUES (3 MED). Convergent MED: gate tightness.

| ID | Sev | Finding | Adjudication |
|---|---|---|---|
| C-1+R-I1 | MED (convergent) | T-M2 gates too loose: defect gate accepts any raise>0; verbatim-limp preservation gate DELETION-BLIND (`if limp and limp != 0.4` skips a zeroed class) | **FIXED** — exact-mix pin {.3,.4,.3} on the CO/BTN pair bands; limp == 0.4 asserted unconditionally on every pair class, all nine seats |
| C-2 | MED | T-F3 gate pins only positive/monotone continue sum, not the mix components | **FIXED** — exact weights pinned (post R-3 refit) |
| C-3 | MED (convergent w/ lane A's Codex MED) | proving gate trusts spec's `emits` path; a repointed spec + crafted fixture keeps all proving tests green while the runtime pack drifts | **FIXED** — gate asserts `emits` resolves to `content/personas/nit.json` |
| R-I2 | MED | omitting a seat's `slopes.pairs` silently TRUNCATES the pairs row (edge tier claims one class, rest drop); lint belt blind to truncated tails (not a "row gap") | **FIXED** — `rr_emit._validate` now fails loud on a missing slope-width entry + negative-control test |
| T-R1 | HIGH | CONTRACT-DEFECT (ARRIVAL-class): nit reaches CO unopened 12.2% / BTN 6.1% of hands, so T-M2's measurable effect is **+0.011pp PFR** — it does NOT close the nit's 2.3pp PFR gap (5.7 vs §5's 8-12). Nit is simultaneously WIDER than dossier per-seat (6 of 7 opening seats past band) and TIGHTER in aggregate: the residual deficit is arrival, not width | **ACCEPT-AND-FILE** — T-M2 closes as composition-fix only, NOT "nit preflop tightness addressed"; arrival gap filed to W-ARR with the T-ARR numbers; standing note: stop widening nit authored RFI until arrival is instrumented |
| T-R2 | HIGH | CONTRACT-DEFECT: maniac vs_4bet node, weighted by its own arriving 3-bet mass, responds fold 0.814 / shove 0.140 / call 0.046 vs dossier 25/35/40 — because ~73.6% of arriving combos (AQo, KQo, ATo, AJs, 44-22, …) have NO mix and fold 1.0. The 99/88/77 hole was a symptom RR-LINT could see (pair rows are contiguity-checkable); the offsuit-broadway coverage gap is the disease | **ACCEPT-AND-FILE** — T-F3 closes as symptom-fix; new roadmap ticket `N-M4BET` (fit the node's arrival-weighted aggregate to the dossier triple) |
| T-R3 | MED | jam-mass inversion: 55/66 shove 0.40 > 77-99's 0.25 (no blocker story); call leg contradicts the slice's own no-set-mining docstring; monotone gate checked continue only, hiding the jam leg | **FIXED** — 77/88/99 → {5bet_shove 0.40, fold 0.60} (level continue, push/fold identity; theory endorses the flat 0.40); gate extended to non-decreasing shove mass |
| T-R4 | MED | at CO the nit limps 55 more than it opens it (.4 vs .3) — a live-$1/$2 shape, not online-nit; the verbatim-limp LAW pins it (aggregate open-limp still in band at 1.07%) | **ACCEPT-AND-FILE** — filed against the W5-b1 verbatim-limp law: scope it to early seats where pair-limping is genuine nit identity; owner decision when next touched |
| T-R5 | MED | BTN authored RFI 21.42→22.23 crosses the nit dossier's DIRECTIONAL 16-21 band (was already at ceiling) | **ACCEPTED-RECORDED** — dossier band is self-declared candidate spec, not observed population (§11 item 6); crossing recorded here so the next slice inherits a decision, not drift; T-R1's arrival numbers make narrowing BTN nearly free if wanted later |
| T-R6 | MED | cumulative graded-coverage delta vs the immutable start snapshot not yet reported | **OWED AT LANDING** — orchestrator reports + adjudicates in this ledger at re-record |
| R-I3 | LOW | "interleaving unrepresentable" emitter claim false (validator-legal spec can produce one) — PRE-EXISTING on main's spec | **ACCEPTED-FILED** — RR-EMIT scope note; shipped content stays lint-clean |
| R-I4/R-I5/T-R7 | LOW | stale in-file readings; one index-addressed validator probe left (the trap this commit's own fix condemns); SB exclusion unlabeled as ticket-scope | **FIXED** (mechanical) |
| R-I6 | LOW | no roadmap/ledger update in the slice commit | **CLOSED HERE** — ledger/roadmap are orchestrator-owned at fan-in by wave convention |
