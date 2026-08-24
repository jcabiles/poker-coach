# Build review — E3, ledger closures, sweep and roadmap reconciliation (2026-08-24)

**Bottom line.** A fresh adversarial reviewer returned **APPROVE-WITH-FIXES** on ticket E3, the last
of the three tickets in this build, with six findings. All six were accepted and fixed before
anything was committed. The one that mattered: the governing roadmap was about to state that every
target in a sister repository's registry is graded low-confidence, and three of them are not. That
claim sits under a heading marking a planned work item as already satisfied, so shipping it would
have invited a future session to close the item believing a swap was total when seven of ten rows
were swapped and three were left on the old values.

Everything else the reviewer checked came back sound: all eleven adjudication notes carry genuinely
distinct dispositions rather than a uniform stamp, the two cross-referencing findings are closed by
one shared reasoning, the still-open residual is unmissable, the three residual limitations are
framed so nobody schedules them, and all three files the worker edited beyond its named list were
genuinely still asserting the withdrawn rule.

This reviewer was a fresh Claude `refuter` agent routed to **Opus at high reasoning effort** rather
than the Sonnet used for the two earlier waves, because this diff is the largest, edits the
governing roadmap, and makes a claim about a different repository's state. It was given the spec,
the ticket, the contract map and the owner's decision memo as criteria, and **not** the worker's
report.

## What E3 did

Improvement slice 3 — the "calldown" slice, the work that made the practice app's simulated
opponents call and fold more like real players — left fifteen numbered findings recorded as "Filed 1"
through "Filed 15". The owner decided six of them on 2026-08-24. E3 wrote the paper trail: dated
adjudication notes under eleven of those findings, a rewrite of the two documents that still
asserted the withdrawn rule as current, the roadmap updates, and a sweep of the whole documentation
tree for anything left contradicting the new state.

Final diff: **nine files, 420 added and 18 removed lines, all under `docs/`.** No file under
`backend/`, `frontend/`, `content/` or `scripts/` was touched.

## The eleven adjudications, and why they are not all "closed"

The reviewer agreed with every disposition. They are deliberately different from one another,
because a later reader acts differently on each:

| Finding | Resolved by | Disposition |
|---|---|---|
| Filed 1 | D3 | **Parked**, not built — the fold lever is filed at the relevant contract row and built only if a slice targets that gap |
| Filed 2 | D1 | **Reshaped, and its residual stays OPEN** — no test may admit it until a sourced margin exists |
| Filed 4 | D6 | **Stays parked**; no action, no closure |
| Filed 5 | D2 | **In scope** for the re-anchor slice, build not authorised; the tension with an existing amendment is flagged for the owner, not resolved |
| Filed 8 | D1 + D6 | **Dissolved** — the obligation it recorded was owed against a rule that no longer exists |
| Filed 9 | D1 | **Closed** — the 24-of-24 breach stops being a breach |
| Filed 10 | D1 | **Upheld and enacted**, closed by the same single reasoning as Filed 9 |
| Filed 11 | none | **Recorded**; no ruling was required or taken |
| Filed 13 | hygiene | **Deferred** to the re-anchor slice, and stays open as an obligation |
| Filed 14 | hygiene | **Closed** in the contract's favour, with one residual reported rather than fixed |
| Filed 15 | D4 | **Adopted** as standing process law |

## The six findings and their adjudication

| # | Severity | Finding | Adjudication |
|---|---|---|---|
| 1 | MEDIUM | The roadmap's verification claim that "every derived target is graded low-confidence throughout" is contradicted by three of the registry's pool rows, and the entry was marked satisfied without disclosing that two of its own four candidate approaches are incomplete. | **ACCEPTED.** Independently confirmed by the orchestrator against the registry file: 49 rows labelled `LOW`, 3 labelled `C-grade literature (unchanged)` — `flop_cbet`, `fold_to_cbet` and `af`. The condition was narrowed to targets *derived from the ingested aggregates*, which is true and checkable, and a fourth residual now records that the swap off the literature bands is partial and that no expert-elicitation panel was run — as a disclosed limitation, not a work item. |
| 2 | LOW | One contract map said "nothing occupies those line numbers now" while the *other* contract map edited in the same change said a live test begins exactly there. | **ACCEPTED.** A contract map exists to resolve line anchors; two of them contradicting each other inside one change is the specific thing it must not do. Now states that no ace-high assertion remains and that those lines hold the cross-persona ordering test. |
| 3 | LOW | A ledger note placed the new reduction-floor rule "alongside §5a's obligations". Section 5a holds exactly two obligations and this is neither; both halves of the rule live in §11. | **ACCEPTED.** The theory contract's own wording was checked and is correct — it says the rule takes the same dual *form*, which is true — so only the ledger note was fixed. A reader following the wrong pointer would have concluded the rule was never landed. |
| 4 | LOW | The close packet the roadmap links as its record still instructs the owner to "rule on the filed decisions", which happened on 2026-08-24. | **ACCEPTED, with a narrow scope exception granted.** Dated reports in that directory are normally not edited. One appended dated paragraph, no body change; the play session, which genuinely is still outstanding, was left alone. Gain: the linked close record stops handing the owner a completed task. Cost: one more file in the diff and a small precedent for annotating dated records — consistent with the withdrawal banner already applied elsewhere in this ticket. |
| 5 | LOW | A research measurement script under `docs/` still opens by stating the withdrawn ruling as its reason for existing. | **ACCEPTED, with a narrow scope exception granted.** The worker had self-restricted because the ticket forbids touching code; the boundary it was given names `backend/`, `frontend/`, `content/` and `scripts/`, and this file is in none of them. Confirmed standalone with no importers. A docstring-only banner was added; the file still parses and no executable line changed. |
| 6 | LOW | The ledger's summary block compressed parked, deferred and closed into one clause and stated one closure more flatly than its own note did. | **ACCEPTED.** The per-item notes were correct; the summary is the first thing a reader sees and should not be blunter than what it summarises. Now separated, with the reported-not-fixed residual named. |

## Independently verified by the orchestrator

Both finding ledgers are **strictly append-only** — 231 and 10 lines added, **zero deleted** — so no
past entry's recorded finding was revised. Every one of the 18 deleted lines in the change belongs
to the two contract maps and the roadmap, and each is either the withdrawn-rule paragraph the spec
explicitly directed be rewritten, a corrected stale anchor, or a line rewrap. The registry
confidence counts were re-derived from the registry file itself rather than accepted from the
review. The measurement script was confirmed to parse and to have no importers before the exception
was granted. The full backend suite is green on this branch at 2189 passed, 2 skipped, zero
expected-failures, with `BACKEND VERIFY OK` and `ruff` clean; E3 touches no file on the test
collection path, so that result stands over its changes.

## One thing this build could not fix — for the owner

`docs/ai-dlc/research/persona-realism-audit-2026-07-24.md` is **deliberately excluded from version
control** (it is listed in `.git/info/exclude`) and exists only in the owner's main checkout. Its
§10.2 still carries the superseded order in which the engine's aggression multipliers are applied —
the order this build just corrected in the theory contract. The theory contract's §11 item 12 sends
a reviewer to that document for exactly that ordering, so the pointer now resolves to superseded
text, and no branch can correct it. This is a pre-existing condition rather than something this
build caused. It is recorded in the finding ledger under Filed 14 with that provenance, and it needs
the owner to edit the file in place.
