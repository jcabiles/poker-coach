# Wave 6 ledger — instrument repair + maniac 77-99 call-leg (2026-08-01)

Three parallel worktree lanes off main `b54fe6e` (post-#153), single fixture-recorder at landing,
serial landings A → B → C. Owner gates cleared before spawn: Fable declined (Opus everywhere);
w5-b2 branch (unmerged 695-line actor-position work) ruled KEEP.

- Lane A = **INSTR-CACHE+HARNESS** (`feat/persona-realism-instr-cache-harness`, $TMPDIR/wt-instr):
  wave-4/5 filed instrument defects — `_STATS_CACHE`/`_STATS_EXT_CACHE` pack-blind keys (same-process
  before/after sweeps reuse the first reading; bit two waves) + harness `_preflop_decision` sizes every
  raise at `la.min_bb` while production 5-bets are all-in (min-raise ping-pong wars; wave-4 9.4%-vs-74.1%
  channel contradiction, finding R-L2). Instrument-only → refuter + Codex Sol review.
- Lane B = **ESTIMATOR-TOCALL** (`feat/persona-realism-estimator-tocall`, $TMPDIR/wt-estim): W1-era
  deferred estimator faced-price blindness (CALL `min_bb=None` → numerator 0, range_estimate.py:301) +
  R10-TAIL-a1 f>1.5 tail parity + blend-gate power (dr-L3: Wilson ±0.045 at n=4000 exceeds the 0.43
  floor margin → assert at n=12000). Production-feature blast radius → refuter + theory + Codex Sol.
- Lane C = **M4BET-CALLLEG** (`feat/persona-realism-m4bet-callleg`, $TMPDIR/wt-m4call): wave-4 T-M4
  follow-up — 77-99 gain a call leg vs 4-bets per §3 T3 direct-price math (~28% needed); 22-66 stay
  jam-or-fold (narrowed law). Behavior slice → full triple review (refuter + theory + Codex Sol).

Laws in force: frozen population band VALUES never move (genuine breach after stable-n escalation
stops the slice → owner); DIRECTIONAL instrument bands re-derivable with paired-sweep provenance
(#154 rulings: §5 LAG PFR is DERIVED/DIRECTIONAL; per-seat RFI provenance-governed); builders never
touch seeded fixtures; cumulative coverage delta vs immutable 28.3% disclosed at landing (position
entering wave: 27.7%); separate-process measurement until lane A lands; merged-state cross-lane gate
interactions verified against actual sibling tips before landing.

---

## ⚠️ Wave-entry finding: main b54fe6e is RED on the 3 seeded-fixture tests

Orchestrator-verified directly on the clean main checkout (separate process, 2026-08-01):
`test_coverage_never_regresses` ("hand stream drifted — harness invariant broken") ·
`test_limper_coverage_fires_on_organic_play` (pre-M3 pair ('UTG2',1) 87 != 92) ·
`test_persona_stats_byte_identical_after_log_refactor` (station AF 0.2628 != golden 0.3064).
Pre-existing at the wave base — the wave-5 landing re-record did not survive the #152/#153
squash-merge chain byte-exactly. First surfaced by lane B (it re-ran its base). Remedy: this
wave's single-recorder landing re-record fixes them on the landing tip; disclosed to owner.

## Lane A — INSTR-CACHE+HARNESS (build commit `516498c`)

Shipped (single file `backend/tests/test_personas_postflop.py`, +275/−37): new `_packs_fingerprint()`
(content hash of all loaded packs, not versions) appended to BOTH cache keys + the `.pop` site; harness
`_preflop_decision` now a thin pass-through to production `play._preflop_decision` (`_play_hand` derives
`current_bet_bb`+`limpers` exactly as `play.bot_decision`); red-first gates
`test_stats_caches_are_pack_content_keyed` (mutate-in-process proof; red under old key via fingerprint
stub) + `test_harness_preflop_raise_depth_matches_production` (legacy b54fe6e body kept as control).
Paired sweep n=2000 seed 20260710 separate processes: harness 5+-raise share 0.0180 (depth tail to 99!)
→ 0.0000; production 0.0000 both sides. The wave-4 INSTRUMENT WARNING rewritten RESOLVED w/ provenance.
1345 pass / 3 base reds / 2 skip; ruff clean.

**⛔ STOP-condition hit and OWNER-ADJUDICATED (2026-08-01, noobified AskUserQuestion):** with the
production-faithful harness, maniac WTSD reads **0.593/0.588 at n=2000/4000** (separate processes) vs
frozen ceiling 0.50 — the bot didn't change, the ruler did (min-raise wars suppressed all-in run-outs;
production 5-bet-all-in restores them). Builder edited no band value and stopped per standing order.
**Owner ruling: DEFER the maniac WTSD assertion to W4-b** (skip + provenance note; band VALUE stays
frozen (0.34,0.50); joins the fish + maniac WTSD deferral family) — over re-anchor-now and
reject-repair. Apply as a fold item. Related instrument facts for the fold round: maniac AF is
n-FLAKY at the band test's auto-budget n (~479-528 → reads 2.30, under the 2.4 floor; 2.99/3.06 at
stable n — and AF asserts before WTSD, masking the breach); passive_fish WTSD moves INSIDE its band
(0.509 vs prior 0.494-0.497 under-floor, already skip-deferred). Cross-lane note: lane C's "WTSD
margin 0.019" worry was measured on the OLD harness and dissolves into this same ruling.

## Lane B — ESTIMATOR-TOCALL (build commit `1461bd8`)

Shipped: `_Ctx` gains `to_call_bb` + `aggressor_contribution_bb`; replay tracks the street's latest
BET/RAISE increment; `_legal_from_ctx` builds CALL with real `min_bb`; sampler receives
`latest_aggressor_contribution_bb` — so f>1.5 tail parity (3b) falls out by construction (production
`_price_factor` now sees real f; `_price_factor(3.0)/_price_factor(1.5) == 4.0` visible in estimator).
Estimator was provably price-blind before (identical response dists at f=0.5/1.5/3.0). Blend gate
asserts at n=12000 (lag 0.4841, CI [0.459,0.509], half-width 0.025 < 0.03 self-check; maniac 0.2616)
with free n=4000 checkpoint; runtime 19.5s→71.4s. Bot decisions byte-identical (the 3 base reds
diff-identical before/after). Red-first verified on 6 new/updated tests. 1346 pass / 2 skip / 3 base reds.
Builder deviation disclosed: also threaded the aggressor increment (contract §7 one-denominator law) —
numerator-only would ship a knowingly wrong price on self-re-raise nodes. Flagged for reviewers:
posterior test metric choice (no-pair mass, not concentration) + stale comment
`personas_postflop.py:841-844` (out of scope, sibling-owned file).

## Lane C — M4BET-CALLLEG (build commit `6cff2f5`)

Shipped: maniac.json 1.4.0→1.5.0, vs_4bet `"22-99"` split → `"77-99" {call .30, 5bet_shove .40,
fold .30}` + `"22-66"` byte-identical. T3 math: break-even 14/(35.5+14)=0.283; equities 77/88/99 =
.362/.357/.362 vs QQ+/AK; jam held at .40 (only value satisfying 66≤77-99≤TT ladder). Red-first
proven at 1.4.0 content. Arrival-weighted: fold .2859→.2764 / call .3359→.3454 / jam .3781. Stable-n
n=4000 separate processes: AF 3.5785→3.5357 · WTSD 0.4744→0.4808 (ceiling 0.50 — margin 0.019,
flagged) · FtC 0.3251. No band value touched. Flagged: stale comment test_pack_range_lint.py:207
(unowned); channels-report 1.4.0 recorded figures don't reproduce at base (pre-existing staleness,
documented not chased).

### Reviews

**Lane C Codex Sol: PASS-WITH-ISSUES.** Verified exactly: mix/ladder/tail (0.1181≤0.15)/aggregate
(fold .2859→.2764, call .3359→.3454, jam .3781)/equities (.3617/.3565/.3618 vs QQ+,AK)/red-first at
base/no weakened bound/stable-n reproduced to 6 decimals. Findings: **C-1 MED** — rationale's
"14 into 35.5, SPR ~1.5" is NOT the probe's recorded sizing (replayed 282 modeled decisions: mean call
28.6 into pot 73.7, median post-call SPR 0.562, 150 OOP/132 IP); T3 conclusion SURVIVES (mean required
equity 0.2827) but sizing/SPR/OOP-realization prose unrepresentative. **C-2 LOW** — T2 F* misstated:
inputs give 0.262–0.279, not "≈0.27–0.31" (T1 0.4191 correct). Both doc/rationale-only.
**Lane B theory: GO-WITH-ISSUES.** Cleared with measurement: threading exact (`to_call_bb` char-for-char
= engine's CALL entry; street-increment reproduces `pot_before_current_aggression` verbatim); the
over-brief aggressor-increment deviation ruled CONTRACT-MANDATED (§7 one-denominator + §9 ledger #12 —
true numerator over legacy denominator would be a WORSE breach; pre-declared overrule of any scope-creep
objection); price-blindness confirmed genuine defect (byte-identical dists at 5 prices); no new constant
(tail = production `_price_factor` by construction); no band VALUE moved. Findings: **T-1 MED** — blend
gate re-power closes dr-L3 for LAG only and REPRODUCES it for maniac: 0.2616 @n_dec 2703, CI
[0.245,0.278] straddles the 0.25 floor; floor distance 0.0116 < half-width 0.0166; fixed 0.03 self-check
is lag-derived; docstring's "maniac mid-band" claim FALSE → ruling: fold the docstring correction now,
FILE the margin-relative form `half_width < min(rate−lo, hi−rate)` + maniac n-raise-or-report-only (do
NOT widen the band — W3R-1 anti-pattern). **T-2 MED CONTRACT-DEFECT (pre-existing, slice faithful)** —
tag continues 53.6% with mid pair vs 1.5×-pot overbet, 22.4% vs 3× (T3 break-evens 60%/75%) — contract
has a price LAW but no LEVEL target for tag/lag at this bucket; newly user-visible via the reveal →
ACCEPT-AND-FILE to W4-b (plateau-height owner; fit tag/lag `call_looseness` on size-bucketed FtC;
extend or explicitly-absent the §5 slope row). **T-3 LOW** — stale comment `personas_postflop.py:841-844`
now false → landing fold (recorder owns the file at landing). Explicitly cleared: item-10 byte-identity
(item 9 overrides for this slice), bot decisions untouched (80 adjacent tests green), item-14 deferred
to landing by wave law.
**Lane C refuter: PASS-WITH-ISSUES (5 LOW, all doc/report-quality).** Independently reproduced:
exact 3-class scope (169-class resolved-policy diff), red-first via old-pack direct load (no git
mutation), no weakened gate (bounds/bands/dossier-report untouched; tf3 pin got STRICTER), ladders,
aggregate to 4dp, tail 0.1181≤0.15, stable-n exact, channel-report figures exact (incl. the honest
1.4.0-doesn't-reproduce admission), N200 golden confirmed stale AT BASE (15 mismatches on 1.4.0
content). WTSD knife-edge probe: NOT knife-edge (4-seed sd≈0.008, ~3.7σ headroom on the old ruler;
moot under lane-A ruling). LOWs: R-L1 pack_range_lint:207 stale comment (builder-flagged, confirmed) ·
R-L2 channel table omits the two CALL-prior strata ranking above its last row (7.8% of decisions —
understates unmodeled mass) · R-L3 counterfactual fold-0.286 sentence reads as shipped state · R-L4
equity quotes ±0.002 off engine-reproduced (suit-pick) · R-L5 WTSD margin consumed with no live gate
(informational). **FOLD ROUND SENT to lane C builder: 9 items (Codex C-1/C-2 + theory CT-1..4 +
refuter L1..4), all doc/rationale/message-only, zero policy-byte changes.**

**Lane B refuter: PASS-WITH-ISSUES.** Re-executed: full suite 1346/2/3 with the 3 base-red failure
VALUES identical (no rng displacement; range_estimate's sole importer is sim_session, play.py doesn't
import it); red-first real (in-process reversion reproduces the docstring's exact pre-fix numbers);
blend gate live-asserts at n=12000, prefix-equivalence verified empirically; posterior metric HONEST
(margin 0.1 vs measured 0.159); min_bb=None readers proven unreachable. Findings: **B-R1 MED** stale
`personas_postflop.py:841-844` comment (≡ theory T-3, convergent — landing fold, orchestrator) ·
B-R2 LOW retire the closed deferral at `docs/ai-dlc/contracts/persona-realism-w1.md:94` (landing) ·
B-R3 LOW lag half-width headroom thin (0.0250 vs 0.03) + gate 110s under load (ACCEPT-AND-FILE with
the margin-relative filing) · B-R4 LOW cache annotation type loosened (fold).

**Lane B Codex Sol: PASS-WITH-ISSUES (1 LOW).** Own 300-hand stress replay: 4,804 decisions matched
live context (1,733 prior-investment prices, 2,740 facing-raise nodes, 1,828 capped all-in calls,
street resets). Threading ruled "correct and minimally necessary". Checkpoint counts exactly match
standalone (231/860, 229/469). **B-C1 LOW**: zero deterministic coverage of the DISCRIMINATING
self-re-raise path (aggressor_contribution ≠ current_bet_to) — bet-to-misthreading would escape the
suite → fold: add one regression. **FOLD ROUND SENT to lane B builder: 3 items** (blend docstring
honesty per theory T-1; discriminating-path regression per B-C1; annotation per B-R4). FILED from
lane B: margin-relative half-width + maniac blend power decision (instrument family) · theory T-2
tag/lag plateau → W4-b · B-R3 runtime.

**Lane A Codex Sol: PASS-WITH-ISSUES.** Verified: fingerprint covers all serialized PersonaPack
fields, deterministic across 3 processes (1b63d266a11a86ae), 0.39ms/call; cache red-first reproduced;
legacy control AST-equal to base; depth control reproduced (0.0170/99 → 0.0000/4); maniac WTSD
0.5929/0.5882 + fish 0.5082 readings reproduced; no data/ file, bands/goldens AST-equal. Findings:
**A-C1 MED** — AF asserted at throughput-derived n (~479-528: reads 2.24-2.31, under the 2.4 floor;
2.99/3.06 at stable n) with NO stable-n retry unlike FtC/WTSD → host-speed-dependent pass/fail AND
masks the WTSD skip (formal instrument defect) · **A-C2 MED** — depth gate under-constrains: an
adversarial wrapper forwarding `current_bet_to=0.0, limpers=0` still PASSES (gate proves only
5+-war elimination, not arg parity; histograms also differ slightly from production via a
pre-existing extra RNG sample) · A-C3 LOW — cache gate mutates only the measured pack (a
tag-only-fingerprint mutant passes; filler-pack coverage unproven) · A-C4 LOW — legacy control
byte-vs-AST fidelity note (accept).

**Lane B fold commit `c6a61f8` (tests-only) + delta re-review: PASS, review-complete.** Fold: maniac
power docstring made honest (false "mid-band" sentence deleted); NEW mutation-killing regression
`test_estimator_prices_a_self_reraise_by_the_increment_not_the_bet_to` (increment 57 vs bet-TO 60,
f 2.2326 vs 2.5946, same overbet bucket — only the tail separates; bet-TO mutant fails exactly this
one test); annotation restored precise; builder self-disclosed runtime honesty fix (71-120s spread =
machine load). Delta refuter verified everything independently: gate body substantively unchanged,
Wilson 0.016560 recomputed, live-engine re-derivation of the regression line (pot-before-aggression
21.5/57.0), mutation replicated via sys.modules pre-registration without touching the worktree,
18 pass + ruff clean. **Lane B review-complete at `c6a61f8`.**

**Lane C fold commit `13765d1` (doc-only) — all 9 items applied** (T1 0.447 w/ villain-cannot-cover-B
caveat both files; T2 F* 0.262-0.279; lever-derived canonical sizing + probe spread separated; mass-
weighted robustness claim naming nit/fish tail; 4dp equities w/ exact combos 7c7d/8c8d/9c9d ±0.002;
call<jam message softened to directional premise; lint comment 1.5.0 reality; 2 CALL-prior rows added;
counterfactual marked + current triple in gate docstring). Policy bytes verified unchanged by builder
diff. **Delta re-review of 13765d1: PASS-WITH-ISSUES — caught a NEW error the fold introduced.** All
arithmetic/policy/AST checks green (assertion literals 1602==1602, policy identical doc-stripped,
channel rows + equities reproduce). **D-1 HIGH**: the new "lever-derived chain" prose is FALSE —
"open 2.5 → 3.3× → 3.0×, from this pack's own sizing block" yields 0.3235, not the (correct) 0.2827;
real chain = opener open_bb 3.0 × maniac 3.3 → opener fourbet_mult 2.4 (mults apply to last_raise_to);
only 3.3 is maniac's own. **D-2 MED**: "maniac 34.7% 4-bet mass" reproduces nowhere (conflation with
the n≥4 channel share 0.3463); combo-weighted first-match ≈19.6%/15.2%. D-3 LOW "cannot cover the
jam" literally false (fully matched; real point = naive B/(P+2B) books an uncovered extra B). D-4 LOW
five CALL-prior strata not three (total 12.4%). D-5 LOW two extra failure-message rewords beyond
authorization — retroactively ACCEPTED (AST-identical conditions). D-6 LOW one-off probe readings
unlabeled. **Fold round 2 SENT (prose-only).**
**Fold-2 commit `b9a10b9` — all 6 delta items applied; ORCHESTRATOR SPOT-CHECK (disclosed, in lieu of
a third agent round): diff prose-only (the only assert-adjacent lines are `_doc` strings containing
the word "unasserted"), chain figures verified by hand (3.0×3.3=9.9 → ×2.4=23.76 → 13.86/35.16;
90.1/76.24 stacks), builder re-ran M4BET 8-pass + lint + ruff, policy bytes re-verified untouched.
Lane C review-complete at `b9a10b9`.**

**Lane A refuter: PASS-WITH-ISSUES.** Verified sound: fingerprint covers every field (no excluded/
computed/set-typed fields; all 6 packs; load not cached), deterministic across PYTHONHASHSEED 1/2/3,
0.19ms; both red-first legs replayed exactly; pass-through arg semantics byte-match production; N200
golden staleness proven pre-existing by executing the b54fe6e module (base maniac AF 3.2258 != golden
4.8222). Findings: **A-R1 HIGH** — maniac AF band test FAILS on HEAD across n∈{150,400-650} (HEAD
2.24-2.45 vs base 3.15-3.52, floor 2.4; systematic ~1.0 AF drop under production sizing; NO stable-n
escalation leg for AF) — but stable-n AF 2.99/3.06 is INSIDE the frozen band → instrument power, not a
breach; branch not mergeable green until folded. **A-R2 MED** — `_derive_n` throughput-derived
per_persona_n = the verdict depends on machine load (passes standalone at n=298, fails full-file at
n=150); W5-b4 texture_n=1500 pin is the in-file precedent. **A-R3 MED** — two WTSD skip rationales now
FALSE: fish skip pins 0.4873-under-floor but repaired harness reads 0.5082 INSIDE (0.50,0.57) — dead
gate that would now pass; maniac skip says "straddle" (it's a 9-pt breach). **A-R4 MED** — wrapper
defaults (0.0, 0) silently collapse to min-raise (vs_rfi 10.5→6.0, vs_3bet 24.0→20.0 probes) = the
R-L2 defect re-creatable; production makes both required. **A-R5 LOW** — stale comments outside the
file: test_sim_session.py:354-358 + play.py:4-6 docstring still assert the eliminated divergence.
**FOLD ROUND SENT to lane A builder: 6 items** (AF stable-n escalation + per_persona_n pin; WTSD
ruling application + both skip rewrites incl. LIFTING the fish skip back to a live assertion;
depth-gate arg-parity mutation-kill leg; defaults dropped + ownership granted for the one
test_sim_session call site + comment + play.py docstring comment-only; filler-pack cache leg;
AST-vs-byte note).

**Lane A fold commit `138770e` — all 6 items applied** (AF stable-n escalation to 4000: maniac 2.357
@n=600 → 3.0553 in-band, escalation free via memoized n=4000 sims; `per_persona_n` PINNED 600 per
W5-b4 precedent; maniac WTSD deferral applied w/ accurate provenance; **fish WTSD skip LIFTED — live
assertion green at 0.5082**, thin 0.008 margin disclosed; new arg-parity gate w/ zeroed-defaults
mutant dead (10.5-vs-6.0 / 24.0-vs-20.0); defaults dropped, params required, test_sim_session caller
fixed + comment; play.py docstring-only correction; filler-pack cache leg w/ tag-only-fingerprint
mutant dead). Suite 1347/3-base-reds/1-skip (skip count 2→1 = fish gate revived).

**Lane A delta re-review of `138770e`: PASS-WITH-ISSUES** (both mutation-kills replicated in-process;
bands byte-identical hash-compared; play.py AST-identical modulo docstring; `_derive_n` pin proven
machine-independent). Findings: **AD-1 MED** — parity gate omits `is_opener` (production always passes
a real boolean; None never selects a role-tagged node): replayed 3973 preflop decisions → 87
divergences (2.2%) at N-3BSTRATA vs_3bet nodes; the five seeds pass by luck. **AD-2 MED** — the AF
escalation shape (`re-measure only on small-n breach`) lets a stable-n breach that reads in-band at
small n pass silently; WTSD asserts stable-n only, and the comment claimed they matched. AD-3 LOW
comment falsehoods created by the fold (`_derive_n` "Scale N DOWN", `budget_s` "load-bearing",
"~650-700"). AD-4 LOW fish "not noisy" conflates determinism with robustness (margin ~1.1σ;
independent-stream probes 0.5049/0.5222/0.5072 all pass). AD-5 LOW filler-leg asserts identity only.
AD-6 informational: pre-existing reveal-test rng-order flake, delta ruled out by A/B seed test.

**ORCHESTRATOR DELTA-FOLDS applied directly (wave-5 precedent, disclosed) → commit `e6fbf8a`:**
AF leg now asserts at stable n=4000 unconditionally (true WTSD rule; small-n read report-only in the
message); parity gate threads `is_opener=play._preflop_opener(state)==position`; filler leg also
asserts the VALUE moved; all four comment falsehoods corrected. Verified: bands 5-pass/1-skip
(maniac WTSD only), 3 instrument gates pass, sim_session 35 pass, ruff clean. **Lane A
review-complete at `e6fbf8a`.**

### Landing A (in progress)

Re-record on the lane A tip (single recorder): coverage_baseline → **1224/339 (27.7% cumulative vs
immutable 28.3%, unchanged from wave-5's intended position)** — exactly the record wave-5 meant to
ship, confirming the base reds were the LOST #153 re-record, and lane A does not touch that stream
(its generator imports no harness code). Limper belt re-pinned to measured (production-only stream —
values identical on base and tip: pure lost-record restoration, e.g. ('UTG2',1) 87, ('LJ',1) 128).
N200 goldens re-recorded with a two-cause disclosure: base staleness + the R-L2 harness-stream change
(station AF 0.2628→0.3241 base→tip = instrument repair, zero production code).

## LANDINGS + PRs (2026-08-01) — wave COMPLETE

- **Lane A landed** → landing commit `86ee32c` (re-record above). Full suite on tip:
  **1350 pass / 1 skip (maniac WTSD deferral) / 0 fail — first fully green state since the wave-5
  merges.** Pushed by OID → **PR #155** (base main).
- **Lane B landed** → clean rebase onto `86ee32c`, landing-fold commit `a2ff452` (stale
  `personas_postflop.py:841-844` price comment corrected — the convergent refuter-MED/theory-LOW;
  W1 contract deferral marked CLOSED; blend docstring gains MERGED-STATE readings). Merged-state
  blend gate PASS: **maniac 0.3054, CI [0.288,0.323] — fully inside [0.25,0.35]: lane A's repaired
  harness dissolves the pre-repair floor-straddle** (margin-relative follow-up stays FILED); lag
  0.4934. Fixtures green on tip (estimator displaces nothing). Pushed by OID → **PR #156**
  (stacked on #155).
- **Lane C landed** → clean rebase onto `a2ff452`, landing re-record commit `84241b5`: coverage
  byte-unchanged 1224/339 (**27.7% cumulative vs immutable 28.3%, −0.6pp — position held through
  the whole wave**); N200 goldens: ONLY the maniac row moves (2.6812/0.34/0.5782 →
  2.5522/0.4468/0.6019, clean attribution to its own vs_4bet mixes); limper belt re-pinned (stream
  displacement). Full suite on final tip: **1355 pass / 1 skip / 0 fail.** Pushed by OID →
  **PR #157** (stacked on #156). **Merge order #155 → #156 → #157.**

### Wave-6 filings (roadmap NEXT candidates)
- **§3 contract amendment (lane C theory CT-1+CT-2, one filing):** T1/T2 need the "villain covers
  B / stacks-cap" caveat (wrong at every re-raise-jam node — exact break-even uses the CAPPED
  final pot); T3 needs the scope line "identities assume all-in equity realization; at a node
  leaving postflop play T3 bounds a RAW price and a realization discount must be stated".
- **Margin-relative blend-gate self-check** (`half_width < min(rate−lo, hi−rate)`) — lane B theory
  T-1; structural even though the merged-state maniac reading now clears.
- **Tag/lag overbet-plateau CONTRACT-DEFECT → W4-b** (lane B theory T-2): tag continues 53.6% w/
  mid pair vs 1.5×-pot (T3 break-even 60%) — price LAW exists, LEVEL target absent; fit
  `call_looseness` on size-bucketed FtC; extend or explicitly-absent the §5 slope row.
- **W4-b watch adds:** maniac WTSD deferral now reads 0.588-0.593 on the trusted ruler (band
  (0.34,0.50) frozen); fish WTSD gate RESTORED LIVE at 0.5082 (thin ~1.1σ floor margin — a red
  here means re-measure at more seeds first).
- Pre-existing reveal-test rng-order flake (`test_reveal_hand_raises_on_missing_or_incomplete_hand`,
  1-in-14 runs) — delta-review ruled it not-this-wave's; small ticket.

### Wave learnings
(1) **Squash-merge chains can LOSE a landing re-record** — main b54fe6e was red on all 3 seeded
fixtures with nobody noticing; verify fixture greenness on main immediately after a wave's merges.
(2) The repaired harness retro-actively invalidates several pre-repair instrument readings — the
wave-5 "maniac blend CI straddles the floor" and lane C's "WTSD margin 0.019" both dissolved on the
trusted ruler. (3) Prose-only fold rounds can introduce NEW false claims (lane C's lever-chain) —
delta re-reviews on fold commits earn their cost.

**Lane C theory: GO-WITH-ISSUES.** Adjudications: call .30 vs dossier .35 = OVERRULED as category
mismatch (dossier row is the NODE aggregate; 77-99 carry 3.16% arrival mass; shipped aggregate call
.3454 within .005 of target, closer than pre-slice; .35 per-class would overshoot); realism = yes,
in-character, if anything conservative (roster-pooled 4-bet range gives 77/99 equity .52/.56 — folding
60% was the unrealistic behavior); WTSD-edge worry OVERRULED as blocker (dissolves into lane-A owner
ruling; direction-of-travel note for W4-b recorded). Findings: **CT-1 MED CONTRACT-DEFECT** — T1 jam
threshold is 0.447 not 0.419 (hero behind = 90.1 not ~92; villain has only 76.24 and CANNOT cover B —
§3's T1/T2 lack the "villain covers B" caveat, wrong at every re-raise-jam node; slice conclusion
STRENGTHENED a fortiori) → fold docstring numbers + FILE §3 caveat. **CT-2 MED CONTRACT-DEFECT** — T3
is an all-in identity used at a node leaving SPR ~1.5 OOP; contract supplies no realization term (shipped
behavior survives any plausible discount: .36×.80=.288>.283) → FILE §3 scope amendment (one filing with
CT-1). **CT-3 MED** — "tightest range" claim FALSE: nit {AA.5,KK.3,QQ.1}/fish {AA.5} 4-bets give 77-99
only ~.19 equity (fails price by 9pts) but carry 0.6% combined mass vs maniac's 34.7% → fold: rewrite as
mass-weighted claim naming nit/fish as the real tight tail. **CT-4 LOW** — call<jam gate hard-freezes the
unquantified realization premise → fold: soften message to DIRECTIONAL. Convergent with Codex C-1/C-2
(same sizing-prose + T2-arithmetic family). Discipline all clean (red-first confirmed at base; one-sided
bounds unwidened; estimator parity automatic via shared pack read).
