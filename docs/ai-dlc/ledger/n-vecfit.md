# Finding ledger — N-vecfit spec review (rev 1 → rev 2)

Review of `specs/n-vecfit.md` rev 1 + `contracts/n-vecfit.md` + `reports/n-vecfit-premise.md`,
2026-08-03. Reviewers: Claude `refuter` (sonnet/high) → **FAIL** (3 HIGH / 3 MED / 1 LOW);
Codex `gpt-5.6-sol` (high) → **FAIL** (5 HIGH / 4 MED / 1 LOW). No reviewer-vs-reviewer conflicts;
Codex independently confirmed the refuter's ρ-arithmetic check (both: arithmetic correct — for tag,
divergence needs |J12| ≈ 0.219 vs 0.040 measured, 5.47×, ~8σ away). Adjudicator: director (Fable).
Every ACCEPTED finding is folded into spec rev 2 and/or the report's Post-review corrections
section.

| # | src | sev | finding (compressed) | adjudication |
|---|-----|-----|---|---|
| R-1 | refuter | HIGH | Doc citations use working-tree line numbers under a "pinned b63dfaa" banner; roadmap ~:2001/:2162/:2203 don't exist at the commit (blob = 2016 lines, tree = 2567; real anchors :1609/:1756). | **ACCEPT-NARROWED.** Verified: blob 2016 vs tree 2567 lines. Content identical, only numbering shifts. Fix = explicit citation convention (code@commit, docs@working-tree, anchors authoritative) — spec rev 2 header. Not a renumbering: working tree IS the authoritative doc surface. |
| R-2 | refuter | HIGH | Within-persona lever coupling (measured) conflated with R9-LOOSEFIT's ACROSS-persona "fit jointly + nit-vs-tag separation gate", on a stat pair (fold/raise-share) the harness doesn't return. | **ACCEPT — the central finding** (= C-1). Rev 2: "unblocks" language replaced with a 4-item enumerated handoff (derived stats, cross-persona design, own ρ/conditioning check, posture decision) that the roadmap entry must carry verbatim; verify-by gate 4 checks its presence. |
| R-3 | refuter | HIGH | Rule 1 requires a fresh measured J per fit → silently re-imports the ~4-call cost the verdict charged against the vector arm. | **ACCEPT.** Rev 2 Rule 1a: the ρ *screen* tolerates approximate/reused J (5× margin, 0.183 vs 1.0) — reuse allowed per persona×pair; one-time 2–4-call cost for new combinations, disclosed. Fresh-slope requirement now applies only to step sizes (Rule 2). |
| R-4 | refuter | MED | "±25% move ≈ 1.5 tolerance units" is a recomputed number dressed as a report citation (report's 1.5× was for a ×1.3 step). | **ACCEPT.** Rev 2 Rule 3 recomputes honestly: |J11|·ln 1.25 ≈ 0.032 ≈ 1.35 units, attributed as computed-from-J. |
| R-5 | refuter | MED | Verify-by #3 (grep) is purely lexical — search-and-replace passes it while the conceptual conflation stands. | **ACCEPT** (= C-7 family). Rev 2 adds gate 4 (consumer-handoff content check) as the semantic gate; grep gate rebuilt with declared exclusions. |
| R-6 | refuter | MED | Verify-by #2 ("changes only under docs/ai-dlc/") already false pre-slice — tree is dirty with unrelated churn (.claude/CLAUDE.md etc.). | **ACCEPT.** Rev 2 gate 0: baseline snapshot; gate 2 is baseline-relative. |
| R-7 | refuter | LOW | Rule 2's secant has no guard for non-monotone regions (study saw only monotone drift). | **ACCEPT.** Rev 2 Rule 2: sign-flip → stop, measure local J. |
| C-1 | codex | HIGH | "Unblocking R9-LOOSEFIT" unsupported: lag untested, fold/raise-share not returned by `_persona_stats`, contract §7 says consumer needs a tool. | **ACCEPT** (= R-2). Same fix. Contract file gets a superseded-note (spec rev 2 file-list item 4). |
| C-2 | codex | HIGH | Call accounting biased: scalar arm was seeded with J11/J22 from the same 4 calls charged only to vector. Fair: near 6 vs 5, far 7 vs 9 — "cheaper on both, 2v5/3v9" withdrawn. | **ACCEPT.** Report correction §1: margins withdrawn; corrected conclusion = scalar competitive near / cheaper far; stale-J non-convergence stands. Spec rev 2 quotes only corrected numbers. |
| C-3 | codex | HIGH | "REFUTED by direct measurement" overgeneralizes: only tag got trajectories; nit only a local J; lag/station/maniac/other pairs/line-aware untested. | **ACCEPT.** Report correction scope statement + rev 2 background rewritten to the narrow claim ("unsupported where tested"), NOT-measured list explicit. Decision (no tool) stands on burden-of-proof: the tool's justifying claim failed at its central test; residual uncertainty is assigned to R9-LOOSEFIT's own Rule-1 check with an escalation path. |
| C-4 | codex | HIGH | "Mispairing is equally fatal to a joint fit" mathematically false — Newton is permutation-invariant; conflates scalar assignment (ρ) with target conditioning (near-parallel rows / station cond 14.3). | **ACCEPT.** Rev 2 splits Rule 1 into 1a (mispairing, scalar-only) and 1b (conditioning, any method). |
| C-5 | codex | MED | 2.2× far-field slope confounded (both levers moved between the cited calls); uncontaminated secants → ~1.45×. | **ACCEPT.** Report correction §2; rev 2 Rule 2 uses ~1.45× and requires other-levers-fixed between secant points. |
| C-6 | codex | MED | "Zig-zag needs ρ≥1" misstates (ρ≥1 = failure to contract; signed −0.183 predicts damped alternation); "stayed inside tolerance" false (far-target call 2 FtC error −1.15). | **ACCEPT.** Report correction §3; rev 2 background states both correctly. |
| C-7 | codex | HIGH | All four rev-1 gates pass without proving usefulness; scripts scratchpad-only, unreproducible; missing consumer-specific proving artifact. | **ACCEPT-NARROWED.** Scripts now preserved (`reports/n-vecfit-premise-scripts/`, 15 files); gates rebuilt (0–5, incl. semantic gate 4). The demanded full proving artifact (fold/raise-share exposure + separation targets + nit/tag/lag ρ under production posture) is **R9-LOOSEFIT's build**, not this doc slice's — that assignment is exactly what gate 4 enforces. Narrowed, not rejected: doing that work here would rebuild the tool-slice the owner just killed. |
| C-8 | codex | MED | Edit list incomplete: contract §7 still prescribes a tool; roadmap ~:2500 quote + wave-a spec :95-96 still promise vector fit; grep gate matches the spec family itself. | **ACCEPT.** Rev 2 file list grew to 4 files (contract note, roadmap :2500 annotation, wave-a annotation — historical text annotated, never rewritten); grep gate has declared exclusions. |
| C-9 | codex | MED | "Line-blind is fine for lever fitting" reverses the report's disclosed residual risk — no measurement establishes line-awareness invariance. | **ACCEPT.** Rev 2 instrument-facts bullet: disclosed limitation, not a blessing; production-posture fitter must add the `line_aware` passthrough first (assigned to R9-LOOSEFIT item 4). |
| C-10 | codex | LOW | "Both lever guard rails" wrong: aggression hit the real 5.6 cap; call_looseness 0.155 has no floor (model bound > 0 only). | **ACCEPT.** Report correction §4; rev 2 wording fixed. |

## Build fan-in review (2026-08-03, after T1–T3)

Reviewers over the four built diffs: Claude `refuter` → **NEEDS-WORK** (2 MED / 1 LOW);
Codex `gpt-5.6-sol` → **FAIL** (1 HIGH / 3 MED). Heavy overlap; all applied by the director at
fan-in. Refuter otherwise confirmed: no withdrawn values resurrected, both annotations strictly
additive, D11 byte-untouched, all 4 handoff items present, 8+ numbers traced clean, referrer
step-number spot-checks clean.

| # | src | sev | finding | adjudication |
|---|-----|-----|---|---|
| B-1 | both | HIGH(C)/MED(R) | Gate-3 sweep fails literally: `reports/r9-defence-design.md:502` carries an affirmative stale promise ("N-vecfit … about to fit"); `specs/n-logit.md:234` + `reports/r10-tail-design.md:623` are bare label mentions outside every declared category. | **ACCEPT.** r9-defence-design ~:502 annotated (bracketed, additive). Spec gate 3 gains category (e): bare label mentions without promise text. Sweep now resolves. |
| B-2 | codex | MED | Roadmap "scalar … not zig-zagging" resurrects the withdrawn no-alternation characterization (C-6 regression). | **ACCEPT.** Reworded: damped alternation contracting 5.5×/48× per round — "zig-zag exists in sign but not in cost". |
| B-3 | both | MED | Fit-loop Rule 2 caveat cited "damped alternation" (the VECTOR arm's trajectory error) as the monotonicity evidence — wrong measurement; the actual evidence is the strictly-monotone 5-point ladder (report §1). | **ACCEPT.** Caveat now cites the ladder; sign-flip guard unchanged. |
| B-4 | codex | MED | Retained lever-reach figures (76.3/59.8/42.2/5.3/4.8/2.3%) orphaned under gate 1 — absent from both allowed authorities. | **ACCEPT-NARROWED.** They are pre-existing roadmap facts retained per spec instruction; original authority is the filing's own design-pass measurement. Provenance parenthetical added in the entry; gate 1 reads on numbers introduced by THIS slice. |
| B-5 | refuter | LOW | `contracts/n-vecfit.md` is untracked — the "prepend" cannot be diff-verified by git, only by reading. | **ACCEPT-AS-NOTED.** Matches initiative practice (uncommitted docs tree); manual read confirms body §§1–7 unchanged. No action. |
| B-6 | build | — | Builder-flagged gate-3 exception: frozen research artifacts under `docs/ai-dlc/research/` contain unannotated "vector-valued" text; builder refused to edit archives. | **ACCEPT builder's call.** Spec gate 3 category (d) added: archives exempt — falsifying transcript history is worse than a stale mention. |
| B-7 | note | — | Gate-0 baseline, done-condition greps, and gate 1/2/4 evidence recorded in the builder's report (T1 greps 3/0; handoff items at roadmap :2021/:2024/:2028/:2031; scope diff clean vs baseline). | Recorded. |

## Codex invocation note

The codex-login-guard hook flagged this run as a failure. False positive: the flagged lines were
`codex_models_manager` model-list refresh probes (the documented harmless blocked-network noise);
the review itself completed (63,508 tokens, full verdict). No re-auth, no substitution.

## Standing lessons reinforced

- The initiative's gate law extends to REPORTS: a comparison must charge shared measurement costs
  to both arms (C-2), and a ratio taken while two variables move is not a partial derivative (C-5).
- "Pinned to commit X" is a claim about a BLOB, not a working tree — state the citation surface
  explicitly when docs live uncommitted (R-1).
- A refutation inherits the scope of its measurement — write the qualifier into the headline, not
  the appendix (C-3).
