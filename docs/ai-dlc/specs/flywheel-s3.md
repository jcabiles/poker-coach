# Delta spec — S3: realism score v0 + validation (bot-realism flywheel) — rev 2

Rev 2 folds the dual adversarial review (Claude refuter NEEDS-WORK 1H/3M/2L + Codex Sol
FAIL 13H/5M; adjudication ledger `../ledger/flywheel-s3.md`). Slice S3 of
`../roadmap/bot-realism-flywheel.md`; implements estimand contract v2.3
(`poker-analytics:docs/methods/estimand-contract.md`) **as amended by A1**. PRD R1.

**Owner rulings folded (2026-08-06, `../ledger/flywheel-s3-contract-defect.md`):** two-tier
fix — pool D(x) stays the verdict anchor; per-persona score added, targets anchored on the
GGPoker regulars-vs-recreationals split; per-persona reported as average (trend) and floor
= worst persona (gate); §e.2 validates the per-persona score. §a.5 guard checkers in scope.
One combined amendment PR. July data: half-day feasibility timebox.
**Appetite: re-costed to 5–7 days** (review finding — the ruling doubled the slice; the
roadmap's 3–4d predates it). ⚠️ Flagged to owner at Gate 2.

## Goal (one line)

A deterministic two-tier realism scorer + executable §a.5 constraint checkers in
poker-analytics, the target registry upgraded to pinned external data, and §e validation
executed with its stop-gate honored — score status recorded in every output.

> ⚠️ **OWNER RULINGS 2026-08-06 (post dual-review, supersede where they conflict):**
> (1) the executable per-persona floor gate — item A1.2 below and A4 rule 6 — is
> **DELETED**; floor = min(S_p) survives only as a non-gating reported diagnostic;
> avg(S_p) remains the per-persona progress metric. (2) §e validation is pre-labeled
> **retrospective face-validity**, not confirmatory. (3) GGPoker source: use + disclose
> (internal contradiction recorded with sensitivity). (4) Mapping VPIP intervals frozen
> as declared contract constants, research-band discrepancy tabled. Director
> adjudication: §e.3 doubling subset stays frozen at 3 rows.

## A1 — Contract amendment + versioned target registry (poker-analytics; owner pushes)

One §g amendment (dated; "no analyses had run"), plus `data/targets/registry-v2.json`.
The amendment must pin ALL of the following (review-forced precision):

1. **Per-persona quantity, orientation, and scale.** `Q_p = (m_p−t_p)ᵀ Σ*_p⁻¹ (m_p−t_p)`,
   `D_p = √Q_p`, higher-is-worse; the validated SCORE is `S_p = −D_p`. Reported:
   `avg(S_p)` (trend) and `floor = min(S_p)` = worst persona. §e.2 legs run on S_p and
   PASS additionally requires the CORRECT SIGN (positive ρ/τ-b for S_p) — a strongly
   reversed ordering must not pass on |statistic| alone.
2. **Persona floor as an executable constraint** (honors the owner's "floor = gate"): new
   §a.5 rule — every persona individually satisfies `D_p < c_p`, `c_p` = √(χ²_{k_p}
   99.7th pct) for that persona's stat count k_p. Familywise interpretation stated
   explicitly (a conjunction of six plug-in tests; approximation, not an exact error
   rate — same honesty clause as §a.3). Pool D(x) < c remains the §a.4 primary. The
   λ-sensitivity report covers the persona gate too; any flip ⇒ INCONCLUSIVE.
3. **Definition-compatible stat subset per persona.** GGPoker publishes per-street
   aggression FREQUENCY, not the pinned AF=(bets+raises)/calls, and no c-bet denominator
   methodology. Per-persona vectors use ONLY definition-compatible stats (k_p ≤ 10, df
   adjusted); incompatible stats (AF; c-bet family unless denominator compatibility is
   established from the source) stay pool-anchored rows and per-persona DIAGNOSTICS. No
   translation between statistic definitions, ever.
4. **Numeric σ construction, preregistered.** A deterministic per-stat recipe for
   `σ_target,p` and `σ_disc,p` (components: strata→persona mapping uncertainty,
   single-site/format mismatch, absent-sample-size inflation), all numbers + rationales
   recorded in the registry BEFORE any score is computed. A categorical LOW grade is not
   a covariance input.
5. **Anti-leakage discipline.** The 12 expert ratings are already public in §e.1. The
   mapping and σ recipes are authored MECHANICALLY (no reference to which personas rated
   high/low), then the registry file is frozen and content-hashed before any campaign
   score is inspected. Residual risk disclosed; if the discipline is breached, §e results
   are labeled retrospective face-validity, not confirmatory validation.
6. **Strata→persona mapping** with written justification (OWNER-1 conditions travel:
   exact filter combo stake·segment·statistic + retrieval date per value; low-confidence
   grades; disclosed limitation in registry + any public write-up). **Degeneracy report
   required:** state how many personas share identical t_p vectors and what that does to
   S_p's discriminative power — a limitation statement, not a fine-print grade.
7. **Registry disposition (roadmap-consistent):** GGPoker values become the TARGETS OF
   RECORD wherever definition-compatible (all-players → pool rows; strata → per-persona
   rows); literature bands demoted to labeled sanity diagnostics. Incompatible stats keep
   their existing rows with class/scope stated. Any cross-source synthesis uses a frozen
   numeric rule, not post-hoc judgment.
8. **§e.3 semantics for per-persona rows:** state exactly which per-persona rows step 2
   doubles (a preregistered subset — NOT blanket-all just because every derived row is
   low-confidence).
9. **Formula identity:** F0 = initial (λ=0.8), F1 = the §e.3 revision. Validation status
   is keyed to (formula ID, registry content hash, stat-definition version); S4/S5 must
   reject mismatches. If F1 runs, it is materialized/versioned and is the only formula
   eligible for its status.
10. **Per-campaign Σ_sim:** each validation campaign gets its OWN ≥5-replicate Σ_sim,p
    (or a shared one with preregistered justification — decided in the amendment, not at
    run time).
11. **Seat-exposure disclosure:** the ratified 9-seat pooling gives duplicated personas
    ~2× observations; Σ_sim,p absorbs the precision difference by construction, and the
    asymmetry is DISCLOSED as a limitation. §a.1's pooling ruling is not reopened.

Prereq: owner adds `bluffaces.com` to poker-coach `.claude/settings.json` allowlist +
restart, before the fetch.

## A2 — Export extension (poker-coach; tooling only, zero bot-code changes)

- `backend/tools/export_analytics.py`: add per-decision `engine_node_key` and
  `hand_class_bucket`. **Pinned semantics:** both nullable; `action='post'` (forced
  blinds) carries NULL and is EXCLUDED from determinism contexts; preflop node key is an
  export-side derivation from public state (facing-state label), NOT new domain logic —
  the derivation is specified in the ticket and lives in the export tool.
- ODCS bump BOTH repos (canonical `poker-analytics:contracts/poker_events.odcs.yaml`,
  vendored `backend/tools/poker_events.odcs.yaml`): nullable column addition per the
  compatibility policy (minor bump; if the policy demands v2 for required-on-decisions,
  the ticket says so and lands the v2 path). Coordinated landing order: canonical
  contract → producer → vendored copy → regenerated data.
- Regenerate sim50k + the ≥5 seed replicates; contract checks must COVER the new columns
  (assert all checks pass — no hardcoded "150"); one negative test proving a corrupted
  batch fails the gate.
- `git diff backend/app/domain/ content/` stays empty.

## A3 — Scorer v0 (poker-analytics `scorer/`)

- **Entry point pinned:** `scorer/score_realism.py` (stub retained, docstring pointing
  forward). Updates travel with it: analytics `Makefile` `score` target, the poker-coach
  bridge script, WORKING-AGREEMENT §2 interface note.
- **Gate first:** invokes the PARAMETERIZED authoritative gate (new
  `make validate DIR=...` / `ingest/validate.py --dir` binding the ODCS model paths to
  that dir — today `datacontract test` reads a hardcoded sample path; that is fixed
  here). Scorer refuses to score an ungated batch.
- Pool tier per §a.3 verbatim: 10 stats (pinned denominators), Σ* = Σ_sim + Σ_disc +
  Σ_target, λ=0.8, cond-number regularization 10⁶ (manifested), χ²₁₀ cutoff 26.61
  (labeled a preregistered contract choice), per-stat I_s diagnostics, VPIP−PFR gap
  diagnostic, ORDINAL/SHAPE side checks (never in D).
- Per-persona tier per A1 (k_p-compatible subsets, S_p, avg, floor).
- **Σ_sim artifact interface:** covariance loaded from a manifest-keyed artifact
  (config-hash · engine sha · scorer/stat-def version · hand count · lineup · seed set).
  S3 ships the baseline artifact; the interface is what S5's config-specific
  re-estimation plugs into.
- λ-sensitivity report mandatory (λ ∈ {1.0, 0.8, 0.5, 0.0}) over BOTH tiers; any
  flip ⇒ INCONCLUSIVE.
- **Output JSON:** `producer_manifest` VERBATIM (WORKING-AGREEMENT §4) + registry content
  hash + formula ID + covariance-artifact ID + scorer version + contract/schema versions
  + duckdb version + score status. **Byte-identity defined over a canonical payload
  excluding volatile fields** (`exported_at` etc.) so same-seed reruns compare equal.

## A4 — §a.5 constraint checkers (executable, not report-only)

Emits one deterministic `a5_pass` + per-rule pass/fail evidence:
1. Label preservation (nearest-centroid 6/6) + separation floor (≥70% baseline min
   pairwise) — z-scales are the PINNED BASELINE scales (§a.5 preamble), never recomputed
   from candidates.
2. Legality/absurdity (AA/KK first-in open-fold <0.5%; ranges; PFR ≤ VPIP; showdown ≤
   flops-seen count identity).
3. Directional persona checks (§a.5.3 exact stats; pool = candidate roster's own pooled
   value).
4. Determinism guard (contexts ≥50 obs of street × engine_node_key × hand_class_bucket,
   posts excluded; modal share ≥0.98 in ≤20% of contexts).
5. Runtime + reproducibility as CONSTRAINTS: ≥350 hands/s measured on the §f reference
   platform; identical (seed, config-hash) ⇒ identical canonical scores.
6. ~~NEW per A1.2: persona floor D_p < c_p, all six.~~ **DELETED per owner ruling
   2026-08-06** — A4 ships five rules; min(S_p) appears in scorer output as a
   non-gating diagnostic only.

## A5 — Validation run (per §e as amended)

- 12 persona-points on S_p; table-level rating excluded, reported descriptively.
- Leg 1: Spearman ρ, exact 720 persona-label permutations (score-PAIRS permuted against
  fixed rating-pairs), `p = #(|ρ_perm| ≥ |ρ_obs|)/720`, realized critical reported;
  PASS = p < .05 AND correct sign. Leg 2: **stratified within-campaign Kendall τ-b** —
  formula written in the amendment (τ-b computed per campaign over its 15 pairs with
  average-rank ties, combined by the preregistered rule; cross-campaign pairs FORBIDDEN),
  same permutation machinery + sign requirement. Leg 3: LOPO; any omission moving ρ below
  0.60 ⇒ fail on fragility. BCa cluster bootstrap (pinned RNG seed, replicate count,
  degenerate-resample rule) labeled "indicative, over-wide, 6 clusters".
- Fail ⇒ §e.3 pinned revision (F1) exactly once ⇒ re-run; still failing ⇒ stop-gate:
  exploratory surrogate in every output; S5 may not issue a score-only verdict.
- **July campaign:** half-day feasibility spike FIRST. Deliverable either a fully pinned
  snapshot recipe (engine commit · pack state · backport patch hash · command · deps ·
  hand count · lineup · seeds · checksums, + its own ≥5 replicates per A1.10) or an
  infeasibility STOP back to the owner (fallback = recorded amendment shrinking
  validation to one campaign). `__file__` printed to prove which code ran.
- No validation leg runs before A1's PR lands.

## Dependency DAG (explicit)

A1 ∥ A2 ∥ A3-gate-fix are independent starts → A3 scorer needs A1 (formula+registry) +
A2 (columns) + the gate fix → A4 needs A2 + A3 → July spike needs A2 (tool exists to
backport) → A5 needs A1 + A3 + A4 + the spike's resolution. Roadmap/PRD wording sync
(two-tier shape) rides A1's poker-coach companion commit. Cross-repo version rule: a
score output naming a registry hash or ODCS version different from the checked-out one
is invalid.

## Out of scope

Sweep runner + counterfactual validator (S4) · detection pilot (S6) · any
`backend/app/domain/` or `content/` change · internal-theory bands as targets ·
rendered-text parsing · emulator fallback · §d changes · reopening §a.1 seat pooling or
the NROY primary rule beyond A1.2 · lineup redesign (exposure asymmetry is disclosed,
not re-engineered).

## Constraints

Scores non-authoritative until validation passes (S4 smoke-data use only) · targets are
versioned data, never hardcoded · every external value pinned per OWNER-1 · <5 min per
50k batch, deterministic · worktrees only, owner pushes poker-analytics · reviewers
git-read-only.

## Verify-by (end-to-end)

1. Parameterized gate on the REGENERATED sim50k: all contract checks pass INCLUDING the
   two new columns; corrupted-batch negative test fails.
2. `scorer/score_realism.py` twice, same seed → identical canonical payloads; <5 min;
   output carries producer_manifest, registry hash, formula ID, score status.
3. `a5_pass` present with all six rule verdicts; determinism guard shows real context
   counts (posts excluded).
4. Validation artifact: ρ, stratified τ-b, realized criticals, exact p's, signs, LOPO
   range, labeled CI, resulting status — or the recorded July infeasibility STOP.
5. poker-coach `./scripts/verify.sh` green; `git diff backend/app/domain/ content/`
   empty.
