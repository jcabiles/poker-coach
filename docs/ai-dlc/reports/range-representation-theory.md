# Range-representation debate — theory-contract review (2026-07-30)

Verdict: **reject full replacement by percentile-over-one-ordering; adopt the constrained middle
ground: authored charts as source of truth + more deterministic ordering GATES; generator
permitted only narrowly (missing-node scaffolding), parameters committed under content/.**
The reviews' defects argue for algorithmic *constraints*, not an algorithmic *generator*.

## Contract findings

- **HIGH / contract:156 (§5a):** "any ordering or monotonicity claim → [UNVERIFIED]" — a
  percentile-over-one-ordering generator IS an ordering claim end to end; it would rest the
  roster's whole preflop identity on the contract's single largest unsourced licence. Percentile
  targets may be fit seeds only, never HARD gates (§5a obligation 1, contract:220).
- **HIGH / roadmap:2269 (R9-N9) + contract:222 (W3R-1 rule):** a width-only generator collapses
  preflop identity onto ONE dial (width), which is structurally the compensating-lever escape
  hatch N9/W3R-1 exist to close. Keep a node-local remedy surface.
- **HIGH / blast radius:** a regenerate rewrites all six packs in one acceptance event — against
  the lane's split-slice anti-laundering rule (roadmap:1998-2001), W5-B's one-owner-per-JSON,
  and R10-COUNT band re-record authority (PRE2 sole re-recorder). No generator emission inside
  the open R10 lane.
- **MED / composition axis:** a width model cannot express action composition at FIXED
  membership — the axis carrying most archetype identity (contract's format-INVARIANT VPIP−PFR
  gap diagnostic, contract:90/96). Measured at HJ unopened: station VPIP 47.8%/RFI 1.2%; fish
  43.3/3.8; tag 38.2/38.2. Station literally limps AA/KK/AKs 0.5 (calling_station.json:22);
  maniac 4-bet/shove tiers are blocker-polar (A5s-A2s shove 0.5 while TT/JJ/AQs only call —
  maniac.json:160-162) — the aggressive set is not a prefix of ANY single ordering. Any
  generator must be two-dimensional (width ladder + per-persona action assignment) and accept
  authored non-monotone overrides at top-of-range and blocker tiers.
- **MED / CONTRACT-DEFECT (silence):** no §4 lever / §5 row covers preflop range CONSTRUCTION or
  per-seat RFI — why R10-1a/1b/1c drifted with no gate able to see them, AND why a generator
  would be unauditable today (no sourced ladder to fit). Fill R9-SEATPROV (per-seat RFI
  provenance, roadmap:1923) BEFORE entertaining percentile-target models. Meanwhile the
  deterministic cross-persona ordering gates are the correct substitute (need only §1's
  caricature ordering, not a sourced level).
- **LOW / contract:252:** nothing in the contract requires HAND-authoring — the binding clause
  is WHERE identity lives (versioned content/ data), not who typed it. Convention ≠ contract.

## Measured nesting analysis

Containment (played-set of A inside B) at HJ: nit→everyone 97-100%; tag→lag 100%;
station→lag 97%; fish→lag 97%; **maniac↔lag 92%/88% — the only genuine mutual non-nesting.**
So the width axis already explains ~90% of authored content — the generator is a modest
labor-saver and NOT where the 3-4/10 realism score comes from. The ~10% residual it would
destroy (action composition, blocker tiers, per-persona suited-vs-offsuit ordering:
recreationals carry 74s+/63s+/53s/43s while stopping at K8o+; nit carries A6o+/K7o+ while
stopping at K4s+/Q6s+) is precisely the realism-bearing part.

**Arrival caveat:** 65-77% of every persona's first-in chances are EP at this limp-heavy table
(roadmap:399); a generator authors a prettier ladder but does not touch the arrival half of
R10-1. Its selling point (clean JSON) is the surface the lane already ruled non-certifying
("certify via R10-COUNT measurements, never via JSON diffs", roadmap:2033-2035).

## Per-defect: does a generator fix it?

| Defect | Generator fixes? | Gate fixes? |
|---|---|---|
| R10-1a ladder below LAG | yes, by construction | **yes — PRE2's gate already is the constraint, no generator needed** |
| R10-1b premium folds | only incidentally | **yes, fully (PRE1, shipped)** |
| W5-b3 nit>tag inversion (missing per-seat nodes) | **yes — strongest pro-generator case** (natural output = one node per seat) | partly (detects; human still authors 8 nodes) |
| R10-1c undifferentiated vs_3bet | **HURTS** — correct vs-3bet ranges are polar/blocker-driven; "top X%" is wrong for maniac/lag | yes (R10-3BET's deterministic gates) |

## Recommendation

1. Authored charts stay source of truth (node-local remedies preserved).
2. Extend deterministic cross-persona/cross-seat ordering gates (current trajectory). Post-lane
   candidates: per-seat monotonicity within pack; nested-containment ordering across the reg
   tier; VPIP−PFR gap ordering (station/fish ≫ regs) as authored-shape assertion.
3. Generator ONLY as scaffold for missing-node axis (W5-b3-class), emitted skeleton hand-filled,
   committed; parameters under content/; build-time tool (backend/tools/), never imported by
   app/domain/; sampler untouched.
4. Never certify generated packs by JSON diff (roadmap:2033-2035).
5. No percentile TARGETS as gates until R9-SEATPROV lands.

## Roadmap impact

No adjustment mid-lane; file as LATER design bet; revisit after R10-3BET closes the lane.
**Nothing queued is wasted if the generator is later adopted** — PRE1/PRE2/3BET gates are
authored-shape assertions on committed JSON and hold identically whether human or tool produced
it; strictly forward-compatible with either answer. What would change the answer: two of {a
second independent per-seat RFI source (unblocks R9-SEATPROV); R10-COUNT showing ordering gates
fail to move measured separation; a fourth+ defect class that is genuinely width-shaped}.
