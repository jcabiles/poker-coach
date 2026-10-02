# Findings — R1 deep-stack research
scheme: 2026-09-26

## Passes
- **Pass 1, 2026-10-01.** Reviewer: Claude `refuter` (same family as the author; Codex was not used for review because the Codex call allowance went to the research lanes). Blind to the research lanes' raw output. Checklist: SPR arithmetic, repository citations, unsupported leaps, requirement coverage, labels, writing rules. It had no web access, so web quotes were verified separately by the author. Record: `docs/ai-dlc/reviews/r1-deep-stack-research-r1-refuter.md`.
- whole-branch review: skipped — documentation-only change; the one blind review above covered the report.

## Findings
| ID | Target | Severity | Finding | Evidence | Status | Resolution test |
|----|--------|----------|---------|----------|--------|-----------------|
| F1 | Repo-facts table, grader row | major | "The grader computes SPR for display only" was wrong: SPR feeds the frozen spot signature. | `backend/app/domain/srs.py:36-43,141`; `grep -rniE "spr\|stack_bb" backend/app/domain/providers` finds nothing | fixed: row now says SPR feeds the frozen signature and depth-aware grader work must leave it unchanged | Row names `srs.py:36-43,141` |
| F2 | Next step 1 | major | Recommendation omitted the 9-max byte-identical rule, misstated the engine rule, and came before the "measure first" step. | `docs/ai-dlc/roadmap/bot-realism-6max.md:266-270` | fixed: measure is step 1; the hand-type threshold is step 2, gated on amending both roadmap rules and 6-max only | Bottom line quotes both rules |
| F3 | Bottom line "Firm", settings row 1 | major | Overstated: two-pair and set cutoffs are single-author, and examples are at 100bb. | Cluff 888poker 2020-02 is the only source for 5 and 10 | fixed: headline says "reasonably supported", single-source rows labelled, extrapolation stated | Commit table marks both rows "single source" |
| F4 | `personas_postflop.py:1889` row | minor | "Unopposed strong draws" misdescribed the code. | `personas_postflop.py:1889-1897` | fixed: reworded to "not facing a bet" | Row matches the code |
| F5 | Bottom line, directions | minor | One CO-versus-BTN finding was generalised. | doc bottom line | fixed: matchup named | Bottom line names CO and BTN |
| F6 | Population evidence | minor | Two reports were dated but not cited. | doc population section | fixed: URLs added and marked lane-reported, not re-opened | Both URLs present |
| F7 | Existing-documents count | minor | "Eight documents" not reproducible; omitted two repeats of the unsourced barrel claim and the earlier graded-commit proposal. | `docs/research/06-postflop-reference-tables.md:49`, `docs/ai-dlc/research/RES-C-postflop-ranges.md:231`, `docs/research/12-persona-engine-and-realism-fixes.md:616` | fixed: count corrected, three repeats listed, prior proposal cited | Paragraph lists the three files |
| F8 | Settings row, set-mining | minor | Marked "Usable" though no bot setting consumes it. | bots read no depth before the flop | fixed: "no consumer today" | Row says so |
| O1 | Repo facts | minor | Local note on seat-hands over 150bb is useful for sizing the measurement run. | `backend/app/services/sim_session.py:133-136` | fixed: added to the stack row | Row cites lines 133-136 |
| O2 | "What this means for the bots" | minor | Optional note that varying raise sizes leaves the gate conclusions unchanged. | reviewer arithmetic | rejected: confirms existing conclusions; no change needed | n/a |
