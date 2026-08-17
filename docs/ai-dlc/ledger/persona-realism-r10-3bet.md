# Finding ledger — R10-3BET

## Spec-stage dual review (2026-07-30) — refuter (Claude) + Codex `gpt-5.6-sol`, adjudicated

Target: `docs/ai-dlc/specs/r10-3bet.md` v1 + `docs/ai-dlc/contracts/r10-3bet.md`.
Refuter verdict PASS-WITH-ISSUES (3) · Codex verdict FAIL (7). No reviewer-vs-reviewer conflicts;
where reviewers disagreed with the artifacts, code/docstrings adjudicated. All accepted findings
folded into spec v2 + contracts same day.

| ID | Src | Sev | Finding | Adjudication |
|---|---|---|---|---|
| R1 | refuter | HIGH | Frozen postflop BANDS (`test_persona_postflop_bands`, `test_personas_postflop.py:2382-2400`) recompute from the same packs; spec had no contingency; bands re-anchor is W4-b-only | **ACCEPTED** — risk register added: breach = STOP + escalate to owner, never widen/re-record |
| R2 | refuter | MED | Maniac cross-val test (`:3679-3717`) rng-coupled to whole pack set, absent from file list; old wording named PRE2 sole re-recorder | **ACCEPTED** — listed; lane rule (open slice = sole re-recorder) supersedes stale PRE2 wording |
| R3 | refuter | LOW | Nit 4-bet headroom unstated; authoring could invert gate ② by trial-and-error | **ACCEPTED** — stated: stay comfortably below tag ~1.69% |
| C1 | codex | HIGH | Strata labels inverted: cold facers = `first_hits`; `all_hits − first_hits` = re-entrants ≈ openers (the externally comparable stratum). Spec v1 + contracts §5 had it backwards | **ACCEPTED** (verified vs docstring `:2579-2591`); rider "add prior-action role tracking" **REJECTED** — docstring's ≈opener approximation is the accepted instrument, no new instrumentation this slice |
| C2 | codex | HIGH | Promised six-persona stratified CI report cannot be produced: formatter is pooled `all_hits`, no CI math, exercised for maniac only | **ACCEPTED** — new report-only helper (six personas, both strata, denominators, Wilson 95% CIs) |
| C3 | codex | HIGH | File list missed `_PRE_M3_FIRES` (`test_limper_coverage_belt.py:175-220`, not test_personas_postflop) and tag's pinned exact vs_3bet 4-bet posterior (`test_range_estimate.py:190-198`) | **ACCEPTED** (both verified) — added to files table |
| C4 | codex | MED | Owner-frozen station zero-4bet / fish AA-only identities unguarded by any gate | **ACCEPTED** — deterministic freeze assertions added as gate ③ |
| C5 | codex | MED | "Combo-weighted 4-bet share" ambiguous under overlapping tiers (double-count risk) | **ACCEPTED** — formula pinned: Σ(combo_count × effective FIRST-MATCH 4bet prob)/1326, 6/4/12 |
| C6 | codex | MED | R9-DEFENCE = FIVE questions (`roadmap:1875`), not six; both design-pass reports ALREADY EXIST locally (`reports/r9-defence-design.md`, `reports/r10-tail-design.md`) | **ACCEPTED** — spec corrected; design-pass tickets collapsed to Director adjudication of existing reports |
| C7 | codex | LOW | Contracts overstated `_node_ordering` as "one wildcard per facing"; validator enforces AT MOST one (`models.py:256`) | **ACCEPTED** — wording fixed |

## Build stage (2026-07-31 — PR #143, commits 2696969 + 79a66c8)

### Done-condition (gate ① before/after)

- **Before (HEAD 38707c9):** nit `vs_3bet` node covers AA/KK only; effective continue weight on
  QQ/AKs/AKo = **0** (verified by loading the HEAD packs: `QQ=0.00 AKs=0.00 AKo=0.00`). The
  756-hand corpus's 20/20 opener folds stand.
- **After:** QQ continue 0.60 (call .5 + 4bet .1), AKs 0.50, AKo 0.40 —
  `test_r10_3bet_defect_gate_nit_continues_premiums` passes; the same test FAILS against HEAD packs.

### Authored provenance (dossier rows, quoted from
`docs/ai-dlc/research/persona-realism-artifacts/playstyle-research/*.md`)

| Pack | Dossier anchor | Authored response |
|---|---|---|
| nit | "Fold 68–82 · Call 12–25 · 4-bet 5–10 of opportunities · Core 4-bet range KK+, AKs · QQ/AKo addition 0–25%" (nit.md:402-411) | Cliff-edge tiers KK .7c/.3 4b · AA .5/.5 · QQ .5c/.1 4b · AKs .5c · JJ/AKo .4c · TT/AQs .25c; share 0.41% |
| tag | "Fold to 3-bet after opening 52–65% · 4-bet 10–18% · 4-bet range 1.5–3.0% of hands" (tag.md:290-293) | AA/KK 4b 1.0 · QQ/AKs .5/.5 · AKo .35 4b/.5c · A5s/A4s .35 4b blockers · share 1.81% (in band) |
| lag | "Fold 43–53 (live 38–50) · 4-bet 10–16% · bluff share 25–50%" (lag.md:325-333) | QQ/AKs .7 4b · AKo/JJ .35/.55 · A5s–A2s .35 4b bluff tier · full suited-ace continue coverage · share 2.33% (below the 3.0–5.5 hands band — filed in N-3BSTRATA as R-4) |
| maniac | "After opening and facing a 3-bet: fold 20–30 · call 45–53 · 4-bet 25–27" (maniac.md:443-448) | QQ+/AKs 4b 1.0 · tier2 .6 4b · tier3 .45 4b · junk tiers 4b .1 (any-two 4-bet bluffs, deliberate identity) · share 15.16% incl. catch-all |
| station | "Fold after own open facing 3-bet 25–40/35–50 · call 58–73/47–63 · 4-bet 1–3%" (calling_station.md:319-321) — **owner froze 4-bet to ZERO** | Long shallow call tail 1.0/.8/.6/.45, no 4bet key anywhere |
| fish | "Open-raised, facing 3-bet: fold 15–25 (live) · call 63–73 · 4-bet 8–12" (passive_fish.md:338) — **owner froze 4-bet to AA@0.5** | Call tiers 1.0/.85/.7 (dossier weights RESTORED after the R-3 adjudication); AA mix last (interleave-monotonicity, policy-neutral) |

### Fixture re-records (slice-authorized, stream displacement)

- `coverage_baseline.json`: 1219/330 → **1218/332** (cumulative vs the immutable start snapshot
  349/1233 → −17 graded; the slice's own contribution is +2 — adjudicated: mapper-orthogonal
  stream displacement, flagged not silent, per §11 item 14).
- `_GOLDEN_STATS_N200`: re-recorded; tag AF falls off the n=200 tripwire (None — call denominator
  under the floor at that n; the population AF band still gates it).
- `_PRE_M3_FIRES` (limper belt): re-pinned; every `_WANT_*` coverage shape still fires.
- tag exact 4-bet posterior (`test_range_estimate.py`): {AA,KK,AKs@1.0}∪{AQo@.4}∪{A5s@.4} →
  {AA,KK@1.0}∪{QQ,AKs@.5}∪{AKo@.35}∪{A5s@.35}; AA/AKo=10/7, AA/QQ=2 hand-verified. A4s authored
  but unreachable from the tag UTG open range — correctly absent from the posterior.
- Maniac cross-val band [0.32, 0.51]: held without re-record.
- **BANDS dict: UNTOUCHED** (risk register honored). passive_fish WTSD assertion skipped
  (owner-approved defer, below).

### Owner adjudications

1. **passive_fish WTSD defer (frozen 0.50 floor):** 0.5104 → 0.4873. Attribution: fish-node-only
   revert reads 0.4949; trimmed tiers 0.4912; dossier tiers 0.4873 — all within noise, so the
   fish's own node is a minor contributor and the WTSD-chasing trim was REVERTED (theory R-3).
   Cross-persona composition is the driver; maniac-junk-4-bet removal probe made it WORSE (0.4888).
   Deferred to W4-b beside the maniac's (band VALUE untouched).
2. **Maniac/lag opener-stratum over-fold (theory R-1, HIGH):** ACCEPT-AND-FILE → roadmap NEXT item
   `N-3BSTRATA` (arrival-strata split, E1-b family). Measured grid recorded there with CIs.

### Fan-in review adjudications (refuter + theory reviewer + Codex gpt-5.6-sol)

| ID | Src | Sev | Finding | Adjudication |
|---|---|---|---|---|
| F-1 | refuter | HIGH | Docs/ledger/roadmap not yet written at review time | FIXED — this section + roadmap updates |
| F-2 | refuter+Codex | MED/LOW | Maniac 4-bet share docstring said 5.66%; true value 15.16% (catch-all mass overlooked) | FIXED — docstring corrected; catch-all mass kept as deliberate identity (gap-neutral) |
| F-3 | theory R-1 | HIGH | Maniac/lag opener over-fold | Owner: accept-and-file → `N-3BSTRATA` |
| F-4 | theory R-2 | MED | Station/fish opener readings above bands but instrument-contaminated (limp re-entrants) | NOTED — re-examine when role tracking exists (in N-3BSTRATA) |
| F-5 | theory R-3 | MED | Fish call trim bought nothing; degraded archetype | FIXED — dossier weights restored (0.85/0.7) |
| F-6 | theory I-1 + Codex-1 | MED | Pack versions not bumped | FIXED — all six 1.0.0 → 1.1.0 |
| F-7 | theory P-1 | MED | Coverage delta silent | FIXED — adjudicated above |
| F-8 | theory R-4 | LOW | Lag 4-bet share 2.33% under dossier 3.0–5.5% | FILED — inside `N-3BSTRATA` |
| F-9 | Codex-2 | LOW | `_vs_3bet_effective_policy` omits implicit-fold + uncovered classes | DOC-NOTED — both no-ops for every consumer (docstring explains) |

### Stratified fold-to-3-bet grid (report-only, Wilson 95% CI, memoized _ARRIVAL_N runs; pre-restore run)

```
station: cold n=24 fold .958 [.798,.993] · opener n=21 fold .952 [.773,.992]
lag:     cold n=25 fold .960 [.805,.993] · opener n=27 fold .704→(final run .821) — see N-3BSTRATA
maniac:  cold n=63 fold .492 [.373,.612] · opener n=55 fold .491→(final run .630) — see N-3BSTRATA
nit:     cold n=30 fold .967 [.833,.994] · opener n=16 fold .812 [.570,.934]  (dossier 68–82 ✓)
fish:    cold n=34 fold .882 [.734,.953] · opener n=17 fold .412 [.216,.640]
tag:     cold n=24 fold 1.000 [.862,1.0] · opener n=23 fold .739 [.535,.875]
```
n underpowered by design — REPORTED, never gated. Cold facers folding heavily is correct (junk
arrival vs two raises); the opener-stratum gaps for maniac/lag are the `N-3BSTRATA` filing.

### Verify

`1154 passed, 2 skipped` (maniac + fish WTSD deferrals) · ruff clean · RR-LINT 3/3 · maniac
VPIP−PFR gap 0.083 (< 0.10 gate) · maniac cross-val agg in [0.32, 0.51].

## T7 — design-pass adjudication (Director, 2026-07-31)

Both wave-parallel design passes were found ALREADY ANSWERED in local reports
(`docs/ai-dlc/reports/r9-defence-design.md`, 627 lines, five questions;
`docs/ai-dlc/reports/r10-tail-design.md`, 651 lines, both tail questions) — discovered at spec
review (Codex C6). Adjudication: **ACCEPT both.** Verified: measured attribution at pinned commit
`803e9dc`; mechanisms softmax-law-compliant (conditioned merit factors pre-normalization, no flat
scalars); N-logit-proofed via two-stage raise-neutrality / additive-exponent guards; red-first
harnesses with HEAD-failing defect gates; R9-SIGNAL's three amendment pins verified SHIPPED in #141
(`aggressor_bet_prev_street` flat kwarg, `personas_postflop.py:658`). Filed to roadmap NEXT:
`R9-DEFENCE-a` (blocked on N-logit), `R10-TAIL-a1`, `R10-TAIL-b1`; `R9-DEFENCE-b` pre-registered.
The ⛔ design-question freeze on `R9-DEFENCE`/`R10-TAIL` is lifted in the roadmap. Zero non-doc
diffs from this ticket; reports stay local per convention.
