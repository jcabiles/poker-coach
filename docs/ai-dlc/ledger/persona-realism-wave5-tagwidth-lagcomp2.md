# Wave 5 ledger — N-TAGWIDTH + N-LAGCOMP2 (2026-07-31)

Two parallel worktree lanes off main `e5e08b6`, single fixture-recorder at landing, triple review per slice
(refuter + persona-realism-theory-reviewer + Codex gpt-5.6-sol), findings adjudicated here — never auto-folded.

- Lane 1 = **N-TAGWIDTH** (`feat/persona-realism-n-tagwidth`, $TMPDIR/wt-tagwidth): trim tag per-seat RFI to dossier envelope.
- Lane 2 = **N-LAGCOMP2** (`feat/persona-realism-n-lagcomp2`, $TMPDIR/wt-lagcomp2): lag CO/BTN/SB offsuit→suited swap, width-neutral.

---

## Lane 2 — N-LAGCOMP2 (build commit `6bc076f`)

Shipped: exactly width-neutral offsuit→suited swap at CO/BTN/SB in `content/personas/ladders/lag.unopened.json`
(spec 1.1.0→1.2.0), re-emitted `content/personas/lag.json` 1.3.0→1.4.0 (other 6 seats byte-identical).
Suited 17.01→20.63 / 19.91→23.53 / 17.01→19.73 (strict class-superset of tag at ≥ weight, 66/78/63 classes);
offsuit funded from weak-kicker bottoms (BTN −J4o/T5o/96o/86o class-level). Pairs untouched. Gates:
`_LAG_SUITED_FLOOR`+`_LAG_OFFSUIT_CEILING` extended to CO/BTN/SB (all six values red at e5e08b6) + computed
lag≥tag suited comparison (tag side read at test time — auto-adapts to lane 1's trim). rr_emit anti-triviality
corpus 132→135 (+7 BTN suited classes, −4 offsuit; arithmetic verified by all three reviewers).
Population (paired 5-seed, n=1500): PFR 17.04→17.36 (§5 floor 17 — moves UP off the floor), VPIP 23.59→23.85,
gap 6.55→6.50. Blend 0.4823 @4000 / 0.4651 @12000 (mid-band, up from base), component pin 0.6170.
Suite 1335/3/2 — reds = the 3 seeded fixtures only.

### Adjudication

| id | src | sev | finding | ruling |
|---|---|---|---|---|
| C-1 | Codex | MED | Comparative gate aggregate-only — class-superset claim ungated (width-neutral mutation could drop a tag class); offsuit preservation tuple omits SB | **FOLDED** — class-by-class superset leg added (computed both-packs-at-test-time); SB added to `_LAG_OFFSUIT_GE_TAG_SEATS` |
| C-2 | Codex | LOW | Wave-3 blend comment figures stale at this HEAD (0.4622→0.4823 @4000) | **FOLDED** — current readings appended, dated; originals kept as history |
| C-3 | Codex | LOW | Red-at-HEAD provenance comment cites `HEAD` — irreproducible post-commit; baseline is e5e08b6 | **FOLDED** — comment now names e5e08b6 |
| R-1 | refuter | HIGH | 3 fixture reds leave `verify.sh` red; prior merged slice re-recorded in-commit | **OVERRULED — wave single-recorder law** (brief mandated leaving them; orchestrator re-records once at landing). Refuter's own measurement shows the re-record is benign: graded ratio would IMPROVE 24.98%→26.51% |
| R-2 | refuter | MED | lag.json `_doc` has no 1.4.0 entry; retained 1.3.0 table now states values the pack no longer ships | **FOLDED** — 1.4.0 entry added, 1.3.0 table annotated (convergent w/ T-4) |
| R-3 | refuter | LOW | Docstring tag totals truncated (48.41 vs actual 48.42 / 58.22 / 46.61) | **FOLDED** |
| R-4 | refuter | LOW | "offsuit ≥ tag all 9 seats" claim overstated — gate tuple covers 4 seats | **FOLDED** (docstring corrected; tuple now 5 seats per C-1) |
| T-1 | theory | MED | **CONTRACT-DEFECT**: per-seat opening ladder authored against NO target — §5 has no RFI-by-seat row, §5a names it format-sensitive; arrival funnel (CO .132/BTN .074/SB .015) means late seats carry ~13.5% of lag first-in mass, so ladders can drift wide unnoticed. Lag CO 53.1/BTN 66.0 now nearer maniac (63.5/73.3) than tag. All existing gates are intra-roster relations — satisfiable by whole-roster upward drift. No lane exists for the lag half after N-TAGWIDTH lands | **ACCEPT-AND-FILE** — strengthens the standing §5 per-seat-RFI contract filing (wave-3/4); NEW roadmap candidate **N-LAGWIDTH** (lag late-seat width vs a dossier-sourced target; blocked on the contract filing + W-ARR arrival instrumentation stance). Not fixable in a width-neutral slice |
| T-2 | theory | MED | Landing must report cumulative graded-coverage delta vs immutable snapshot (§11 item 14) AND adjudicate the lag AF golden move 2.6→2.29 @n=200 (AF is HARD §5 3–4) — noise vs real, one sentence | **ACCEPT — landing duty** (coverage delta is standard wave practice; AF checked at stable-n before fixture bump) |
| T-3 | theory | LOW | SB opens 43s@1.0 but not 53s — inherited verbatim from tag.json SB row (lag honours superset); root cause upstream | **ROUTED to lane 1** (N-TAGWIDTH fold round examines tag SB row); no lag change — would break width-neutrality |
| T-4 | theory | LOW | Pack `_doc` missing 1.4.0 entry | **FOLDED** (= R-2) |
| T-5 | theory | note | BTN suited saturation: full universe @1.0 adjudicated CORRECT for lag at 66% open (tag already opens all 78 classes, 7 mixed); optional 32s mixed bottom offered | **DECLINED** — composition confirmed; saturation noted (BTN suited can never rise again; randomization now 100% offsuit) |

Fold round = commit `d700af4` (test+doc only, zero content bytes — verified). Superset leg measured RED at
e5e08b6 (short 12/14/9 tag classes at CO/BTN/SB), green post-slice; `_LAG_OFFSUIT_GE_TAG_SEATS` now 5 seats;
blend annotation re-measured (0.4823 @4000 / 0.4651 @12000, pin 0.6170 — moves AWAY from the floor). Suite
unchanged 1335/3/2, same 3 fixture reds. Documented accepted failure mode: a future tag change that ADDS a
suited class the lag lacks reds the leg in the lag's file.

Delta re-review (refuter, fold commit only): **PASS-WITH-ISSUES** — everything reproduced (content byte-identity
`True` with `_doc` popped; superset-leg red counts replayed exactly at e5e08b6; no assertion weakened). One LOW:
gate docstring says the 17 lighter-weight classes sat at tag 0.5 — actually 14/17 at tag 1.0 (gap UNDERSTATED,
no assertion affected). Ruling: **orchestrator fixes the one docstring line at landing** (disclosed here), no
third builder round. **Lane 2 review-complete at `d700af4`.**

### Lane 2 LANDED → PR #152

Landing commit `8d6991c` (orchestrator, single recorder): coverage 1269/317→1275/338 — cumulative graded
ratio **26.5%** vs immutable start 28.3% (−1.8pp, strongest recovery since wave-3's −3.8pp low; graded ratchet
UP 317→338, mapper-track class, disclosed). Limper belt re-pinned (all `_WANT_*` shapes fire). N200 goldens:
only lag+nit rows move; **T-2 duty done** — lag AF adjudicated REAL composition at stable n=1200
(2.8121→2.5176, inside HARD band (1.5,4.5)). Delta-review LOW docstring fix folded. Suite 1338/0/2, ruff clean.
Branch `feat/persona-realism-n-lagcomp2` pushed by OID; **PR #152 open**.

---

## Lane 1 — N-TAGWIDTH (v1 commits `23f4dc7`+`98c3693`) — REWORK ORDERED

v1 shipped an offsuit-only trim (HJ/CO/BTN/SB; BTN 58.22→46.46). Triple review:
**refuter PASS-WITH-ISSUES** (all mechanics verified: emitter ≡ pack, red-at-HEAD real, no gate weakened,
BANDS re-anchor legitimate DIRECTIONAL, sweep reproduced exactly) · **theory NO-GO (3 HIGH)** ·
**Codex FAIL (1 HIGH)** — convergent on two core defects:

| id | src | sev | finding | ruling |
|---|---|---|---|---|
| T-H1 ≡ C-H1 | theory+Codex | HIGH | Envelope gate transcribed from the GITIGNORED dossier (BTN 42–48) contradicts the COMMITTED `rfi-seat-provenance.md` synthesis (BTN 30–45, verified anchor 40; SB 15–36) — the gate's floor excludes the correct solver value; provenance doc says no full row is gate-grade, shape only | **ACCEPTED** — rework: targets from committed provenance; one-sided ceilings + ordinal shape gates only |
| T-H2 | theory | HIGH | BTN offsuit (18.10) now BELOW SB offsuit (19.00) — inversion created by the slice, invisible to its own gates (blinds scoped out) | **ACCEPTED** — rework restores BTN > SB offsuit + gate |
| T-H3 ≡ C-M2 | theory+Codex | HIGH/MED | Offsuit-only constraint deleted the range's BEST marginal hands and kept the WORST (BTN opens 72s/32s @0.5, J2s/T2s @1.0; folds K8o/98o); cliff falls 2.7257 < nit 2.9480, inverting cliff(TAG)>cliff(NIT) | **ACCEPTED — owner escalated (AskUserQuestion) → REWORK authorized**: `_TAG_SUITED_FLOOR` may be lowered at late seats (junk suited retired, good offsuit restored); walks back part of N-TAGCOMP's suited push at HJ/CO/BTN/SB, owner-approved |
| T-M1 | theory | MED | Infeasibility blocker over-confident: PFR-floor edge is DIRECTIONAL; cascade cost brackets the floor (0.7pp adjusted – 2.1pp unadjusted); blocker (1) "requires cutting suited" only true at UTG — real argument is HJ-in-band ⇒ no AKo absurdity | **FOLDED into rework** (_doc restated); early-ladder-vs-floor conflict FILED as owner contract question |
| T-M2 | theory | MED | Only UTG strictly requires suited cut — per-seat budgets misstated | **FOLDED into rework** |
| C-M3 | Codex | MED | Suited preservation gate aggregate-only — can't prove class identity | **FOLDED** — class-level suited pin per trimmed seat in rework |
| R-M1 | refuter | MED | Fixture-red deferral has no in-repo trace | **ACCEPTED** — landing commit carries the provenance note (wave law) |
| R-M2 ≡ C-M4 | refuter+Codex | MED | Pack _doc claims false ("K5o–K9o gone", "broadway-or-ace"; corpus list names 13, actual 9 drops) | **FOLDED into rework** |
| C-L5 / T-Q2c | Codex/theory | LOW | SB 43s-in/53s-out (inherited, lane-2 T-3 routed here) | **CLOSED per theory**: connectedness exemption legitimately applies (43s true connector); not a defect |
| R-L1..4, C-L6 | refuter+Codex | LOW | UTG1 13.73 not 13.27; seat-avg 30.4843 not 30.38; 12.67−2.1=10.57 (1.43pp); BANDS edges not exactly ±2.0 | **FOLDED into rework** |

Owner decision (2026-07-31, noobified AskUserQuestion): **"Rework the slice"** — suited authority granted,
targets re-derived from committed provenance, one more build + review round.

### v2 rework (commit `129e8e3`) — second triple review

v2: junk-suited retired at HJ/CO/BTN/SB + standard offsuit restored (BTN A2o+/K9o+... 43.89 inside 30–45,
SB 34.39 inside 15–36, cliff 3.0632 > nit, BTN offsuit > SB) + UTG trimmed 17.04→14.33 (builder deviation,
cliff-forced) . Verdicts: **refuter PASS-WITH-ISSUES** (all 18 width numbers, sweep, corpus 126→97 reproduced
exactly) · **theory NO-GO w/ explicit path to GO** · **Codex FAIL**.

| id | src | sev | finding | ruling |
|---|---|---|---|---|
| T2-H1 ≡ C2-H1(cliff leg) | theory | HIGH | Cliff gate hard-asserts an [UNVERIFIED] cross-persona ordering — §5a forbids; provenance's safe-to-gate list is within-persona only. Gate was load-bearing (sole stated reason UTG moved). **Overrules the v1 remedy in part** | **FOLDED** — cliff demoted to REPORT-ONLY; UTG trim re-justified on provenance direction; lag cliff inversion (2.6318 < tag, pre-existing) noted + FILED to lag lane |
| T2-H2 ≡ C2-M3 | theory+Codex | HIGH/MED | UTG recreated v1's BTN defect at the highest-arrival seat: folds AJo/ATo/KQo/KJo, raises 87s/K7s@0.5, A2s-A8s@1.0 | **FOLDED** — UTG recomposed: suited tail retired (~2.7pp), AJo (+KQo if width allows) restored, ~width-neutral |
| T2-H3 ≡ R2-H1 | theory+refuter | HIGH | Fixture reds unrecorded + no coverage delta | **OVERRULED-AS-DEFECT / ACCEPTED-AS-DUTY** — wave single-recorder law; landing carries re-record + cumulative delta (same as lane 2) |
| C2-H1 (doc leg) ≡ T2-M3 | Codex+theory | HIGH/MED | Gates cite UNTRACKED rfi-seat-provenance.md — unauditable from repo | **ACCEPTED — BLOCKING landing duty**: orchestrator commits the provenance doc before/with the lane-1 PR; ceiling comment gains "unattributed band edges, no-regression bounds only" line |
| C2-H2 ≡ R2-M1 | Codex+refuter | HIGH/MED | PFR NOT statistically cleared: mean 12.0525, 95% CI [11.88, 12.23] straddles 12; 4/10 seeds below (min 11.558); ~41% per-seed breach odds; AND the floor is unwatched (nothing reds at 11.9 — metric #3 never compared to §5) | **ADJUDICATED NO-STOP per contract** (theory T2-Q3: §5a PFR band edges DIRECTIONAL; §5 "no RP6 number becomes a test gate until W4-b"; instrument is not the §5 reference pool — no frozen-band breach exists to escalate). **FOLDED**: all "inside §5"/"frozen floor" wording replaced with the full disclosure + DIRECTIONAL citations; **FILED to W4-b watch list: tag PFR straddles 12** |
| R2-M2 | refuter | MED | "UTG forced" framing self-selected (BTN kept at 43.89 vs tag-specific guidance ~35-40; at BTN 40 cliff needs UTG<13.57) | **FOLDED as _doc context** (road-not-taken recorded); moot once cliff demoted |
| R2-L1 | refuter | LOW | **CROSS-LANE RED**: v2 silently ADDED 53s at tag SB — lane-2's per-seat class-superset gate (merged path) reds on exactly this (lag SB lacks 53s) | **FOLDED — 53s REVERTED** (theory had already ruled 43s-in/53s-out not-a-defect via connectedness exemption) |
| C2-M4 | Codex | MED | Half-weight offsuit tier unpinned (98o→87o swap passes every gate) | **FOLDED** — class+weight pin extended to the 0.5 tier |
| T2-M1 | theory | MED | `_TAG_UNTOUCHED_SUITED_PIN` two-sided exact forecloses the escalated early-seat trim | **FOLDED** — one-sided leak guard |
| T2-M2 | theory | MED | LJ/HJ/CO 1.4pp plateau (CO÷LJ 1.10 vs sources 1.27-1.85) — seam consequence, invisible to strict-increase gate | **ACCEPT-AND-FILE** — joins the early-ladder owner escalation: decision is "PFR under 12?" AND "may the LJ/HJ/CO plateau ship in the interim?" |
| R2-L2, C2-L5, T2-LOWs | all | LOW | Stale v1-era notes; suited-floor-below-pre-N-TAGCOMP disclosure; "frozen" wording | **FOLDED** |

### v3 fold (commit `9485aa4`→rebased `a8267c6` family) + dual delta re-review + LANDING → PR #153

Fold shipped: UTG recomposed 14.18 (offsuit ATo+/KQo restored to HEAD's 4.52; suited tail + wheel aces
retired — RR-EMIT top-anchored-row limit, disclosed); SB 53s reverted (cross-lane superset gate verified
GREEN against the ACTUAL merged #152 lag pack); cliff report-only (prints nit 2.9480 / tag 3.0957 /
lag 2.6318); one-sided pins; honest PFR CI disclosure (refuter delta reproduced the corrected sweep to the
digit: 12.0392 ±0.2091, CI [11.910, 12.169], 4/10 seeds below, min 11.750 — the v2 "12.05 ±0.24" was a
wrong reading the builder caught itself: scratch harness resolved `import app` to the MAIN checkout).

Delta verdicts: **theory GO-WITH-ISSUES — NO-GO CLEARED** (UTG clears the HIGH, "net realism gain over the
pre-slice A2s+-at-full-weight UTG"; cliff demotion adjudicated correct, v1 prescription withdrawn) ·
**refuter PASS-WITH-ISSUES** (mutation-tested: 98o→87o swap now fails; one-sided directions verified).

Delta folds applied by ORCHESTRATOR at landing (disclosed): `test_tagwidth_utg_offsuit_block_pinned`
(theory delta M1 — exact per-tier ATo+/KQo pin, the one rewritten shape without a pin); UTG dropped from
`_TAG_SUITED_FLOOR` (theory delta L3 — de-facto two-sided freeze); 0.75→0.74 factor (refuter delta L1);
"§5a marks PFR row directional"→"VERIFIED (conf MEDIUM) w/ DIRECTIONAL band edges" (theory delta L4);
"COMMITTED" wording dropped (theory delta L5). Theory delta M2 (RR-EMIT needs a per-row except/keep token
for non-contiguous shapes — wheel-ace approximation recurs at every emitter-authored seat) **FILED**.

LANDED stacked on the #152 tip (clean rebase, then landing commit `b674e40`): rfi-seat-provenance.md
**COMMITTED** (137 lines — the blocking Codex/theory HIGH); fixtures re-recorded on the stacked tip —
coverage 1275/338→1224/339, cumulative **27.7%** vs immutable 28.3% (−0.6pp, best position since wave-3's
−3.8pp; ratchet UP again); all six N200 golden rows move (tag re-deals every tag pot); tag n=200 AF
2.5→1.53 adjudicated small-n NOISE at stable n=1200 in separate processes (2.5134→2.4711, band (1.4,3.6) —
same-process reads invalid per the filed `_STATS_EXT_CACHE` defect, re-confirmed live this landing).
Suite 1346/0/2, ruff clean. **PR #153 open, base = feat/persona-realism-n-lagcomp2 (stacked; merge #152
first).**

---

## Contract-filings pass → PR #154 (stacked on #153)

Owner adjudicated both forks via noobified AskUserQuestion (2026-07-31): **§5 LAG ruling = "VPIP + gap
primary, PFR derived/DIRECTIONAL"** (over restating PFR 16–23 or deferring to W4-b) · **per-seat RFI =
"provenance-governed"** (rfi-seat-provenance.md as one-sided bounds + within-persona shape only; over a
numeric per-seat band table the source itself calls unsettled). Both recorded in
`docs/ai-dlc/contracts/persona-realism-theory-contract.md` (§5 + §5a), no band value edited,
`test_contract_provenance.py` 6/6 green. Doc-only, owner-dictated content — no separate review round.

**Wave-5 merge order: #152 → #153 → #154.** Worktrees to clean after merges: /tmp/claude-501/wt-lagcomp2,
/tmp/claude-501/wt-tagwidth (holds both later branches).
