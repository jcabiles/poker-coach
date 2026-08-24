# Build review — E1, theory-contract amendments (2026-08-24)

**Bottom line.** A fresh adversarial reviewer returned **APPROVE-WITH-FIXES** on ticket E1, the
first of the three tickets in this build. Five of the six owner rulings, both hygiene corrections,
and every checkable factual claim came back clean and independently verified against the engine
source and the slice-3 finding ledger. Two defects were found and both were accepted: one paragraph
presented an agent's *interpretation* of existing ratified text as though the owner had ruled it,
and a new amendment label was cited three times without ever being defined. Both were sent back to
the worker and fixed before anything was committed.

The reviewer was a fresh Claude `refuter` agent on Sonnet at high reasoning effort. It was given the
approved spec, the contract map, the owner's decision memo and the slice-3 finding ledger as its
criteria, and it was **not** given the worker's report — the maker's reasoning is deliberately kept
out of a checker's context. It was told to flag only defects that affect correctness or the written
acceptance criteria.

## What "E1" and the surrounding names mean

- **E1** is simply ticket 1 of 3 in this build. It amends one document.
- The document is the **theory contract**, `docs/ai-dlc/contracts/persona-realism-theory-contract.md`
  — the file that governs how the practice-app's villain bots (the simulated opponents) are built
  and how a reviewer judges a change to them.
- **Slice 3**, nicknamed the **calldown slice**, is the third improvement slice of the bot-realism
  initiative: the batch of work that made the bots call and fold more like real players. It shipped
  and left six decisions for the owner, taken on 2026-08-24 and labelled **D1** through **D6**.
- **α (alpha)** is the minimum-defence identity from poker theory: facing a bet of *f* times the
  pot, a defender who folds more than `f/(1+f)` of its hands makes that bet profitable with any two
  cards. Ruling D1 settled that this bound applies to a player's **whole range** of possible hands,
  not to a single hand-strength class such as naked ace-high.

## Deterministic checks

Both were re-run by the reviewer in a fresh process, not read from the worker's transcript.

| Check | Result |
|---|---|
| `pytest tests/test_contract_provenance.py -q` | `6 passed in 0.01s` |
| `git status --short` | one line — the theory contract only |

## Findings and their adjudication

| # | Severity | Finding | Adjudication |
|---|---|---|---|
| 1 | HIGH | The paragraph recording ruling D2 (the value-side commitment slope is in scope for the future re-anchor slice) also asserted that the slope's engine work "lands in a separate pull request inside the same slice, ahead of the calibration one". That is a reading of pre-existing ratified amendment A6, not something the owner ruled — and it sat inside a paragraph headed as an owner ruling, with none of the file's existing provenance marking. | **ACCEPTED. Kept in substance, re-marked.** Striking it was the alternative and was rejected: amendment A6 opens by calling the re-anchor slice "calibration and hand-off only" while ruling D2 places engine work inside that same slice, so the tension is real and a future worker who cannot see it will hit it unwarned. The worker re-separated the owner-ruled sentence from the inferred one and attached the file's own `⚠️ Provenance of this clause … not itself owner-ratified text` convention, already used in §11 item 7 for exactly this case. Gain: the contradiction stays visible and is routed to the owner. Cost: one more item awaiting owner confirmation. |
| 2 | MEDIUM | "Amendment A10" was named three times but never defined. Amendments A1 through A9 are each a headed, dated block; A10 existed only as inline references inside a numbered reviewer-checklist item. | **ACCEPTED, second remedy taken.** The label was removed rather than a heading invented, because the rule structurally *is* a checklist item and not a block in §3, §4a or §7 like every real A-letter. The rule is now cited as "§11 item 16, owner-ratified 2026-08-24", which keeps its authority visible. Gain: the amendment index stays truthful and searchable. Cost: the rule loses a short handle. |

## Verified-clean claims worth keeping

The reviewer read `backend/app/domain/personas_postflop.py` read-only and confirmed the position
multiplier is applied **after** the multiway factor on both the value and the bluff paths
(`:1501`, `:1792`, `:1822`, `:1874`) — so the §7 factor-order correction fixes the contract, and the
engine was right all along · the α arithmetic quoted in the new amendment (24 of 24 river cells
breaching by 0.27 to 0.64 points; roughly 60× the shipped constant needed against a 7.5× ceiling)
matches the slice-3 finding ledger exactly · the watch-band figures recording ruling D5 match the
owner's decision memo verbatim · every line anchor the contract map supplied was still accurate,
nothing had drifted · no pre-existing ratified sentence was deleted or softened; the single §7
factor-order sentence is the only replacement, which is what the spec authorises.

## One item the worker surfaced for a later ticket

This came from the worker's own report, not from the review, and is recorded here so it is not lost.
§11 item 12 of the theory contract points readers at "the §10.2 order" in the source audit document
`docs/ai-dlc/research/persona-realism-audit-2026-07-24.md`, which presumably still carries the old,
wrong factor order. That document is outside E1's file ownership. It is handed to ticket E3, whose
consistency sweep covers it.
