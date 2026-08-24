# Tickets — slice3-decisions-execution + publication readiness

status: approved (owner, 2026-08-24) — scoped: the owner's `/ai-org:build` invocation
authorized **Lane A + Lane B only**, which is Chain 1 (E1 → E2 → E3). Chain 2 (P1–P4,
the poker-analytics publication readiness lane, called Lane C in the spec) is NOT
authorized in this run and remains `draft` for a later build.

**Bottom line.** Seven tickets in two independent chains. Chain 1 (poker-coach, E1→E2→E3,
serial — same doc surfaces) executes the six owner rulings + roadmap reconciliation. Chain 2
(poker-analytics, P1→P2→P3→P4, serial — maker≠checker ordering) delivers publication
readiness. The chains share no files and may run in parallel. Spec:
`../specs/slice3-decisions-execution.md`. Contract map:
`../contracts/slice3-decisions-execution.md`. Review ledger:
`../ledger/slice3-decisions-execution.md`.

## Chain 1 — poker-coach (one PR, branch `chore/slice3-decisions-execution`, own worktree)

- **E1 — Theory-contract amendments.** Implement spec Package 1 items (a)–(f) in
  `docs/ai-dlc/contracts/persona-realism-theory-contract.md`: α per-range amendment block +
  2026-08-19 withdrawal; §11 item 16 in the W3R-1 dual pattern; §7 :446 factor-order text
  fix; §3 A8 item 5 cross-ref; §4 P8 parking note; Filed-13 deferral note.
  *Acceptance:* every one of the six rulings traceable to a dated edit; amendment convention
  followed (no version bump). *Done-condition:* `cd backend && PYTHONPATH=. python -m pytest
  tests/test_contract_provenance.py -q` green. *Owns:* the theory contract file.
- **E2 — Test deletions + comment corrections** (depends on E1 for wording consistency).
  Delete the three α tests, the :980-1034 narrator block, and orphaned helpers per spec;
  correct the surviving :8421-8428 docstring; comment-only corrections in
  `personas_postflop.py` :323-370 and :1742-1748. *Acceptance:* no surviving text asserts
  the per-bucket ruling as live; no code token outside comments changes in the domain file.
  *Done-condition:* `./scripts/verify.sh` green, `ruff check .` clean, suite shows 0 xfails
  from the α family (baseline had 6). *Owns:* the two backend files.
- **E3 — Ledger closures, consistency sweep, roadmap edits** (depends on E2). Dated
  adjudication notes under Filed 1/2/4/5/8/9/10/11/13/14/15 (9+10 together);
  `contracts/flywheel-slice3-calldown.md` :76-84 tension resolved + :108 refs fixed;
  roadmap slice-3 entry updated (S3-T4 ruled, six-decisions batch recorded) AND the Lane-B
  NEXT entry marked satisfied-2026-08-06 by registry v2 (spec Package 2); grep sweep for
  remaining live citations. *Done-condition:* sweep grep returns only
  historical/adjudicated mentions. *Owns:* ledger, contract map, roadmap
  (`bot-realism-flywheel.md` is a hotspot-class shared doc — single owner, this ticket).

## Chain 2 — poker-analytics (one PR, branch `chore/publication-readiness`, own worktree)

- **P1 — README front door.** Rewrite `README.md` for a skeptical senior-analytics reader:
  what the repo is, the three write-ups, decision records, limitations. *Done-condition:*
  README links resolve; `make scorer-test` untouched/green.
- **P2 — Methodology write-ups pass + cards** (after P1). Publication-grade clarity pass
  over the three `docs/methods/` write-ups + a score-design/validation-failure narrative;
  dataset/model cards with reproducibility pins. Content corrections only where a claim is
  wrong against its own sources; no result softened; every limitation travels.
  *Done-condition:* each doc opens with a standalone bottom line; limitations sections
  present and complete.
- **P3 — Hiring-manager red-team** (after P2; fresh reviewer agent, maker≠checker).
  Adversarial review of the would-be-public surface from a skeptical hiring-manager persona.
  Findings adjudicated in a ledger, never auto-folded. *Done-condition:* red-team report +
  adjudication committed under `docs/`.
- **P4 — Readiness report + strip-list proposal** (after P3). Final report naming every file
  judged, the proposed strip list, and the open owner decisions (visibility flip). Filed for
  the owner; nothing published, repo stays private.

## Parallelization

Chain 1 ∥ Chain 2 (disjoint repos/files). Within each chain: serial.

## Not in any ticket

Engine behavior, pack values, registry content, finale run, play session, PR merges,
visibility changes.
