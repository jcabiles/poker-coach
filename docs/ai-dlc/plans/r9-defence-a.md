# Wave plan — R9-DEFENCE-a

```
status:   approved      # owner, 2026-08-02 — "Go — build all six waves"; Fable declined (Opus sufficient)
slug:     r9-defence-a
spec:     docs/ai-dlc/specs/r9-defence-a.md (rev 2)
tickets:  docs/ai-dlc/tickets/r9-defence-a.md (status: approved)
ledger:   docs/ai-dlc/ledger/r9-defence-a.md
base:     origin/main 8cc6c38 — verified green (1386 passed, 1 skipped, exit 0, read unpiped)
risk:     medium-high
```

## Why this plan is gated

**One rule fires: external side effects** — the slice ends in a `git push` and a `gh pr create`
(remote mutations). GATE.md v3 makes that a floor no project setting waives, so this plan is written,
presented, and **not executed until an explicit affirmative**.

Everything else is **ungated**: max 2 concurrent workers per wave (cap is 5) · max **2** concurrently
active Opus agents, all at pinned `high` effort (the Opus rule permits ≤2 at ≥high) · no foreman · no
irreversible action (no force-push, no delete, no re-record).

## Worker routing — every ticket classified

Terra pilot precondition **fails and Terra is skipped entirely**: zero tickets carry a positive signal
(S1/S2/S3), so there is nowhere near the ≥10 genuine candidates the pilot requires. Records below are
mandatory, not decorative.

| Ticket | route | evidence | exclusions | conf | Model / agent (pinned effort) | Why |
|---|---|---|---|---|---|---|
| T1 lever | sonnet | none | X1 | high | `implementer` — sonnet / **medium** | Scoped: one bounded field + a validator on a landed precedent, six JSON edits. |
| T2 mechanism | sonnet | none | X1, X2, X3 | high | `heavy-worker` — **opus / high** | Engine spine. Scope predicate, facing-branch gate, and a comment block that must state two things rev 1 got wrong. |
| T3 estimator | sonnet | none | X1, X2 | high | `heavy-worker` — **opus / high** | Behaviour-touching, and the naive implementation passes heads-up while being wrong multiway (ledger R-9). |
| T4 node gates | sonnet | none | X1, X3 | high | `heavy-worker` — **opus / high** | The gates are what two reviewers just broke. Highest-judgment ticket in the slice. |
| T5 harness + paired run | sonnet | none | X1, X3 | high | `heavy-worker` — **opus / high** | Must re-plumb seed generation without moving one pinned number. |
| T6 parity gates | sonnet | none | X1 | high | `implementer` — sonnet / **medium** | Four named discriminators, fixture construction, no design judgment left open. |
| T7 mutants | sonnet | none | X1, X3 | high | `implementer` — sonnet / **medium** | Six pre-specified mutants; path is known, the work is running it. Escalation (not repair) is a brief boundary. |

Effort is delivered by **agent pin**, not by a parameter — the Agent tool has none. `implementer` is pinned
medium; `heavy-worker` is pinned high.

## Waves

| Wave | Tickets | Owned files (disjoint within wave) | Concurrent Opus | Barrier |
|---|---|---|---|---|
| **1** | T1 | `content/models.py` · `content/personas/*.json` | 0 | pytest + ruff · **tag `RED-REF`** |
| **2** | T2 | `personas_postflop.py` | 1 | pytest + ruff |
| **3** | T3 ∥ T4 | `range_estimate.py` ‖ `tests/test_personas_postflop.py` | 2 | pytest + ruff · red-first evidence captured |
| **4** | T5 ∥ T6 | `tests/test_personas_postflop.py` ‖ `tests/test_range_estimate.py` | 1 | pytest + ruff · bands diffed unchanged |
| **5** | T7 | scratch only | 0 | mutant table complete |
| **6** | T8 | `ledger/` · `roadmap/` | — | **fan-in LLM review + adjudication (Director)** |

**Serialization I am forced into, stated rather than hidden:** T4 and T5 both own
`tests/test_personas_postflop.py`, so they **cannot** run concurrently — T5 waits for T4. That is why waves
3 and 4 exist instead of one four-way fan-out. Real parallelism in this slice is two pairs, nothing wider.

## The RED-REF decision

Red-first evidence is captured **after wave 1, before wave 2** — packs authored, engine untouched — not
against bare base. At bare base the lever does not exist, so the gates would raise `AttributeError`; that is
technically red but it is *evidence of a missing attribute*, not evidence the mechanism is absent. At
RED-REF the gates fail on their assertions and produce the table that matters: `ΔP(fold) = 0.000000` per
persona against a gate demanding `≥ 0.05`. This mirrors N-LOGIT's own red-first shape.

Mechanically: after wave 1 lands, its commit is checked out into a second read-only worktree whose path is
handed to the T4 and T5 workers as the red measurement target.

## Review policy

**Tier 1 (GATE.md) — there is an executable oracle, so no LLM reviewer per wave.** Deterministic checks at
every barrier (`pytest` unpiped into a file, `ruff`), plus the acceptance gates themselves. LLM review is
concentrated where it earns its cost:

- **T7 is a maker≠checker mechanism, not a document review** — a different agent attacks the harness with
  six mutants. If the harness passes a mutant it should catch, that is a harness defect and the ticket
  escalates rather than repairs.
- **Wave 6 fan-in:** fresh `refuter` (Opus) + `persona-realism-theory-reviewer` + Codex Sol, all
  **GIT-READ-ONLY** and all **pinned to base explicitly** (a contract scan in this slice mapped a stale tree
  and reported the prerequisite as missing — ledger S-0.1). Findings are **adjudicated with pushback, never
  auto-folded**; every accept and reject recorded with reasoning.

## Non-negotiables injected into every worker brief

Domain purity (`backend/app/domain/` imports no web/DB, test-enforced) · results are frequency + EV, never
boolean · strategy lives in versioned `content/` data · `spot_signature()` frozen · **never edit
`tests/test_price_tail.py`** (23 frozen exact-equality vectors — needing to edit it means the implementation
diverged) · **a fixture that moves is a signal, not a re-record opportunity** · **never read a suite result
from a piped exit code** — redirect to a file and read the file · workers self-verify but never self-approve
· workers touch only their owned files · workers never commit and never run git mutations.

## Escalation triggers pre-registered

- Any pinned band exits → **STOP, escalate to W4-b**; do not widen, do not re-scope (spec P-7).
- A mutant passes a gate that should catch it → harness defect; fix the harness, never the mutant.
- `tests/test_price_tail.py` needs an edit → implementation has diverged from the spec.
- T5 cannot hold the existing bands byte-identical → the harness threading leaked into the default path.

## Cost shape

Five sequential waves, ≤2 workers each — this is a mostly-serial build with two parallel moments, not a
fan-out. Four Opus tickets (T2, T3, T4, T5) are the substantive spend; T1/T6/T7 are Sonnet. The fan-in
adds one Opus reviewer, one project reviewer, and one Codex Sol run.
