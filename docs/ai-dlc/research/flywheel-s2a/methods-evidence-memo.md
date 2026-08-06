# P2 — Methods & Target-Evidence Memo (flywheel-s2a)

Research artifact for slice **S2a** of `../../roadmap/bot-realism-flywheel.md` (PRD R0). Substrate for the estimand contract (`poker-analytics docs/methods/estimand-contract.md`) — not the contract itself. Every conclusion has an ID, an **evidence grade**, and a **landing tag**.

**Grades:** **A** peer-reviewed/replicated or authoritative standard · **B** textbook or widely-accepted practice · **C** single credible source or industry/vendor writeup · **D** reasoned here, unverified against any source (an argument, not evidence).
**Landing tags:** **(a)** search-space & decision rule · **(b)** target registry · **(d)** detection protocol · **(e)** score validation.

**Boundaries.** Not covered (another session owns them): poker-AI research lineage, commercial training tools, corpus GO/NO-GO and licensing. No hand histories downloaded. `persona-realism-theory-contract.md` was read as **INPUT ONLY** — no target below comes from it.

---

# HALF 1 — METHODS

## M1. Simulator-calibration practice

**M1.1** *Grade A · (a)* — **History matching** is the calibration idiom that fits our question, because its output is a **set of not-ruled-out inputs (NROY space)**, not a posterior. It scores each candidate input by an **implausibility** measure — standardised distance between observed target and simulated output, where the denominator sums *three* variances: simulator/Monte-Carlo variance, **model discrepancy**, and observation (target) uncertainty — and rules out regions iteratively in waves. ([Andrianakis et al., PLOS Comp Biol 2015](https://journals.plos.org/ploscompbiol/article?id=10.1371%2Fjournal.pcbi.1003968) · [hmer](https://arxiv.org/pdf/2209.05265) · [JASSS 25(2)1](https://www.jasss.org/25/2/1.html))

**M1.2** *Grade D · (a)* — Maps onto our verdict almost one-to-one: **NOT-REACHABLE ≡ "NROY space empty at the declared cutoff after the declared waves"**; **INCONCLUSIVE ≡ "NROY non-empty but unresolved, or coverage insufficient to empty it."** Adopting that vocabulary gives the decision rule a published referent instead of a bespoke one.

**M1.3** *Grade B · (a), (b)* — **The model-discrepancy term is not optional and is where we are most exposed.** Our simulator is a 9-max 100bb heuristic table; every human target in Half 2 comes from a *different* population. Set discrepancy to zero and implausibility is overstated — we would declare NOT-REACHABLE when the truth is "our targets don't describe our environment." The contract must require a **declared, non-zero discrepancy variance per stat**, with justification.

**M1.4** *Grade A/C · (a)* — **ABC** is the other mainstream likelihood-free calibrator, well established for agent-based models, but it targets a *posterior over parameters* and is expensive in high dimension; recent work adds ML screening precisely to cut that cost (~52% faster than rejection-ABC in one Covasim study). ([J Math Biol 2024](https://link.springer.com/article/10.1007/s00285-024-02144-2) · [ML-ABC](https://www.sciencedirect.com/science/article/pii/S1755436525000696))

**M1.5** *Grade D · (a)* — **Recommend history matching, not ABC.** We are asked a *feasibility* question ("does any config reach the bands?"), not an inference question ("what are the true dial values?"). ABC's posterior is the wrong object and its cost the wrong trade.

**M1.6** *Grade D · (a), (f)* — **Emulation is probably unnecessary at our scale; say so explicitly.** History matching normally needs a Gaussian-process emulator because a run costs hours; ours is a 50k-hand seeded export scored in minutes (PRD R1: <5 min). We can evaluate implausibility directly on design points and skip the emulator's own error term. If the P3 benchmark shows the declared design exceeds the 8h cap, an emulator becomes the declared fallback.

## M2. DoE / response surface for the reachability study

**M2.1** *Grade B · (a)* — **Design-family trade-off.** Latin hypercube sampling guarantees one-dimensional uniformity (one point per equal-probability stratum per input) but gives **no multi-dimensional coverage guarantee**; Sobol and other low-discrepancy sequences do better in multiple dimensions but **degrade when sample size is small relative to dimension**. ([arXiv 2203.06334](https://arxiv.org/pdf/2203.06334) · [AFIT primer](https://www.afit.edu/stat/statcoe_files/Space%20Filling%20Designs%20Final.pdf))

**M2.2** *Grade D · (a)* — **Ruling: optimised (maximin) LHD for the numeric dials, Sobol reserved for a refinement wave.** Our numeric dimension is modest (order 5–15 dials per persona) and N is budget-capped — exactly the regime where Sobol's small-n degradation bites and LHD's balance helps.

**M2.3** *Grade C · (a)* — **Sample-size floor:** the widely-repeated rule of thumb for computer experiments is **N ≈ 10 × d** design points (d = swept inputs). It is a floor for a first wave, **not** a coverage proof. ([arXiv 2203.06334](https://arxiv.org/pdf/2203.06334))

**M2.4** *Grade D (recipe) / C (underlying literature) · (a)* — **Mixed numeric + structural spaces.** Structural dials (lever present/absent, distribution family, frozen-vs-swept reference) are not points on a continuum and must not be interpolated. Standard handling: **stratify** — treat each structural combination as a block, run a space-filling numeric design *within* each block, estimate structural effects as between-block contrasts. This keeps the numeric design balanced inside every structural level and makes "does turning lever X on change reachability?" a clean comparison. ([blocked space-filling LHDs](https://www.sciencedirect.com/science/article/abs/pii/S016771521400279X))

**M2.5** *Grade B · (a)* — **Per-dial + interaction probes: resolution-IV fractional factorial at block level.** In resolution IV, main effects are not aliased with any two-factor interaction (they alias with three-factor interactions), but **two-factor interactions alias with each other**. That buys clean per-dial main effects cheaply, at the stated cost that a significant 2FI cannot be attributed to a specific pair without follow-up. The contract must state this alias limitation rather than claim clean interaction estimates. ([JMP](https://www.jmp.com/en/statistics-knowledge-portal/design-of-experiments/screening-designs/fractional-factorial-designs) · [design resolution](https://learnche.org/pid/design-analysis-experiments/fractional-factorial-designs/design-resolution))

**M2.6** *Grade A/B · (a)* — **Sensitivity analysis: Morris first, Sobol only on survivors.** Morris elementary-effects screening costs **r × (p+1)** runs and returns μ* (importance) and σ (nonlinearity-or-interaction) but **cannot separate nonlinearity from interaction**. Variance-based Sobol indices decompose output variance into main and interaction contributions and are the gold standard, but need far more evaluations. The literature's own recommendation for expensive nonlinear models is exactly this two-stage combination. ([Morris+Sobol, EMS 2020](https://www.sciencedirect.com/science/article/abs/pii/S1364815219302300) · [sensitivity::morris](https://rdrr.io/cran/sensitivity/man/morris.html) · [GSA caveats](https://pmc.ncbi.nlm.nih.gov/articles/PMC7367914/))

**M2.7** *Grade A/B · (a), (f)* — **Common random numbers should be mandatory across the sweep.** Evaluating competing configs under identical seeds induces positive correlation between paired outcomes and strictly reduces the variance of the *difference*; where correlation is absent it degrades gracefully to independent evaluation, so it cannot hurt. Reported effects are large (93.6% variance reduction on a mean incremental cost in one health-economics study). This makes PRD R2's "same (seed, config) reproduces identical scores" a variance-reduction asset, not only a reproducibility one. ([CRN in CEA](https://pmc.ncbi.nlm.nih.gov/articles/PMC3725537/) · [paired-seed evaluation](https://arxiv.org/abs/2512.24145))

**M2.8** *Grade B (remedy) / D (naming) · (a)* — **Selection bias when picking the best config is real; the remedy is standard.** Taking the max over noisy estimates biases the winner's estimate upward; the ranking-and-selection literature's remedy is **confirmatory re-evaluation on fresh seeds** before any claim, and supplies the vocabulary for "how sure are we the selected system is best" (indifference zone, probability of correct selection, multiple comparisons with the best). The "optimizer's curse" *name* was not verified against a primary source this session. ([Mgmt Sci 41(12)](https://pubsonline.informs.org/doi/10.1287/mnsc.41.12.1935) · [ACM TOMACS](https://dl.acm.org/doi/10.1145/502109.502111))

**M2.9** *Grade D (composed here) · (a)* — **Minimum-coverage criterion, proposed shape.** NOT-REACHABLE requires *all* of: (i) declared space covered at a stated design density (M2.3 floor met per structural block); (ii) every design point's best achievable graded distance excluded from the tolerance band **after** seed noise and target uncertainty enter via M1.1's three-variance denominator; (iii) a screening result (M2.6) showing no *excluded or frozen* dial has leverage on the failing stats — else the space was declared too small to answer the question; (iv) the fresh-seed confirmation (M2.8) applied to the **closest** configs, not only to REACHABLE ones. Any of (i)–(iii) failing ⇒ **INCONCLUSIVE**, never NOT-REACHABLE.

**M2.10** *Grade B (standard) / D (the preference) · (a)* — **Multiplicity.** A verdict over ~10+ stat families and many configs is a large multiple-testing surface. Two defensible preregistered options: (1) make the verdict a **single composite distance** so no per-stat testing occurs — multiplicity then dissolves into the weighting problem (T-COV); (2) keep per-stat decisions and control false-discovery rate across stats. Mixing them post hoc is the failure mode. Prefer (1).

## M3. Detection statistics

**M3.1** *Grade B · (d)* — **Balanced accuracy is the only one of the three valid on binary labels alone** — mean of sensitivity and specificity, immune to class imbalance, corresponding to a *single operating point*.

**M3.2** *Grade B · (d)* — **AUC and d′ require a graded response.** Both summarise a *family* of operating points; from one forced binary label there is no curve to integrate and "AUC" collapses to balanced accuracy. Reporting AUC or d′ therefore **obliges the protocol to elicit a calibrated confidence/probability per item** — a protocol requirement, not an analysis choice. ([SDT from confidence ratings](https://link.springer.com/article/10.3758/s13428-019-01231-3))

**M3.3** *Grade A (variance point) / B (extreme-rate correction, standard practice but the specific log-linear form unverified here) · (d)* — **d′ assumes equal-variance Gaussian signal and noise; AUC does not.** With heterogeneous seats and judges that assumption is suspect, so AUC is the safer primary and d′ secondary. Hit/false-alarm rates of exactly 0 or 1 make d′ undefined and need a declared correction rule. ([SDT models from confidence ratings](https://pmc.ncbi.nlm.nih.gov/articles/PMC6797662/))

**M3.4** *Grade D · (d)* — **Preregister balanced accuracy as PRIMARY, with AUC and d′ secondary and explicitly conditional on the confidence elicitation working.** Balanced accuracy is the statistic that survives if judges fail to give usable graded confidence — a realistic LLM-panel failure mode.

**M3.5** *Grade B · (d)* — **Our judgments are CROSSED-clustered, not nested: by judge and by seat/session.** One judge rates many seats; one seat is rated by many judges. Treating judgments as independent understates standard errors.

**M3.6** *Grade A/B · (d)* — **Cluster bootstrap — resample whole clusters with replacement — is the recommended uncertainty method.** It is the simplest robust route to valid AUC intervals under clustering and outperformed GEE sandwich standard errors in at least one comparison; GEE/sandwich remains the standard alternative. ([ROC from clustered data](https://pmc.ncbi.nlm.nih.gov/articles/PMC5181834/) · [ClusterBootstrap](https://link.springer.com/article/10.3758/s13428-019-01252-y) · [correlated-eye ROC tutorial](https://pmc.ncbi.nlm.nih.gov/articles/PMC8586066/))

**M3.7** *Grade B/D · (d)* — **With a small LLM panel, resample SEATS/SESSIONS and treat judges as fixed.** Cluster-based inference is unreliable with few clusters (the standard concern is roughly a few dozen), and a 3–7-model panel has far fewer judge-clusters than that. Resampling the seat dimension — where many clusters exist by design — is the honest choice, with panel composition then explicitly a *fixed* feature of the study rather than a sample from a judge population. ([few-cluster bootstrapping](https://pmc.ncbi.nlm.nih.gov/articles/PMC5965657/))

**M3.8** *Grade C (numbers, one preprint) / B (phenomenon, independently corroborated) · (d)* — **The single most important detection finding: LLM judges are severely correlated, so a panel is worth far fewer independent votes than its size suggests.** A 9-model, 7-family frontier panel measured **n_eff = 2.18 effective independent votes (24% of nominal)** via Kish's design effect `n_eff = k / (1 + (k−1)·φ̄)` with mean pairwise error correlation **φ̄ = 0.391**; an eigenvalue check gave 2.16. Same-family correlation (0.437) was **barely above** cross-family (0.389) — "use different vendors" does *not* buy independence. Chain-of-thought made it worse (1.94). The first 5 judges give ~90% of achievable independence; asymptote 1/φ̄ ≈ 2.56. Panel accuracy fell 22pp below the independence prediction, and unanimous panels erred **9.1%** of the time versus ~0.02% predicted under independence. Human annotator panels reach n_eff = 4.0–5.8. ([Nine Judges, Two Effective Votes](https://arxiv.org/html/2605.29800v1) · [Correlated Errors in LLMs](https://arxiv.org/abs/2506.07962))

**M3.9** *Grade C/D · (d)* — **Contract requirement that follows: report n_eff alongside k, computed by Kish's formula from the observed pairwise judge-agreement matrix in our own pilot, and treat n_eff — not k — as the panel's weight in every interval.** Quote the source's own diagnostic ("treat with caution if n_eff/k < 0.5") as a preregistered flag.

**M3.10** *Grade D on Grade C evidence · (d)* — **Aggregate by averaging per-judge confidence, not by majority vote.** Majority vote discards the graded response M3.2 requires, and correlated panels suppress disagreement exactly on the items they are collectively wrong about — so unanimity is the *least* informative signal a panel emits, not the most. Report per-judge statistics alongside the aggregate.

## M4. Small-n score validation (n = 13)

**M4.1** *Grade A · (e)* — **Do not use the software-default Spearman test.** The shipped test is asymptotic and documented to perform poorly at small n or under non-normality; a **permutation test on an appropriately studentized statistic** controls Type-I error robustly, including at small n. ([arXiv 2008.01200](https://arxiv.org/pdf/2008.01200))

**M4.2** *Grade B (arithmetic + standard practice) · (e)* — **Exhaustive permutation at n = 13 means 13! ≈ 6.23 × 10⁹ orderings — enumerable in principle, not worth it.** Preregister a **Monte-Carlo permutation test, fixed seed, ≥ 100,000 resamples**, reporting the Monte-Carlo standard error of the p-value (≈ 0.0007 at p ≈ 0.05 with 10⁵ draws — negligible against the decision).

**M4.3** *Grade A · (e)* — **Fisher-z confidence intervals are the wrong default here.** Under non-normality, nominal 95% Fisher z′ intervals have measured actual coverage as low as **68%**. Rank-based and bootstrap alternatives were the only universally robust performers; the best-behaved bootstrap variant came closest to nominal coverage but produced **overly long** intervals. ([Bishara & Hittner 2017](https://link.springer.com/article/10.3758/s13428-016-0702-8))

**M4.4** *Grade D · (e)* — **Report ρ + Monte-Carlo permutation p + a BCa bootstrap CI explicitly labelled "indicative, over-wide, n = 13".** The CI exists to be honest about imprecision, never as a precision claim, and must not be used to argue two candidate scores differ.

**M4.5** *Grade B (standard formulas; arithmetic shown so it can be checked) · (e)* — **What n = 13 can detect.** At n = 13 (df = 11) the critical correlation at α = .05 two-sided is **r ≈ 0.553** (t = 2.201 ⇒ r = t/√(t²+df) = 2.201/3.980). Power ≈ 0.80 needs a true ρ ≈ **0.70** (Fisher z = 0.867, SE = 1/√10 = 0.316 ⇒ z ≈ 2.74). The study is powered **only** for a strong monotone relationship; a true ρ of 0.4 — real but moderate — would be missed most of the time.

**M4.6** *Grade B/D · (e)* — **"Directional-only" is therefore a limit, not a hedge.** n = 13 can support "the score orders personas broadly as the expert does." It **cannot** support: distinguishing ρ = 0.4 from ρ = 0.8; validating the score's *level* or calibration (only its ordering); any subgroup or per-stat claim; any comparison between two candidate scoring formulas.

**M4.7** *Grade B (statistic) / D (its use as the composite's second leg) · (e)* — **Sign-agreement check.** Over all 13·12/2 = **78 pairs**, count the proportion whose ordering the score reproduces (this is Kendall's τ rescaled: τ = 2·concordant/78 − 1) and test it with the same permutation machinery as M4.2 at a threshold fixed in advance. More interpretable than ρ to a non-statistician, and degrades gracefully when one rating is unreliable.

**M4.8** *Grade B (jackknife influence is standard) / D (the fragility rule) · (e)* — **Leave-one-out at n = 13 is an influence diagnostic, not inference.** Refit ρ 13 times omitting one point; report min, max, range. If dropping any single expert rating moves ρ across the decision threshold, the validation is **fragile** and the composite should fail on fragility even when the full-sample ρ passes. No valid p-value can be computed from the 13 LOO fits.

**M4.9** *Grade D · (e)* — **Composite pass rule, proposed shape:** all three of (i) permutation p < α **and** ρ ≥ a preregistered floor stated explicitly rather than left implied by α; (ii) sign agreement above its preregistered threshold; (iii) LOO fragility check passed. Any leg failing ⇒ the stop-gate fires.

## M5. Turing-test / believability evaluation literature

**M5.1** *Grade B (protocol) / C (the 52.2% figure) · (d)* — **The believability literature's operative statistic is the "humanness rate": judged-human ÷ total judgments, with 50% as the pass line.** In the 2K BotPrize (Unreal Tournament 2004) judges tagged opponents in-game as BOT or HUMAN; the 2012 winners were the first to cross the line, at ~52% humanness over the contest's five years. ([ERCIM News](https://ercim-news.ercim.eu/en84/special/conscious-like-bot-wins-the-2k-botprize) · [phys.org](https://phys.org/news/2012-09-artificially-intelligent-game-bots-turing.html))

**M5.2** *Grade B · (d)* — **Judge expertise is a first-order design variable in game-bot believability, not a nuisance.** Dedicated protocol work exists on assessing computer-player believability and on how judge expertise changes verdicts. The contract must pin the judge's *stated competence level* as a protocol parameter (for an LLM panel: the prompt's declared poker expertise) — changing it changes the estimand. ([Frontiers CS 2021](https://www.frontiersin.org/journals/computer-science/articles/10.3389/fcomp.2021.774763/full) · [judge-expertise protocol](https://web.enib.fr/~buche/article/CW_18a.pdf))

**M5.3** *Grade A · (d)* — **The best modern template is Jones & Bergen's three-party Turing test: preregistered, randomised, fixed 5-minute exposure, simultaneous human-vs-system comparison, judgment + written justification + confidence score, replicated on two independent populations.** GPT-4.5 with a persona prompt was judged human **73%** of the time, LLaMa-3.1-405B **56%**, baselines ELIZA **23%** and GPT-4o **21%** — significantly *below* chance, showing the design discriminates in both directions. ([PNAS](https://www.pnas.org/doi/10.1073/pnas.2524472123) · [arXiv 2503.23674](https://arxiv.org/abs/2503.23674))

**M5.4** *Grade D (the transfer) on Grade A evidence · (d)* — **Design elements to copy verbatim:** preregistration before judging; balanced priors (judges told the base rate); matched information (bot and human seats rendered identically); fixed exposure declared in advance (their 5 minutes → our "N hands per seat"); confidence elicited per judgment; and a **deliberately bad control seat** so a floor result proves the instrument discriminates.

**M5.5** *Grade B (preprint, directly on point) · (d)* — **The surrogate-bias finding the contract must disclose.** In a displaced/inverted Turing test, **GPT-4 as adjudicator was markedly worse than interactive human interrogators (36.4% vs 64.8% accuracy)** and, decisively for us, its errors were **asymmetric**: it judged real humans to be human only **34.8%** of the time while judging AI to be human **70.9%** of the time. ([arXiv 2407.08853](https://arxiv.org/pdf/2407.08853))

**M5.6** *Grade D (composition) on Grade B evidence · (d)* — **Expected bias direction of the S6 pilot: an LLM panel will likely OVER-credit humanness, so measured detection is biased DOWN and our bots will look more human than they are.** Two independent mechanisms push the same way: M5.5's pro-AI-as-human asymmetry, and the fact that our judges are **displaced** (reading logged play) rather than interactive — the less accurate mode. Consequence: a *low* detection rate from the LLM pilot is **weak evidence at best**; a *high* detection rate (bots caught despite a lenient judge) is comparatively strong.

**M5.7** *Grade B · (d)* — **General LLM-judge failure modes to preregister controls for:** position/order sensitivity, verbosity preference, self-preference for a judge's own family's outputs, prompt-phrasing sensitivity, run-to-run inconsistency — plus the standing warning that judge *reliability* (self-consistency) is routinely mistaken for *validity* (agreement with the construct). Controls: randomise seat order per judge, fix decoding settings, snapshot model versions, run repeats to measure within-judge inconsistency, and never report agreement-among-judges as evidence of correctness. ([Reliability without Validity](https://arxiv.org/html/2606.19544v1) · [Galileo](https://galileo.ai/blog/llm-as-a-judge-vs-human-evaluation))

---

# HALF 2 — TARGET EVIDENCE

Targets must come from EXTERNAL human evidence. The internal theory contract was read only to know which families need targets. Where the external record is empty, this memo says so rather than borrowing the internal number.

**Our environment, for compatibility grading:** 9-handed (full ring), ~100bb effective, recreational- and live-adjacent mix, modern era.

## T-SRC. Source inventory

COMPAT = fitness of the source's population/format/class for *our* environment. **Class** is the decisive and most-often-ignored column: an *ideal target for a winning regular* and an *observed population average* are different statistics and must never be compared to the same measurement.

| ID | Source | Population / format / stakes | Era | Class | Citability | COMPAT | Grade |
|---|---|---|---|---|---|---|---|
| **X1** | [BlackRain79, "Best Poker HUD Stats"](https://www.blackrain79.com/2017/10/what-are-the-best-poker-hud-stats.html) | online micro NL2–NL25; publishes **6-max AND full-ring side by side** | 2017 | ideal winning-reg target | public blog | MED (format ✓, stakes ✓, class ✗) | C |
| **X2** | Selbrede, *The Statistics of Poker* (3rd ed.), data-mined **~6M hands**; free excerpts in [PokerNews A](https://www.pokernews.com/strategy/donkey-poker-low-stakes-live-games-differ-online-27134.htm) / [PokerNews B](https://www.pokernews.com/strategy/donkey-poker-do-you-play-too-many-hands-27182.htm) | online **full ring** NL10–NL200 (excerpts quote NL50/NL100); companion **live Vegas $1/$2** from "a few hundred" hands across four card rooms | ~2013–17 | **observed population average** | book © (don't reproduce tables); excerpt numbers public + attributable | **HIGH** online; MED live | B (database design) · C (individual numbers) |
| **X3** | [GipsyTeam, "WTSD in Poker"](https://gipsyteam.com/poker/wtsd-in-poker) | 6-max vs full ring side by side | recent | mixed | public | MED | C |
| **X4** | [Poker Copilot stat docs](https://pokercopilot.com/poker-statistics/continuation-bet) + [essential stats](https://pokercopilot.com/essential-poker-statistics) | tracker vendor, **format-blind**; c-bet doc scoped to **heads-up flop pots** | recent | mostly target; c-bet ranges read population-class | public | MED–LOW | C |
| **X5** | [Hand2Note postflop stats](https://hand2note.com/Blog/Features/essential-postflop-stats) | vendor, format- and stakes-blind | recent | winning-reg descriptive | public | LOW | C |
| **X6** | [MyPokerCoaching](https://www.mypokercoaching.com/poker-statistics-stats/) / Upswing-class writeups | format-blind or 6-max-leaning | recent | mixed | public | LOW | C |
| **X7** | Hold'em Manager official forum, full-ring HUD thread | **format-explicit full ring** colour bands | old | practitioner band | forum | LOW | D |
| **X8** | [Siler, *J. Gambling Studies* 26:401–420 (2010)](https://link.springer.com/article/10.1007/s10899-009-9168-2) | **~27M online hands**, PokerTracker-derived, small/med/high stakes; secondary reports describe 6-seat NLHE | 2008–09 | observed population | **peer-reviewed**, paywalled — **full text NOT retrieved** | UNKNOWN (likely 6-max ⇒ possibly LOW) | A as a class; **UNUSABLE until read** |
| **X9** | [Fiedler & Rock (2009)](https://www.liebertpub.com/doi/10.1089/glre.2008.13106) | 51,761 players, online NLHE 2008 | 2009 | skill study | peer-reviewed | **N/A** — reports critical repetition frequency, not behavioural frequencies | A but off-target |
| **X10** | [Sakai, Brown (2005)](https://cs.brown.edu/media/filer_public/3e/8e/3e8e2e01-0811-483c-80e6-18e8cd33b71e/hsakai.pdf) | online hands across blind levels; **only empirical bet-size distribution found** | 2005 | observed population | public thesis | LOW (era, format unstated) | C |
| **X11** | [IRC Poker Database (U. Alberta)](http://poker.cs.ualberta.ca/irc_poker_database.html), 10M+ hands | play-money IRC, mostly limit | 1995–2001 | observed | — | **LOW** (wrong game, era, money) | pointer only; corpus lane owns it |
| **X12** | [uoftcprg/phh-dataset](https://github.com/uoftcprg/phh-dataset), 341M limit + 278M HUNL | **Annual Computer Poker Competition = BOT hands** | — | machine play | — | **NONE for human targets** | flagged so volume isn't mistaken for relevance |

**T-SRC.1** *Grade B/C · (b)* — **X2 (Selbrede) is the single most useful source found**: the only one simultaneously full-ring, population-class, and backed by a stated multi-million-hand database. Every other source is format-blind, target-class, or both.

**T-SRC.2** *Grade D · (b)* — **X8 (Siler 2010) is the only peer-reviewed candidate and it could not be read.** Abstract and secondary coverage confirm ~27M hands and stakes-stratified strategy prevalence, but no per-stat values were retrievable, and one secondary report describes the tables as **six-seat**, which would make it format-incompatible. **Record it in the contract as an OPEN evidence item with explicit "unread" status, not as a citation.** Retrieving it is the highest-value single follow-up for the registry.

**T-SRC.3** *Grade B · (b)* — **Volume is not evidence.** X11 and X12 are the two largest public hand corpora and **neither describes our target population** (1990s play-money limit IRC; bot-vs-bot competition logs). The registry must not treat corpus size as compatibility.

**T-SRC.4** *Grade B · (b)* — **Class is the registry's most load-bearing column.** X1's full-ring "VPIP 15 / PFR 12" (winning-reg *target*) and X2's "VPIP 22 / PFR 8.5" (observed full-ring *population*) do not conflict — they are different statistics. A registry storing one number per stat without its class will silently compare a population measurement to a winning-player aspiration.

## T-STAT. Per-family evidence

**T-VPIP.1** *Grade C · COMPAT HIGH · (b)* — Full-ring VPIP has **two credible anchors of different class**: observed online full-ring population ≈ **22** (X2, NL50/NL100, ~6M hands); winning-reg target ≈ **15** (X1, NL2–25). Poker Copilot's "15–20% for tight play at full ring" (X4) corroborates the target class.

**T-VPIP.2** *Grade C, sample explicitly weak · (b)* — For the **recreational/live-adjacent** end there is one anchor: **live Vegas $1/$2 average VPIP ≈ 37** (X2), which its own author states rests on "a few hundred" recorded hands across four card rooms. Too small to fix a band; usable as **direction and rough magnitude** ("live low-stakes ≈ 1.7× looser than online full ring"), not as a target.

**T-PFR.1** *Grade C · (b)* — Observed online full-ring population PFR ≈ **8.5**; live $1/$2 ≈ **6** (both X2). Winning-reg full-ring target ≈ **12** (X1). Note the **inversion**: the population plays *more* hands and raises *fewer* than the winning-reg target.

**T-GAP.1** *Grade C (numbers) / B (inference) · (b)* — **The VPIP−PFR gap is strongly class-dependent — the most consequential target finding in this memo.** X2's population figures give a gap of **≈ 13.5** online (22 − 8.5) and **≈ 31** live (37 − 6); X1's winning-reg figures give **≈ 3** (15 − 12). A registry carrying a single "gap ≈ 3" target would encode a *winning regular*, while our roster is deliberately mostly recreational. **The gap target must be stored per archetype class, carrying its class label.**

**T-GAP.2** *Grade B (direction) / C (level) · (b)* — The gap's *direction* as a passivity diagnostic (bigger gap ⇒ more passive) is corroborated by every source consulted and is the least controversial claim in Half 2. Its *level* is not.

**T-3BET.1** *Grade C · (b)* — Full-ring 3-bet: winning-reg target ≈ **6** (X1); "good at low stakes" **5–9** (X4); observed **live $1/$2 ≈ 0.8** with online stated at roughly 3× live ⇒ **≈ 2.4** observed online population (X2). The population-vs-target spread here (~2.5×) is the widest of any preflop stat.

**T-F3B.1** *Grade C · (b)* — Fold-to-3-bet: full-ring winning-reg target **70** (X1; 65 at 6-max); "balanced ≈ 55, higher at low stakes" (X4); exploitative reference points 30 and 65 as the extremes worth attacking (X4). **No observed population number was found for full ring.**

**T-CBET.1** *Grade C (each number) / B (the class diagnosis) · (b)* — **Flop c-bet's class conflict is unresolved and must be recorded as such.** X1 gives **70 full ring = 70 6-max** as an *ideal target*; X4 gives an observed **40–60%** but scoped to **heads-up flop pots** with no format stated; X6 gives **45–60**; industry commentary reports low-stakes opponents c-betting **~80%** of flops. That is a ~40pp spread across four sources measuring at least three different things. **Recommendation: the registry stores c-bet with an explicit denominator declaration (aggressor-side? heads-up only? all flops including multiway?) and treats any target lacking that declaration as unusable.**

**T-CBET.2** *Grade C, low confidence · (b)* — Turn and river c-bet: **only X1** offers numbers (turn 50 / river 50, stated identical for both formats). Single-source, target-class, round to the nearest 10.

**T-FCB.1** *Grade C · (b)* — Fold-to-flop-c-bet: **60** full ring = 60 6-max (X1, target class); **42–57** for good opponents at lower stakes (X4, heads-up-flop scope); **~40** (X6); full-ring practitioner band "0–40 tight / 40–70 normal / 70+" (X7). Turn/river fold-to-c-bet **40 / 40** from X1 only.

**T-FCB.2** *Grade B on direction · **no evidence** on magnitude · (b)* — **The size-elasticity slope (fold-to-c-bet by bet size) has no quantified external source.** Every source states only the direction: most players fold more to a large c-bet and less to a small one.

**T-WTSD.1** *Grade C per source; the format contrast is the strongest cross-format claim available · (b)* — WTSD is the **best-evidenced** postflop family: two independent sources split it by format and agree — full ring ≈ **25** vs 6-max ≈ **27** (X1), and full ring **24–25** vs 6-max **27–28** (X3). Format-blind vendor sources put regs at **27–32** (X5, X6), consistent once you notice those sources are 6-max-leaning.

**T-WSD.1** *Grade C (level) · **no evidence** (format) · (b)* — W$SD: winning regs **50–55** (X5), **49–54** (X6-class). **No source found splits W$SD by table size**, so its format transferability is genuinely unknown — neither licensed nor prohibited.

**T-WWSF.1** *Grade C · (b)* — WWSF ("won when saw flop"): **~48** (X5), **45–53** (X6-class). Format-blind, single-class.

**T-AF.1** *Grade C · (b)* — Aggression: **AF = 3 for both 6-max and full ring** (X1) is the only side-by-side statement found. Poker Copilot gives **aggression frequency 50–60%** conditioned on VPIP 15–20 (X4).

**T-AF.2** *Grade B · (b)* — **Aggression is a definitional minefield; pin the formula, not the name.** Three incompatible statistics travel under "aggression": **AF = (bets + raises) / calls**; **AFq = (bets + raises) / (bets + raises + calls + folds)**, which puts folds in the denominator; and Hold'em Manager's "Agg%", computed differently again. A target of "3" is meaningless without saying which. ([AF](https://upswingpoker.com/glossary/aggression-factor-af/) · [AFq](https://upswingpoker.com/glossary/aggression-frequency-afq/))

**T-CR.1** *Grade D · (b)* — **Check-raise has essentially no external target.** The only quantitative statement located is a tracker user-guide line that typical check-raise frequency is **"2% or lower"** — no format, stakes, class, or street breakdown; the related "raise vs c-bet 8–12%" (X6) is a different statistic with a different denominator. ([Poker Copilot HUD guide](https://pokercopilot.com/userguide/8/en/topic/hud-statistics))

**T-SIZE.1** *Grade C · COMPAT LOW · (b)* — **Bet-sizing distributions have exactly one empirical external source, 20 years old.** X10 reports that at the lowest blind level bets are **distinctly skewed toward the small end**, with the skew shifting upward as blinds rise, and that players at $0.10 blinds **overbet the pot more than twice as often** as higher-blind players. Directionally useful; quantitatively unusable for a modern 9-max 100bb target.

**T-CALL.1** ***no evidence*** *· (b)* — **Calldown / showdown-value thresholds have NO external source at all.** Nothing resembling "frequency of calling a river bet with second pair" is published anywhere consulted. The nearest observable proxies are WTSD (how often a player reaches showdown) and W$SD (how often they win there) — *aggregate consequences* of calldown policy, not the policy itself.

**T-DET.1** ***no evidence*** *· (b), (a)* — **Behavioural determinism/variance has no external human target**; no source publishes an entropy, repeatability, or action-mix-variance statistic for human players, in any format.

**T-SPREAD.1** *Grade B · (b), (a)* — **No source published a per-archetype spread for ANY stat.** Every source gives a single pool-level number or a single winning-reg target. The six-archetype fan the score needs is externally unsupported for every family without exception. This is the structural limit of the whole exercise: **external evidence can anchor a pool level and, for a few stats, a format contrast; it cannot anchor a persona's band.**

## T-COV. Covariance and joint structure

**T-COV.1** *Grade B (an exhaustive-enough negative) · (b)* — **No source found provides a joint distribution, covariance matrix, or correlation coefficient between any pair of these statistics for a human player pool.** Searches across tracker vendors, poker media, and the academic player-modelling literature returned only (i) qualitative quadrant descriptions of the VPIP × PFR plane and (ii) clustering studies that produce *player-type labels* from VPIP/aggression features without publishing usable centroids or covariances for a general pool. **Stating this plainly is the honest answer: the joint-structure evidence base is empty.** ([LIACC, arXiv 1301.5946](https://arxiv.org/pdf/1301.5946) · [arXiv 1301.5943](https://arxiv.org/pdf/1301.5943))

**T-COV.2** *Grade C · (b)* — Two candidate joint sources were checked and both fail: a K-means-vs-LPA clustering thesis (PDF unreadable; a student dataset in any case) and a public "poker strategy map" writeup that turns out to be **six friends in a lockdown home game**, hand-logged, with no correlations reported. Neither is citable.

**T-COV.3** *Grade B/D · (b)* — **Only three things are actually known about joint structure:** (i) a **hard definitional constraint**, PFR ≤ VPIP, plus analogous accounting constraints among WTSD / W$SD / WWSF; (ii) the gap (VPIP − PFR) is a *named diagnostic* whose level is class-dependent (T-GAP.1) — i.e. VPIP and PFR are strongly positively dependent, with the dependence differing between winning regs and recreational players; (iii) the two axes archetypes are conventionally defined on — loose/tight (a VPIP statement) and passive/aggressive (a gap/aggression statement) — are treated as near-orthogonal *by construction* everywhere, which is a modelling convention, not a measurement.

**T-COV.4** *Grade B (shrinkage as a practice; the specific Ledoit–Wolf form unverified here) / D (this four-step recipe and every entry of `R_prior`) · (b)* — **Preregistered fallback.** Absent an external covariance source, preregister a **shrinkage weighting** rather than either extreme:
1. **Enforce hard constraints first** (PFR ≤ VPIP; the accounting identities) as feasibility filters, not soft weights — the only *certain* joint facts available.
2. **Weight matrix** `Σ = λ·diag(σ²) + (1−λ)·(σσᵀ ∘ R_prior)`, where `diag(σ²)` is the independent-stats target and `R_prior` is a **rank-correlation prior written from first principles and committed before any scoring** — e.g. VPIP–PFR strongly positive; WTSD–W$SD negative (looser calldowns reach more showdowns with weaker holdings); c-bet vs fold-to-c-bet near zero (different actors). Every `R_prior` entry carries a one-line rationale in the contract.
3. **Preregister λ high** (recommend λ = 0.8, i.e. mostly diagonal): the prior is reasoned, not measured, and a wrong off-diagonal is more dangerous than a missing one.
4. **Preregister a sensitivity report** of the verdict across λ ∈ {1.0, 0.8, 0.5, 0.0}. If the REACHABLE/NOT-REACHABLE verdict flips inside that range, the verdict is **INCONCLUSIVE by construction** and must be reported so. Step 4 is what makes an unmeasured prior safe to ship.

**T-COV.5** *Grade D · (b), (a)* — **Do NOT estimate the covariance from our own bot runs.** Bot-generated correlations are a property of the architecture under test; using them to weight the distance lets the system grade its own homework. Any empirical covariance must come from human data.

## T-HOLE. Families with NO credible external target — where the floor is literature-free

| # | Family | External evidence | Consequence for the contract |
|---|---|---|---|
| **H1** | **Calldown / showdown-value thresholds** | **Nothing** (T-CALL.1) | Target **indirectly** via WTSD/W$SD, or declare unscored. A direct calldown target would be invented. (b) |
| **H2** | **Behavioural determinism / variance** | **Nothing** (T-DET.1) | Either drop from the score and keep as a **Goodhart side constraint** (bots must not be deterministic), or declare explicitly target-free. (a), (b) |
| **H3** | **Per-archetype bands, every stat** | **Nothing** (T-SPREAD.1) | The six-band fan is internally derived; label every band edge non-external, and the decision rule must not treat band edges as evidence. (a), (b) |
| **H4** | **Check-raise rates** | One format-blind, class-blind vendor line ("≤2%"), no street split, no denominator (T-CR.1) | DIRECTIONAL only; cannot bound a verdict. (b) |
| **H5** | **Bet-sizing distributions** | One 2005 thesis, direction only (T-SIZE.1) | Score sizing ecology on **shape/direction** (multi-modal? skews small at low stakes?), never against a numeric target. (b) |
| **H6** | **Fold-to-c-bet size elasticity** | Direction only, no magnitude (T-FCB.2) | Ordinal target only: fold rate must **increase** with bet size; slope untargetable. (b) |
| **H7** | **W$SD by format** | Level triangulates (~49–55); **no source splits by table size** (T-WSD.1) | Format transfer neither licensed nor prohibited — declare it an open assumption. (b) |
| **H8** | **C-bet level** | Four sources, ~40pp spread, three denominators (T-CBET.1) | Unusable until the denominator is declared; the class conflict, not table size, is the defect. (b) |

**T-HOLE.1** *Grade D (the mapping) · (b), (a)* — **Five of the remeasure's named defect families map onto these holes:** calldown looseness → H1; raise-merit → H4/H6; sizing ecology → H5; determinism → H2; preflop identity → T-VPIP/T-GAP. **Only the last has a usable external anchor.** The registry's coverage floor can be *met* (every family gets a row), but four of five rows will read "no external target exists; here is what we score instead." That is a legitimate registry entry — silently substituting an internal number is not.

---

## Self-verification

- **Both halves present.** Half 1: M1 calibration · M2 DoE/sensitivity/coverage · M3 detection statistics · M4 small-n validation · M5 Turing/believability. Half 2: T-SRC inventory · T-STAT per-family · T-COV covariance · T-HOLE literature-free floors.
- **Every conclusion** carries an ID, an evidence grade (A/B/C/D, or an explicit "no evidence"), and a landing tag in {(a), (b), (d), (e)}.
- **Tag coverage:** (a) M1.1–M1.6, M2.1–M2.10, T-SPREAD.1, T-DET.1, T-COV.5, T-HOLE.1 · (b) all of Half 2 · (d) M3.1–M3.10, M5.1–M5.7 · (e) M4.1–M4.9.
- **External-evidence-only rule held:** no Half-2 number comes from `persona-realism-theory-contract.md`; X1–X12 are all external and linked.
- **Stated limits of this memo:** Siler 2010 — the one peer-reviewed candidate — was **not read** (T-SRC.2); two covariance candidates were unreadable PDFs (T-COV.2); the "optimizer's curse" naming (M2.8), the d′ extreme-rate correction (M3.3) and the Ledoit–Wolf shrinkage form (T-COV.4) are standard practice but were **not verified against a primary source in this session**, and are graded accordingly.
- **Not self-approved.** Director reviews at fan-in.
