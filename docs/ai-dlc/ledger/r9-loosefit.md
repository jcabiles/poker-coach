# Finding ledger — R9-LOOSEFIT spec review (rev 1 → rev 2)

Review of `specs/r9-loosefit.md` rev 1 + `contracts/r9-loosefit.md` +
`reports/r9-loosefit-feasibility.md`, 2026-08-03. Reviewers: Claude `refuter` (sonnet/high) →
**FAIL** (2 HIGH / 2 MED); Codex `gpt-5.6-sol` (high) → **NEEDS-WORK** (4 HIGH / 6 MED / 1 LOW —
and it ran read-only probes, incl. a seed measurement at the CI posture). Overlap on two items;
no reviewer-vs-reviewer conflicts. Adjudicator: director (Fable). Every ACCEPT folded into
spec rev 2.

| # | src | sev | finding | adjudication |
|---|-----|-----|---|---|
| C-1 | codex | HIGH | CI band gate runs `context_aware=False`, n=600 (+escalation) — the feasibility study measured True/24–48k. Probe: seed nit AF ≈ 2.4167 > 2.4 ceiling at the CI posture. T1 as written can approve a seed that deterministically reddens G-BAND. | **ACCEPT — the central finding.** Verified structurally (call site `:5644` passes no `context_aware`; `per_persona_n = 600` at `:2384`). Rev 2: "posture lesson" section; T1 step 1 runs the ACTUAL pytest gates; seed demoted to starting point; feasibility report gains an additive posture caveat (files-to-touch 7). |
| C-2 | codex | HIGH | G-SEP "at the band harness n" is unmeasurable there — at n=600 nit's cbet denominator (~20) is under the ≥30 floor → FtC None; the −0.012 base gap is a 48k/True number. | **ACCEPT.** Rev 2 G-SEP names its own posture/n (4,000 / False), asserts denominators ≥ 30, threshold T_sep via a pre-registered symmetric ≥3σ rule derived in T1. |
| C-3 | codex | HIGH | G-RS's nit direction was wrong: N-LOGIT's own 1e-12 gate proves the CONDITIONAL raise share RAISE/(RAISE+CALL) is invariant in cl (both merits scale ∝ cl); only ABSOLUTE raise probability falls. | **ACCEPT.** Verified against N-LOGIT theory. Rev 2 rebuilds G-RS: invariance leg (±3σ — kills the call-only misroute, which breaks proportionality) + absolute leg (nit's absolute raise probability falls >3σ). Verify-by 4 records the deliberate asymmetry: revert leaves G-RS-i green, G-RS-ii red. |
| C-4 / R-1 | both | HIGH | "Append to the 6-tuple, callers intact" is false: five call sites unpack exactly six positionally (`:5644,:5662,:5681,:5742,:5774`) — appending breaks the very band/ordering tests the gates depend on. | **ACCEPT.** Rev 2: `_persona_stats` untouched; sibling accessor `_persona_stats_shares` sharing loop + cache internals; zero call-site edits. |
| R-2 / C-6 | both | HIGH/MED | Seed violates its own robustness targets: tag−lag margin 0.0296 = 2.11σ < the 2.5σ (0.035) target; lag @0.62 WTSD ≈ 0.568 → ~0.022 nominal margin, ~0.011 after measured cross-persona displacement — inside noise. No gate checked margins, only band membership. | **ACCEPT.** Rev 2 T1 acceptance criteria pre-registered: ordering margins ≥ 0.035 on all nit/tag/lag legs; WTSD margin ≥ 0.02 at the loose edge at gate posture; fine-tune until ALL hold (lag likely moves below 0.62). |
| R-3 / C-5 | both | MED | G-RS tag/lag "measured band" had no width rule — [0,1] qualifies; revert proof reds only on nit; vacuous thresholds possible. | **ACCEPT.** Rev 2: width IS the ±3σ formula (σ measured at gate n in T1), no wider; denominators ≥ 30; misroute mutant named per persona (verify-by 5). |
| R-4 / C-7 | both | MED | G-NODE uncheckable as written: the only exact node pins sit on the unopened branch cl cannot reach; trace records normalized probabilities not merits; "~0" had no ε; no facing bluff-catcher node exists in the pack. | **ACCEPT.** Rev 2: add ONE crafted facing bluff-catcher probe (files-to-touch 5) with explicit thresholds — nit FOLD +>0.05 vs base, all legal actions ≥ 0.01, node reached by construction. Red at base. |
| C-8 | codex | MED | Rule-1 conditioning check cited but never scheduled — roadmap assigns R9-LOOSEFIT its own ρ/conditioning measurement; T1 requested none. | **ACCEPT.** Rev 2 T1 step 3: document 1a pairing (single lever per persona, no 2×2 ρ applies), MEASURE cross-persona coupling at gate posture, escalation criterion (any cross-delta > 3σ ⇒ joint re-fit round). |
| C-9 | codex | MED | R9-DEFENCE-b inherits absolute raise frequencies measured at rscale=1; this slice moves the same cells; no handoff filed. | **ACCEPT.** Rev 2 files-to-touch 6: roadmap rebaseline note for R9-DEFENCE-b. T-cover confirmed anchor-free (waits on distribution settling only). |
| C-10 | codex | MED | N-LOGIT G3's "bit-exact at authored values" claim silently becomes false of shipped packs — `_nlogit_probe(mult=1)` overwrites the live value with the anchor, so the test stays green while its description goes stale. | **ACCEPT.** Verified (`:6911` authors `anchor × mult` on the copy). Rev 2 files-to-touch 4d: docstring/name amended to "calibration anchor"; assertions unchanged. |
| C-11 | codex | LOW | "7–8× windows" wrong (nit 58×, tag 7.1×, lag ≥8.4×); pack `version` bump missing from files-to-touch; `_doc` legality confirmed (schema-ignored extra key). | **ACCEPT-NARROWED.** The "7–8×" phrase was quoted faithfully from the feasibility report's own §VERDICT line — the REPORT's phrasing is imprecise (nit's window is far wider); spec rev 2 drops the phrase, adds version bumps. Report text left as-is (the per-persona window tables in it are correct and are what the spec now cites). |
| C-blast | codex | — | Green blast checks run by the reviewer at the seed: 5-persona WTSD ordering green; arrival continuation nonempty (nit 100/35/13 flop/turn/river); texture guards green; golden confirmed the only exact population fixture re-pinning. | Recorded as corroboration; T1 re-establishes all of it at final values. |

## Build-phase findings (T1, 2026-08-03) — the fit is BLOCKED, slice returns to spec

T1 ran under `/ai-org:build` and did exactly what spec rev 2 told it to: it measured against the
REAL pytest gates instead of proxies. That is what surfaced the rows below. Instrument delivered
and verified byte-neutral (full suite 1416 passed / 1 skipped, identical to base; `content/`
restored byte-for-byte after 8 temporary edit cycles); committed alone as `7736156` on
`feat/persona-realism-r9-loosefit` (push blocked by the sandbox's SSH path — commit lives in the
shared object DB). Full evidence: `reports/r9-loosefit-t1-measurement.md`.
Owner ruling 2026-08-03: **re-spec to rev 3 folding all six findings.** No pack edit, no gate, no
PR from this build.

| # | sev | finding | status |
|---|-----|---|---|
| B-1 | HIGH | **R9-DEFENCE-a's ladder gate floors nit's `call_looseness` at ≈0.42** (≥0.45 for margin). `test_r9d_s5_fold_rate_rise_follows_the_defensible_ladder` asserts nit has the LARGEST probability-space fold-rate rise under a barrel; tightening nit cuts its base continue rate, so the same multiplicative damp yields a smaller rise. Its own docstring names the coupling ("probability-space ordering differs from the λ ordering because base continue rates differ"). | **CONFIRMED by the director independently** — real pytest at nit `cl=0.40`: `ordering broke between ('nit',) (min 0.0625) and ('tag',) (max 0.0856)`; pack restored, md5 verified. Two slices five days apart want opposite things from one number. This is a THEORY conflict, not a fitting problem → rev 3 must adjudicate it (candidate CONTRACT-DEFECT for the theory reviewer). |
| B-2 | HIGH | **tag's `call_looseness` is pinned to its `stickiness` (0.6) by two gates never mapped in `contracts/r9-loosefit.md` §1.** `test_elasticity_split_faithful_decomposition_byte_identical` (`:1321`) builds its "unset persona" baseline from the SHIPPED tag pack and sets `call_looseness = stickiness` on the copy — it passes today only because those two happen to be equal. Plus four `abs=5e-4` pins on tag's normalized P(RAISE) (`test_one_pair_raise_damped_facing_raise_pre_river[…-tag]`). | **CONFIRMED structurally by the director** (tag authors `stickiness: 0.6`, `call_looseness: 0.6`). The elasticity test's premise is STALE — tag is no longer an unset persona. Rev 3 decides: re-scope it onto a synthetic pack (correct fix) or accept tag as immovable. |
| B-3 | HIGH | **With tag immovable, spec criteria 2b and 2c are mutually exclusive.** 2b (`lag < tag` ordering margin ≥ 0.035) needs lag ≳ 0.58; 2c (lag WTSD ≥ 0.02 from the loose edge) needs lag ≲ 0.50. Empty. Both criteria ALSO fail at HEAD (margins 0.0224 and 0.0112), so this is a pre-existing conflict the criteria exposed, not one a candidate value introduced. | ACCEPT. Only a tag move opens the window. Feeds B-2's ruling. |
| B-4 | HIGH | **The pre-registered T_sep rule is unreachable at CI-affordable n.** Best gap found is +0.07731 FtC points = **4.63 σ_gap** at n=32,000; the symmetric rule (≥3σ above 0 AND ≥3σ below the measured gap) needs ≥6σ ⇒ n ≥ 53,800 (~+4–7 min CI against a 274 s suite). The spec's named n=4,000 reading (0.178) is a 1.7σ over-read — anyone certifying there would have pre-registered a threshold against a fluctuation. | ACCEPT. Rev 3 must either pay the n, change the statistic, or replace the symmetric rule — with the choice made BEFORE re-measuring. |
| B-5 | HIGH | **G-RS-ii (nit's absolute facing-node raise probability falls > 3σ) is unreachable.** Measured fall 0.00571 vs paired 3σ 0.02031 = **0.84 σ**; 3σ needs n ≈ 405,000. Cause is a genuine mechanism surprise: a tighter nit ARRIVES at a stronger facing population that raises more, restoring most of the mass `rscale` removed. The conditional-share invariance (G-RS-i) holds exactly, as N-LOGIT's theory predicts. | ACCEPT. Rev 3 either drops the leg or moves it to a fixed-node probe where the arrival-composition effect does not exist. |
| B-6 | MED | **Files-to-touch is incomplete**: two further sanctioned re-record fixtures move under this fit — `test_limper_coverage_fires_on_organic_play` (any of the three personas) and `test_coverage_never_regresses` (lag-only). Neither is named in spec rev 2. | ACCEPT. Add to rev 3's re-record list. |
| B-7 | MED | **The slice's motivating claim does not survive stable-n measurement.** At the gate posture the base FtC gap nit−tag reads −0.06300 (n=4k) → −0.01196 (16k) → **+0.00287 (32k, 3σ 0.04753)**. The ledger's "−0.063 base gap" (recorded under C-2) is an n=4,000 fluctuation. Both postures agree the two are a statistical **tie**, not an inversion. | ACCEPT. The case for SEPARATING them stands (a tie between the tightest and a mid-range archetype is itself the defect); the spec's framing "nit measurably folds LESS than tag" must be restated in rev 3. |
| B-8 | MED | **The feasibility report's flat-FtC-slope claim is posture-bound.** "∂FtC/∂ln cl is essentially constant, −0.15..−0.19 at every point measured" is a `context_aware=True` statement; the gate-posture secant is **−0.345, 2.3× steeper**. Anchor-seeded FtC steps are NOT safe at the posture CI judges at. | ACCEPT. The posture lesson (C-1) is broader than rev 2 recorded — it governs SLOPES, not just values. Fold into rev 3 and into the report's caveat. |
| B-9 | LOW | **Over half the lever's facing nodes are inert.** SPR-committed share of fold-legal decisions: nit 27.9 %, tag 57.0 %, **lag 65.0 %** (conservative SPR-only predicate). Contract §4 anticipated the direction; nobody had the magnitude. | Recorded. Explains why AF-side effects are weaker than any prior document assumed. |
| B-10 | LOW | **`_persona_stats`'s returned tuple is identity-asserted**, not just value-asserted (`test_stats_caches_are_pack_content_keyed` `:3123/:3151/:3182` use `is base`). A `record[:6]` slicing design would build a fresh tuple per cache hit and fail. | Handled in the instrument (record holds the pre-built 6-tuple as element 0; both accessors return a stored element). Recorded so rev 3 does not re-derive it. |

## Rev-4 THEORY REVIEW — NEEDS-WORK, 2 HIGH / 2 MED / 2 LOW (2026-08-04)

`persona-realism-theory-reviewer` on the finished diff. **The most consequential review of this
slice**: both shipped gates read only non-draw facing nodes, so neither could have seen the
regression below, and neither is a fit to the stat the slice's own claim is grounded in.

| # | sev | finding | adjudication |
|---|-----|---|---|
| TH-1 | **HIGH** | **Strong-draw regression — the lever is flat over the WHOLE continue mass, so tightening the nit also tightens it against hands nobody folds.** At `node_trace.py`'s `flop_facing_bet_strong_draw` (JhTh on 9h8c2h, ⅔-pot), nit P(fold) **0.3535 → 0.4217**, and the shipped nit is now the **highest folder of a strong draw of all six personas** — above passive_fish 0.4173, vs lag 0.2277 / tag 0.2504 / maniac 0.1682 / station 0.0915. The spot's own committed prescription reads *"strong combo draw vs a bet: semi-bluff raise / call, **few folds**."* Price needs ~28.6 % equity; a 9-out flush + open-ender is ~50 %+ by the river. **This is a large −EV fold, and no gate in the slice looks at a draw node** — G-NODE's five nodes are all `DrawCategory.NONE` and G-SWEEP's degeneracy window does not separate draws from air. | **ACCEPT.** Pre-existing in kind (0.3535 was already wrong) but this slice moves it ~7 points further from reality. **Disclosed here and in the roadmap note per the initiative's own "record what you measured" law; filed as `N-DRAWLOOSE`.** Substantive fix is engine work out of this slice's scope: exempt or floor the draw-bearing continue merit from `call_looseness`, leaving `_DRAW_CALL_BONUS` on a price/equity gate. **This slice must not close claiming "the nit folds more" without saying WHICH hands it now folds.** |
| TH-2 | **HIGH** | **`N-LADDER-PREMISE` ruling: the premise is UNSOUND as a population gate.** Decisive: the reviewer moved `call_looseness` across six values with `line_sensitivity` **held constant at 0.60 in every run** — and the gate flipped PASS → FAIL (cl 0.60 rise +0.1463 · 0.45 +0.1613 · 0.42 +0.1319 · **0.35 +0.0312 FAIL** · 0.25 +0.0333 FAIL; tag pinned at +0.0856 throughout). **A gate whose verdict changes when the parameter it claims to order never moves is not measuring that parameter.** Mechanism: ΔP(fold) is a compressed, non-monotone image of λ — inverted-U in the base fold rate, ceiling 0.1489 (nit) vs 0.1244 (tag), so the entire nit-over-tag window is **2.45 fold-points wide at both personas' best case** — compounded by the nit reaching only **30–41 in-scope barrel nodes per 8,000 hands** (1–5 binary flips, 3σ ≈ ±0.26). Poker objection too: a barrel harvests fold equity from players who called *wide*, so a genuinely tight nit has the least to give. **Measured cost: the ≈0.42 floor this gate imposes is EXACTLY passive_fish's authored `call_looseness` (0.42), so the gate structurally forbids the nit from ever being authored tighter at facing nodes than the passive fish** — the opposite of the archetype it is named after. | **ACCEPT the analysis; the disposition is an OWNER RULING** (put to the owner 2026-08-04). Reviewer's recommendation: re-express the population ladder in **log-odds** (`Δ ln(p/(1−p)) ≈ λ` — base-rate-invariant, no ceiling, the exact prediction rather than a compressed image), which `test_r9d_s4_ordering_is_strict_between_tiers_and_equal_within_the_tie` already does correctly at a fixed node; **or** demote S-5(c) to report-only per the N-TAGWIDTH precedent, keeping only the strictly-positive-rise leg. Either way unblocks the lever below 0.42. |
| TH-3 | MED | **The slice never measured the stat its own claim is grounded in.** 0.45 was chosen as ladder-floor + margin, not fit to any closed-loop statistic; no §5 target is cited anywhere in the spec, ledger or test comments. The reviewer measured it: **nit Fold-to-C-bet 0.259 (@0.60) → 0.359 (@0.45)**, tag 0.303 — so the move is right *and repairs a live cross-persona inversion* (at 0.60 the nit folded LESS than tag). That is the slice's best evidence and it was absent from the slice. Separately the §5 target (nit 60–75) is **unreachable on this lever**: secant ≈ −0.348 per ln-unit ⇒ needs `call_looseness ≈ 0.225`, below both the ladder floor and the α ceiling. | **ACCEPT.** Numbers recorded below. Per §5a's W3R-1 rule, infeasibility is evidence about the TARGET — routed to the pending `W5-a2-f` demotion of that conf-LOW single-source row rather than left implicit. |
| TH-4 | MED | **passive_fish still outfolds the nit** — 540 of 692 cells, aggregate FtC **fish 0.489 vs nit 0.359**. Against §5 (nit 60–75, fish 35–50) the roster's tightest defender is the recreational calling type, and the only persona inside its own band is the fish. Direct authored cause: fish `call_looseness` 0.42 < nit 0.45. No NEW inversion is created — nit now correctly outfolds tag, lag, station (692/692 each) and maniac (676/692). | **ACCEPT.** Pre-existing and improved by this slice, but it is the headline cross-persona result and was unrecorded. Roster ordering recorded below; the roadmap note now says explicitly that the nit is **not** the roster's tightest defender. This is the concrete cost of TH-2. |
| TH-5 | LOW | **Raise shape is directionally wrong.** `rscale = 0.45/0.6 = 0.75` scales RAISE by the same factor as CALL, so the raise:call ratio is held **exactly** constant (0.0962 at every panel node) while absolute raise frequency falls 0.0544 → 0.0483. A real player tightening a defence removes the weakest *calls* and keeps every value raise, so the raise share of continues should RISE. Magnitude ~0.6 pp — immaterial in play. | **ACCEPT as filed.** No change here; the frozen `continue_ref` is a deliberate N-LOGIT feature. Filed alongside N-LOGIT's design: does an archetype-tightness lever belong on the raise leg at all? Irony worth recording: re-syncing `continue_ref` to 0.45 — which the pack's `_doc` correctly forbids — would have produced the MORE realistic raise shape. |
| TH-6 | LOW | The limper re-record comment reports only that every coverage shape "still fires"; **BB² fell 34 → 24 (−29 %)**, and neither the ledger nor the comment states the §7 cumulative graded-coverage delta. | **ACCEPT.** Verified: `test_coverage_baseline.py` is green on this branch **without a re-record**, so the cumulative delta is nil. Recorded below. |

### Measured numbers the slice owed and did not have (all at the harness's stable n = 4000)

- **nit Fold-to-C-bet: 0.259 → 0.359.** Comparator tag 0.303. The move repairs a real inversion.
- **Roster FtC ordering after the slice:** fish 0.489 > **nit 0.359** > maniac 0.345 > tag 0.303 >
  lag 0.301 > station 0.161. Against §5, only the fish sits inside its own band.
- **Strong-draw fold at the trace node:** nit 0.3535 → **0.4217**, now the roster's highest.
- **Cumulative graded coverage vs the immutable snapshot: unchanged** (baseline green, no re-record).

### Checklist items the reviewer passed, and one it praised

Engine untouched · no EV threshold cited (it re-derived the 0.071797 ceiling independently and
confirmed it) · no refuted claim re-introduced · BANDS untouched and nit's new WTSD 0.6491 sits
inside the frozen (0.37, 0.80) · estimator parity intact · domain purity and scope clean.
**Called out as a strength worth keeping as the house pattern:** the price-assertion instrument —
intercepting the engine's own `_price_factor` and refusing a reading unless the engine-computed
faced fraction matches the declared one — enforces the contract's denominator rule at the test
boundary, is the correct remedy for the rev-3 mispricing, and is what exposed `N-NLOGITPRICE`.

## Rev-4 FAN-IN REVIEW — 1 MED, folded (2026-08-04)

Reviewed the finished diff (`e6708bf`, 3 files, 546+/13−). Claude `refuter` → **FAIL (1 MED)**,
folded as `b7faa01`. Theory reviewer running separately.

| # | src | sev | finding | adjudication |
|---|-----|-----|---|---|
| F-1 | refuter | MED | **The gate's own comment still carried the disproven acceptance window.** Beside `_R9LF_PRE_SLICE_LOOSENESS` it read "G-NODE … accepts any shipped lever value in roughly 0.42–0.48". BR-1 disproved that during the build and the **spec** was corrected; the **code comment sitting next to the threshold constant was not.** Reviewer reproduced independently: the panel's own self-leg logic passes at 0.20, 0.30, 0.35 and 0.42. | **ACCEPT — folded (`b7faa01`).** Comment now states the gates impose no lower bound, names where the floor actually comes from, and records that the earlier claim was disproven. **This is the same stale-statement defect class the slice fixed five instances of, except self-inflicted — the reviewer went looking for it *because* the slice had just demonstrated the pattern.** Lesson: when a build corrects a claim, grep the code for that claim too, not just the docs. |

### Independently re-derived by the reviewer (not taken from the ledger)

This is what makes the fan-in worth its cost — every load-bearing number was recomputed from the
code, not read back from the documents that asserted it:

- **Both fixture re-records, from scratch**, by loading `content/personas/` with `nit.json` swapped
  for the exact `b63dfaa` blob and calling the harness's own functions: golden reproduced shipped
  `0.6491228070175439` / reverted `0.7450980392156863` with the other five rows byte-identical in
  both states; limper belt reproduced all nine shipped counts and all nine reverted ones **digit for
  digit, including which two pairs did not move.**
- **G-SWEEP** at both packs: `denom=970, folds_more=970, by-margin=826, folds_less=0` shipped;
  `denom=982, folds_more=396, margin=312` reverted — matching BR-3's corrected reading.
- **The disclosed non-kill mutant, reconstructed from data alone** (forcing `rscale ≡ 1.0` via
  `continue_ref = call_looseness` on a probe copy): survives G-NODE (worst +0.0532 at P4) and
  G-SWEEP, killed by G1 with **drift 0.332927–0.333332 at BOTH the broken 600×/1200× grid and a
  correctly re-priced one, with the identical worst-case cell in both regimes** — independently
  confirming S-11's structural claim that G1's power is price-invariant by construction.
- The price self-check fires (raises on the rev-3 mispricing, returns a real distribution once
  relabelled); `continue_ref`/`stickiness` byte-untouched; all five corrected comments read true and
  changed no assertion logic; R9-DEFENCE-a's ladder passes at the shipped 0.45.

### Attacks that found nothing

Off-by-one or loose-inequality bugs in the sweep's thresholds (operators match the pre-registered
spec exactly) · a way for G-NODE to pass while asserting nothing (floor derivation checks out
against the 0.071797 ceiling; panel provably red at a true self-delta of 0) · a second silent no-op
path via global-state leakage in the price-factor wrapper (restored in a `finally`, and the
refusal test confirms module identity is restored).

## Rev-4 BUILD — T1…T6 complete, suite fully green (2026-08-04)

Worktree `/private/tmp/claude-501/wt-r9lf4`, branch `feat/persona-realism-r9-loosefit-rev4`, based
on `origin/main` = b63dfaa (NOT on the halted build's `7736156`). Clean state after T6:
**1419 passed, 1 skipped, 0 failed** · `ruff` clean · `BACKEND VERIFY OK` ·
`test_price_tail.py` / `test_node_trace.py` / `test_mw_catch_toppair.py` /
`test_arrival_range_ftc.py` all green **without edit**.

**T6 was run by an agent that wrote none of the gates** and owned no files; every mutation was
restored byte-for-byte with SHA-256 verification.

### The blocking question, answered: NO ESCALATION

S-11 required the build to prove that N-LOGIT's G1 gate actually kills the disclosed CALL-only
mutant **at sane prices**, not only at the canonical grid's broken 600×/1200× ones. Measured at
both regimes, re-executing G1's body verbatim over each: clean-engine drift 0.000000000, mutant-2
drift **0.332927–0.333332 at every faced fraction, sane and broken alike** (6,400 comparisons per
persona per regime, 0 collapsed cells). **Structural reason, not luck:** price enters only the FOLD
merit via `_price_factor`, while G1's statistic `R/(C·L + R)` conditions FOLD away entirely — so
mutant 2's drift is price-invariant by construction. **`N-NLOGITPRICE` stays FILED, not blocking.**

### Mutant kill table

| mutant | G-NODE self | G-SWEEP-a | G1 | verdict |
|---|---|---|---|---|
| **no-op** (lever read, discarded — crash-free variant) | **KILLED** (0.000000 ×5) | **KILLED** (396/982 vs floor 800) | **passes** | dies on the new gates ONLY |
| **CALL scaled, RAISE unscaled** (`rscale = 1.0`) | survives (worst +0.0532) | survives | **KILLED** (drift 0.3329) | disclosed non-kill, delegation confirmed |

**The no-op row is the strongest evidence in the slice:** G1 — the pre-existing gate — is *blind*
to a lever no-op. The two gates R9-LOOSEFIT ships are the only thing in 1,419 tests that catches
it. They are not decorative.

### Build findings (all ACCEPTED; spec corrected in place)

| # | sev | finding | adjudication |
|---|-----|---|---|
| BR-1 | MED | **The spec's acceptance window is wrong on the low side.** It claimed G-NODE "accepts ≈0.42–0.48"; measured, both gates pass at 0.20/0.30/0.35/0.40/0.42/0.45/0.48 and redden only at 0.50. **The new gates impose NO lower bound.** The real floor is elsewhere: `test_fold_to_bet_respects_alpha_ceiling[nit]` fails at 0.20, and the R9-DEFENCE-a ladder binds at ≈0.42. | **ACCEPT.** Spec verify-by 6 corrected. Neither shipped gate is a value pin and neither may be cited as one. |
| BR-2 | MED | **G-SWEEP is an ORDERING gate, not an ATTRIBUTION gate.** Leaving nit at 0.60 and raising *tag*'s `call_looseness` to 0.80 reads **982/982 and 772 — green on both legs**, with the wrong cause. Only G-NODE's self leg ties the movement to the nit. | **ACCEPT as characterisation.** The two gates are genuinely complementary and neither carries the slice's claim alone — that is now stated in the docs. Not a defect: G-SWEEP's job is the general direction, G-NODE's is attribution. |
| BR-3 | LOW | Spec verify-by 5 still said "every identity leg red" after S-9 removed the identity leg; and its revert figure (384/970) is the *other* mask — under revert the shipped and pre-slice packs coincide, so the enumeration is **396/982**. | **ACCEPT.** Both corrected; the gate reports its own denominator and readers are told to trust that over the doc. |
| BR-4 | LOW | T5's brief (written by the director) predicted all six golden rows would move; measurement showed **only nit's WTSD** did, the other five reproducing byte-identically. T5 recorded what it measured and cited two same-chain precedents. | **ACCEPT — the director's brief was wrong, the worker was right.** Recorded because "the contract map says every row moves" is exactly the kind of inherited assumption this initiative keeps having to re-measure. |
| BR-5 | LOW | A third suite failure appeared once during T2: `test_sim_session.py::test_reveal_unavailable_on_live_hand_and_unknown_scope`. Measured flake rate **2/400 = 0.5 %**, traced to `app/services/sim_session.py:16-18` seeding from unseeded `secrets.randbits`; mechanism is preflop-only, this lever postflop-only. | **ACCEPT — pre-existing, unrelated.** Widens `N-SIMFLAKE` to a **second** test file (the filing named `test_sim_session_buyin_cap.py`). |

### What still passes this whole suite while being wrong (measured, not speculated)

Scaling CALL without RAISE (only G1 stops it — if G1 is ever skipped, this slice has no defence) ·
any lever value ≤0.48 (no lower bound from these gates) · loosening tag instead of tightening nit
(passes G-SWEEP) · anything outside a facing node with a live FOLD leg (SPR-committed nodes are
lever-inert by construction, and preflop/bet/check nodes are untouched) · computing correct weights
then sampling from them wrongly (both gates read the weight vector, never a drawn action).

## Rev-4 spec review — FAIL, folded in place (2026-08-04)

Delta review of `specs/r9-loosefit-rev4.md`. **Both scheduled reviewers died on transport, not on
content** — the Claude `refuter` dropped twice with "connection closed mid-response" (once after a
resume from its own transcript), and Codex hit a reconnect/TLS failure loop after completing its
measurements but before writing findings. A third, deliberately narrow attack-only review then
completed and returned **FAIL** (1 HIGH / 2 MED). All three findings accepted and folded into rev 4
in place; no rev 5 needed.

**Verification status of rev 4's numbers is nonetheless strong** — they were reproduced three
independent ways before any verdict: the director reproduced all five panel rows exactly at their
labelled prices and stress-tested the ceiling on drawing hands (the B5b damp path subtracts a
looseness-proportional term, which *should* break a common-factor derivation and does not — error
5.6e-17); Codex independently reproduced the sweep denominator and counts
(`{'nd': 970, 'head_less': 26, 'head_equal': 560, 'after_less': 0, 'after_equal': 0}`), the ceiling
on four edge classes, the panel with the line signal on, and the 600×/1200× mispricing.

| # | src | sev | finding | adjudication |
|---|-----|-----|---|---|
| S-9 | refuter | **HIGH** | **The identity gate was VACUOUS.** `identity = self + HEAD_gap` is an exact telescoping identity, and `HEAD_gap` is fixed at HEAD and untouched by this slice (tag is out of scope). Clearing the self floor of 0.040 therefore *forces* identity to 0.0933 / 0.0968 / 0.0867 / 0.0828 at P1–P4 — all above the 0.075 floor before it is reached. **The gate could not fail while the self gate passed.** | **ACCEPT — director verified by arithmetic on the spec's own published numbers.** Rev 3 was killed for mispriced nodes; rev 4 disclosed the decomposition *and still shipped a gate the decomposition makes redundant*. **Identity leg REMOVED from the panel**; the cross-persona claim is carried by G-SWEEP, which is a genuine population comparison, red at HEAD by 2.08×, and subsumed by nothing. Raising the floor to bind would have left 1.02× margin at P4 — noise-thin on a deterministic gate. |
| S-10 | refuter | MED | Rev 4 quietly dropped "tightest defender" from its title and goal (a legitimate S-3 narrowing to a pairwise nit-vs-tag claim) **but never stated the narrowing as such**, and nothing constrained the wording of the roadmap's "mark built" note. Every gate here can pass while nit folds less than lag, fish, maniac or station. | **ACCEPT.** Rev 4 now states the pairwise scope explicitly as the S-3 resolution and **binds the build**: the roadmap note must say "nit folds more than tag" and must not use "tightest defender" or any all-persona ranking language. The phrase has been used loosely in this initiative before and would ride on gates that do not support it. |
| S-11 | refuter | MED | The slice re-prices the canonical grid **for its own sweep** while leaving `_NLOGIT_PRICES` broken for N-LOGIT's own consumers — leaving two divergent constructions of the same 1,728-cell grid in the repo. That is not just documentation debt: verify-by 6 delegates the disclosed CALL-only mutant's kill to **N-LOGIT's G1 gate, which runs at faced fractions 600 and 1200** — a regime this very spec excludes from its own panel as degenerate. The spec asserted that ownership without ever checking G1 still discriminates there. | **ACCEPT.** Rev 4 and ticket T6 now require the build to **demonstrate** G1's kill on both the shipped construction and a correctly-priced one. If G1 discriminates only at the broken prices, the build STOPS and reports — that escalates `N-NLOGITPRICE` from filed to blocking. |

**Standing lesson added:** *disclosing a decomposition is not the same as checking what it implies.*
Rev 4 wrote down `identity = self + HEAD_gap` in its own text and still presented the two as
independent legs. Whenever a spec decomposes a quantity, the next line must ask whether the parts
can fail independently — and if they cannot, one of the gates is decoration.

## Rev-3 spec review — DUAL FAIL (2026-08-04)

Reviewers: Claude `refuter` → **FAIL** (1 HIGH); Codex `gpt-5.6-sol` (high) → **FAIL** (2 HIGH /
3 MED / 2 LOW). No reviewer-vs-reviewer conflict; the two HIGH classes are independent and both
were reproduced by the director before acceptance. Spec rev 3 is withdrawn pending re-derivation.

| # | src | sev | finding | adjudication |
|---|-----|-----|---|---|
| S-1 | refuter | **HIGH** | **Every price in rev 3's feasibility table is mislabeled.** Calling `sample_postflop_decision` without `latest_aggressor_contribution_bb` trips the legacy denominator branch (`personas_postflop.py:954-955`), so the engine reads a LARGER faced price than the label: the three "½-pot" flop nodes are pot-sized, the "⅔-pot" turn node is a 2×-pot overbet. **At the true ½-pot price the spec's own named binding node fails BOTH thresholds** — self +0.0222 (needs ≥0.025), identity +0.0399 (needs ≥0.05). | **ACCEPT — decisive.** Director reproduced it exactly: mislabeled `nit.60=0.1197/nit.45=0.1535/tag=0.0921`; true ½-pot `0.0737/0.0959/0.0560`. **Aggravating:** this initiative already documented this trap at `reports/r9-defence-design.md:78-85` with the corrected pair (0.2637 vs 0.3798) — and **0.3798 is verbatim row 1 of rev 3's table.** A known-wrong reading was reused and thresholds pre-registered against it. Rev 3's build instruction compounded it by naming `_dist_for_pack` (`:1218`), which has no such parameter, so the builder would have reproduced the mislabeling silently. |
| S-2 | codex | **HIGH** | **The panel nodes are underspecified**, and legal-action shape is load-bearing: same cards/board/price with FOLD/CALL/RAISE gives identity +0.0614; with FOLD/CALL only it gives +0.0368 and **fails**. | **ACCEPT.** Director reproduced: at FC-only, nit@0.60 and tag@0.60 read **identically** (0.133026) — the whole nit-vs-tag difference at that node flows through the RAISE branch, so **the identity leg silently collapses into the self leg whenever raise is illegal**, and the two legs stop being independent evidence. Every node must be a complete tuple (cards, board, street, legal actions + raise bounds, pot, stack, opponents, current bet, contribution, context). |
| S-3 | codex | **HIGH** | **Four hand-picked nodes cannot support a general "tightest defender" claim.** A sweep of 1,728 canonical cells: 486 non-degenerate; **132 miss the 0.025 self threshold, 198 miss the 0.05 identity threshold**; a non-degenerate overpair vs ⅓-pot reads self +0.0095 / identity +0.0225. Also a **second degeneracy class**: a river ace-high node whose legal CALL probability is exactly zero. No reversal found — the weakness is vanishing effect and omitted legal shapes, not reversed direction. | **ACCEPT.** Rev 4 must either narrow the claim to "selected non-committed bluff-catcher nodes" or gate on a measured fraction of the canonical cell population. ⚠️ The sweep's own prices may share S-1's defect — **re-run at correct prices before using any of these counts.** |
| S-4 | codex | MED | **`N-ANCHORSTALE` ships FIVE false statements, not one** (`:6899`, `:6925`, `:7208`, `:8468`, `:8610`). "File it" is not defensible when the file is already being edited. | **ACCEPT.** Rev 4 corrects those five to "calibration anchor" in-slice; only the broader 41-site `model_copy(update=` audit stays filed. |
| S-5 | codex | MED | **G-POP is vacuous as designed.** `pytest -q` does not emit passing-test stdout (`verify.sh:7-8`), so a print-only report leaves no visible baseline while adding a passing test that asserts nothing — violating this initiative's own "every gate asserts movement or kills a mutant" law. | **ACCEPT.** Rev 4 either makes it a non-collected measurement whose output is committed to the report, or gives it a real validity assertion. It must not be a collected test that asserts nothing. |
| S-6 | codex | MED | Rev 3 defers the shares-accessor disposition to an unrelated ticket, contradicting the accepted B-15 resolution. | **ACCEPT-NARROWED.** Rev 4 states explicitly: **branch from `origin/main` WITHOUT `7736156`**, which makes B-15 inapplicable to this slice. The accessor's fate rides with `N-ANCHORSTALE`, recorded there, not silently deferred. |
| S-7 | codex | LOW | "Exactly three tests move" misstates the blast radius; the measured result is **2 pre-existing failures** (`1414 passed, 1 skipped`) plus a NEW gate that is green at 0.45 and red at 0.60. | ACCEPT — wording. |
| S-8 | codex | LOW | The excluded pot-sized node is **rounded**-degenerate, not exactly forced: folds are 0.9999942860 / 0.9999957145 / 0.9999927823, self movement 1.4285e-6. Rev 3 called the table "exact" and the node "1.0000". | **ACCEPT.** Director reproduced. Say "effectively degenerate — continue actions below 0.01", not "forced". |
| S-blast | both | — | **Convergent PASS:** the 0.42→0.45 extrapolation rev 3 flagged as unverified **holds**. Both reviewers ran the full suite in-memory at nit 0.45 and got exactly the two sanctioned fixtures failing; ladder, bands, price-tail, node-trace, arrival-range and coverage baseline all green. | Recorded. The one thing rev 3 got right about its own risk. |
| S-flake | refuter | — | `test_sim_session_buyin_cap.py::test_every_hand_starts_every_seat_inside_the_buyin_band` failed once and passed on re-run and standalone at HEAD — traced to `app/services/sim_session.py:16-18` using unseeded `secrets.randbits`. **Pre-existing flakiness, unrelated to this lever.** | **FILE separately** — a genuinely unseeded test in a suite whose whole discipline is determinism. |

**Standing lessons added:**

- **A price is not what you label it — it is what the engine computes.** Assert the derived faced
  fraction inside the measurement, or the label is a guess. This trap has now cost this initiative
  twice, and the second time the correction was already written down in a sibling report.
- **Convenience helpers encode defaults that silently change the physics.** `_dist_for_pack` omits
  the aggressor contribution; naming it in a spec instructs the builder into the bug.
- **Two legs of a gate are only independent evidence while the mechanism keeps them apart.** Remove
  the raise branch and the identity leg becomes the self leg with extra words.

## Independent verification of the T1 findings (director-commissioned, 2026-08-03)

Four fresh-context agents re-checked the build findings above; three ran in isolated worktrees at
`7736156` so their pack edits could not collide. **One finding is REFUTED, one is narrowed, the
rest survive and two are strengthened.** Every agent was briefed git-read-only and every pack was
md5-verified restored.

| verifier | scope | verdict |
|---|---|---|
| V-A (`refuter`) | the instrument commit | **PASS** on all four claims (no rng draw, no call-site change, cache identity holds, exclusion predicate sound). Ran the persona file whole: 294 passed / 1 skipped. Attacks tried and failed are enumerated in its report. |
| V-B (`implementer`) | B-1's floor | **CONFIRMED.** 0.38 FAIL, 0.42 pass, 0.45 pass, 0.60 pass; both boundary values run twice, identical — deterministic, not noise. Crossover pinned only to (0.40, 0.42]. α ceiling passed at every value 0.38–0.60. |
| V-C (`implementer`) | B-2's tag pin | **CONFIRMED, and widened.** Prediction written before running; both culprits failed exactly as predicted and returned to green on byte-restore. But the FULL suite shows **7** failures, not 5 — see B-6R. |
| V-D (`heavy-worker`) | the statistics and the premise | Claims 1 and 3 **SUPPORTED**, Claim 2 **PARTIALLY**, Claim 4 **REFUTED** — see B-8R, B-11, B-14. |

| # | sev | finding | status |
|---|-----|---|---|
| B-8R | HIGH | **B-8 IS REFUTED — withdraw it.** The claim that the gate-posture FtC slope is "−0.345, 2.3× steeper than the True-posture value, so anchor-seeded steps are unsafe at the gate posture" rests on a secant between two n=4,000 readings whose own 1σ (±0.1907 per ln-unit) is **larger than the entire effect claimed**. Re-measured over the same two lever points at n=32,000: **−0.195 ± 0.064**, inside the feasibility study's −0.15…−0.19 band, and the posture difference is **0.91σ — not resolvable**. | **ACCEPT the refutation.** This is the same n=4,000 unreliability the report itself diagnoses twice and then failed to apply to its own slope. Rev 3 must NOT carry "the posture lesson governs slopes" or force fresh 32k secants at every fit step on this basis. Rule 2 (fresh secants) may still be good practice; it was simply not demonstrated here. |
| B-11 | MED | **The paired noise band is ~1.18× too narrow.** The analytic binomial σ is right per-persona (empirical/analytic ratios 0.89–1.13 over 56 independent seeds), but the two arms are not independent: corr(nit FtC, tag FtC) = **−0.387** (z = −2.8), so `σ_gap = √(σ²_nit + σ²_tag)` is mis-specified. No mechanism identified; the 95% CI on the inflation (0.96–1.40) covers 1.0, so it may be a 56-sample artifact. | ACCEPT as a caveat. Direction of every conclusion is **unchanged and strengthened**: 4.63σ → **3.9σ**; B-4's n ≥ 53,800 → **≈75,000**; B-5's n ≈ 405,000 → **≈566,000**. Rev 3 should state the inflated figures and decide whether to re-measure the correlation. |
| B-12 | MED | **B-7's premise correction is stronger than stated, and its evidence was weaker than stated.** The report's 4k/16k/32k series is a **nested prefix of one run**, so "the gap shrank as n grew" was a within-sample statement, not three measurements. Genuine independent evidence: a second 32k draw (gap −0.0136) plus **56 independent seeds at n=4,000** (mean +0.01282, SE 0.00710). Inverse-variance combination: **gap = +0.0087 ± 0.0063, 95% CI [−0.0035, +0.0210]**. The premise value −0.063 sits **11.5σ** away; only 4 of 56 seeds reach it. | ACCEPT. B-7 stands and is strengthened: at the CI posture the point estimate has the **opposite sign to the premise** — nit folds ~1.3 fold-points MORE than tag, not less. Rev 3's restated background should use the ensemble figure, not a single-seed reading. |
| B-13 | LOW | **§5.3's "tag's FtC at 4k is 1.7σ below its own stable value" is not reproducible.** Against the disjoint remainder of the same 32k run it is **−3.17σ**. The 1.7 looks transposed from §6's 1.74σ coupling delta. | ACCEPT. The over-read is real and larger than reported; correct the figure in rev 3. |
| B-14 | LOW | B-4's extrapolation arithmetic is right to 0.04 % (53,799.5 vs the stated 53,780); B-5's reproduces exactly (404,853). Both hold the measured effect fixed and n ∝ 1/effect², so a ±1σ revision of the gap alone swings B-4's n between **36,400 and 87,600**. | ACCEPT. Rev 3 must quote these as ranges, not point estimates. |
| B-6R | MED | **B-6's re-record footprint was undercounted.** A tag-only edit to 0.52 fails **7** tests: the 5 pins (B-2), plus `test_persona_stats_byte_identical_after_log_refactor` (**passive_fish's** AF) and `test_limper_coverage_fires_on_organic_play` (**calling_station's** fire counts). Neither names tag or the lever — they move because all six personas share one seeded rng stream, so changing tag's call/raise mix re-deals every persona simulated after it. Restoring tag.json returns all 7 to green. | ACCEPT. The golden was already T4's; the limper belt was already B-6. Record the mechanism explicitly so rev 3 budgets a **4-test remediation** for any tag move (2 stale pins to re-scope + 2 goldens to re-record). |
| B-15 | LOW | **The instrument has no regression test of its own** — nothing asserts `_persona_stats_shares`'s field order or arithmetic against a hand-computed reference (V-A). Defensible for an instrument-only commit exercised in a real campaign, but it is unprotected code. Separately, its docstring says fold-legal nodes are "exactly" where `rscale` applies; the engine also requires `continue_ref is not None`. All six shipped packs author it, so not a live bug. | ACCEPT both. Rev 3 gives the accessor a small correctness gate and fixes the docstring wording. |

**Standing lesson added:** *a slope deserves the same sample-size discipline as a level.* The T1
report caught the n=4,000 problem for its headline statistic and then quoted a derivative built
from two n=4,000 points. Diagnosing an instrument's unreliability does not immunise the rest of
the document against it.

**Process note:** rev 2's central fix (C-1, "run the ACTUAL pytest gates, no posture proxying")
is what found B-1, B-2 and B-4 within the first hour. The rev-1 plan would have reached T5 before
discovering that the seed was illegal. The review round paid for itself.

## Codex invocation note

Same as the two prior runs: `codex_models_manager` / rmcp noise lines in the output are harmless
blocked-probe chatter; the review completed fully (it read the tree AND ran read-only python
probes — the C-1 posture measurement came from such a probe and was structurally verified by the
director before acceptance).

## Standing lessons reinforced

- **A gate's verdict lives at the gate's own posture.** A measurement campaign at a
  "better" posture can be geography, never certification (C-1/C-2).
- **Check the direction of a gate against the mechanism's own invariants** before pre-declaring
  it — N-LOGIT's invariance gate said the conditional share cannot fall, and the spec claimed it
  would (C-3).
- **"Append to the tuple" is an API change** — grep the unpackers before promising
  compatibility (C-4).
- A robustness rule stated in a report ("keep ≥0.02 margin") binds the spec that cites the
  report — quoting the recommendation while adopting a seed that violates it is self-refuting
  (R-2/C-6).
