# Slice 3 close — the decisions filed for the owner, in one place

**Bottom line.** Improvement slice 3 (calldown — how often a bot keeps calling
instead of folding) shipped its whole ticket chain and left **one decision that
unblocks two other items (the α question, decision 1), two scope decisions for
the future re-anchor slice (decisions 3 and 4), one acknowledgment (decision 5),
and two follow-ups that stay parked (decision 6)**. Nothing here blocks the
blind play session; every engine value is already merged and stable at the tip
the session will judge. Each item below states what is being decided, the
recommendation, and what the recommendation gains and costs. Full evidence
lives in the ledger (`../../ledger/flywheel-slice3-calldown.md`, "Filed" items)
— this memo cites but does not repeat it.

*(2026-08-23 note: two decisions were already taken at the wave-5 go gate and
are recorded, not re-asked: the LAG's calling dial stays filed untouched, and
the table-controls lane stays frozen until the finale. See
`local/session-2026-08-23/rulings.md`.)*

---

## Decision 1 — Is α a per-RANGE bound or a per-BUCKET bound? (ledger Filed 10; reshapes Filed 2, gates Filed 8 and 9)

**What is being decided.** α = f/(1+f) is the poker-theory ceiling on how often
a defender may fold facing a bet of f times the pot. Your 2026-08-19 ruling
applied it to one hand class — naked ace-high on the river — and the guard
built to enforce that fails for all six personas at all four prices (24 of 24
cells, by +0.27 to +0.64). The theory reviewer then showed the obligation
itself is mis-specified: α bounds the defender's **whole range**, and applied
to the ace-high bucket alone it is provably wrong in both directions — too
strict at large bets (the range's stronger hands already supply all the
required defence, so ace-high may fold outright) and too loose at small bets
(the identity actually demands ace-high continue essentially always). The
arithmetic is in Filed 10 and is not close.

**Recommendation: re-rule that α is a per-range bound; withdraw the 2026-08-19
per-bucket ruling; DELETE `test_ace_high_river_alpha_ceiling` (not soften it).**
- **Gains:** closes Filed 9 (the 24-cell breach stops being a breach — there is
  no per-bucket obligation to breach); dissolves Filed 8's target (no damp
  re-derivation owed against a bound that doesn't exist); reduces Filed 2 to
  its real residual question (below). The W3R-1 rule — infeasibility is
  evidence about the target, not a licence to widen levers — points exactly
  here: compliance would need a constant ~60× its shipped value, which the
  showdown bands already refused at 7.5×.
- **Costs:** the river loses its only ace-high-specific guard (the one-way
  tripwire from ticket S3-T4 is deleted with it), and if you later decide
  ace-high folding IS a realism defect, that claim will need a new, correctly
  grounded target — the α identity can no longer be borrowed for it.
- **If you rule the other way** (α does bind buckets): say so with a source,
  and the ~60×-constant conflict between that ruling and the went-to-showdown
  bands comes back to you as Filed 9 unresolved.

**Residual of Filed 2 either way:** may a tight archetype (the nit) sit closer
to the range-level α wall than a loose one, or cross it deliberately, as real
nits do? Needs a sourced margin before any test admits it. No recommendation —
this is a modeling-philosophy call, and it only becomes live when a slice next
pushes the nit's calling dial.

## Decision 2 — Value-side commit slope: in scope for the re-anchor slice? (Filed 5, HIGH; the one open item from the withdrawn S3-T3 lever)

**What is being decided.** A bot's probability of betting top pair or middle
pair is measured FLAT in stack depth — identical to twelve decimal places at a
stack-to-pot ratio of 10 and of 0.3, for every persona — where commitment says
it should rise toward certainty as stacks shorten. The missing mechanism is a
continuous commitment slope over those two hand classes; it interacts with the
existing commit step (which it would partly subsume), which is why it was
filed rather than built.

**Recommendation: rule it IN scope for the single designated re-anchor slice,
with the replace-vs-compose question decided inside that slice's spec.**
- **Gains:** the highest-severity open engine defect gets a home instead of
  floating; the re-anchor slice is already the place where §3/§4 contract rows
  get re-derived together, which this needs.
- **Costs:** the re-anchor slice grows by one genuinely hard mechanism
  (regression risk on the commit step it touches); if the re-anchor is far
  away, the flat-in-stack-depth tell stays in the roster until then.

## Decision 3 — Bucket-aware fold lever: same question, smaller item (Filed 1)

**What is being decided.** The calling dial multiplies fold-versus-continue
odds equally in every hand-strength class, so it cannot close the
fold-to-continuation-bet gap (the nit runs out 16 points short with air
already folding 0.89). The natural fix is a per-bucket term on the fold side,
owned by theory contract §4 row P8.

**Recommendation: park it under row P8 as written; build only if a slice is
ever opened whose goal is the fold-to-continuation-bet gap.** Severity is
MEDIUM precisely because nothing currently red depends on it.
- **Gains:** no speculative engine work before the finale; the item is already
  filed where the contract says it must be specified.
- **Costs:** the FtC gap (nit 0.435 vs a grounded floor of 0.60) stays as-is —
  visible to anyone reading the band harness, though no gate asserts it.

## Decision 4 — Adopt Filed 15's registration rule as standing process law?

**What is being decided.** S3-T5 registered a reduction floor against a
three-persona configuration and then shipped one persona, making a real but
misleading-looking shortfall. Filed 15 proposes the rule: a floor is registered
against the configuration proposed to ship, and if the ship list changes, the
floors are re-derived before values land.

**Recommendation: adopt it — add one line to the pre-registration section of
the theory contract's obligations (§11) at the next contract-touching PR.**
- **Gains:** prevents a recurring class of fake misses on any gate-decided
  ship list.
- **Costs:** one contract edit; slightly more re-derivation work on tickets
  whose ship list is decided late.

## Decision 5 — Acknowledgment: watch band re-centred in PR #215

The unopened-arrival watch band (a non-gating diagnostic) was re-centred
0.305 → 0.325, upper edge 0.335 → 0.355, when S3-T2's dial retune moved the
statistic it watches. The 12-seed table is in the T2 fix-round report. Nothing
to decide unless you object; **acknowledge and move on.**

## Decision 6 — Two follow-ups that stay parked (no action needed)

- **`_ACE_HIGH_RIVER_CALL_DAMP` re-derivation (Filed 8):** blocked by its own
  headroom bar (station and LAG each ≥5pp down; measured 4.05pp and 5.41pp
  short) AND dissolved entirely if decision 1 goes per-range. Do nothing now.
- **`_DRAW_FREE_RIVER_PROB` at 0.30 vs ~0.50 (Filed 4):** ruled out of this
  slice on 2026-08-22; owned by contract §4 row P6/F7 for whichever slice
  re-derives it. Do nothing now.

## Smaller contract-hygiene items (bundled for whoever next touches the contract)

- **Filed 13 (MEDIUM):** no theory-contract row governs unopened late-street
  betting — the node S3-T5 just added a lever to. Becomes blocking the moment
  a second ticket touches that node. The hard part: a credible row would
  require a river checking range containing some strong hands, which today's
  engine cannot produce there (value cells at 0.83–0.99, one-pair floored at
  zero). Recommend: write the row at the re-anchor slice, where the river leg
  is recalibrated anyway.
- **Filed 14 (LOW):** the engine applies the position multiplier last where §7
  writes the order the other way. Arithmetically irrelevant today
  (multiplications commute); fix the contract text before any factor becomes a
  clamp or floor.
- **Filed 11 (recorded, already fixed in the harness):** "never faced a wager"
  and "checked down" are different statistics (nit: 51.5% vs 31.7%); older
  documents quote the first where they mean the second. Future gates should
  use `checked_down`.
