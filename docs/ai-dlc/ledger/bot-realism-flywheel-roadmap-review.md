# Ledger — bot-realism-flywheel roadmap dual review (2026-08-05)

Reviewers over roadmap rev 1 + PRD rev 1: Claude `refuter` (sonnet/high) → **NEEDS-WORK**
(1 HIGH / 3 MED / 4 LOW); Codex `gpt-5.6-sol` (high) → **FAIL** (8 HIGH / 5 MED / 2 LOW).
Heavy overlap; no reviewer-vs-reviewer conflicts. Adjudicator: director. All accepted findings
folded into **rev 2** of both docs. Deterministic checks (refuter): all cross-references,
numbers, pause banner, profile flip verified clean.

| # | src | sev | finding (compressed) | adjudication |
|---|-----|-----|---|---|
| 1 | both | HIGH | ρ≥0.5 gate underpowered at n=13 (crit ≈0.56); revise-until-pass = circular fitting; downstream inherits fake validity. | **ACCEPT.** Rev 2: n=13 declared directional-only; report ρ+CI+p + sign agreement; ONE pre-registered revision; then STOP-GATE (score = exploratory surrogate; no score-only S5 verdict; convergent detection evidence required). |
| 2 | sol | HIGH | "Space-filling sweep" undefined against a config model that is not a 5-dim box; finite sweep can't prove a negative over continuous space. | **ACCEPT.** New S2a/R0 search-space & estimand contract; verdict reframed as *operational ceiling within declared space + compute budget*. |
| 3 | sol | HIGH | Winner's curse — best-of-sweep config can look "reachable" from selection noise. | **ACCEPT.** S5: top configs re-run on fresh seeds before any REACHABLE claim. |
| 4 | sol | HIGH | Sweep as specified can't diagnose mechanisms/interactions. | **ACCEPT.** S5 adds DoE-style per-dial + interaction probes per S2a design. |
| 5 | sol | HIGH | Reachability disconnected from north star; binary gate forced from weak evidence. | **ACCEPT.** Verdict set = {REACHABLE, NOT-REACHABLE, INCONCLUSIVE}; detection protocol preregistered in S2a (before S3); phase-3 gate packet requires a preregistered decision matrix incl. capability gaps + effort/risk + INCONCLUSIVE path. |
| 6 | both | HIGH/MED | Owner HERO hands can't be the north-star human baseline (single subject/session/opponent-composition; pseudoreplication). | **ACCEPT.** S6 reframed as single-player feasibility PILOT, biases + direction-of-effect named; true multi-player baseline + owner target = NEXT item. |
| 7 | sol | HIGH | "Perfect realism = 50%" only under an unstated protocol; "detection rate" ambiguous. | **ACCEPT.** S2a preregisters judgment unit, exposure, balanced priors, matched info, balanced accuracy/AUC/d′, leak controls, cluster-aware CIs. |
| 8 | sol | HIGH | S2∥S3 not parallel-safe — DS-methodology lane must shape score/sweep design. | **ACCEPT.** S2 split: S2a methods contract (blocking) absorbs the DS lane; S2b (academic/commercial/corpus) stays parallel. |
| 9 | sol | MED | Literature bands treated as more coherent than evidence supports; hard in/out cliffs invite gaming. | **ACCEPT.** Target registry with per-stat provenance/compatibility/uncertainty/confidence; graded distance, covariance-aware weights. |
| 10 | sol | MED | Read-only pack boundary contradicts dial sweeps absent an override contract. | **ACCEPT.** Counterfactual-config schema (ephemeral, validated through the real pack model); "read-only" = no COMMITTED changes. |
| 11 | sol | MED | Goodhart: detection optimizable by going bland / imitating the owner. | **ACCEPT.** Constraint set added to north-star section + no-gos (archetype-separation floor, red-flag limits, pedagogy, perf budgets). |
| 12 | sol | MED | Phase-3 decision rule missing; pack-only ceiling can't decide the whole architecture. | **ACCEPT.** Preregistered decision matrix in the NEXT gate-packet item; capability gaps explicitly inputs. |
| 13 | both | MED/LOW | Appetite arithmetic exceeds the ~2–3 wk cap; S6 scheduling unstated. | **ACCEPT.** Appetite declared a CAP with ordered scope valves (S5 confirmatory deferred → S2b commercial lane cut → S6 judge count shrinks, never blinding); S6 declared parallel to S5; critical path stated. |
| 14 | ref | MED | PRD "before anything downstream" vs roadmap "before S5" — S4 ambiguous. | **ACCEPT.** Aligned in both docs: scores non-authoritative until validation passes; S4 may use them as reproducibility smoke data only. |
| 15 | sol | LOW | Reproducibility pins insufficient for portfolio replay. | **ACCEPT.** PRD ✅Always extended (scorer version, registry version, lockfile, checksums; dataset/model cards at publication). |
| 16 | sol | LOW | Dossier "claims cited" ≠ research consumed. | **ACCEPT.** S2b adds the consumption map deliverable with evidence grades. |
| 17 | ref | LOW | SYNTHESIS §5 mislabeled as a contract map; S1 "existing export" ambiguous. | **ACCEPT.** Citation relabeled (measurement instrument); S1 pins the sim50k export. |
| 18 | sol | HIGH(part) | Build a multi-judge, multi-config expert-rating dataset for score validation. | **ACCEPT-NARROWED.** Cost-prohibitive now; rev 2 substitutes the stop-gate + convergent detection evidence + leave-one-out on the 13 points where usable. Revisit IF the validation plan fails its single revision. |
| 19 | sol | verdict | "FAIL — return to shaping before specification." | **ACCEPT-IN-SUBSTANCE.** The fold IS the reshape: rev 2 embeds the methods contract (S2a) as a blocking slice, so specification of S3–S6 cannot begin before the shaping work Sol demanded. |

Disagreement surfaced to the owner: refuter NEEDS-WORK vs Sol FAIL — adjudicated as
fold-and-revise rather than restart, because every FAIL-driving defect maps to a concrete
rev-2 change and no finding attacked the initiative's direction.
