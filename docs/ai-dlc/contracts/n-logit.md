# Contract map — the postflop facing-chips node (ahead of `N-logit`)

**Source:** `contract-mapper` sub-agent (read-only), run against HEAD `61efc42` / `origin/main` `c12f773`.
**Persisted by:** the Director, with **measured corrections** appended per finding. The mapper's report is an
input, not gospel — several of its highest-ranked risks are **moot under the design actually chosen** (see
"Design-conditional status" on each), and one of its numeric claims is **superseded by measurement**.

Scope mapped: `backend/app/domain/personas_postflop.py::sample_postflop_decision` — the FOLD/CALL/RAISE merit
block (`:817-899`), the SPR-commit block (`:958-996`), and the single normalization + action draw
(`:998-1004`).

---

## ⚠️ REV-2 AMENDMENT (2026-08-02) — read before any status line below

This map was written against **spec rev 1**, whose design edited no pack. Rev 1 was rejected (ledger R-1: the
mechanism cancelled and was a measured no-op). **Spec rev 2 adds a new pack field `continue_ref`, edits all
six `content/personas/*.json`, and bumps six `version` strings.** Codex Sol's rev-2 delta review raised this
staleness as a MED finding; it is accepted. Corrections, which **override** the per-contract status lines
further down wherever they conflict:

| contract | rev-1 status below | **rev-2 correction** |
|---|---|---|
| **C4** (`aggression` unbounded; JSON Schema does not model `postflop`) | "DISSOLVED — no pack edit" | **Partly stands, partly superseded.** No `aggression` value moves and the 5.6 cap still never binds — that part holds. But rev 2 **does** edit packs, adding `continue_ref`. Because `persona.schema.json` does not model the `postflop` block at all, **the new field gets no JSON-Schema validation** — pydantic's `Field(gt=0.0, le=8.0)` is the only gate, and Codex proved that gate insufficient (accepts subnormal `5e-324`; `model_copy(update=…)` bypasses it entirely). |
| **C6** (`looseness` positivity is the division's safety guarantee) | "🔒 load-bearing; G7 pins it" | **Superseded.** Rev 2 performs **no runtime division by `looseness`** — the divisor is `continue_ref`. The safety obligation therefore **moves to the new field**, and the model-layer argument is *not* sufficient on its own: a meaningful lower bound plus a runtime guard is required, because `model_copy` skips validation. |
| **C8** (pack versions not enforced) | "NOT TRIGGERED — no pack edit" | **NOW TRIGGERED.** Six packs change and six versions bump. Nothing enforces the bump, so it must be asserted by test. The suite's `_packs_fingerprint` hashes pack **content**, so the fingerprint moves by design — expected, not a defect. |
| **Blast radius #4** ("pack-authored numeric pins: NONE") | "Dissolved" | **Re-opened at MEDIUM.** Not for `aggression` (untouched), but for the new field's load / serialize / fingerprint / cache path. |
| **Gate IDs cited in C1, C3, C8** (`G5`, `G6`, `G7`) | rev-1 numbering | **Renumbered in rev 2.** One-draw is now **G5**, estimator **G6**, validation **G7**, provenance **G8**. The estimator criterion is no longer "exactly three keys" — it is conditioned on the node's legal set. |

**New surfaces rev 2 introduces that this map did not cover** (flagged, not yet mapped — they are the build's
responsibility and are gated in the rev-2 ticket plan): schema/pack atomicity, unknown-field behaviour on
load, model serialization + `_STATS_EXT_CACHE` fingerprinting under a changed pack, validation bypass via
`model_copy`, and the authorship question of whether an explicit JSON `null` is forbidden while field
*absence* remains the legacy opt-out.

**Unchanged and still authoritative:** C1 (single action draw), C2 (single normalization), C3 (estimator
capture + the parity-tests-cannot-catch-shared-corruption trap), C5 (`_AGGRESSION_CAP` rationale — rev 2 does
not touch it), C7 (B5b absolute subtraction), and every "Traps" entry.

---

## Contracts

### C1 — the action draw is the FIRST `rng.choices` call, and the sizing draw is the SECOND
Stated in the docstring (`personas_postflop.py:788-790`) and again at `:1004`. Consumers that hard-depend on
exactly one pre-sizing draw, each recording only the first call:

| consumer | file:line |
|---|---|
| estimator capture rng | `app/domain/table/range_estimate.py:307-324` |
| node-trace harness | `tests/node_trace.py:51-66` |
| price-tail probe | `tests/test_price_tail.py:61-74` |
| multiway catch probe | `tests/test_mw_catch_toppair.py:10-14` |
| `_FirstChoicesRecorder` | `tests/test_personas_postflop.py:473-486` |
| `_CaptureWeights` | `tests/test_personas_postflop.py:849-857` |
| `_SeededCaptureRng` | `tests/test_personas_postflop.py:1031-1044` |
| `_CaptureFirstChoices` | `tests/test_range_estimate.py:494-504` |

**How a naive N-logit breaks it:** a literal two-stage implementation draws stage 1 (`{FOLD, CONTINUE}`) then
stage 2 (`{CALL, RAISE}`). Every capture above then records a **2-outcome** vector where all consumers expect
the 3-outcome `(FOLD, CALL, RAISE)` vector, and the sizing draw becomes the 2nd or 3rd call depending on the
outcome drawn — a call count no capture rng is built for.

> **Design-conditional status: NOT TRIGGERED.** The chosen design keeps **one** normalization and **one**
> action draw; the nesting is achieved algebraically (a shared factor on the defend pair), not by a second
> `rng.choices`. C1 is preserved by construction. The spec still gates on it (`G4`) because the property is
> load-bearing and must not be lost silently in a later refactor.

### C2 — normalization is single, over the flat `entries` list
`personas_postflop.py:998-1004`, pinned by the docstring at `:753-754`. Every downstream operator
(`_commit_transform`, the B5b damp, `_price_factor`, `_MW_CATCH_TIGHTEN`) is defined as an operation on flat
**pre-normalization merits** sharing one denominator.

> **Design-conditional status: PRESERVED.** The chosen design adds one multiplicative pass over the existing
> `entries` list immediately before `:998`; the list shape, ordering and denominator are unchanged.

### C3 — `range_estimate` treats the captured first-call weights as the whole action distribution
`_postflop_action_dist` (`range_estimate.py:345-367`) returns `dict(zip(cap.population, cap.weights))`
directly as `P(action | context)`, feeding the Bayesian reweight at `:429-433`. The reweight uses
`dist.get(ctx.observed, 0.0)` (`:431`) — an unrecognised key **silently degrades to a 0.0 factor** rather
than raising.

**⚠ Mapper trap, accepted and carried into the spec:** the two parity tests
(`tests/test_range_estimate.py:507` and `:565`) compare estimator-vs-live using the *same* capture mechanism
on both sides. A capture that became structurally wrong but self-consistent would **still pass them**. They
detect divergence, not shared corruption.

> **Design-conditional status: NOT TRIGGERED, but gated anyway.** One draw is preserved, so the capture shape
> cannot change. The spec adds `G5` — an assertion that the captured distribution has exactly the three keys
> `{FOLD, CALL, RAISE}` — to close the shared-corruption hole for good, since it is cheap and permanent.

### C4 — `aggression` has no upper bound in the schema; the only ceiling is code-side
`content/models.py:170` — `aggression: float = Field(gt=0.0)`, **no `le=`**.
`content/schema/persona.schema.json` does not model the `postflop` block at all (required keys are
`id, version, domain, persona, display_name, sizing, preflop`), so **JSON-Schema validation provides zero
protection** for any postflop lever value.
Code ceiling: `_AGGRESSION_CAP = 5.6` (`personas_postflop.py:450`), applied at `:783`.

Authored values at HEAD: `nit 0.6 · tag 2.4 · lag 3.2 · maniac 15.0 · calling_station 0.5 · passive_fish 0.6`.

**Mapper finding (correct, and the reason the original plan was abandoned):** re-authoring
`aggression := aggression / effective_looseness` produces `lag 3.2 → 5.818`, which **crosses the 5.6 cap**
where it never did before, and `maniac 15.0 → 27.27` (already clamped). The cap's own justifying comment
(`:433-449`) anchors 5.6 to "1.75 × the highest non-maniac lever (lag 3.2)" and claims the cap "is the
identity map for every other authored persona (all ≤ 3.2)" — a claim that becomes false the moment lag is
re-authored to 5.818.

> **Design-conditional status: DISSOLVED.** ✅ Independently reproduced by measurement (Director probe,
> 2026-08-02): lag needs 5.8182 and maniac needs 10.1818, both over the cap. **The chosen design performs the
> re-parameterisation in code at the facing node only and edits no pack**, so no authored `aggression` value
> moves, the cap never binds differently, and the `:433-449` comment stays true. This finding is the direct
> cause of the design change and is recorded as ACCEPTED-AND-DESIGNED-AROUND.

### C5 — `_AGGRESSION_CAP`'s stated rationale is load-bearing, not decoration
`personas_postflop.py:433-449`, encoded as a passing test at `tests/test_personas_postflop.py:1451-1464`
(`test_maniac_still_strictly_most_aggressive`) plus the F3 entropy-floor pins at `:1175-1194`.
> **Design-conditional status: PRESERVED** — no authored aggression changes, so both the comment and the
> tests stand untouched. Also: the cap's *intent* is a bound on the raise-side merit relative to the others;
> the chosen design leaves the facing node's realised raise:call odds numerically identical, so the bound's
> behavioural meaning is preserved exactly, not merely nominally.

### C6 — `call_looseness` falls back to `stickiness`, which is a **shared** fallback
`personas_postflop.py:775`. Enforced both directions by `_stickiness_authorship`
(`content/models.py:207-227`): `stickiness` is REQUIRED while any split lever is unset and FORBIDDEN once
both are authored (key presence, not value — an explicit `null` still fails).

`maniac` authors **no** `call_looseness`, so its effective looseness **is** `stickiness = 0.55`
(`content/personas/maniac.json`). `stickiness` is *also* the fallback for `_price_exponent`
(`personas_postflop.py:627-644`) when `size_elasticity` is unset — two independent levers, one fallback.

**Confirmed by the mapper and re-confirmed here:** nothing derives `stickiness` from `aggression` or vice
versa, so the price exponent is not perturbed by this slice.

**🔒 Safety guarantee this slice depends on:** `call_looseness` is `Field(gt=0.0)` (`content/models.py:186`)
and `stickiness` is `Field(gt=0.0)` (`:177`). The effective looseness is therefore **strictly positive at the
model layer**, which is what makes dividing by it safe without a guard. This is a pre-existing invariant, not
a new assumption — but it is now load-bearing, so the spec pins it (`G7`).

### C7 — the SPR-commit block subtracts ABSOLUTE quantities from CALL/RAISE merits
`_commit_transform` (`:674-687`) zeroes FOLD, multiplies BET/RAISE by `_COMMIT_AGG_BOOST = 3.0` (`:313`),
leaves CALL. The B5b damp (`:986-996`) subtracts literal amounts:
`m -= _DRAW_CALL_BONUS[draw] * looseness * removed` and `m -= _DRAW_RAISE_BONUS[draw] * agg_scale * removed`.

**Named prior-art warning** (`docs/ai-dlc/reports/r9-defence-design.md:250-253`): scaling merits *before*
this subtraction changes the subtraction's relative size and can drive a merit negative into the
`max(m, 0)` clamp at `:999`.

> **Design-conditional status: ACCEPTED — and it is the sharpest real constraint on this slice.** The chosen
> design (a) restates both B5b subtractions in the same pre-aggregate units as the merits they subtract from,
> and (b) applies the defend factor **after** the whole commit block, immediately before normalization — the
> exact attach point `r9-defence-design.md:246-258` independently recommends. Verified: the commit path and
> the B5b path both reproduce HEAD exactly (probe sweep includes SPR 8.0/20.0 draw cells at four prices).

### C8 — pack version strings are NOT enforced
Each pack carries a `version` (`calling_station 1.1.1 · passive_fish 1.1.1 · nit 1.3.0 · tag 1.3.0 ·
lag 1.4.0 · maniac 1.5.0`). Nothing validates a bump on content change; the suite's own
`_packs_fingerprint` (`tests/test_personas_postflop.py:2475-2496`) hashes pack **content** precisely because
"a version string is hand-maintained and lags an in-flight edit" (`:2485-2486`).
> **Design-conditional status: NOT TRIGGERED** — this slice edits no pack, so no version moves. `G6` asserts
> that as a gate rather than leaving it to inspection.

---

## Integration points

**Production callers of `sample_postflop_decision`:**
- `app/domain/table/play.py:154-188` (`_postflop_decision`) — the live bot path; threads every kwarg through.
- `app/domain/table/range_estimate.py:350-363` (`_postflop_action_dist`) — the villain-range reveal.

**Test / harness callers:** `tests/test_personas_postflop.py` (~30+ sites) · `tests/node_trace.py:252-266` ·
`tests/test_price_tail.py:99-113` · `tests/test_mw_catch_toppair.py:134` · `tests/test_bet_sizing.py:129` ·
`tests/test_range_estimate.py:{535,550,607,615,664,732,876}` · `tests/test_arrival_range_ftc.py:{173,222}`.

**Shared state:** none. The function is pure given `(pack, hole, board, legal, …)` plus the injected `rng`;
no DB or file I/O. Its `Decision` return feeds `play.py`'s hand loop and, transitively, every population-level
band.

**Content packs:** all six `content/personas/*.json` carry `postflop.aggression` and either
`call_looseness` or the `stickiness` fallback. **This slice edits none of them.**

---

## Blast radius (mapper's ranking, re-ranked by the Director against the chosen design)

| # | Surface | Mapper rank | Actual rank here | Why |
|---|---|---|---|---|
| 1 | Seeded fixture files | not ranked (flagged as a gap) | **HIGHEST** | The only surface that can move. The design is exact to ~1 ulp, not bit-exact; 12/5040 cells drift by 1e-15. Fixture contents are simulated decisions, so a drift *could* in principle flip one draw. Must be measured, never assumed. |
| 2 | `range_estimate` capture (C3) | HIGHEST | LOW-but-gated | One draw preserved ⇒ shape cannot change. Gated by `G5` regardless, because the parity tests structurally cannot catch shared corruption. |
| 3 | Exact-weight capture tests (C1) | HIGH | LOW | Same reason. All eight capture sites see an unchanged 3-outcome first call. |
| 4 | Pack-authored numeric pins (C4/C5) | HIGH | **NONE** | Dissolved — no pack edit. |
| 5 | `BANDS` population tests (`tests/test_personas_postflop.py:2432-2472`) | MEDIUM | MEDIUM | AF / fold-to-c-bet / WTSD for all six personas. Should not move; they are the canary for any residual non-identity. |
| 6 | B5b / commit-path tests | MEDIUM (enumeration incomplete) | MEDIUM | The mapper did not finish enumerating these. Director probe covers the *policy* at SPR 8.0 and 20.0 across four prices; the *test* enumeration is a build-time task. |
| 7 | JSON-Schema gate | LOW-MED | N/A | No pack edit; and the schema does not model `postflop` anyway (C4). |

---

## Traps (mapper's, all accepted)

1. **The estimator parity tests cannot catch a self-consistent capture bug** — both sides use the same
   capture mechanism. Closed permanently by `G5` (assert the captured distribution has exactly the keys
   `{FOLD, CALL, RAISE}`).
2. **`lag`'s re-authored aggression 5.818 crosses the cap** — not an edge case, the second-most-aggressive
   persona, produced by the obvious formula. **This trap is why the pack-editing design was dropped.**
3. **Other facing-branch multipliers share the same flat `entries`** — `_MW_CATCH_TIGHTEN` (`:527`),
   `_ONE_PAIR_RAISE_DAMP` (`:358`), `_ACE_HIGH_FLOAT_RAISE_DAMP` (`:374`). All are applied before the
   normalization the defend factor also precedes. Director probe covers all three (the latter two require
   `facing_raise=True`, which the sweep varies) and finds exact agreement.
4. **`r9-defence-design.md:230-266` is prior art** for a stage-1/stage-2 split and deliberately chose the
   *less* invasive path — a shared multiplicative factor on CALL and RAISE inside the existing single
   normalization, proven raise-neutral to 1.11e-16 (`:260-266`). **This slice adopts that same shape**, so
   the two items compose at the same attach point rather than colliding.

---

## Explicit gaps carried forward (mapper's own "NOT INVESTIGATED", unresolved here)

- `tests/test_bet_sizing.py:129` and `tests/test_arrival_range_ftc.py:{173,222}` — call sites not read in
  detail. Low expected risk (both sit downstream of an unchanged action draw); **build must run them**.
- Full enumeration of B5b-damp-path tests.
- Whether any **golden/fixture JSON** stores postflop decision output — a targeted glob was not run. This is
  blast-radius #1, so the build ticket owns it explicitly.
- Whether `spot_signature()` / `grading.py` transitively consume this output. A shallow grep found no direct
  reference from `personas_postflop.py` or `range_estimate.py`. Frozen-signature risk assessed LOW, unverified.
- Whether `r9-defence-design.md`'s `λ_p` ever shipped. **Resolved by the Director: it did NOT** — it is a
  design pass only, and `R9-DEFENCE-a` is filed in the roadmap NEXT section as blocked on this slice.
