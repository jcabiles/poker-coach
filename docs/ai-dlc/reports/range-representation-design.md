# Range representation — design decision (2026-07-30)

**Context.** Three reviews (`range-representation-{refuter,research,theory}.md`) disagree on how villain
preflop ranges should be authored going forward; the owner's constraint is "don't build things that get
scrapped later." This document decides the artifact, its scope, its sequencing against the open R10 lane,
and what the owner still has to choose. All in-repo claims below are cited `file:line`; every measurement
labelled **[measured]** was re-derived here from `content/personas/*.json` via
`app.domain.content.notation.parse_range`, not taken from the input reports.

---

## 0. New measurements (this pass) — the reports were both partly wrong

The debate turned on "is the authored corpus really just a floor vector?". Both reports asserted a number.
Neither is right. Re-derived here, over **every** node in all six packs:

**The lattice is 25 rows, not 27.** `pairs` + 12 suited rows (A-high … 3-high) + 12 offsuit rows. There is
no "2-high" row. The refuter's "13 suited + 13 offsuit" (`range-representation-refuter.md:34`) overcounts
by two, which also inflates its per-node parameter estimate.

**Representability, by facing** — a row is *representable* iff the classes it plays form a top-anchored
contiguous segment **and** the action-bands stack down that segment without interleaving (this is the exact
condition for a floor-vector encoding to reproduce the node under `sample_preflop_action`'s
first-match-wins, `backend/app/domain/personas.py:76-90`):

| facing | nodes | rows occupied | gapped | interleaved | representable |
|---|---|---|---|---|---|
| `unopened` | 33 | 441 | **7** | 0 | **98.4%** |
| `vs_limpers` | 6 | 68 | 3 | 0 | 95.6% |
| `vs_rfi` | 6 | 91 | 8 | 0 | 91.2% |
| `vs_3bet` | 6 | 29 | 2 | 3 | 82.8% |
| `vs_4bet` | 6 | 13 | 3 | 0 | 76.9% |
| **all** | **57** | **642** | **23** | **3** | **95.95%** |

**[measured]** Two conclusions the reports missed, and they set the whole scope of this design:

1. **`unopened` has SEVEN holes, not three.** The refuter found three (`refuter.md:36-39`, all in `tag.json`).
   Four more exist, in packs it declared clean, and each is the same off-by-one class — a row that plays a
   weaker combo while skipping the *stronger* neighbour immediately above it:
   - `content/personas/tag.json:79` (BTN) — plays `T5s+` and `T3s`, **`T4s` missing**
   - `content/personas/tag.json:95-96` (BB) — `K5s+`/`K3s` → **`K4s` missing**; `Q7s+`/`Q5s` → **`Q6s` missing**
   - `content/personas/calling_station.json:35` (wildcard) — `63s+` and `53s`, **`54s` missing**
   - `content/personas/passive_fish.json:35` (wildcard) — same token family, **`54s` missing**
   - `content/personas/maniac.json:30` (UTG) — plays `QTo` but not **`QJo`**
   - `content/personas/maniac.json:87` (BTN) — `52s+` and `42s`, **`43s` missing**

   All seven are *strictly dominated omissions*: no archetype story explains playing `53s` and folding `54s`.
   **There are zero instances of intentional texture in the `unopened` membership layer.** With the seven bugs
   removed, `unopened` is **100% floor-vector representable**.

2. **Response nodes are NOT representable, and their failures are the identity-bearing part.** The 16 gaps
   and all 3 interleavings outside `unopened` are mostly *deliberate poker*: `maniac.json:158-162`'s polar
   `vs_4bet` (shove `AA/KK`, shove `QQ/AKs/AKo`, shove `A5s-A2s` blocker-bluffs at 0.5, but only *call*
   `TT/JJ/AQs`) produces an `As` row reading `AKs, AQs, —, A5s..A2s` — a genuine non-prefix set; `maniac`'s
   `vs_3bet` `Ao`/`Ks`/`Qs` rows genuinely **interleave** bands `[0,2,1,2]`; `tag.json:113-120`'s `vs_rfi`
   skips `77` in the pairs row on purpose. This is exactly the theory report's action-composition axis
   (`theory.md:24-28`) made measurable.

**Dead-token audit [measured].** 5 tokens are wholly inert under first-match-wins (`maniac.json:89`'s `K2o`,
already covered by `K2o+` on line 87; `maniac` `vs_rfi` mix2 `JTo`; `tag` `vs_rfi` mix2 `ATs`, `KJs`; mix3
`KQo`). A further **44 individual combos** are shadowed inside otherwise-live tokens (the refuter's larger
count, `refuter.md:64-69` — it counted shadowed *combos*, this counts inert *token text*; both are real and
neither is caught by `backend/tests/test_content.py:128-146`, which only rejects a wholly dead mix).

**Ladder inversions [measured]** — authored combo-weighted `raise+3bet` width, per seat:

|  | UTG | UTG1 | UTG2 | LJ | HJ | CO | BTN | SB | BB |
|---|---|---|---|---|---|---|---|---|---|
| nit | 13.6 | 29.1 | 29.1 | 29.1 | 29.1 | 29.1 | 29.1 | 29.1 | 29.1 |
| tag | 17.2 | 18.7 | 21.4 | 27.9 | 36.3 | 48.7 | 58.4 | 46.6 | 30.5 |
| lag | 25.1 | 27.5 | 33.7 | 37.6 | 47.7 | 53.2 | 66.1 | 52.0 | 45.4 |
| maniac | 15.9 | 20.6 | 25.6 | 34.3 | 42.4 | **49.1** | **47.2** | 44.0 | 24.2 |
| station | 0.6 ×9 (flat) | | | | | | | | |
| fish | 2.6 | 3.8 ×8 | | | | | | | |

Confirms R10-1a (`roadmap:2020-2028`, maniac < lag at 9/9), W5-b3's nit>tag inversion at UTG1/UTG2/LJ
(`roadmap:2029-2031`), and the refuter's un-roadmapped **maniac CO 49.1 > BTN 47.2** inversion
(`refuter.md:49-51`) — reproduced independently here.

---

## 1. The decision

> **Adopt a two-layer authored representation, scoped to `unopened` only, emitted by a build-time tool,
> semantically-identical-first, and sequenced AFTER the open R10 lane — with one tests-only lint slice
> buildable immediately.**

Concretely:

- **MEMBERSHIP + band structure of `unopened` nodes** becomes an authored **band-floor table** under
  `content/personas/ladders/<persona>.unopened.json`. The `combos` strings in `content/personas/*.json` are
  **emitted** from it by `backend/tools/emit_persona_ranges.py` and stay committed exactly as today.
- **ACTION COMPOSITION stays authored** — band weights are authored per band in the same table (they are
  numbers, not derived); `vs_limpers`, `vs_rfi`, `vs_3bet`, `vs_4bet` stay **hand-typed combo strings, not
  emitted, not schema-changed**, because §0 measurement proves floor vectors cannot express them.
- **Runtime sampler, `content/schema/persona.schema.json`, and `PersonaPack` are untouched.** The emitter's
  output is the identical artifact the loader already reads (`personas.py:49`,
  `content/schema/persona.schema.json:5-8` types `combos` as a plain string).

### Why this resolves the three-way disagreement rather than splitting it

The three reports are not actually proposing three things; they are answering three different questions.

- **Theory (`theory.md:1-6`) rejects a *model*** — percentile-over-one-ordering — because it is an ordering
  claim resting on the contract's single largest unsourced licence (`contract:151,156`), and because a
  width-only generator is the compensating-lever escape hatch W3R-1 exists to close (`contract:222`).
  **This design proposes no model.** The band-floor table has **no width scalar, no percentile parameter,
  no ranking metric, and no fit**. It is a *lossless re-encoding of what is already authored*: 25 numbers
  per node instead of the same information as free text. Nothing is derived from anything. Theory's own
  LOW finding concedes the point that matters — `contract:252` binds *where* identity lives (versioned
  `content/`), not who typed it (`theory.md:35-36`).
- **The refuter (`refuter.md:79-92`) proposes the *artifact*** — a row-floor table as the authored surface.
  Adopted, with two corrections from §0: it is 25 rows not 27, and it must be **scoped to `unopened`**,
  because the refuter's contiguity finding does not hold on response nodes where it matters most.
- **Research A2 (`research.md:34-38`) proposes the *mechanism*** — generate offline, freeze as data, the Loki
  / CFR-blueprint / GTOW-library pattern. Adopted verbatim: emission is build-time, output is committed,
  content/ stays the truth. Research's stated cost ("two sources of truth + temptation to hand-patch") is
  paid down by the `emit --check` CI gate in §2.4.

The one place all three agree, and this design keeps: **certification is by measured counters
(`R10-COUNT`), never by JSON diff** (`roadmap:2033-2035`, `theory.md:71`).

### What this design explicitly refuses

- **No percentile or "top X%" parameter, ever, in this table.** Not even as a seed. If `R9-SEATPROV`
  (`roadmap:1923-1927`) later sources a per-seat RFI ladder, it may be used to *review* floors; it may not
  become a table parameter, because the moment a floor is a function of a target the design becomes the
  one-dial model theory refuted.
- **No extension to postflop.** Postflop identity is levers + merit composition, not ranges. This is not a
  precedent for a "content generator" pattern; say so in the tool's docstring so no later slice generalises it.
- **No schema change, no sampler plumbing, no Alembic migration.** If a proposal needs one, it is E1-b
  (`roadmap:2143-2152`), a different, owner-gated item.

---

## 2. The design

### 2.1 The artifact: a per-persona band-floor table

One file per persona (`content/personas/ladders/tag.unopened.json`), **not** one combined file — this
preserves W5-B's "serialize per pack, one owner per JSON file" rule that the R10 lane runs under
(`roadmap:1998`), so a ladder edit has the same ownership granularity as a pack edit today.

```jsonc
{
  "id": "ladder_tag_unopened",
  "version": "1.0.0",
  "domain": "persona_ladder",      // NOT "persona" — different loader, never read at runtime
  "persona": "tag",
  "facing": "unopened",
  "emits": "content/personas/tag.json",
  "seats": {
    "UTG": {
      // Bands are ordered STRONGEST-FIRST and are DISJOINT by construction.
      // Each band names, per row, the LOWEST class it includes; the band's
      // membership in that row runs from (previous band's floor − 1) down to
      // this floor. A row absent from every band is not played.
      "bands": [
        { "weights": { "raise": 1.0 },
          "floors": { "pairs": "5", "As": "6", "Ks": "8", "Qs": "9", "Js": "T",
                      "Ao": "9", "Ko": "J" } },
        { "weights": { "raise": 0.5 },
          "floors": { "As": "5", "Ks": "7", "Ko": "T", "Qo": "J" } }
      ]
    },
    "UTG1": { "bands": [ /* … */ ] }
    // … nine seats, or fewer + a "*" wildcard seat, mirroring today's node structure
  }
}
```

**Semantics, stated once so the emitter and the reviewer agree:**

- A row key is `pairs` or `<rank><s|o>`; a floor value is a single rank character. `{"As": "6"}` in band 0
  means band 0 owns `AKs` down to `A6s`. `{"As": "5"}` in band 1 means band 1 owns exactly `A5s` (down to
  the previous floor − 1, i.e. `A5s..A5s`).
- **A hole is unrepresentable**: a band is an interval, so `T5s+ , T3s` cannot be written. This is the
  mechanism that makes all seven §0 defects *impossible*, not merely *detected*.
- **A dead token is unrepresentable**: bands partition, they do not overlap, so shadowed text cannot exist.
- **Interleaving is unrepresentable**: bands are strongest-first and disjoint. This is a *feature* for
  `unopened` (0 legitimate instances measured) and a *fatal limitation* for `vs_3bet` (3 legitimate
  instances measured) — which is precisely why response nodes are out of scope.
- **The 33 unopened nodes need 633 band-floor entries [measured]** (mean 19.2/node). Note honestly: this is
  **not a compression win** over today's `unopened` share of 1031 tokens. The win is *shape* — a fixed-schema
  numeric table whose 9 seats are dimension-wise comparable, sortable and monotonicity-assertable, versus
  free text whose combined width is a nonlinear first-match-wins aggregate (`refuter.md:44-48`).

### 2.2 The emitter

`backend/tools/emit_persona_ranges.py` — a build-time tool, alongside the existing
`backend/tools/{export_session,reject_counts}.py`. **It is never imported by `app/domain/`** (domain purity
is test-enforced, `contract:250`); it *may* import `app.domain.content.notation` read-only for token
synthesis, which is a tools→domain direction and therefore legal.

```
emit_persona_ranges.py --check     # exit 1 if any committed pack differs from what the table emits
emit_persona_ranges.py --write     # rewrite the `unopened` nodes of the six packs in place
emit_persona_ranges.py --diff      # human-readable per-class diff (NOT the certification surface)
```

Determinism requirements — these are what keep git diffs reviewable and are non-negotiable:

1. **Canonical row order**: `pairs`, then suited A-high→3-high, then offsuit A-high→3-high. Never dict order.
2. **Canonical token synthesis**: greedily emit `X+` when the band reaches the top of its row, `XY-AB`
   only for pair spans, single tokens otherwise; a fixed rule, no heuristics, no shortest-string search.
3. **Byte-stable JSON**: emit only the `mixes` array of `unopened` nodes, in place, preserving surrounding
   file bytes; 2-space indent, one mix per line where the current files do, `ensure_ascii=False`, no
   trailing whitespace. Verified by an idempotence test (`--write` twice is a no-op).
4. **The emitter never touches `postflop`, `sizing`, or any non-`unopened` node.** Enforced by a test that
   diffs those subtrees before/after.

### 2.3 Where texture overrides live

`unopened` needs none today (§0: zero intentional instances). But the design must not make texture
*impossible* forever, or the first legitimate need scraps it. So the schema reserves — **unused at
adoption, and shipped empty**:

```jsonc
"seats": { "BTN": {
  "bands": [ /* … */ ],
  "overrides": {                       // OPTIONAL. Empty in all six packs at adoption.
    "add":    { "2": ["A5o"] },        // band index -> extra classes forced INTO that band
    "remove": ["K2o"]                  // classes removed from every band
  },
  "override_rationale": "…"            // REQUIRED whenever overrides is non-empty
} }
```

Three rules make this an escape valve rather than a back door:

- **Overrides bypass the by-construction guarantees.** A test asserts `override_rationale` is non-empty
  whenever `overrides` is, and a second test asserts the *total* override count across all six ladder files
  is ≤ some small committed number (start at 0). Overrides are visible in a summary line, so the review
  question "is this texture or a bug?" is asked explicitly, once, instead of being invisible in 1031 tokens.
- **Overrides may not create a hole.** `remove` that produces a gapped row is rejected at emit time — the
  seven §0 defects stay unrepresentable even through the override path.
- **If a response node ever needs a ladder, it does not get one.** Response nodes stay hand-typed. The
  override mechanism is not the seam through which `vs_3bet` sneaks into the table.

### 2.4 Certification: semantic-identity first, byte-identity second

The owner's constraint is "byte-identical-first". Stated precisely, that is **two** gates, and conflating
them is how this slice would fail:

- **Gate A — semantic identity (the real "nothing changed" proof).** For every `unopened` node of every
  pack: `parse_range(emitted_mix.combos) == parse_range(committed_mix.combos)` for every mix, in order, and
  `emitted_mix.weights == committed_mix.weights`. This is checkable **today**, against HEAD, with the
  packs untouched. It is the proof the table is a lossless re-encoding.
- **Gate B — byte identity.** Achievable only if the emitter's canonical token synthesis happens to
  reproduce the human's token choices. It will not (`22+, A2s+, K2s+, …` vs canonical output). So Gate B is
  reached by a **separate, mechanical normalise commit** whose own test asserts Gate A held across it — i.e.
  the reformat provably changes text and not content. After that commit, `emit --check` is a clean CI gate
  and hand-editing an `unopened` node fails the build.

**This is owner decision #2 below.** The alternative — build a token-synthesis emitter that reproduces
existing strings byte-for-byte — is achievable but requires encoding each author's stylistic choices, which
is exactly the fragile surface the design exists to delete.

---

## 3. Sequencing

### 3.1 The seat-aware-responses fork — position, and why the research report's ordering worry dissolves

Research (`research.md:48-51`) argues: *"deciding generator-vs-authored before deciding whether responses
become positional is deciding in the wrong order,"* because going positional on responses adds ~216 cells,
"at which point A2 becomes strongly attractive."

**Position: the ordering concern does not apply to this design, because response nodes are out of scope on
evidence, not on convenience.** §0 measures response membership as 82.8% (`vs_3bet`) and 76.9% (`vs_4bet`)
representable, with every failure being deliberate polar/blocker structure. An emitter cannot author
`vs_3bet` correctly, and theory's per-defect table already scores it **HURTS** for R10-1c
(`theory.md:60`). Multiplying an unrepresentable node by 9 seats does not make it representable — it makes
216 hand-authored cells instead of 24. So:

- **The two decisions are independent and may be taken in either order.** Adopting the ladder table does
  not constrain the response-axis decision, and vice versa.
- **The ~216-cell expansion is not an argument for this design.** If seat-aware responses are adopted, the
  authoring burden lands entirely in hand-typed territory. If that burden proves intolerable, the correct
  response is a *scaffold* (theory's recommendation 3, `theory.md:68-70`: emit a skeleton, hand-fill it),
  not an emitter — and the ladder table's row/band vocabulary is directly reusable as that skeleton's shape.
- **What is already committed:** `W5-b2` (E1-a, actor-position `vs_rfi` + `vs_limpers`) is **already NOW**
  and JSON-only (`roadmap:1229`, `roadmap:2146-2150`). `E1-b` (opener-position axis) **stays LATER, owner-
  gated**, needs a `models.py` schema change plus sampler plumbing (`roadmap:2143-2145`). Neither moves as a
  result of this document. Do not sneak the opener axis in (`roadmap:2048`).

### 3.2 Order relative to the open R10 lane

The lane is `R10-COUNT → R10-PRE1 → R10-PRE2 → W5-b4 → R10-3BET` (`roadmap:527-529`), opens after T-STICKY,
and is the **sole re-recorder of sim fixtures while open, one slice at a time** (`roadmap:540-543`).
PRE1 shipped (PR #137); PRE2 is in flight; W5-b4 and R10-3BET are action-layer slices.

```
IMMEDIATELY, outside the lane (tests only, no pack edit, no fixture re-record):
  RR-LINT ─────────────────────────────────────────────────────────────────────┐
                                                                               │
open R10 lane (unchanged, NO emission inside):                                 │
  R10-PRE2 → W5-b4 → R10-3BET ──────────────────────────────────────────┐      │
                                                                        ▼      ▼
after the lane closes:                             RR-EMIT (Gate A, no pack edit)
                                                                        │
                                                   RR-NORM (Gate B, text-only)
                                                                        │
                                                   RR-HOLES (first parameter edit — 7 holes,
                                                             fixture re-record, own event)
                                                                        │
                                                   RR-FLIP (emit --check becomes CI law)
```

**Why nothing in the open lane is scrapped.** Every lane slice is an *authored-shape assertion on committed
JSON* — R10-PRE2's per-seat `maniac > lag` ordering, R10-3BET's nit-continue gate and 4-bet-share ordering
(`roadmap:2049-2052`). Those assertions read the emitted artifact and hold identically whether a human or
the tool produced it (`theory.md:77-79`). Additionally:

- **PRE2 edits `maniac.json`'s `unopened` — the exact nodes RR-EMIT will later encode.** That is fine and in
  the right order: the ladder table is built *from* the packs as they stand when RR-EMIT runs, so PRE2's
  widening is simply the input. Building the table first would guarantee a merge conflict and would put an
  emission event inside the lane, which is forbidden (`roadmap:1998-2001` anti-laundering; `theory.md:17-20`).
- **W5-b4 and R10-3BET touch `vs_limpers`/`vs_rfi`/`vs_3bet` — nodes this design never emits.** Zero overlap.
- **RR-LINT touches only `backend/tests/`.** No pack edit, no fixture re-record, so it does not contend for
  the lane's sole-fixture-owner role. It is the one piece buildable today.

**Relationship to W5-b3** (nit per-seat ladder, NOW, `roadmap:1286-1314`). W5-b3 must author **nine** nit
seats and is theory's own "strongest pro-generator case" (`theory.md:59`). Tempting to block it on RR-EMIT.
**Do not.** W5-b3 is in NOW, RR-EMIT is not, and W5-b3's pass/fail is an authored-width ladder assertion
that is representation-neutral. Recommendation: let W5-b3 ship hand-authored; it then becomes RR-EMIT's
*best test case* (nine fresh seats that must round-trip). If RR-EMIT happens to be ready first, W5-b3 may
author floors instead — its acceptance criteria do not change either way.

**Relationship to R9-SEATPROV** (`roadmap:1923-1927`): **none, by construction.** The table has no level
parameter. Seat-monotonicity is a *shape* claim on floors and is exactly what `roadmap:1926-1927` permits
("seat-axis work asserts shape … and never level"). Percentile/level targets stay soft until SEATPROV lands,
and this design gives them nowhere to hide even after it does.

---

## 4. Constraint table — by construction vs by test

| Constraint | Today | After adoption | Note |
|---|---|---|---|
| **No holes in a row** (7 live defects, §0) | *nothing* | **BY CONSTRUCTION** — a band is an interval | RR-LINT gates it in the interim |
| **No dead tokens** (5 live, §0) | *nothing* | **BY CONSTRUCTION** — bands are disjoint | `test_content.py:147` only catches a wholly dead *mix* |
| **No shadowed combos** (44 live) | *nothing* | **BY CONSTRUCTION** | ditto |
| **No fully-shadowed mix** | test (`test_content.py:128-146`) | test — **KEEP** | still guards hand-typed response nodes |
| **No duplicate position coverage / node ordering** | validator (`models.py:248-281`) | validator — **KEEP** | emitter output is validated by the same model |
| **Weights ≤ 1, legal action vocabulary** | validators (`models.py:103-127`) | validators — **KEEP** | composition layer is authored either way |
| **Within-persona seat monotonicity** (floors non-increasing UTG→BTN) | *nothing* | **BY CONSTRUCTION, optional** — enforceable at emit time per row | ⚠ must NOT be forced on station/fish — W5-b3b says a ladder is anti-realistic for them (`roadmap:1316-1331`). Make it an opt-in flag per ladder file. |
| **maniac CO ≤ BTN (the un-roadmapped inversion)** | *nothing* | **BY CONSTRUCTION** if the flag above is on for maniac | otherwise a one-line test on the width vector |
| **maniac > lag at every seat** (R10-PRE2) | test (in flight) | **test — KEEP** | cross-*persona*, cross-*file*: not a per-node property, cannot be a construction constraint without a cross-file solver. Do not try. |
| **nit < tag** (W5-b3) | test (pending) | **test — KEEP** | same reason |
| **four-way chain nit<tag<lag<maniac** | test (after W5-b3, `roadmap:2031`) | **test — KEEP** | same reason |
| **Premiums never fold unopened** (R10-PRE1, shipped) | test | **test — KEEP** | this is the *weights* layer, not membership; the table cannot enforce it |
| **Authored-width BANDS** (`test_personas.py:230-255`) | test | **test — KEEP** | aggregate behaviour, orthogonal to representation |
| **4-bet share ordering** (R10-3BET) | test (pending) | **test — KEEP** | response nodes, never emitted |
| **Emitter parity** | — | **NEW test** | Gate A / Gate B, §2.4 |

**Nothing is deleted.** Every existing gate keeps running against the emitted artifact — that is the entire
point of emitting into the committed pack rather than replacing the loader. The by-construction column is
purely additive: it removes a *defect class*, not a *check*.

---

## 5. Scrap-risk analysis

| Future | Does it scrap this? | Why not / mitigation |
|---|---|---|
| **Seat-aware responses adopted** (`W5-b2` now, `E1-b` later) | **No** | The ladder is keyed `(persona, facing, seat)`. Adding seats to a facing adds table rows. Responses are never emitted, so the expansion happens entirely outside this artifact. |
| **`E1-b` opener-position axis** (schema change + sampler plumbing, `roadmap:2143-2145`) | **No** | It changes `PersonaNode`, which the emitter writes *into*, not the ladder vocabulary. The emitter would gain a key; the floors are unchanged. |
| **Villain-range rungs G1-b/c** (`roadmap:2073-2075`) | **No — it helps** | Rung (b) needs a persona-conditional *range prior*. A 25-row floor vector **is** a range prior in closed form; today the prior is recovered by replaying the sampler (`range_estimate.py`). The table is a strictly better input. |
| **`T-agentcoach`** (LLM session coaching) | **No — it helps** | A coach must *describe* a villain ("opens any suited ace from the cutoff"). 25 floors are describable in one prompt; 1031 tokens are not. |
| **Postflop analogue demanded** | **Would scrap it if attempted** | Postflop is levers + merit, not ranges. Declare it a non-goal in the tool docstring (§1) so no later slice generalises the pattern and then abandons it. |
| **`R9-SEATPROV` lands and someone fits floors to a sourced ladder** | **Would scrap it if allowed** | Prohibited in §1: no level parameter in the table, ever. SEATPROV may inform *review*, not *derivation*. Enforce by the table simply having nowhere to put a target. |
| **A fourth defect class appears that is genuinely width-shaped** | **No — it confirms it** | Theory names this as one of the three things that would change its answer (`theory.md:79-81`). |
| **⚠ The emitter never acquires a second use** | **THE REAL RISK** | If roster realism is arrival-bound (65-77% of first-in chances are EP, `theory.md:48-50`), a prettier ladder buys little and the tool rots. **Mitigation, and it drives the recommendation in §7 decision 3: do not build RR-EMIT speculatively. Gate it on a named consumer** — a slice that must author ≥9 seats (W5-b3-class) or that must move a whole ladder (R10-PRE2-class). Until then, ship RR-LINT only, which is cheap and independently valuable. |

---

## 6. Ticket sketches

Sized as lane slices. Each states its fail-at-HEAD or identity condition explicitly, per the gate-design
rule that a criterion which already passes must be labelled a PRESERVATION check (`roadmap:2050-2051`).

### `RR-LINT` — frozen defect inventory for preflop packs. *Tests only. BUILDABLE IMMEDIATELY.*
**Scope:** `backend/tests/` only. No pack edit, no schema change, no fixture re-record, no lane contention.
**Build:** a new test module that, for every node in every pack, computes (a) per-row gaps, (b) fully inert
tokens, (c) band interleaving, and asserts the result equals a **committed inventory constant** listing
exactly the §0 defects. Any new defect fails; any *fixed* defect also fails, forcing the constant to be
updated in the same commit as the fix.
**Fail-at-HEAD proof:** a naive strict `assert no gaps` fails at HEAD on 7 `unopened` rows + 16 response rows
and `assert no inert tokens` fails on 5 tokens — verified. The shipped inventory form therefore *passes* at
HEAD by design and is labelled a PRESERVATION-plus-tripwire check, not a defect gate.
**Why now:** it is the only piece with zero interaction with PRE2/W5-b4/R10-3BET, and it is the instrument
that makes RR-HOLES certifiable later.
**Appetite:** ~1 small slice.

### `RR-EMIT` — build-time emitter + ladder tables, semantic-identity gate. *After the lane closes.*
**Scope:** new `backend/tools/emit_persona_ranges.py`; new `content/personas/ladders/*.unopened.json`;
new tests. **The six persona packs are NOT edited.**
**Pass/fail (Gate A, identity — this is an EXEMPT identity criterion, it must pass):** for every `unopened`
node of every pack, emitted mix list == committed mix list under `parse_range` set-equality and weight
equality, in order. Plus: `--write` is idempotent; non-`unopened` subtrees byte-unchanged; ladder files
contain zero `overrides`.
**Fail-at-HEAD:** the tool does not exist; the test suite gains a check that cannot pass without it.
**Blocked by:** the R10 lane closing (PRE2 and any later lane slice edit `unopened` nodes; the table must be
built from the settled packs). **Gated by:** a named consumer — see owner decision 3.
**Appetite:** ~1 medium slice.

### `RR-NORM` — canonicalise pack text to emitter output. *Text-only, mechanical.*
**Scope:** the `unopened` node text of six packs; nothing else.
**Pass/fail:** Gate A holds across the commit (proved by RR-EMIT's own test running before and after), and
after the commit `emit_persona_ranges.py --check` exits 0 — i.e. **byte identity is reached, and provably
without content change**. Every existing gate (`test_personas.py` BANDS, `test_content.py`, R10 lane
assertions) passes untouched. **No fixture re-record** — behaviour is bit-identical.
**Appetite:** ~1 small slice. May be folded into RR-EMIT if the owner prefers one acceptance event; keeping
it separate is the anti-laundering-consistent choice.

### `RR-HOLES` — fix the 7 membership holes + 5 inert tokens. *First real parameter edit.*
**Scope:** ladder parameter files (or, if RR-EMIT is not adopted, the six packs directly).
**Pass/fail:** ① strict per-row contiguity over all `unopened` nodes — **FAILS at HEAD on 7 rows**
(`tag.json:79`, `tag.json:95`, `tag.json:96`, `calling_station.json:35`, `passive_fish.json:35`,
`maniac.json:30`, `maniac.json:87`), passes after; ② zero inert tokens — **FAILS at HEAD on 5**; ③ RR-LINT's
inventory constant is emptied of the `unopened` entries in the same commit; ④ combo-weighted per-seat width
moves by < 0.5pp per seat (these are 6-to-12-combo additions) — REPORTED via `R10-COUNT`, not gated.
**Fixture re-record:** yes, small, owner-authorised, one slice — must respect whoever owns fixtures at the
time (`roadmap:540-543`).
**Note:** this is a *behaviour change* and must not be smuggled into RR-NORM.
**Appetite:** ~1 small slice.

### `RR-FLIP` — packs become generated artifacts. *Process change.*
**Scope:** CI/`verify.sh` runs `emit_persona_ranges.py --check`; `CLAUDE.md` + the pack files gain a
"generated — edit the ladder" header comment; `README`/roadmap note the new authoring path.
**Pass/fail:** a deliberate hand-edit to an `unopened` node fails `./scripts/verify.sh`; a ladder edit plus
`--write` passes. Response nodes remain hand-editable and are unaffected by the check.
**Appetite:** ~1 small slice.

**Optional, not recommended in the first cut:** `RR-LIMPERS` — extend emission to `vs_limpers` (measured
95.6% representable, 3 gaps, all the same `54s`/`42s` bug family). Defer: it interacts with W5-b4 and W5-b2,
and the marginal gain over 6 nodes is small.

---

## 7. Decisions needed from the owner

Each is self-contained; read the situation, pick, and nothing above needs re-reading.

### Decision 1 — adopt the ladder table at all, and at what scope?
*Situation:* villain preflop ranges are authored today as free-text combo strings inside each persona pack.
Measurement (§0) shows the first-in (`unopened`) ranges contain **zero intentional texture** and **seven
authoring bugs** that no test can see, while the response ranges (`vs_rfi`/`vs_3bet`/`vs_4bet`) contain
genuine polar structure that a floor table cannot represent.

- **A — Adopt for `unopened` only** *(recommended)*. Gain: the seven-hole and dead-token defect classes
  become impossible; nine seats become nine comparable number-vectors. Cost: one new build-time tool, one
  new content directory, two representations coexisting (ladder for `unopened`, hand-typed for responses).
- **B — Adopt for `unopened` + `vs_limpers`.** Gain: 6 more nodes covered, 3 more bugs killed. Cost: touches
  nodes W5-b4 and W5-b2 are actively editing; more lane contention for little return.
- **C — Lint only, stay hand-authored** (theory's recommendation 2). Gain: zero new machinery; the defects
  become *detected*. Cost: they stay *possible* — W5-b1 and P1 both shipped this exact defect class through
  refuter + Codex review (`refuter.md:20-29`), so detection has a demonstrated miss rate.

**Recommendation: A.** It takes the refuter's artifact, the research report's mechanism, and honours
theory's actual objection — which was to a *percentile model*, not to a tool. Scoping to `unopened` is the
part neither report got right, and it is what makes the design defensible on measurement rather than taste.

### Decision 2 — how is "byte-identical-first" satisfied?
*Situation:* the emitter's canonical token synthesis will not reproduce the human's stylistic token choices
(`22+, A2s+, K2s+, …`), so literal byte identity against today's files is not achievable by a first run.

- **A — Semantic identity gate + a separate mechanical normalise commit** *(recommended)*. The emitter must
  first prove per-mix set-and-weight equality against HEAD (nothing changed); a second, text-only commit then
  rewrites the strings to canonical form and reaches byte identity provably without content change.
  Gain: the strongest possible "nothing was scrapped" evidence, in two reviewable events. Cost: two commits.
- **B — Build a style-preserving emitter that reproduces existing bytes exactly.** Gain: one commit, literal
  byte identity. Cost: the emitter must encode each author's token idioms — the fragile surface the whole
  design exists to delete, and it breaks the first time a ladder value changes anyway.

**Recommendation: A.** B buys a one-time cosmetic property at the cost of permanent emitter complexity.

### Decision 3 — when is the emitter built?
*Situation:* the risk that would actually scrap this work is the tool acquiring no second use, because
roster realism may be arrival-bound rather than range-bound (`theory.md:48-50`).

- **A — Gate `RR-EMIT` on a named consumer** *(recommended)*: build it when a slice must author ≥9 seats
  (W5-b3-class) or move a whole ladder (R10-PRE2-class). Ship `RR-LINT` now regardless. Gain: the tool is
  never speculative; its first use is its own justification. Cost: the defect classes stay possible until
  then (mitigated by RR-LINT).
- **B — Build `RR-EMIT` immediately after the lane closes.** Gain: the by-construction guarantees land
  sooner. Cost: it may sit unused if the next waves are all spine-side/arrival-side.
- **C — Build it inside the lane, in parallel.** **Rejected, not offered as a live option** — an emission
  event inside the open lane violates the split-slice anti-laundering rule (`roadmap:1998-2001`) and the
  sole-fixture-owner rule (`roadmap:540-543`).

**Recommendation: A**, with `RR-LINT` starting now.

### Decision 4 — build `RR-LINT` now, outside the lane?
*Situation:* the lint slice touches only `backend/tests/`. No pack edit, no fixture re-record, so it does not
contend for the lane's sole-fixture-owner role — but the lane's discipline is "one thing at a time".

- **A — Yes, build it now** *(recommended)*. Gain: seven live authoring bugs and five inert tokens become
  visible today, and any *new* one fails immediately — including one introduced by PRE2/W5-b4/R10-3BET
  themselves. Cost: one more open branch alongside the lane.
- **B — Queue it behind the lane.** Gain: strict single-threading. Cost: the lane's own pack edits ship
  unlinted, which is precisely how the R10-1a and R10-1b defects were shipped in the first place.

**Recommendation: A.** A tests-only tripwire that would have caught the last two defect waves is the
cheapest thing on this list.

### Decision 5 — do the seven holes get their own slice?
*Situation:* `RR-HOLES` is a real behaviour change (6–12 combos added across four packs) needing a fixture
re-record, and it touches four different pack files.

- **A — One dedicated slice, all four packs** *(recommended)*. Gain: one causal change, one acceptance event,
  one fixture re-record, trivially attributable. Cost: it edits four packs, bending W5-B's one-owner-per-JSON
  rule (`roadmap:1998`) — defensible because the change is a mechanical single-combo insertion per hole.
- **B — Fold each hole into whichever lane slice next touches that pack.** Gain: obeys one-owner-per-JSON
  literally. Cost: mixes an unrelated correctness fix into slices with their own causal claims — exactly the
  laundering the split-slice rule forbids.

**Recommendation: A**, with the diff shown per pack in the PR body.

### Decision 6 — one ladder file per persona, or one combined file?
*Situation:* the R10 lane serialises pack edits by file ownership.

- **A — One file per persona** *(recommended)*: `content/personas/ladders/<persona>.unopened.json`. Gain:
  ladder edits inherit the same ownership granularity as pack edits; two slices can touch two personas.
  Cost: six small files.
- **B — One combined `ladders/unopened.json`.** Gain: cross-persona ordering is visible in one view — the
  refuter's strongest argument (`refuter.md:86-89`). Cost: every ladder edit contends on one file, breaking
  the lane's serialisation rule.

**Recommendation: A**, and recover B's benefit with `emit_persona_ranges.py --diff`, which can print the
6×9 width matrix (the §0 table) on demand — a *view*, not a *file*.
