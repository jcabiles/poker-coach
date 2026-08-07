# Ledger — S3 contract defect + owner ruling (2026-08-06)

## The defect (independently verified this session; found by the prior spec-S3 session)

The committed estimand contract (`poker-analytics:docs/methods/estimand-contract.md` v2.3,
merged as poker-analytics PR #11) contains a §a.1 ↔ §e.2 contradiction:

- §a.1 defines the primary score D(x) as **pool-level** (one number per campaign for the whole
  table); per-persona distances are "diagnostics only, never part of any verdict."
- §e.2 validates "the score" by Spearman ρ over **12 persona-points** (6 personas × 2
  campaigns). A pool-level score yields 2 points, not 12. The per-persona quantity §e.2
  correlates is **never defined anywhere in the contract** (grep-verified).
- §e.3's pinned revision manipulates λ/σ_disc — parameters that exist only inside D(x) — so §e
  plainly believes it is validating D(x), which cannot produce the required data layout.

Corroboration: round 1 of the contract review killed "pool-target-per-persona" as
roster-blanding (`flywheel-s2a.md`); four review rounds reworked §e without checking the
correlated quantity exists. **Additional finding this session:** the roadmap's S3 pass/fail
AND the PRD's R1 both say "per-persona score" — the contract drifted from both governing docs
during review. Consequence if unfixed: the validation report would certify a different number
than the ceiling verdict uses — the exact slippage the stop-gate exists to prevent.

Related: S2b's corpus brief (03 §5) partially dissolves §a.1's forcing premise ("no external
per-archetype data exists") — GGPoker aggregates publish a regulars-vs-recreationals split, a
real external anchor on the loose/tight axis (strata, not archetypes; mapping must be
constructed per the OWNER-1 ruling).

## Owner ruling (2026-08-06, via interactive picker after discussion)

**Fix = two-tier, human-anchored amendment under §g:**

1. **Community (pool-level) score D(x) stays the verdict's primary anchor** — unchanged; it is
   the best-externally-anchored quantity and the only place cross-persona defects (bot-farm
   similarity, table-mix realism) are visible.
2. **Add a defined per-persona score**, targets anchored on the GGPoker
   regulars-vs-recreationals split with a constructed, written strata→persona mapping
   (the OWNER-1 conditions travel: exact filter combo + retrieval date, low-confidence grades,
   justified mapping, disclosed limitation). Where the two strata cannot pin an archetype, the
   residual assumptions are declared, not invented silently.
3. **Reporting shape (owner direction from the metric discussion):** per-persona scores
   reported as BOTH an average (trend metric) and a floor = worst persona (the gate metric —
   detection is weakest-link, so the floor is the release-style guard). North star is
   unchanged (blind detection rate); these are tiers of the inner-loop surrogate.
4. §e.2's validation legs then test the per-persona score — the quantity they always required.

Amendment status: **no analyses had run** when ruled (recorded per §g — this is what makes it
cheap). The amendment text lands as a PR to poker-analytics (owner pushes; sandbox cannot
write that repo). Rejected alternatives, recorded: internal-bands diagnostic validation
(certifies the wrong number); firing the stop-gate at the outset (discards a roadmap pass/fail
condition, puts S6 on the critical path).

## Process notes

- Dual review confirmed ON for the S3 spec (Claude refuter + Codex; both tools verified
  present this session).
- `bluffaces.com` must be added to the sandbox network allowlist before the registry
  ingestion/amendment work can fetch values (currently blocked).
- 2026-08-06 merges: poker-coach PR #171 (S2a completion set) and poker-analytics PR #11 (the
  contract) — working-tree copies verified byte-identical to merged main; the handoff's
  "roadmap collision" and "untracked contract" warnings are obsolete.
