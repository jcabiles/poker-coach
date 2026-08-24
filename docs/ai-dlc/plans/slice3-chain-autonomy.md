# Wave plan — slice 3 chain, autonomous run (2026-08-22)

```
status:   approved       # owner, 2026-08-22 — "Go — no Fable"
slug:     slice3-chain-autonomy
spec:     docs/ai-dlc/specs/flywheel-slice3-calldown.md
tickets:  docs/ai-dlc/tickets/flywheel-slice3-calldown.md (status: approved) + S3-T5 (spec'd inside this run)
ledger:   docs/ai-dlc/ledger/flywheel-slice3-calldown.md
base:     origin/main aaaee50 (local main is 7 behind — fast-forwarded in wave 0)
rulings:  local/session-2026-08-22/rulings.md (1–11) + the six 2026-08-22 picker answers below
budget:   ~600k tokens, no check-ins; stop before the owner's blind play session
```

## 0. Bottom line

Finish improvement slice 3 (calldown — how often a bot keeps calling instead of folding) end to
end: repair the blocked S3-T2 dial retune under ruling 11, build S3-T3 and S3-T4, spec and — if
budget allows — build a new S3-T5 for the checked-down path (42–48% of showdown hands never face a
wager; the measured real lever), then hand over a close packet. Each ticket is built by one Opus
worker in its own worktree, reviewed by theory-reviewer + refuter + Codex Sol, then squash-merged
by me. Owner answers already given: merge myself · T5 spec AND build if budget remains, one
bounded pack-read lever (off = byte-identical) · ship the admissible T2 reduction with shortfall
recorded if the target misses · commit the 8 stale doc edits as a docs-only PR first.

## Why this plan is gated

**Two rules fire:** (1) **external side effects** — pushes, PR creation and **squash-merges to
main** (remote mutations, owner-authorized 2026-08-22); (2) **Opus rule borderline** — up to 2
concurrent Opus agents per wave, all at pinned `high` (within the ≤2 rule, recorded for
transparency). No foreman · ≤3 workers per wave · no force-push, no delete · re-records only under
ruling 4 (provenance + revert-to-prove-attribution).

## Worker routing

Terra pilot precondition **fails — skipped entirely**: every code ticket touches
`backend/app/domain/personas_postflop.py` (X1 + hotspot X6). No routing records emitted.
Fable: **not recommended** — Opus `heavy-worker` (pinned opus/high) covers the hard tickets; the
Director session already runs on Fable.

## Waves

| Wave | Task | Owned files | Model / agent (pin) | Barrier |
|---|---|---|---|---|
| 0a | Docs-only PR of the 8 stale edits, checked against current state | the 8 modified doc/agent files (settings.json excluded) | sonnet `implementer` (medium) | Tier 2: one blind Codex Sol review → adjudicate → merge |
| 0b | Contract map: checked-down path (nodes where no wager is made, check-through logic, river-free-showdown constants) | read-only → `docs/ai-dlc/contracts/flywheel-slice3-t5-checkdown.md` | sonnet `contract-mapper` (medium) | — |
| 0c | Contract map refresh for S3-T3 (made-value aggression path, SPR availability at the node) | read-only → `docs/ai-dlc/contracts/flywheel-slice3-t3-valueside.md` | sonnet `contract-mapper` (medium) | — |
| 1a | **S3-T2 fix round** (ruling 11): rebase WIP `319e4de` onto origin/main; guard A computed comparator; guard C log-odds; pre-reg re-derived (MDF as floor); tune nit+TAG to deepest admissible; LAG withdrawn+filed; α contract-defect filed; re-records with provenance | `personas_postflop.py`, `test_personas_postflop.py`, `content/` packs, `docs/ai-dlc/research/slice3-calldown/*` | opus `heavy-worker` (high), worktree | theory-reviewer (opus/high) + `refuter` (high) + Codex Sol (high) → adjudicate → fix loop ≤2 → verify.sh → merge |
| 1b | S3-T5 spec + pre-registration draft (Director-written from 0b; one bounded lever) | `docs/ai-dlc/specs/flywheel-slice3-t5-checkdown.md`, tickets file append | Director | Tier 2: `refuter` (high) + Codex Sol (high), blind |
| 2 | **S3-T3** SPR multiplier on made-value aggression + contract §3 amendment | postflop module + test + theory-contract §3 | opus `heavy-worker` (high), worktree | same triple review → merge |
| 3 | **S3-T4** α-guard over ACE_HIGH + non-vacuity test; damp re-derivation only if ruling 7 fires | postflop module + test | opus `heavy-worker` (high), worktree | theory-reviewer + refuter (+ Sol if re-derivation fires) → merge |
| 4 | **S3-T5 build** (only if ≥150k budget remains after wave 3) | postflop module + test + packs | opus `heavy-worker` (high), worktree | triple review → merge |
| 5 | Close packet: band harness + 50k export before/after across chain; analytics `FLYWHEEL-STATUS.md` pointer refresh; roadmap rev 6; play-session checklist | docs + analytics status | sonnet `implementer` (medium) for measurement runs; Director for docs | `review-work` completeness pass |

Waves 1a‖1b, and each later wave's review, run concurrently where files are disjoint. Code
tickets are strictly serial (single-owner hotspot).

## Stop conditions (no check-in; report at the end)
- LAG–TAG separation floor binds → stop that ticket, report, continue the chain (ruling 3).
- Ceiling breach → hold below, never ship (ruling 5).
- Any reviewer CONTRACT-DEFECT → file in ledger; never edit the α test (ruling 10).
- Budget reached → finish the current PR's review, do not start the next.

## Wave 5 execution plan (2026-08-23 — /ai-org:build ceremony; supersedes the one-row wave-5 entry above)

```
status:   approved        # owner picker 2026-08-23: merge-after-review · LAG dial stays filed ·
                          # table-controls freeze KEPT · prune merged-only. Go gate: "Go" + no-Fable-workers, owner 2026-08-23.
base:     main 0561e8f (S3-T5 merged; chain complete)
budget:   run until Director context ~300k (owner directive 2026-08-23)
```

Scope: close improvement slice 3's record. No engine, pack, or frontend change of any kind —
the tip your blind play session judges stays byte-identical at `0561e8f`.

| Wave | Task | Owned files | Agent (model / pinned effort) | Barrier |
|---|---|---|---|---|
| 5a | Measurement runs: band harness + 50k export went-to-showdown at baseline `d351150` and tip `0561e8f`; write the before/after table with pins | `docs/ai-dlc/research/slice3-calldown/close-measurements.md` (+ scratchpad outputs) | `implementer` (sonnet / medium) | joint fan-in below |
| 5b | Finale-readiness packet: rule-breaker control (PR #184) vs estimand §d.2, execution-checklist walk-through, cost band recomputed at live prices; read-only otherwise | `docs/ai-dlc/research/slice3-calldown/finale-readiness.md` | `implementer` (sonnet / medium) | joint fan-in below |
| 5c | Prune worktrees/branches whose commits are ALL in main — `git worktree remove` (no force) + `git branch -d` (lowercase only) + `git worktree prune`; never touch unmerged refs, remotes, or the two dirty files in the shared tree | git worktree/branch state + `local/session-2026-08-23/prune-log.md` | `implementer` (sonnet / medium) | joint fan-in below |
| — | **Fan-in:** Director audits each worker's output; 5a's tool runs must have exited 0 with pins recorded; 5c's log lists every removal with its merge proof | | | |
| 5d | Director synthesis: committed close packet (from the local draft + ledger Filed 1–15 + 5a numbers) · owner decision memo · roadmap rev 6 · play-session checklist · `profile.md` Resume block · analytics `FLYWHEEL-STATUS.md` pointer refresh (ruling 9) | `docs/ai-dlc/research/slice3-calldown/close-packet.md`, roadmap, profile, checklist; `poker-analytics:docs/FLYWHEEL-STATUS.md` | Director | `refuter` (high) blind on the coach PR + `review-work` completeness pass → fix loop ≤2 |
| — | **Merges:** one coach docs PR + one analytics docs PR, squash-merged after review per the 2026-08-23 merge-authority answer | | | |

Maker≠checker: Director writes 5d, so the refuter review is mandatory (no Tier-0 exemption
taken). GATE.md triggers: external side effects (push, PR create, squash-merge to main) —
hence this written plan and the explicit go gate. Concurrency: 3 Sonnet workers, disjoint
files, no foreman, no Opus spawns, no Fable workers (Fable gate asked 2026-08-23).

## Progress log (2026-08-22)
- Wave 0 ✅ — #214 merged `b151c17` (docs). Two contract maps written. T5 spec rev 2 READY (rev 1 failed blind review; confirmation pass PASS-WITH-FIXES applied).
- Wave 1 ✅ — S3-T2 #215 merged `4f653ef`: nit −1.80pp / TAG −6.15pp WTSD, LAG withdrawn (coupling, filed). Review: refuter PASS, Sol PASS-WITH-FIXES, theory NEEDS-WORK → all docs fixes applied. ⚠️ Owner ack needed: unopened-arrival watch band re-centred 0.305→0.325 (upper edge 0.335→0.355).
- Wave 2 ▶ — S3-T3 worker spawned on `feat/slice3-t3-spr-value`.
- Wave 2 ✅ — S3-T3 #216 merged `abcfd97` as INSTRUMENT + LIMITS: the SPR value damp was built (all criteria green), then WITHDRAWN after theory reviewer (2 HIGH) + Codex Sol (BLOCKER) converged that its direction contradicts SPR commitment play (TOP_PAIR P(bet) flat in SPR for every persona; `s/(1+2s)` reversed). Refuter PASS on the build. Engine byte-identical to main. Open item filed: value-side commit SLOPE.
- Wave 3 ▶ — S3-T4 worker spawned on `feat/slice3-t4-alpha-acehigh` (ruling-7 condition known not to fire: station 70.1 / LAG 57.7 vs ≥5pp down from 71.1 / 57.3).
- Wave 3 ✅ — S3-T4 #217 merged `72322d0`: α guard over ace-high river FAILS 24/24 → shipped xfail(strict) + finding; damp re-derivation not fired (ruling 7 missed). ⚠️ Owner re-ruling filed: α per-RANGE vs per-BUCKET (ledger Filed 10). Refuter PASS; theory NEEDS-WORK → docs fixes applied.
- Wave 4 ✅ — S3-T5 #218 merged `0561e8f`: late-street bet lever; per the pre-registered
  per-persona ship rule only the LAG ships it (nit and TAG withdrawn). Triple review; report +
  rev-2 pre-registration in `../research/slice3-calldown/`.

## Progress log (2026-08-23, wave 5 under /ai-org:build)
- Wave 5a ✅ — chain-wide WTSD measured, both instruments, `d351150` → `0561e8f`
  (`../research/slice3-calldown/close-measurements.md`); every number reproduces its source
  report cell-for-cell; sonnet implementer, exit 0 on all four runs.
- Wave 5b ✅ — finale-readiness packet (`../research/slice3-calldown/finale-readiness.md`).
  Crux: control problem solved in shipped code (PR #184 + §g.5 A). Director verified and FIXED
  the one gap found: checklist §5 aligned to §g.5 clause C (all four judge slots); control-
  redesign ticket closed as superseded; Anthropic prices filled from the current reference.
- Wave 5c ✅ — 11 fully-merged branches deleted; 0 worktrees removable (sandbox denies
  `.git/worktrees/` writes — owner terminal commands in `local/session-2026-08-23/prune-log.md`).
- Wave 5d ✅ — Director synthesis: close packet, owner-decisions memo, play-session checklist,
  roadmap rev 6, profile.md Resume block, analytics FLYWHEEL-STATUS pointer refresh.
- Fan-in record: maker≠checker honored — Director-authored docs reviewed by a fresh refuter
  (high) before merge; worker outputs audited by Director (5a's anomaly attribution corrected:
  S3-T5, not S3-T3/T4, is the post-T2 behaviour change).
