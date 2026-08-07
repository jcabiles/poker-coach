# Ledger — flywheel-s3 (spec dual review, 2026-08-06)

Reviewers over spec rev 1: Claude `refuter` (sonnet/high) → **NEEDS-WORK** (1 HIGH / 3 MED /
2 LOW); Codex `gpt-5.6-sol` (high) → **FAIL** (13 HIGH / 5 MED). Complementary; no
reviewer-vs-reviewer conflicts. Adjudicator: director — every finding verified against the
contract/repos before folding (Makefile hardcode and GGPoker AF-incompatibility checked
directly; Codex confirmed edit-free afterward, both trees clean). All folded into **spec
rev 2**; two narrowed, zero rejected outright.

| # | src | sev | finding (compressed) | adjudication |
|---|-----|-----|---|---|
| 1 | sol | HIGH | Spec demoted the owner's persona floor to "reporting", nullifying the gate. | **ACCEPT.** A1.2: floor = executable §a.5 constraint, D_p < c_p all six; pool D(x) stays §a.4 primary. Flagged at Gate 2 for owner confirmation. |
| 2 | sol | HIGH | D_p orientation/scale unpinned; reversed ordering could "pass" two-sided legs. | **ACCEPT.** A1.1: Q_p/D_p/S_p=−D_p pinned; PASS requires correct sign + p<.05. |
| 3 | sol | HIGH | Floor is a max-statistic; no cutoff/multiplicity rule; λ flips unhandled. | **ACCEPT.** A1.2: per-persona χ²_{k_p} cutoffs, familywise interpretation stated, λ-sensitivity covers the gate, flip ⇒ INCONCLUSIVE. |
| 4 | sol | HIGH | GGPoker publishes per-street aggression frequency, not pinned AF; c-bet denominator unestablished. Verified true (corpus brief §5). | **ACCEPT.** A1.3: definition-compatible subsets only (k_p ≤ 10, df adjusted); no cross-definition translation; incompatibles stay diagnostics. |
| 5 | sol | HIGH | LOW-confidence grade is not numeric σ; distance needs numbers. | **ACCEPT.** A1.4: preregistered deterministic σ_target,p/σ_disc,p recipes, recorded before scoring. |
| 6 | sol | HIGH | Ratings already known while designing mapping — leakage into §e. | **ACCEPT-NARROWED.** A1.5: mechanical authorship, freeze+hash before scores; breach ⇒ relabel retrospective. Full blinding impossible (ratings predate contract — same residual §e.3 discloses). |
| 7 | sol | HIGH | July snapshot underspecified; per-campaign Σ_sim undecided. | **ACCEPT.** A5 spike deliverable = fully pinned recipe; A1.10 decides per-campaign Σ_sim in the amendment. |
| 8 | sol | HIGH | §e.3 revision could validate one formula while S4/S5 run another. | **ACCEPT.** A1.9: formula IDs F0/F1; status keyed to (formula, registry hash, stat-def version); mismatches rejected downstream. |
| 9 | sol | HIGH | `make validate` hardcodes the sample dir; `datacontract test` reads a fixed path — the advertised gate checks the wrong dataset. Verified true (Makefile). | **ACCEPT.** A3: parameterized gate binding ODCS paths to `--dir`; scorer refuses ungated batches; negative test required. |
| 10 | sol | HIGH | Runtime/reproducibility watered down to "report only" vs §a.5 "ALL". | **ACCEPT.** A4: executable constraints, single `a5_pass`, pinned baseline z-scales. |
| 11 | sol | HIGH | S5's config-specific Σ_sim re-estimation has no scorer interface. | **ACCEPT-NARROWED.** A3: manifest-keyed covariance artifact interface; S3 ships baseline artifact only (S5 supplies its own). |
| 12 | sol | HIGH | ODCS change lacks nullability/semantics/landing order; forced posts have no decision context. | **ACCEPT.** A2: nullable columns, posts NULL + excluded from determinism contexts, preflop key = export-side derivation, coordinated landing order, checks cover new columns. |
| 13 | sol | MED | Scorer entry point/bridge/Makefile updates unlisted. | **ACCEPT.** A3: `score_realism.py` pinned; Makefile, bridge script, WORKING-AGREEMENT §2 updates in-scope. |
| 14 | sol | HIGH | A1–A5 dependency DAG incomplete. | **ACCEPT.** Explicit DAG section added; cross-repo version-mismatch rule stated. |
| 15 | sol | MED | τ-b "same machinery" not executable (cross-campaign pairs, tie handling, p convention, BCa pins). | **ACCEPT.** A5: stratified τ-b formula written in the amendment; p-counting, ties, BCa seed/replicates pinned. |
| 16 | sol | HIGH | "Join the existing literature rows" contradicts the approved registry swap. | **ACCEPT.** A1.7: GGPoker = targets of record where compatible; literature demoted to labeled sanity diagnostics. |
| 17 | sol | MED | producer_manifest + hashes missing; byte-identity undefined over volatile fields. | **ACCEPT** (merges refuter LOW). A3: verbatim manifest + registry hash + formula ID + covariance ID; canonical payload excludes volatile fields. |
| 18 | sol | MED | Unequal seat pooling (3 personas ~2× observations) skews Σ_sim,p/ranks. | **ACCEPT-NARROWED.** A1.11: disclosed limitation; Σ_sim,p absorbs precision asymmetry by construction; §a.1's ratified pooling NOT reopened (lineup redesign would change the declared ecology/estimand). |
| 19 | ref | HIGH | Two strata → six personas can produce degenerate identical t_p vectors, penalizing extreme archetypes. | **ACCEPT.** A1.6: mandatory degeneracy report + explicit discriminative-power limitation statement. |
| 20 | ref | MED | Roadmap S3 / PRD R1 wording predates the two-tier ruling — traceability gap. | **ACCEPT.** Wording sync rides A1's poker-coach companion commit (T1). |
| 21 | ref | MED | 3–4 day appetite stale after the scope-doubling ruling. | **ACCEPT.** Re-costed 5–7 days in rev 2; flagged to owner at Gate 2 (roadmap edit needs owner nod). |
| 22 | ref | MED | §e.3 step-2 row selection ambiguous when every per-persona row is LOW-graded. | **ACCEPT.** A1.8: preregistered subset named in the amendment. |
| 23 | ref | LOW | Output omits producer_manifest the stub already carries. | **ACCEPT** (folded into #17). |
| 24 | ref | LOW | `engine_node_key` has no preflop semantics; only `postflop_node_key` exists in domain. | **ACCEPT.** A2: preflop facing-state label derived in the export tool — no domain-adjacent logic invented at implementation time. |
