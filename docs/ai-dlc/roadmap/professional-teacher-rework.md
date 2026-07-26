# Professional Teacher Rework — Roadmap (updated 2026-07-10)

> **2026-07-10:** the Simulate initiative (`roadmap/simulate-table.md`) **supersedes the
> turn/river deferral**: turn/river graders (2f–2i) + multiway (2j) are pulled into its Now
> column as slices S5–S8. The Later bet below stays for full-hand (2k) only.

> Living, pass/fail, resumable. A fresh context should read this and know exactly what's left.
> **Supersedes the sequencing** in `roadmap-review-and-proposal.md`: the Learning-Experience pillar becomes the **Now**
> column; turn/river coverage (2f–2k) moves to **Next/Later**. PRD: `docs/ai-dlc/prd/professional-teacher-rework.md`.
> Contract maps (honest current-state): `docs/ai-dlc/contracts/{feedback-evaluation,persistence-datamodel,frontend-ia-tokens}.md`.
>
> **Gate decisions (2026-07-02):** audience = *"me now, others later"* (seams not machinery) · *teaching + UX first* ·
> *concept-cards now, lessons library later* · appetite = *large/comprehensive*.
>
> **Resume rule:** work the Now column top-down; do the first unchecked slice; verify its pass/fail actually passes
> before marking `[x]` (agents falsely mark work done). Hand ONE slice at a time to `/ai-dlc`.

---

## North-star outcome(s) — the WHY

- **Primary (you):** *become a winning $2/$3 player.*
  Metric: trained-spot **decision accuracy ↑ / EV-loss ↓** across sessions (already computed by `services/stats.py`).
  Baseline: today's accuracy + EV-loss per leak category → Target: sustained upward trend on the pressure spots that gate the move-up.
- **Enabling (others later):** *a cohesive teacher a stranger can pick up.*
  Metric: **cold-start → first-understood-rep** is walkable with zero author explanation.
  Baseline: cold-start dumps you into a random `vs_limpers` spot, no onboarding, tautological "why" → Target: oriented,
  placement-seeded, every rep links to the concept behind it. *Seams, not the multi-user machinery.*

**Why these, and why now:** the engine already grades the most-played spots (all preflop + all flop). ~40 more turn/river
tickets deepen a tool that still doesn't *teach*. Highest leverage now = the human-facing layer. The maps confirm the
teaching data is *partly* free (`chosen_eval` unrendered, 12 authored exploit rationales, `due_items()` already computed)
and *partly* real new work (baseline preflop + all postflop are templated tautologies) — sized honestly per slice below.

---

## NOW — spec-ready vertical slices (work top-down; ICE = Impact·Confidence·Ease, 1–10)

> Each is thin + end-to-end + observable. ICE surfaced as the "why" for order — a lens, not a law; re-order at the gate.

- [x] **N1 — Tiered feedback shape (teaching walking-skeleton).** *(done 2026-07-02: FeedbackTiers via pure domain/feedback.py composer + TieredFeedbackProvider wrapper in the factory — every provider inherits; chosen_eval rendered; deep-dive collapsed; refuter pass)* ICE 9·8·6.
      **Problem:** post-answer "why" is one flat, tautological string (`grading.py:196` "AKo from CO: raise is the play");
      the promised verdict→reasoning→deep-dive was never built, and `chosen_eval` is delivered-but-never-rendered.
      **Outcome-link:** primary (teach the why) + enabling (stranger understands a rep).
      **Solution:** add a **structured tiered field** to `EvaluationResult` (verdict / reasoning / deep-dive as distinct
      fields — NOT parsing the one prose slot), author it via a **shared post-processing wrapper** so a future solver
      provider inherits it (the teaching seam), render the tiers in `FeedbackPanel` incl. the free `chosen_eval`
      (freq/EV of the action you actually picked). Update the FE type surface to match the new shape — **manual `types.ts`
      edit is acceptable** until the Next "FE type-gen CI gate" wires `gen:api`→`schema.d.ts` (that pipeline is unwired
      today; nothing imports `schema.d.ts`). *(Recommended: consider pulling that gate into Now before N1/N5 — both touch
      API shapes and would pay for it twice.)*
      **Pass/fail:** a graded drill renders ≥2 distinct tiers incl. chosen-action freq/EV; postflop+exploit reasoning is
      non-tautological; the new field appears in `types.ts` and typechecks against usage; `./scripts/verify.sh`→
      `BACKEND VERIFY OK` + FE `typecheck && build` clean; locked string-assert tests (`test_grading.py:43,204,225-237`)
      updated deliberately.
      **Appetite:** ~1 epic. **No-gos:** don't author baseline-preflop prose here (that's N3); no DB persistence of rationale.

- [x] **N2 — Accuracy debt paydown.** *(done 2026-07-02: CW-3b via embedded equity-vs-random table replacing the proxy — false ties dissolved; CW-2b noted; doc-06 fold-equity EV wired into grade_cbet; EVs labeled ≈ in UI; both refuters pass)* ICE 7·8·6.
      **Problem:** grades we're about to *teach from* have known leaks — teaching amplifies a wrong grade. CW-3b
      (pocket-pair ranks) was **reverted** in the Challenge merge; CW-2b unresolved; EVs shown as hard numbers though proxy.
      **Outcome-link:** primary (trustworthy accuracy metric).
      **Solution:** anchor pocket-pair ranks to computed-equity ordering in `hand_rank.py`, **reconciling
      `test_hand_rank.py` determinism/tie model** (don't just bump a coefficient); CW-2b one-line documented scope note in
      `postflop.py`; wire a **credible interim fold-equity EV** from `equity.py` + doc-06 fold tables; label proxy EVs
      *approximate* in `FeedbackPanel` until Phase 3.
      **Pass/fail:** `pytest` green incl. updated hand-rank expectations; EV labeled approximate in the UI; `verify.sh` +
      FE build clean. **Appetite:** ~1 small epic. **No-gos:** no solver tables; don't touch `spot_signature()` (orphans SRS).

- [x] **N3 — Authored strategic rationale (content path + first tranche).** *(done 2026-07-03: non-exploit preflop + postflop rationale paths wired into authored_rationale; rfi 6/6 + vs_rfi 6/6 + new content/postflop/cbet.json 3/3 authored, doc-grounded; refuter pass)* ICE 9·7·4.
      **Problem:** the bulk teaching gap — every non-exploit preflop pack has **zero** authored `rationale` (~85% of reps),
      and postflop graders **never read `Entry.rationale`** at all. N1's tiers are empty without this.
      **Outcome-link:** primary (teach the why across streets).
      **Solution:** wire a content-pack `rationale` path into the **postflop graders** (they take range strings today, not
      `Entry`), and **author** `rationale` for the first preflop tranche (`rfi` + `vs_rfi`). Remaining packs → Next.
      **Pass/fail:** RFI + vs-RFI + at least one postflop node render non-tautological authored reasoning sourced from
      content (not f-strings); content validates against the pack schema; `verify.sh` + tests green.
      **Appetite:** ~1 epic. **No-gos:** not all packs (tranche only); no new prose-generation model — authored data.

- [x] **N4 — Design-system foundations (tokens · scales · elevation).** *(done 2026-07-02: --text/--space/--radius ramps + felt→panel→card→overlay shadows both themes; all raw px + rgba tokenized; refuter pass)* ICE 6·9·7 (cheap enabler).
      **Problem:** `tokens.css` has solid semantic colors but **no type scale, no space/radius/shadow ramps, no
      felt→panel→card→overlay elevation model**; font sizes are raw px scattered across `app.css`. No visual hierarchy for a hub.
      **Outcome-link:** enabling (professional/attractive) — unblocks N6/N7 visuals.
      **Solution:** add `--text-*` type scale + `--space/--radius/--shadow` ramps + an elevation model to `tokens.css`;
      refactor raw-px/`rgba` usages to tokens; keep AA contrast + visible focus both themes.
      **Pass/fail:** token scales exist and are used (no new ad-hoc px/hues); contrast check passes light+dark; FE build clean.
      **Appetite:** ~1 small epic (pure FE). **No-gos:** no component redesign here (tokens only); don't restyle the grid (N5).
      *(INVEST note: a near-horizontal enabler, kept standalone deliberately — it DOES change observable contrast/focus, is
      cheap, and de-risks N6/N7 by giving them a real visual hierarchy to build on. Fold into N6 if you'd rather not ship it alone.)*

- [x] **N5 — Frequency-mix grid cells (backend contract + FE render).** *(done 2026-07-03: range_grid() returns per-action freqs; stacked-segment cells with mix aria-labels; challenge.py adapter lossless for RFI; orphaned mixed legend dropped; refuter pass)* ICE 6·8·4.
      **Problem:** grid cells show one dominant color; the real per-action mix is computed then **collapsed to a single
      label** in `range_grid()` (`grading.py:241-257`) before the wire — the #1 grid oversimplification. It's a *backend*
      contract, not a FE-only change.
      **Outcome-link:** enabling (truthful, professional data-viz).
      **Solution:** widen `range_grid()` + the API response to return **per-action frequencies**; restructure
      `RangeGrid.tsx` cell markup + CSS into proportional stacked bars; update the FE type surface for the new shape
      (**manual `types.ts` edit acceptable** until the Next CI-gate wires `gen:api`; nothing imports `schema.d.ts` today).
      **Pass/fail:** a mixed-frequency handclass renders proportional segments; API returns per-action freqs; `types.ts`
      matches the new response shape and typechecks; `verify.sh` + typecheck/build green. **Appetite:** ~1 epic.
      **No-gos:** don't change grading logic/thresholds; don't restyle non-grid components.

- [x] **N6 — App-shell + minimal routing (hub walking-skeleton).** *(done 2026-07-03: hand-rolled hash routing #/<view>[/<mode>], reload+deep-link restore, back/forward safe, keyboard guard intact, no router lib; refuter pass)* ICE 5·8·6.
      **Problem:** no router — pure conditional rendering; reload resets to drill/random; no deep-link/resume; `App.tsx`
      owns all state with the topbar/StatsStrip/VIEWS-row unconditional and shortcuts gated on `view==="drill"`. A hub/path
      can't be resumable without this.
      **Outcome-link:** enabling (cohesion; resumable "today's plan").
      **Solution:** introduce minimal (hash-based) routing + a thin shell so views are deep-linkable/resumable **without
      breaking** the drill keyboard-guard, topbar, or StatsStrip assumptions.
      **Pass/fail:** reload restores the current view (not reset); a view is deep-linkable; drill shortcuts still gated
      correctly; FE build green. **Appetite:** ~1 small epic. **No-gos:** no new nav content yet (that's N7); no router lib
      unless justified at spec.

- [x] **N7 — Home / curriculum hub + "today's plan".** *(done 2026-07-03: Home = first tab + default route (absorb); GET /review/plan surfaces due_items() read-only with family+position labels; 9-node ordered path with attempts-weighted mastery (solid ≥80% · 20+ reps); refuter pass. Known limit: 5 preflop nodes map to random mode pending a per-family /drill/next filter — see Next)* ICE 8·7·5 (needs N6, benefits from N4).
      **Problem:** flat tab pile; mastery hidden; no "what to work on next." The SM-2 due-queue (`due_items()`, already
      computed + indexed `ix_srs_item_due_date`) is invisible.
      **Outcome-link:** primary (guided improvement) + enabling (cohesion).
      **Solution:** a home view rendering `due_items()` as **"today's plan"** (pure read-only surfacing — new endpoint/view,
      no new storage) + a **single ordered learning path** with surfaced mastery thresholds; navigating a node loads its drill.
      ⚠️ **Decision (surface at spec):** does the hub **replace / absorb / sit above** the existing `VIEWS` tab row (which is
      the de-facto top-level nav today)? The map flags this as an IA decision, not a silent insert — resolve it before building.
      **Pass/fail:** home lists today's due items from `due_items()`; a single path with mastery labels renders; a path node
      loads its drill; `verify.sh` + build green. **Appetite:** ~1 epic. **No-gos:** no branching skill-tree (single path);
      no new SRS storage; onboarding/placement is N-Next, not here.

- [x] **N8 — Concept cards (point-of-need, ~10–15).** *(done 2026-07-03: 15 doc-grounded cards + leak/tag matcher in services + /cards/match endpoint + FeedbackPanel point-of-need render with hash-route drill-this; refuter pass, live-probed against real grader outputs)* ICE 8·6·4 (benefits from N1/N3).
      **Problem:** research docs 01–08 are **invisible in-app**; a missed rep explains nothing conceptual; no leak→card map
      exists and `leak_category` alone is too coarse to key one (e.g. `VS_RFI=112` = call/3bet/fold together).
      **Outcome-link:** primary (teach the concept) + enabling (stranger learns).
      **Solution:** a NEW versioned card content type under `content/` + schema (mirror `ContentPack`); a card component;
      rep→card linkage keyed on **`leak_category` + disambiguating `rationale_tags`** (map lives in `app/services`, not
      `app/domain`); card → "drill this" round-trip.
      **Pass/fail:** ≥10 cards validate against schema; a wrong answer surfaces the correct card; card→drill round-trips;
      `verify.sh` + build green. **Appetite:** ~1 epic. **No-gos:** no browsable lessons library (Later); cards are
      point-of-need only; no full docs-01–08 port.

- [x] **N9 — Portable-data seam ("others later" insurance).** *(done 2026-07-02: migration 0006, owner_id `''`-sentinel on both tables, srs_item PK = (owner_id, signature), 6 selects scoped; refuter pass)* ICE 4·6·6 (do before N-Next onboarding seeds data).
      **Problem:** persistence has **zero identity/tenancy**; `srs_item.signature` is a content-derived **PK** looked up via
      bare `session.get()` — a 2nd user would *silently overwrite* SM-2 progress. Deferring the PK change gets expensive
      (full-table rebuild once data exists).
      **Outcome-link:** enabling (multi-user isn't a rebuild).
      **Solution:** migration `0006` — nullable `owner_id` on `drill_attempt` + `srs_item` (additive, existing pattern) AND
      **widen `srs_item` PK to `(owner_id, signature)` now while zero data to migrate** (⚠️ the one shape decision — surfaced
      for gate approval; do NOT fold owner into the signature hash); thread `owner_id IS NULL` scoping into the 6 unscoped
      `select()` sites (`services/review.py`, `services/stats.py`).
      **Pass/fail:** migration applies; all existing read/write paths work unchanged (single-user implicit, NULL owner);
      domain-purity + full `pytest` green; `verify.sh` OK. **Appetite:** ~1 small epic.
      **No-gos:** no auth/login/accounts/hosting; no per-tenant DB routing; single SQLite file stays.
      ⚠️ **INVEST exception (acknowledged):** this is a **gate-mandated infrastructure seam** — by design it changes *no*
      observable behavior for today's single user; the value is future-proofing (the gate chose "design the seams now"). It's
      the one Now item not thin-and-vertical; accepted as a scoped exception, not an oversight. Do it before N-Next onboarding
      seeds `srs_item` rows, so those seeds are owner-scoped from birth.

## NEXT — validated problems / opportunities (not yet spec'd)

> 🔭 **Four items below (T-cover, T-agentcoach, T-oppo, T-blinddef) came out of the 2026-07-25 181-hand
> review.** Owner flagged them as must-not-lose. Full evidence:
> `docs/ai-dlc/research/persona-realism-artifacts/hand-analysis-181/SYNTHESIS.md` + `findings/HERO-findings.md`.
>
> ⛔ **SEQUENCING — OWNER DECISION 2026-07-25: FIX THE BOTS FIRST. These items are BLOCKED behind the
> persona-realism remediation set.** The same review produced a bot-fix program filed as **R8** in
> `roadmap/persona-realism.md` (`W-ARR` arrival instrumentation + the `N-*` NEXT items). That program is
> **higher priority than everything in this block** and goes through `/roadmap-ai-dlc` first. Do **not** start
> `T-agentcoach` — or pull any item here into NOW — until the bot-fix set has been planned and landed.
>
> Two independent reasons this order is correct, not arbitrary:
> 1. **`T-agentcoach` coaches against the bots.** The roster currently scores **3–4/10** realism, and the
>    review's own hero analysis had to caveat its bb/100 estimates for exactly that reason. An agent coach
>    trained on unrealistic opponents teaches exploits that do not transfer — the failure mode the project's
>    N2 principle already names ("teaching amplifies a wrong grade").
> 2. **`T-cover`'s target is a moving one.** Persona-realism is *changing the distribution of spots the mapper
>    must handle* (more limping, multiway, donk-leading, off-grid sizing). Widening the mapper against
>    today's bot behaviour means re-widening it after the bots change. Wait for the bot distribution to settle.

- **T-cover — "No baseline yet" is the dominant grader output, and the cause is the MAPPER, not the graders.**
  *Evidence (measured, 181-hand session `adaadc548`):* **105 of 247** graded decisions (**42.5%**) returned
  `coverage: unmappable` → the UI's "No baseline yet" (`simGrade.ts:24`, `SimDashboard.tsx`, `SimRecap.tsx`,
  `HandReplay.tsx`, `SimPostflopChart.tsx` — it is on **five** surfaces). Postflop it is far worse: **4 of 66
  graded = 6.1%**, with **turn 0/23** and **river 0/15**. The turn/river graders are **not** the problem —
  S5–S8 are done and `providers/turn.py` / `providers/river.py` exist and are dispatched. The gate is
  `backend/app/domain/table/grade_map_postflop.py`, which by its own docstring classifies **ONLY the HU
  single-raised-pot continuation line** and returns `None` on **any** doubt. **Not one** of the session's 66
  postflop decisions fit that shape — they were three-way, 3-bet pots, or limped pots. One hand (H6) *did*
  pass the HU-SRP gate and still failed, because the fish donk-led three streets and donk/lead has no baseline.
  *Candidate slices:* widen the mapper past HU-SRP — multiway · limped pots · 3-bet pots · donk/lead ·

> ⚠️ **CORRECTION 2026-07-25 (verified against HEAD) — do NOT quote `grade_map_postflop.py`'s module
> docstring; it is STALE.** It claims "ONLY the HU single-raised-pot continuation line," but HEAD ships
> **19 postflop mappers**, including **nine multiway** (`map_mw_flop_cbet`, `map_mw_vs_turn_bet`,
> `map_mw_caller_vs_river_bet`, …), **two limped-pot** (`map_limped_flop_lead`, `map_limped_flop_vs_lead`)
> and `map_flop_vs_caller_raise`. Consequence: **"multiway" and "limped pot" are NOT rejection reasons** —
> they are *supported shapes* that reject for some further reason. The measured 4/66 (turn 0/23, river 0/15)
> is unchanged; the CAUSE is gate predicates, not absent mappers, and the reason distribution is **unknown
> until `T-REJECT` measures it**. One structural hole is already confirmed: the limped-pot mappers are
> **flop-only**, so every limped turn and river has no mapper at all. **Scope any widening from `T-REJECT`'s
> observed matrix, never from prose.** (Fix the stale docstring while you are in there.)

  **bet-fraction tolerance** (bot bets like `1.16`, `3.49`, `21.38` must currently land within **0.06bb** of a
  recognized fraction; this already caused one regression where "bots never open 2.5" zeroed HJ/CO/BTN
  coverage — `simulate-table.md:493`, filed as R5). Ship with per-reason rejection counters so the next dip is
  attributable.
  *Open questions:* which rejection reason to attack first (needs the counters); whether multiway gets a real
  baseline or an explicit "multiway — not graded" tier distinct from "no baseline".
  ⚠️ **Coupling — this is actively eroding.** `persona-realism` is making the bots limp, cold-call, donk-lead
  and size off-grid *by design*. **Every persona-realism win starves this mapper further.** Counters are filed
  there as `W-ARR-b`; the fix lives here.

- **T-agentcoach — LLM-agent session coaching (EPIC-sized; owner-originated 2026-07-25).**
  *Origin:* the owner read an agent-written analysis of his own 181-hand session and asked for it as a product
  feature. **The target output shape is `findings/HERO-findings.md`** — read it before spec'ing; it is the
  acceptance bar. That shape is: a level read · a stat-line table vs target ranges · **leaks ranked by
  estimated bb/100** each with evidence hands and a concrete replacement action · an **opponent-specific
  adjustment** section · honest strengths · and a "was the result skill or variance" decomposition.
  *Why an agent and not more heuristics:* the highest-value findings were **cross-hand patterns no
  per-decision grader can see**. Example: the same player bluffed 75% pot with ace-high **into a calling
  station** (H77) and **checked back trip fours against that same station** (H107) — opposite-sign errors from
  one cause (no opponent-type adjustment). Nothing that grades decisions independently can surface that.
  *Foundation already shipped:* **N6** built the seam — `backend/app/services/coach.py`, Anthropic Claude API
  behind a **swappable provider seam with a templated fallback** so tests and offline both work, key by env
  var. This epic extends that seam; it does not invent a new one.
  *Owner decisions locked 2026-07-25 (do not re-litigate):*
  - **NARRATE ONLY.** The agent emits prose. It **must not** emit a correctness tier or an EV number. "No
    baseline yet" remains the grade; the coaching appears **alongside** it. This preserves the invariant that
    grading stays behind the one async `StrategyProvider`, keeps LLM output out of leak buckets and SRS
    scheduling, and keeps EV credible. *(Full-verdict authority is a LATER bet — see "Bet: LLM verdict
    authority".)*
  - **Both shapes, sequenced.** **Phase 1 = session-level review** (one pass over the whole hand history →
    the HERO-findings shape). **Phase 2 = per-spot backfill**, reusing the same agent/prompt to fill the
    "No baseline yet" surfaces on demand. Phase 1 first — it establishes the prompt, the quality bar and the
    persona context that Phase 2 reuses.
  *Candidate slices:* session-transcript builder (the exporter written for the review is a working reference —
  it reconstructs hole cards, positions, per-street action, made-hand category and showdown result, and
  reconciles to each seat's stored `invested_total_bb`) · agent prompt + output contract · a rendered
  session-review surface · Phase-2 per-spot path · cost/latency budget + caching.
  *Open questions:* one call per session or map-reduce over hands (181 hands is a large context) · does the
  review persist as a row or regenerate on demand · **the agent needs seat→persona to give opponent-specific
  advice** — that is the same input `N-oppo` wants (see below), so build it once · privacy scope is wider than
  N6's per-decision call (a whole session leaves the device; N6's precedent accepted per-hand data, this is a
  larger disclosure and should be an explicit opt-in).

- **T-oppo — opponent type as a grader input.** *Evidence:* across **all 142** reasoning texts in the session,
  the words `station`, `fish`, `nit`, `maniac`, `lag`, `exploit` and `villain` appear **zero** times. The
  advice would be identical against eight solvers. At a table where the entire edge is opponent-specific this
  is the single largest quality gap in the existing feedback, and it is **currently filed nowhere**.
  Concrete cost: the app graded the H77 ace-high bluff into a station and the H107 check-back of trips against
  that same station without ever noticing the opponent. *Candidate slices:* thread seat persona into the
  grading context; opponent-aware rationale selection. *Open question:* does this stay descriptive
  ("this opponent rarely folds") or become prescriptive — the latter edges toward exploit-coaching, which the
  persona roadmap treats as an owner-gated architecture line.

- **T-blinddef — `blind_defense` endorses folding almost universally.** *Evidence:* it fired in ~21% of
  blind-vs-raise spots (5 of ~24) and **endorsed a fold all 5 times**, including BB `KTo` (H35) and BB `87o`
  (H152) — both routine defends. The user defends his big blind **1 hand in 13**; the coach confirmed that was
  correct on every occasion it had an opinion. *Candidate slice:* re-author the `blind_defense` node rationale
  + check the underlying range. *(Related: `_hand_category` mislabels — a flopped wheel straight came back
  `draw` (H47), two pair on a four-flush paired board came back `strong` on all three streets (H6). The
  postflop graders consume it. Grading **inputs** before grading prose.)*

- **Onboarding + placement diagnostic.** *Evidence:* cold-start into a random spot; competent-novice deserves a seeded
  start; maps show the natural fit = seed `srs_item` rows via `record_attempt()` (no new table) + an "onboarded" flag.
  *Candidate slices:* first-run orientation; a short diagnostic; scoring→SM-2-seed mapping; needs N7 (path to seed into) +
  N9 (owner-scoped seeds). *Open questions:* diagnostic length/shape; how performance maps to initial `ease_factor`/`due_date`.
- **Turn barrel (2f) — with its lesson.** *Evidence:* research §5.1–5.2 (scare-card / picked-up-equity / capped-range);
  `range_advantage()`'s `node_context` param is dead code needing real new scoring. *Candidate slices:* aggressor 2nd-bet
  grader + turn drill mode + leak bucket + **its concept card + tiered feedback** (per the mandate — a street ships *with*
  teaching). *Open questions:* barrel-sizing buckets; multiway deferral.
- **Remaining rationale authoring tranches.** *Evidence:* N3 does the path + RFI/vs-RFI only; `vs_3bet/vs_4bet/vs_limpers/
  blind_defense` + all postflop nodes still templated. *Candidate slices:* author per pack; extend the postflop content path.
- **Engagement: streak-with-forgiveness + consistency heatmap.** *Evidence:* SOTA UX research (`best-practices-drafts/`) —
  Duolingo streak-freeze cut churn 21%. *Candidate slices:* streak model + forgiveness; a calendar-heatmap view over
  `drill_attempt.created_at`. *Open question:* does a single local user value streaks — validate before building.
- **FE type-generation CI gate.** *Evidence:* `types.ts` is hand-maintained + already drifted (missing `solver_node_key`);
  `verify.sh` only checks paths exist, not schema equality. *Candidate slice:* wire `gen:api` + a CI check tying FE types to
  the live backend schema. *(N1/N5 regenerate locally; this makes it enforced.)*

## LATER — bets / outcomes (unexplored · NO hard dates)

- **Bet: full browsable lessons library** (docs 01–08 in-app). *Segment:* self + future learners · confidence: med ·
  assumptions to test: do point-of-need cards (N8) satisfy the need, or is a library wanted? · review-by: after N8 lands + used.
- **Bet: complete turn/river/multiway/full-hand coverage** (2g facing-turn · 2h river value/bluff · 2i facing-river ·
  2j multiway · 2k full-hand). *Confidence:* hi (well-sequenced in old roadmap) · **assumptions to test:** does 2f + its
  teaching move the primary metric (accuracy↑/EV-loss↓) enough to justify continuing the full engine build-out — or does the
  teaching layer alone capture most of the gain? · review-by: after 2f + teaching land.
  > **OWNER DECISION 2026-07-25 — `T-agentcoach` IS the test of this bet.** This assumption was standing open with no
  > experiment attached. It now has one: ship the LLM-agent session coach (NEXT → `T-agentcoach`), measure whether it
  > moves accuracy / EV-loss, and let that result decide whether 2g–2k is ever built. If the teaching layer captures
  > most of the gain, this bet closes unbuilt and five engine epics are saved. **Do not start 2g–2k before
  > `T-agentcoach` has shipped and been measured.** Note the supporting evidence is already strong: the deterministic
  > engine's *graders* for turn and river exist and work — they are simply never reached (`T-cover`), so the marginal
  > value of *more graders* is unproven while the marginal value of *more reach* is demonstrated.

- **Bet: LLM verdict authority** — let the agent coach emit a correctness tier, and much later an EV number, for spots
  the heuristic mapper cannot grade. *Segment:* self + future learners · confidence: med ·
  **owner decision 2026-07-25: "narrate only for now, full verdict much much later"** — `T-agentcoach` ships
  narrate-only and this stays a bet. **Assumptions to test:** can an LLM tier be made reproducible enough to feed
  leak buckets and SRS scheduling (both currently deterministic), and can an LLM EV be made credible enough to sit
  next to engine EVs that the product promises are *approximate but principled*? **Blocking invariants to renegotiate
  first:** grading stays behind the one async `StrategyProvider`; results are freq+EV never boolean; `spot_signature()`
  is frozen. *Review-by:* after `T-agentcoach` Phase 1 has shipped and its prose quality has been judged in real use —
  if the narration is not trusted, verdict authority is moot.
- **Bet: solver-grade strategy (Phase 3)** — `SolverTableProvider` + `HybridProvider` on the same interface; revisit **2d
  equity-backed range advantage** (deferred — needs solver EV data). *Confidence:* med · review-by: after postflop breadth.
- **Bet: live integration + mental game (Phase 4)** — live session logger, move-up readiness diagnostic, variance framing.
  *Confidence:* lo · review-by: after the trainer proves it moves the primary metric.
- **Bet: real multi-user** (auth / hosting / accounts) — the "others" the N9 seam enables. *Confidence:* lo ·
  assumptions to test: is there demand beyond the primary user? · review-by: after primary-user value is proven.
- **Bet: custom scenario builder + content-pack editor UI (Phase 5).** *Confidence:* lo · review-by: open-ended.

## Out of scope / no-gos (global)

- 🚫 **No auth / accounts / hosting / billing / multiplayer machinery now** — N9 builds the *data seam* only.
- 🚫 **No solver tables now** (Phase 3) — heuristic + credible interim EV only; EVs labeled *approximate*.
- 🚫 **No hand-history imports** — leaks come from drilling (core product decision).
- 🚫 **No live-session logger / mental-game module now** (Phase 4).
- 🚫 **No full browsable lessons library now** — concept cards at point-of-need only.
- ✅ **Invariants held throughout:** domain core free of web/DB imports (test-enforced); results freq+EV never boolean;
  grading behind the one async `StrategyProvider`; strategy as versioned content-data; FE types generated from
  `openapi.json` (stop hand-editing `types.ts`); CSS = design tokens only; AA contrast + visible focus both themes; every
  schema change ships an Alembic migration; `spot_signature()` is frozen (changing it orphans SRS history).
- ⚠️ **Ask-first:** any `StrategyProvider` interface-shape change; any migration that rewrites existing rows (vs additive);
  pulling a Later engine epic (2g–2k) into Now; adding a new top-level dependency.
- **Process:** may `git push` + open PRs on `feat/*`/`fix/*`/`chore/*` autonomously; never push to `main`, force-push, or
  merge a PR without explicit confirmation.
