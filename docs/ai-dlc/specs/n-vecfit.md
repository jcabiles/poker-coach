# Spec — N-vecfit (reshaped): measured fitting rules for the persona fit loop

status: draft-rev2 (rev 1 FAILED dual review — 4 HIGH refuter + 5 HIGH Codex, all adjudicated in
`ledger/n-vecfit.md`; every accepted finding folded below)
slice: n-vecfit · initiative: persona-realism · code pin: origin/main = b63dfaa
shape ruled by owner 2026-08-03: **slim doc amendment — no tool, no engine code, no pack edits**

**Citation convention (rev-2 fix):** code files are cited at commit `b63dfaa`. The ai-dlc docs
(roadmap, specs, contracts, reports) are cited at the **working tree of the main checkout** — the
initiative's docs carry ~551 uncommitted lines beyond the commit, so working-tree line numbers are
the only ones that resolve. All doc citations below also carry anchor text; trust the anchor over
the number.

## One-line goal

Amend `docs/ai-dlc/contracts/persona-realism-fit-loop.md` with measured fitting rules and update
the roadmap so `R9-LOOSEFIT` stops waiting on a vector-fitting tool the evidence does not support —
while enumerating, honestly, what R9-LOOSEFIT still has to build for itself.

## Background — what the measurement established, exactly

The roadmap's N-vecfit entry (working-tree ~:2001, anchor "N-vecfit — make the fit loop
vector-valued") claimed the scalar one-lever-at-a-time fit loop "zig-zags" on the coupled
(`call_looseness`, `aggression`) system and prescribed a vector-valued fitting tool. A pre-spec
measurement (`reports/n-vecfit-premise.md` + its Post-review corrections section + preserved
scripts in `reports/n-vecfit-premise-scripts/`) found, **scoped precisely**:

- **For tag on the (FtC, AF) stat pair, near and far targets, context-aware/line-blind posture,
  with local Jacobian corroboration for nit:** the expensive-zig-zag claim is false. Scalar
  coordinate descent contracts coupling error 5.5× (tag) / 48× (nit) per round
  (ρ = |J12·J21/(J11·J22)| = 0.183 / 0.021; divergence needs ρ ≥ 1 — note ρ ≥ 1 is the threshold
  for failure to *contract*; the signed factor −0.183 predicts *damped alternation*, which is what
  the trajectories show).
- With consistent call accounting (post-review corrected): near target scalar 6 vs vector 5 calls;
  far target scalar 7 vs vector 9 — scalar competitive-to-cheaper, and the premise's prescribed
  fixed-Jacobian Newton arm **failed to converge at all** on the far target (damped ringing past
  its 5-call cap, caused by ~1.45× far-field slope drift).
- The measured hazards are elsewhere: **scalar mispairing** (swapped lever↔stat assignment,
  ρ = 5.47) empirically diverged — `aggression` pinned at its 5.6 runtime cap, `call_looseness`
  driven to 0.155 (an extreme value; that lever has no floor), ending worse than it started.
- **NOT measured:** lag, station (cond(J) = 14.3 caveat), maniac (no authored `call_looseness`),
  stat pairs other than (FtC, AF), the line-aware posture, and cross-persona joint fitting.

The honest conclusion: the vector-tool prescription is unsupported where tested and its central
mechanism (reused Jacobian) is the measured-fragile object. The tool is dropped. The measurement's
transferable value is a set of fitting rules plus an explicit statement of what remains unknown.

## Files to touch (complete list — all docs, no code)

1. `docs/ai-dlc/contracts/persona-realism-fit-loop.md` — the amendment (content below).
2. `docs/ai-dlc/roadmap/persona-realism.md` — (a) the N-vecfit entry (~:2001); (b) the order-of-work
   line (~:2167, anchor "Correct order: `N-logit` → `N-vecfit`"); (c) the dependency-table row
   (~:2203, anchor "Prerequisite of `R9-LOOSEFIT`"); (d) an annotation at ~:2500 (anchor
   "fixable with a vector-valued fit loop") — that line quotes the 250-hand review verbatim, so
   annotate `[premise later refuted where tested — see reports/n-vecfit-premise.md]` rather than
   rewriting history.
3. `docs/ai-dlc/specs/persona-realism-wave-a.md` ~:95-96 (anchor: N-vecfit described as a
   vector-valued, band-moving loop) — same bracketed annotation, no rewrite (historical spec).
4. `docs/ai-dlc/contracts/n-vecfit.md` — prepend a status note: the scan mapped the ORIGINAL
   (tool) shape; §7's "needs a working joint-fit tool" is superseded by this spec; the scan's
   facts remain valid.

## Amendment content (fit-loop doc)

New section "Multi-lever fitting — measured rules (N-vecfit, 2026-08-03)" + light retouch of steps
2–4 to reference it. Required content, every number traceable to `reports/n-vecfit-premise.md`
(including its Post-review corrections) or `contracts/n-vecfit.md`:

- **Rule 1a — pair each lever with the stat it dominates (scalar fits).**
  `call_looseness`→FtC, `aggression`→AF. Mispairing is a *scalar-assignment* failure: swapped
  pairing has ρ = 5.47 and empirically diverged. Check: ρ = |J12·J21/(J11·J22)| < 1.
  **The ρ screen tolerates an approximate or previously measured Jacobian** — the measured margin
  is 5× (0.183 vs 1.0), so a stale J is fine HERE (unlike Rule 2's step sizes, where it is not).
  New persona/stat-pair combinations need a one-time ~2–4-call J measurement, amortized across all
  later fits of that combination; this cost is disclosed, not hidden.
- **Rule 1b — target-pair conditioning (any method, including joint fits).** Distinct hazard:
  near-parallel Jacobian ROWS (e.g. FtC + RaiseShare) make the fit ill-conditioned for scalar AND
  vector methods alike — a joint solve is permutation-invariant, so "pairing" cannot rescue it;
  only re-choosing target stats can. The station's cond(J) = 14.3 on air-heavy ranges is this
  hazard, not mispairing. If no well-conditioned target pair exists, escalate to the roadmap.
- **Rule 2 — fresh slopes for STEP SIZES, never a saved table.** Re-estimate each 1-D slope by
  secant from the last two measurements **with all other levers held fixed between those two
  points** (moving two levers between measurements confounds the secant — measured post-review).
  The harness is nonlinear enough that a base-point slope under-predicts far-field gain ~1.45×,
  which made the fixed-Jacobian Newton arm ring past its call cap while secant-based scalar
  converged. Initial slope: from the Rule-1a J if fresh enough, else one probe step. Caveat: a
  secant across a non-monotone region is unguarded — the study observed only monotone drift; if a
  slope changes sign between measurements, stop and measure a local J.
- **Rule 3 — budget n so the 3σ noise band is smaller than the move.** At n = 48,000: FtC band
  ±0.0234, AF ±0.0852; a ±25% `call_looseness` step moves FtC ≈ 0.032 (|J11|·ln 1.25) ≈ 1.35
  tolerance units — barely resolvable. The harness is deterministic-seeded and memoized per
  pack-fingerprint; common random numbers make paired differences cleaner than the independent
  bound.
- **Instrument facts:** ~105–138 s/call at n = 48,000; ≤3 measurement processes in parallel
  (6 concurrent measured 40× per-process slowdown). `_persona_stats` cannot pass `line_aware`
  (forwards only `context_aware`) — **a disclosed limitation, not a blessing**: no measurement
  establishes lever fits are invariant to line-awareness, and W4-b-grade work requires
  `context_aware=True` AND `line_aware=True` (R9-DEFENCE-a ledger). The fitter that needs the
  production posture must first give the harness a `line_aware` passthrough.
- **Metric-DoD (D7) reading for procedure-only slices:** no pack movement → nothing to HARD-gate;
  the gate is traceability + adversarial review.
- **Citation fix:** the precedent pointer `test_personas_postflop.py:1337-1480` is stale → `BANDS`
  dict ~:2563, `_persona_stats` ~:2634 at b63dfaa; cite by anchor + commit.
- **D11 unchanged.**

## Roadmap entry update (the consumer-handoff, rev-2 core)

Rewrite the N-vecfit bullet: premise ("scalar zig-zags; vector tool needed") **unsupported by
direct measurement where tested** (link report incl. corrections; state the scope qualifier —
tag + nit, one stat pair, line-blind). Slice reshaped by owner to this doc amendment. Keep the
confirmed facts (lever reach, block-triangularity). Then — because "unblocks R9-LOOSEFIT" was
rev 1's overclaim — the entry MUST enumerate what `R9-LOOSEFIT` still needs and now owns:

1. **Fold-share/raise-share metrics do not exist** — `_persona_stats` returns AF/FtC/WTSD only;
   the counts are computed internally but not surfaced. R9-LOOSEFIT's spec must add the derived
   stats (test-harness code, in ITS scope).
2. **Cross-persona joint fitting was NOT measured.** The premise study covered within-persona
   lever coupling only. R9-LOOSEFIT's "fit nit/tag/lag jointly + pairwise nit-vs-tag separation
   gate" is a different problem; its design pass must define the separation targets and decide its
   own procedure (the fit-loop rules apply per-fit; they do not answer the across-persona
   question).
3. **Its own Rule-1 check:** measure ρ + row-conditioning for ITS personas × ITS stat pair before
   fitting (station cond 14.3 and maniac's missing `call_looseness`/stickiness-fallback surface
   are the known dangers).
4. **Posture decision:** line-blind vs line-aware measurement; if production-faithful, add the
   `line_aware` passthrough to `_persona_stats` first.

Update ~:2167 / ~:2203 wording: N-vecfit's contribution to the chain = "fit-loop rules + refuted
vector-tool prerequisite"; R9-LOOSEFIT's real prerequisites are the enumerated items above (all
inside R9-LOOSEFIT itself). Chain order unchanged: `N-logit ✅ → N-vecfit (this) → R9-LOOSEFIT →
W4-b`.

## Out of scope

No pack value changes · no engine code · no tool · no test edits · no `BANDS` movement · no new
measurements (station/lag/maniac/stat-pairs/line-aware — all assigned above) · no fixture touches ·
`tests/test_price_tail.py` untouched · no rewriting of historical quoted text (annotations only).

## Constraints (repo law)

Strategy in versioned content/ data (untouched) · domain purity untouched (no code) · docs tree is
uncommitted working-tree state — this slice edits docs in place in the main checkout; no branch/PR
needed per initiative practice (all prior ai-dlc doc edits stayed local); if the owner wants it
committed, git rules apply (own worktree, immutable-OID push, bare, absolute paths, never merge).

## Verify-by (rebuilt after review — each gate asserts something is TRUE, not merely consistent)

0. **Baseline snapshot first:** record `git status --porcelain` + `wc -l` of the four target docs
   BEFORE editing; all later checks are relative to it (the tree is pre-dirty with unrelated
   session churn — absolute cleanliness gates are meaningless).
1. **Traceability:** every number in the amended sections resolves to
   `reports/n-vecfit-premise.md` (WITH its Post-review corrections — the corrected values, not the
   withdrawn ones: 6v5/7v9 not 2v5/3v9; ~1.45× not 2.2×) or `contracts/n-vecfit.md`. Zero orphans;
   reviewer checks claim-by-claim.
2. **Scope:** relative to the step-0 baseline, changes exist ONLY in the four listed doc files.
3. **Stale-promise sweep with declared exclusions:** grep the docs tree for `vector-valued|vecfit`;
   every hit must be (a) one of the four edited files, (b) the n-vecfit spec/ledger/tickets/report
   family itself, (c) a historical doc carrying the bracketed annotation, or (d) a frozen research
   artifact under `docs/ai-dlc/research/` (session transcripts, dated review syntheses/proposals —
   archives are never edited; falsifying transcript history is worse than a stale mention;
   adjudicated at build fan-in, see ledger B-row), or (e) a bare `N-vecfit` label mention carrying
   no vector-tool promise (e.g. dependency lists naming the slice). An affirmative stale promise in
   a live reference doc gets the bracketed annotation (applied to `reports/r9-defence-design.md`
   ~:502 at build fan-in). Any other hit fails.
4. **Consumer-handoff gate (the anti-hollow check):** the amended roadmap entry contains all four
   enumerated R9-LOOSEFIT items above — reviewer verifies each is present AND correctly assigned
   (none silently claimed as solved by this slice).
5. **Dual adversarial review** of the final diffs (Claude refuter + Codex Sol), findings
   adjudicated to `ledger/n-vecfit.md`. Reproduction material exists: preserved scripts under
   `reports/n-vecfit-premise-scripts/`.
