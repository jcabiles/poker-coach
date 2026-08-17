# Range-representation debate — external research survey (2026-07-30)

Web-grounded survey: how poker tools/bots/trainers represent villain preflop policy.

## Survey table (sources verified via WebSearch/WebFetch)

| System | Representation |
|---|---|
| OpenHoldem / OpenPPL (mature OSS bot framework) | **Hand-authored rule charts**, top-to-bottom first-match-wins (`f$preflop`), charts compiled by hand from training resources; "put the exception on top" override idiom — semantics IDENTICAL to this repo's sampler |
| GTO Wizard "Profiles" | **Fully algorithmic**: numeric action incentives (e.g. Fish = +4% call incentive) injected into a SOLVER which derives the whole strategy. Only viable because a solver re-equilibrates the tree |
| GTO Wizard core | **Precomputed solved ranges shipped as a lookup database** — generated offline, shipped as data |
| PokerSnowie | **Learned neural-net policy** (no charts). Known realism artifact: one bet size for the entire range |
| Pluribus / Slumbot / CFR bots | **Learned blueprint tables computed offline, shipped as data**; preflop needs no abstraction (169 states) |
| Loki / Poki (U. Alberta, canonical rule-based bot) | **Hybrid: algorithmically generated then frozen** — Income Rates from Monte-Carlo rollouts per opponent-count, then "hardcoded"; rule logic on top |
| Advanced Poker Training | Villains described by profile attributes (looseness, aggression, …); internals NOT public — marketing copy only |
| Equilab / Flopzilla / PokerCruncher | BOTH authored range strings AND a "top X%" percentile slider — with a USER-SELECTABLE ranking metric (equity vs 1 random ≠ vs 3 random; PokerCruncher picks vs-3 to avoid under-ranking draws) |
| Hobby OSS sims (e.g. HUPS) | Percentile-threshold generators over a 169-hand win% ordering |

## Key answers

**(b) Is hand-authored chart data the established pattern?** Yes for rule-based/scripted bots
(OpenPPL is the mature analogue, same first-match semantics); no for solver/learning systems —
but those replace charts with a bigger *table generated offline and shipped as data*, not a
runtime formula. **Nobody credible generates realistic villain preflop ranges from a scalar
"looseness" knob at runtime.** The two chart-free systems (GTOW Profiles, Snowie) both substitute
a solver or neural net — ruled out here by the no-solver invariant. Realistic choice: **authored
charts vs OFFLINE-generated charts** (the Loki pattern: simulate/generate, then freeze as data).

**(c) Alternatives ranked:**
- A1 percentile-over-one-score: documented severe failure modes — Chen non-linearity ("AKo 10,
  T9s 8, 55 5 yet any can be strongest depending on villain range"), context blindness (multiway
  favors suited/connected, ordering doesn't move), metric-dependence (top-10% differs by chosen
  equity metric), Sklansky-Chubukov "much too tight" (face-up shove ranking). Fatal for personas:
  makes every persona a nested subset of every looser one.
- **A2 generate-offline-freeze-as-data — strongest hybrid, real precedent** (Loki income rates,
  CFR blueprints, GTOW library). Preserves content/-is-truth, diffs stay reviewable, width gates
  keep working. Cost: two sources of truth + temptation to hand-patch output; authoring moves
  (to the bias/parameter table) rather than disappearing.
- A3 incentive-deltas-over-base-chart: only meaningful with a solver to re-equilibrate; without
  one it degenerates toward A1.
- A4 learned policy: ruled out (no-solver invariant; loses reviewability entirely).

**(d) Maintenance-burden correction (measured in-repo):** the authored surface is NOT
6×9×5=270 cells; it is **57 preflop nodes / 129 mixes**. Per-seat unopened nodes exist only for
tag/lag/maniac; nit/station/fish have UTG + wildcard. **Every response node (vs_limpers, vs_rfi,
vs_3bet, vs_4bet) is a position-blind wildcard for all six personas.** Consequences:
1. Maintenance alone does NOT justify a generator at 57 nodes.
2. The real gap is COVERAGE: villain responses are seat-independent (BB defend vs BTN open ==
   UTG facing UTG1 open). Going positional adds ~216 cells — at which point A2 becomes strongly
   attractive. **Deciding generator-vs-authored before deciding whether responses become
   positional is deciding in the wrong order.**
3. The explicit-node-beats-wildcard discipline + no-overlap tests is the OpenPPL idiom made
   SAFE — a strength a percentile generator would discard.
4. The width gates are the industry-standard verification framing (VPIP/PFR archetype
   thresholds); authored width ≠ realized PFR (~0.35 ratio) is intrinsic either way.

**Confidence caveats:** Loki "income rates hardcoded" wording from a search snippet (PDF
extraction failed) — substance corroborated across sources. APT internals not public.
