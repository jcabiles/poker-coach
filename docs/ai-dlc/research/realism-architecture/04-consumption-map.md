# Consumption map — where each S2b conclusion goes

Slice S2b of `../../roadmap/bot-realism-flywheel.md`, PRD requirement R5.
Session R, 2026-08-05.

**Purpose.** Research that nobody consumes is waste. Every conclusion from the three dossiers is
routed here to exactly one destination, with an evidence grade and — where it matters — the
specific change it should cause. **Conclusions routed to `REJECTED` are recorded so they are not
re-proposed later.**

**Destinations:** `SCORER` = S3, the realism score · `SWEEP` = S4, the batch sweep runner ·
`DETECTION` = S6, the detection-protocol pilot · `ESTIMAND` = S2a, the methods and estimand
contract (including the target registry) · `ARCH` = the phase-3 fix-vs-overhaul gate ·
`CORPUS` = the corpus decision and the roadmap's corpus NEXT item · `REJECTED` = considered and
explicitly not adopted · `OWNER` = needs an owner ruling before it can be consumed.

**Evidence grades:** **A** = retrieved primary source · **B** = retrieved credible secondary
source, or primary source with an unverified detail · **C** = single/weak source or metadata-only
retrieval · **D** = unverified. Grades below are post-adjudication (Lead corrections applied).

---

## 1. Plain-language version (read this first)

Three research dossiers produced about thirty usable conclusions. This page decides what happens
to each one, so nothing gets read once and forgotten.

The short version of where things landed:

- **The score being built (S3) gains four concrete measurement recipes** borrowed from chess and
  game-AI research, and one warning: nobody has ever published a formal "distance" formula for
  comparing poker action frequencies to human ones, so that choice is ours to make and defend.
- **The detection pilot (S6) gains the most.** It turns out no public poker experiment of this kind
  exists, so we are designing rather than copying — but commercial poker rooms have been doing a
  version of it for fifteen years, and their oldest technique (spotting *groups* of accounts that
  play too similarly) exposes a weakness our own bots have by construction: seven personas built
  from one engine may cluster together the way a bot farm does.
- **The architecture decision (phase 3) gains a third option it did not have.** The one experiment
  in this research where an agent actually fooled human judges did it by **hand-writing extra
  scoring rules describing how people behave** — not by learning from recordings of real play. Our
  dials are already hand-written scoring rules; they just describe *good poker* rather than
  *human poker*. So "keep the engine, change what it aims at" is a live branch, alongside "keep
  tuning" and "rebuild." Some rebuild options do need human hand data we cannot get; others
  (self-play, authored rewards) do not — but the ones that escape the data problem generally aim
  at *winning*, which is the wrong target.
  *(An earlier draft of this page said flatly that every alternative was blocked by the data
  problem. Blind review caught that, and checking the sources confirmed it was wrong.)*
- **The corpus question resolves as PARTIAL**: no hands, but modern human *statistics* are
  obtainable, which is what our targets actually need. One provenance question needs your ruling.

---

## 2. The map

### 2.1 → `ESTIMAND` (S2a: methods, estimand contract, target registry)

| # | Conclusion | Grade | What S2a should do with it |
|---|---|---|---|
| E1 | Modern **segmented** human NLHE population statistics **are** publicly available and free (GGPoker pool, NL25–NL500, split into all / top-100 winners / regulars / recreationals; VPIP, PFR, 3-bet, fold-to-3-bet, 4-bet, aggression by street, WTSD, W$SD, WWSF, c-bet, fold-to-c-bet) | B | **Make this the primary modern source for the target registry**, superseding literature bands wherever it has coverage. *Gated on `OWNER-1`.* |
| E1b | ⚠️ **Those segments are population strata, not play-style archetypes** — "all players" and "top-100 winners" are not styles, and regular/recreational is a profitability-and-VPIP threshold, not TAG/LAG/nit/station/maniac | B | *(Corrected after blind review; an earlier draft said they map to personas "directly".)* **S2a must construct and justify the strata→persona mapping explicitly**; every target derived through it is a modelled inference carrying its own confidence grade |
| E2 | That source publishes **no sample size and no methodology**, and uses a **rolling 12-month window** | B | Every target derived from it needs a **low confidence grade**. **A retrieval date alone is insufficient** — the page changes under you, so the registry must record **every consumed value plus its exact filter combination** (stake, segment, statistic), or archive a dated snapshot. Cheap at first use, impossible later |
| E3 | The project's current literature bands are **explicitly uncited author opinion** (verified on a named example) | A | Demote literature bands to a **floor and sanity check**, never a target of record. Record this as the reason the registry changed |
| E4 | Peer-reviewed 2009–10 NLHE numbers exist at very large scale (76.9M hands, 600k+ players) and the **published results are freely usable** even though the underlying data is not | A (paper) | Use as an **independent magnitude sanity-check** against E1. Two sources disagreeing is a finding; one source is a single point of failure |
| E5 | Structured expert elicitation (SHELF / Delphi) is an established protocol for exactly this sparse-data situation, producing **distributions rather than point estimates** | B | Use **only for statistics E1 and E4 do not cover.** Do not re-elicit numbers a published aggregate already gives — that adds anchoring bias for no information |
| E6 | Limit-era (IRC) data can support **ordering/shape claims only**, never magnitudes; anything bet-sizing-dependent cannot transfer at all | B (reasoned, flagged as analysis not evidence) | Admit a rung-(i) parameter **only with a written mechanism-based justification per parameter**; the registry should refuse an unjustified one rather than accept it silently |
| E7 | No quantified era-drift trend line for NLHE population statistics exists anywhere; but one retrieved study found involvement measures **stable** across a decade | B / A | Do not assume uniform drift **or** uniform stability. Record era as an explicit uncertainty dimension per stat |
| E8 | Variance-reduction estimators (DIVAT/AIVAT) give 75–85% variance reduction on hand-outcome measurements | A | Adopt if any registry stat or validation quantity is estimated from noisy hand outcomes rather than counted directly |

### 2.2 → `SCORER` (S3: realism score v0)

| # | Conclusion | Grade | What S3 should do with it |
|---|---|---|---|
| S1 | **Move-matching accuracy** — fraction of decisions where the predicted action equals the human's actual action | A | Candidate component metric; requires per-decision human data, so **available only if `CORPUS` changes** |
| S2 | **Likelihood / perplexity** — average probability assigned to the human's actual action; captures distribution match even when the top pick differs | B | Same data dependency as S1; note as the metric to adopt *if* data ever arrives |
| S3 | **Discriminator accuracy** — train a classifier to separate bot traces from human traces; **accuracy near chance = indistinguishable**. Runs offline, so the speed constraint is irrelevant | A | **Adopt as a design target for the score's validation story** — the one measurement architecture a corpus NO-GO does not kill. ⚠️ **But "a modest human sample, e.g. the owner's own hands, suffices" is unsupported** (blind-review finding, accepted): one player's hands confound human-vs-bot with player identity, stake and session conditions, and the cited survey names limited/imbalanced human data as a known problem. **Require multiple humans, held-out-player evaluation, matched conditions, and a power analysis** — the same single-subject bias the roadmap already flags for the S6 pilot applies here |
| S4 | **Not found in this session's documented search (as of 2026-08):** any formal distributional-distance metric (KL, Wasserstein, Jensen-Shannon) applied to poker action frequencies for a human-likeness objective | A (search outcome, **not** a universal negative) | S3 appears to be choosing its distance function without precedent. Document the choice and its rationale explicitly — a defensible novelty for the portfolio, but only if argued rather than assumed |
| S5 | Internal statistics correlate with, but do not guarantee, indistinguishability to a judge | A | Reinforces the S2a stop-gate: the score stays an **exploratory surrogate** until convergent evidence exists. Do not let a good score stand in for a detection result |
| S6 | Strength and human-likeness are measured by **disjoint** toolsets across the whole literature | B (structural) | Do not let win-rate or EV sanity checks stand in for realism anywhere in the scorer |

### 2.3 → `DETECTION` (S6: detection-protocol pilot)

| # | Conclusion | Grade | What S6 should do with it |
|---|---|---|---|
| D1 | **Not found in this session's documented search (as of 2026-08):** any public blind human-vs-bot labelling experiment for poker | A (search outcome, **not** a universal negative) | State plainly in the write-up that S6 **designs** a protocol rather than reproducing one, and that this rests on a documented search rather than an exhaustive survey. A portfolio strength if disclosed, a weakness if implied otherwise |
| D2 | Blind-judge protocols must test for **statistical indistinguishability**, not a high score | A | Preregister the indistinguishability test, not a threshold |
| D3 | **Always report the human baseline.** In BotPrize, real humans were rated non-human ~59–60% of the time; bots "beat" a ~40% bar | B | The S6 write-up must report **how often judges misclassify the human class**, or its bot number is uninterpretable. This is a concrete reporting requirement, not a caveat |
| D4 | Commercial detection's oldest documented technique is **grouping accounts that play too similarly to be chance** | B | **Add a cross-persona similarity statistic.** Seven personas from one dial engine over one merit table are structurally the thing this method catches — a realism risk the current architecture creates *by construction*, invisible to any per-persona distance metric |
| D5 | The same finding sharpens the roadmap's **Goodhart guard from the opposite direction** | B | Archetype separation is currently framed as a coaching-value floor; it is **also an anti-detection requirement**. Update the guard's rationale so it is not traded away later as a mere product concern |
| D6 | Operators use **expert humans reviewing hand histories** as judges today (GGPoker Integrity Council; 888poker community reports) | A / B | Weak external validation that the protocol shape is sound. **Zero** evidence about calibration — do not import any operator accuracy number |
| D7 | Cicero is the strongest verified blind precedent (40 games, 82 humans, top-10%, undetected) but is **Diplomacy, with a dialogue channel** | A (numbers) / B (blindness detail) | Cite as precedent that the outcome is achievable; **do not import the protocol**. Poker's surface is decisions, timing and sizing only — narrower, and arguably harder to hide in |
| D8 | Survey proposes: the harder human-likeness is in a game, the **easier** bot detection becomes in it. ⚠️ **The paper explicitly calls this an OPEN HYPOTHESIS inviting validation or refutation**, and its single tactical-game detector does not establish a cross-game relationship | A (paper) / **relationship unestablished** | *(Corrected from grade A after blind review.)* If S6 preregisters an expected direction, label it a **hypothesis under test**, not an evidence-backed prior. Do not let it justify a one-sided interpretation of the pilot result |
| D9 | No commercial detection accuracy figure is independently audited | A | Never use an operator number as a target or benchmark |
| D10 | **NEW — human judges can be confidently wrong at scale.** A large FIFA player base convinced itself it could detect hidden difficulty manipulation, sued EA in 2020, and **dropped the case in Feb 2021** after seeing the engineering; EA says the system was never shipped in those games | A | A documented false-positive of exactly the judgment S6 asks judges to make. **Reinforces D3:** the pilot must report how often judges misclassify the *human* class, and must not treat judge confidence as signal |

### 2.4 → `ARCH` (phase-3 fix-vs-overhaul gate)

> **⚠️ This section was substantially rewritten after blind cross-family review.** Its original
> headline — "every alternative architecture requires human training data" — was **false**, and the
> evidence for its second claim pointed the opposite way from how it was reported. Both are
> corrected below. The corrections make the phase-3 picture *better*, not worse: they open a third
> option that the original framing had closed off.

| # | Conclusion | Grade | Consequence for the gate |
|---|---|---|---|
| A1 | **⭐ Candidate architectures split into corpus-gated and not.** Blocked by the `CORPUS` NO-GO: behaviour cloning per style, empirical archetype clustering (and partially adversarial imitation, mixture-over-clones). **Not blocked:** persona-conditioned policies trained from *designer-authored* personas and rewards, self-play policies, and re-aimed dials | A | **The overhaul is narrowed, not blocked.** The gate's decision matrix needs this as a per-candidate column, not a global blocker. *(Corrected: the original claimed the blocker was universal. PCSP trains from authored personas; "Navigates Like Me" used no human training traces; self-play poker policies use no human data at all.)* |
| A1b | **The residual dependency that IS universal: every candidate needs an external human *target* to aim at and be scored against** | A | This is the real coupling to carry into phase 3. After this slice that target is **aggregate statistics** (`ESTIMAND` E1), not hands — a far cheaper dependency, and obtainable |
| A2 | **Competence-only training was detected under a blind test; the agent whose objective explicitly encoded human-like traits was not.** ⚠️ **That agent used hand-designed reward shaping — penalties for swift camera changes, wall collisions, standing still — NOT human demonstrations.** Human data was evaluation-only; both baselines were themselves deep-RL agents | A (full text verified) | **Reverses the original reading.** This is the dossier's only mechanism with a blind-test pass behind it, and the mechanism is **deliberate hand-authored targeting of human-likeness** — structurally what our dials already are, aimed at strategic merit instead. **Evidence for a third gate option (A11), not for overhaul.** Scope honestly: one navigation task, not poker |
| A3 | Behaviour cloning **has** been done in NLHE (Teófilo & Reis 2011): state → human action from real human game logs. Base result: insufficient for a **competitive** agent, strategy **static and cannot adapt**. **But the same paper then combines tactics from several players and reports greatly improved results** | A | Read on the right axis — "uncompetitive" is a *strength* failure, not our objective. The adaptivity warning still transfers: imitation yields a fixed style; humans adjust. **And static cloning is the paper's starting point, not its endpoint** — the mixture/selection layer is a hybrid option in its own right (A12) |
| A4 | **Speed is plausible but UNBENCHMARKED for our workload.** At 500 hands/sec × ~8–15 villain decisions/hand, the budget is ~**130–250 µs per decision, single-threaded, on a laptop CPU**. Published figures: CS:GO ~16 FPS **on a gaming GPU**; PCSP ~**183–202 µs per CPU ONNX call**; AlphaHoldem ~**2.9 ms/decision on GPU** | B | **Not "comfortable" — the nearest CPU figure sits inside our band with no headroom, and AlphaHoldem is 10–20× outside it.** *(Corrected from a grade-A "comfortably meets".)* **Require a representative CPU microbenchmark, including decisions-per-hand, before any overhaul proposal is graded on throughput** |
| A5 | Per-decision game-tree re-solving (DeepStack-style) costs seconds per decision | A | **Disqualified.** Consistent with the existing no-go on per-decision LLM policies |
| A6 | The Alberta lineage itself abandoned hand-tuned heuristics for a learned value function once progress stalled — **on strength, not realism** | A | Suggestive precedent for the overhaul direction. Do **not** overstate it: they were solving a different problem |
| A7 | Fixed architectures hit a documented **adaptivity** ceiling (CPRG's own account of Poki) | B | The nearest thing to a literature ceiling result. It is about adaptivity, not human-likeness — do not present it as the latter |
| A8 | **Not found in this session's documented search (as of 2026-08):** any statement of the owner's exact negative result ("a tuned dial architecture provably plateaus below a human-likeness threshold") | A (search outcome, **not** a universal negative) | **The ceiling question cannot be answered from the literature we found. It must be measured — which is precisely what S5 exists to do.** S2b therefore *validates the roadmap's sequencing* rather than short-cutting it |
| A9 | Bias injection over a solved baseline, with a handful of named archetypes, is the **disclosed commercial state of the art** (GTO Wizard), and its own vendor scopes it as a study aid, not realism | A | Our architecture is not naive — it is the state of the disclosed art. Cuts both ways: no shame in the current design, and no commercial evidence this family reaches believability |
| A10 | A mature, shipped human-imitation system (Drivatar) was **withdrawn** in 2023 for fairness and quality reasons | B | "Trained on human data" is necessary, not sufficient. An overhaul plan needs a correction/curation layer designed and budgeted up front |
| A11 | **⭐ NEW — a third gate option exists: keep the architecture, change what it optimises.** "Navigates Like Me" passed a blind test using hand-authored terms encoding human-like traits. Our dials are hand-authored terms encoding *strategic merit* | B (one non-poker task) | **The phase-3 gate is not a clean fix-versus-rebuild binary.** Add "re-aim the dials at human-likeness rather than merit" as an explicit third branch in the decision matrix. It is not corpus-gated, not speed-gated, and reuses the existing engine |
| A12 | **NEW — mixture / strategy-selection over cloned or authored styles** (Teófilo 2011's own extension, which combined tactics across players for "greatly improved" results) | B | A hybrid branch between one frozen style and a full rebuild. Also the most direct answer to A3's adaptivity warning |
| A13 | **NEW — self-play poker policies exist and need no human data at all** (Poker-CNN, arXiv 1509.06731; AlphaHoldem, AAAI 2022, DOI 10.1609/aaai.v36i4.20394) | B (metadata level) | Breaks the "all alternatives are corpus-gated" claim (A1) — **but they optimise *strength*, and strength and human-likeness are disjoint objectives (S6).** Self-play escapes the data blocker by aiming at the wrong target. Include in the matrix; do not mistake it for a realism route |

### 2.5 → `CORPUS` (corpus decision + roadmap NEXT item)

| # | Conclusion | Grade | Consequence |
|---|---|---|---|
| C1 | **NO-GO on a licensing-clean, modern, full-action human NLHE hand corpus.** Every candidate of adequate size traces to datamining that poker sites' own terms prohibit by name | A (verdict) / B (ToS text) | Close the "acquire a corpus" option for now. **Blocks the corpus-gated half of `ARCH` A1.** The roadmap's corpus NEXT item should be re-scoped from *acquire hands* to *acquire statistics* |
| C1b | ⚠️ **This is a project-policy and ethics NO-GO, not a legal ruling** (blind-review finding, accepted). Collector contract breach, unauthorised-access law, copyright and privacy are four separate questions; a downstream *user* sits differently from the original collector; and US authority cuts both ways (hiQ v. LinkedIn on scraping and CFAA; Feist on facts not being copyrightable) — **neither case resolves this**, since poker hand data is arguably non-public | B | **Restate the verdict in these terms wherever it is repeated, including any public write-up.** The practical outcome is unchanged; the justification becomes one we can actually defend. Do not present a legal conclusion we are not qualified to give |
| C2 | **PARTIAL overall**, because target *statistics* — what the registry actually consumes — are obtainable (E1) | B | The flywheel is **not blocked** under any branch. Record that the corpus bet, as originally framed, does not pay off |
| C3 | A downstream open licence (CC-BY/MIT) **does not cure** an upstream terms violation — independently confirmed by both the Claude lane and the cross-family sweep | A | Standing rule for any future data acquisition in either repo. **Check provenance at two levels, always** |
| C4 | Formal operator data-sharing agreements are a **demonstrated** access route, but the one working precedent delivered financial aggregates, not play data | A | The only credible path to a real GO. Cheap to keep open; expensive to pursue. Not recommended now |
| C5 | The Pluribus supplementary file's reuse terms are **unresolved**; asking AAAS is cheap | B | Low-cost open question. Even resolved, 10,000 hands / 13 players is too narrow to be a target source |
| C6 | Screen-name-keyed hand data is **personal data** and none of these corpora document a modern consent process | B | Applies to any future acquisition and to anything published from it |

### 2.6 → `OWNER` (rulings needed before consumption)

| # | Question | Blocks | Recommendation |
|---|---|---|---|
| **OWNER-1** | ✅ **RESOLVED 2026-08-06 — ruling: (A) use and disclose.** The registry may consume the published GGPoker pool aggregates. **Binding conditions:** record every value with its exact filter combination (stake · segment · statistic) + retrieval date; grade every derived target low-confidence; construct and justify the strata→persona mapping (E1b); state the provenance limitation in the registry **and** in any public methodology write-up | Unblocks `ESTIMAND` E1 | Ruling as recommended. Argument preserved in Dossier 3 §8 |
| **OWNER-2** | ✅ **RESOLVED 2026-08-06 — ruling: re-scope.** The roadmap NEXT item is now "Population-statistics ingestion + target-registry upgrade"; the acquire-hands framing is closed, with a formal operator data-sharing agreement retained as the only credible route back to hands (listed, not pursued) | Roadmap NEXT lane | Edit applied to `../../roadmap/bot-realism-flywheel.md` on the owner's explicit instruction — noted because the roadmap is normally director-owned and outside session R's boundary |

### 2.7 → `REJECTED` (considered, explicitly not adopted — do not re-propose)

| # | Option | Why rejected | Grade |
|---|---|---|---|
| R1 | Any datamined hand corpus (`phh-dataset` human core, HHDealer/HHmailer/pokerenergy, the PLOS ONE underlying data) | Prohibited by the originating sites' terms; an open downstream licence does not cure it | A |
| R2 | The Absolute Poker leaked hand-history file | Security-breach artifact containing real IP addresses | B |
| R3 | DeepStack human-study hands | No public download location found despite targeted search; existence of a release unverified | D |
| R4 | Kaggle "poker hand dataset" listings as a hand source | The widely-mirrored UCI set is **synthetic card combinatorics with no betting action**; others unverifiable | A |
| R5 | ACPC competition logs (620M+ hands) as a human-behaviour source | 100% bot-versus-bot | A |
| R6 | `statname.net` as a population-statistics source | Per-player lookup only, not aggregates; opaque provenance | B |
| R7 | MassBuster Pro / Hand2Note pool analysis as a statistics source | Both compute pool statistics from a database **the user supplies** — puts the datamining problem back on us | C |
| R8 | DeepStack-style per-decision re-solving as an architecture | Seconds per decision; fails the ~500 hands/sec constraint outright | A |
| R9 | Importing any commercial bot-detection accuracy figure as a benchmark | Every one is self-reported and unaudited | A |
| R10 | Importing Cicero's protocol wholesale for S6 | Diplomacy's detectability surface is dialogue; poker has none | A |
| R11 | Rung (i) limit-era data for magnitude targets | Fixed-limit lacks the bet-sizing dimension that drives most no-limit statistics | B |
| R12 | Expert elicitation for statistics already covered by published aggregates | Adds anchoring bias for no additional information | B |

---

## 3. Coverage check

Every conclusion in the three dossiers is routed above. Counts: `ESTIMAND` 9 · `SCORER` 6 ·
`DETECTION` 10 · `ARCH` 15 · `CORPUS` 7 · `OWNER` 2 · `REJECTED` 12. **Total 61**
(up from 53 — blind review added A11–A13, D10, E1b, C1b and split A1).

**Highest-value items, if only three things survive contact with reality:**
1. **`ARCH` A11 + A2 — there is a third gate option.** The only mechanism in this research with a
   *blind-test pass* behind it achieved human-likeness through **hand-authored terms encoding
   human-like traits**, not by learning from human data. Our dials are hand-authored terms — aimed
   at strategic merit. "Re-aim the dials at human-likeness" is not corpus-gated, not speed-gated,
   and reuses the engine. **The phase-3 gate should not be framed as a fix-versus-rebuild binary.**
   *(This replaces the pre-review headline, which claimed the overhaul was universally data-gated.
   That claim was false — see the correction banner in §2.4.)*
2. **`DETECTION` D4/D5** — cross-persona similarity is a detection surface our architecture creates
   by construction, and no per-persona metric can see it. Seven personas from one dial engine over
   one merit table is structurally what commercial grouping detectors are built to catch.
3. **`ESTIMAND` E1 + E1b** (pending `OWNER-1`) — modern segmented targets replace uncited literature
   bands, which was the original complaint that started this initiative. But the segments are
   population strata, and the mapping to personas must be built and justified, not assumed.

**Runner-up worth not losing: `ARCH` A4** — the ~500 hands/sec budget works out to ~130–250 µs per
decision, and the nearest published CPU figure sits *inside* that band with no headroom. Any
overhaul proposal owes a CPU microbenchmark before it can claim throughput.
