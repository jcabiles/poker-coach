# Dossier 1 — Academic prior art: human-likeness in poker and game AI

Slice S2b of `../../roadmap/bot-realism-flywheel.md`, PRD requirement R5.
Session R, 2026-08-05. Evidence trail: `_raw/lane-a-academic-evidence.md` (Claude lane) +
`_raw/lane-d-codex-sweep.md` (cross-family breadth sweep) + Lead verification (§6).

---

## Bottom line

1. **The Alberta lineage does not answer our question, and that is itself the finding.** Thirty
   years of University of Alberta Computer Poker Research Group work — the named prior art this
   project was faulted for missing — is about *beating* humans or *exploiting* a modelled
   opponent. Not one retrieved source optimizes for, or measures, whether a poker bot reads as a
   person. The gap is real, not an artefact of searching badly.
2. **A separate, rigorous literature does answer it — outside poker.** Chess, first-person
   shooters, racing games and navigation all have work that treats human-likeness as the
   objective, with reusable measurement recipes and shipped real-time systems. This is the
   literature the phase-3 architecture decision should be read against.
3. **Human-likeness must be targeted explicitly — optimising for competence does not produce it.
   But targeting it does *not* require learning from human data.** In the one study that compared
   them under a blind test, agents trained only to navigate well were detected; the agent that
   passed was one whose designers **hand-authored extra reward terms encoding human-like traits**.
   Learning from human demonstrations (chess, CS:GO) is the *other* way to target human-likeness,
   not the only way.
   *(Corrected after blind review — §6.5. The original reading was wrong in a way that mattered:
   it pointed away from hand-authored targeting when this evidence points toward it.)*
4. **The speed constraint is probably survivable but is NOT established.** No retrieved system
   benchmarks our workload — a laptop CPU at ~500 hands/sec. The closest published CPU figure lands
   *inside our per-decision budget with no margin* (§7.1). Per-decision LLMs and per-decision
   game-tree re-solving stay firmly excluded; everything else needs a microbenchmark, not an
   assumption.
5. **Some candidate architectures are corpus-gated and some are not** — the distinction decides how
   much Dossier 3's NO-GO actually costs. Demonstration-learning approaches need human hands we
   cannot legitimately obtain; self-play, authored-reward and persona-conditioned approaches do not.
   **But every approach still needs an external human *target* to aim at and be scored against, and
   after this slice that target is aggregate statistics rather than hands.**

---

## 1. Plain-language version (read this first)

**The question behind the dossier.** Our poker bots are built from hand-tuned numbers — a few
"dials" that scale entries in tables of how good each hand is in each situation. They score
4.8 out of 10 on "would a human believe this is a person." The owner needs to know whether more
tuning can ever get there, or whether the whole approach has to be replaced. Published research
is one input into that judgment.

**What we found, in ordinary terms.** Poker AI research is famous, and it is almost entirely
about *winning*. The Alberta group in Canada spent decades building bots that model their
opponent's weaknesses in order to exploit them, culminating in programs that beat professionals.
None of that work ever asked "does this bot *seem* human," because nobody needed it to. So the
prior art we were told we'd missed turns out not to contain the answer — it contains a warning
and a set of tools, which is different.

The research that *does* ask our question lives in other games. Chess has models trained to
predict the move a human of a given skill level would actually play — deliberately not the best
move. A shooter has a bot trained by copying millions of frames of real human play. And a
navigation agent was built to move the way people move, then tested by showing videos to
crowdsourced judges, who could not reliably tell it from a human — while ordinary competent AI
agents in the same test were spotted.

That last comparison is the most decision-relevant result in this dossier, and **how** the agent
was built matters as much as the result. It was **not** trained on recordings of human play. Its
designers wrote extra scoring rules by hand — penalise swinging the camera around wildly, penalise
bumping into walls, penalise standing still — encoding what "moving like a person" looks like, and
let the agent learn against those. Human recordings were used only to *judge* it afterwards.

So the honest lesson is: *playing well does not make an agent look human; you have to aim at
looking human on purpose — and you can aim either by copying real people or by hand-writing rules
that describe what people do.* **That second route is structurally what our dial architecture
already is** — except our dials encode strategic merit ("is this a good hand to raise") rather than
human-likeness ("do people ever do this"). That is a live and rather encouraging option for the
fix-versus-rebuild decision, and an earlier draft of this dossier got it backwards.

**The one poker exception, and why it cuts both ways.** A 2011 paper from Porto did exactly what
we would consider doing: it trained a No-Limit Hold'em agent by learning, from logs of real human
play, which action a human took in each situation. The authors report it was **not good enough to
be competitive**, because the learned strategy was *static* — it could not adapt. Read carefully,
that is a failure on the *strength* axis, which is not our axis. We do not need our bots to win;
we need them to look human, and "plays a fixed human-like style" is closer to a description of
our goal than of our failure. But the adaptivity warning is real: real humans do adjust, and a
frozen imitation will not.

**The catch that should govern the phase-3 decision.** Every approach that worked, worked by
learning from human data. Dossier 3 concludes we cannot legitimately obtain a corpus of human
no-limit hands. So "replace the dials with a learned model" is not a decision we can make purely
on architecture grounds — it is gated on data we do not currently have a clean route to.

**Jargon, defined once.** *Behaviour cloning* = training a model to copy recorded decisions, by
showing it the situation and the action a human took · *imitation learning* = the broader family
that includes behaviour cloning · *policy* = the function that maps a game situation to an action
· *opponent modelling* = building a statistical picture of how a specific opponent plays, usually
in order to exploit them · *Nash equilibrium / solver strategy* = a mathematically unexploitable
way to play, which is not how humans play · *CFR* = counterfactual regret minimisation, the
algorithm behind most strong poker bots · *discriminator* = a classifier trained to tell real from
fake, used here as a bot-detector.

---

## 2. The Alberta (CPRG) lineage — what it does and does not give us

Lineage confirmed: Loki (1997) → Poki (1999) → PsOpti/Sparbot (2002) → Vexbot (2003) →
Hyperborean (2006) → Polaris (2007–08) → Cepheus (2015) → DeepStack (2017).
Sources: https://poker.cs.ualberta.ca/ (A) · https://www.pokerlistings.com/blog/from-loki-to-libratus-a-look-at-20-years-of-poker-ai-development (B) · as of 2026-08

**What is directly usable:**

- **Opponent modelling from sparse observation.** Billings et al., *Opponent Modeling in Poker*
  (AAAI 1998) — models built from betting patterns and hand frequencies, with Loki-2 adding
  selective sampling biased toward weighted opponent ranges rather than uniform sampling. The
  sparse-data problem (you rarely see the opponent's cards) is solved here in a way that is
  reusable. **But the paper's own framing is to "identify and capitalize on predictable
  weaknesses"** — style capture as a means to exploitation. Grade **A**.
  https://poker.cs.ualberta.ca/publications/AAAI98.pdf
- **Variance-reduced evaluation — DIVAT / MIVAT / AIVAT.** Control-variate estimators that strip
  card-luck out of a measured result: DIVAT reports **75–85% variance reduction** versus Monte
  Carlo in heads-up limit hold'em and was later proven unbiased; AIVAT generalises it to also
  remove variance from known-strategy player actions. Grade **A**.
  https://poker.cs.ualberta.ca/publications/divat-icgaj.pdf · https://ar5iv.labs.arxiv.org/html/1612.06915
  **This is the most directly reusable machinery in the entire lineage** — but for measuring
  *strength* cleanly, not human-likeness. No retrieved source repurposes it for a humanness
  metric. Flagged as an opportunity, not a finding.
- **Bounded exploitation — Restricted Nash Response** (Johanson, Zinkevich, Bowling, NIPS 2007):
  solve a modified game where the opponent follows a learned model with probability *p* and
  deviates otherwise, trading exploitability against exploitation. Grade **A**.
  https://johanson.ca/publications/poker/2007-nips-rnash/2007-nips-rnash.html
  Its documented weakness matters to us: it is **fragile when the opponent model comes from
  sparse or naively frequentist data** (grade B). A sampling-based variant, MCRNR, exists
  (Codex lane, DOI 10.1.1.186.9298, grade **C** — metadata only).
- **The lineage's own abandonment of hand-tuning.** DeepStack (Science 2017) replaced hand-built
  heuristics with a learned value function plus real-time re-solving, and beat professionals over
  44,000 hands. Grade **A**. https://arxiv.org/abs/1701.01724
  **Explicitly disqualified as a candidate for us**: its per-decision cost is subgame re-solving,
  orders of magnitude outside a ~500 hands/sec budget. It is cited as precedent that the field
  itself moved off hand-tuning once progress stalled — on strength, not realism.
- **Cepheus** essentially solved heads-up limit hold'em (Science 2015; best counter-strategy wins
  0.000986 big blinds/game). Grade **B**. Pure strength result, zero human-likeness content.

**The documented ceiling claim, stated honestly.** The closest thing to "hand-authored
architectures plateau" in this lineage is CPRG's own account that Poki **"cannot adapt its
strategy fast enough to exploit its opponents or prevent its own exploitation"** (grade **B**,
secondary source). That is an *adaptivity* ceiling, not a *human-likeness* ceiling.
**No retrieved source states the negative result the owner most needs** — "we exhaustively tuned
a fixed dial architecture and it provably could not close a human-likeness gap." See §7.

**Data released:** the **IRC Poker Database** — real human data at trainable scale, but limit-era.
CPRG's own page says **"more than 10 million complete hands"**; the frequently-quoted 9,478,019
figure is a *third-party parser's extracted count*, not the primary page's number, and must be
attributed as such (blind-review finding, accepted). Grade **A** for the primary page's qualified
count, **B** for the parser figure. https://poker.cs.ualberta.ca/irc_poker_database.html
See Dossier 3.

**Codex lane additions (metadata-level, grade C — DOIs retrieved, papers not read):** two Alberta
opponent-modelling dissertations (10.7939/r3s756v00, 10.7939/r3-g4gx-az85), *Algorithms and
Assessment in Computer Poker* (10.7939/r3-w2xj-av70), *The challenge of poker*
(10.1016/S0004-3702(01)00130-8), and *Computer poker: A review* (10.1016/j.artint.2010.12.005).
Listed as follow-up reading, not as evidence for any conclusion here.

---

## 3. Human-likeness as an objective — the literature that does answer us

- **"Navigates Like Me" (Milani et al., CHI 2023) — the single most decision-relevant result, and
  the one most easily misread.** A navigation agent was compared against baseline agents and real
  humans in a crowdsourced blind evaluation. **The proposed agent passed the Turing test; the
  baselines did not.** Grade **A**. https://arxiv.org/abs/2303.02160
  **Method, verified from the full text (§6.5) because the abstract does not disclose it:** the
  agent is **reinforcement learning with hand-designed reward shaping**, *not* imitation learning.
  On top of a dense navigation reward, its authors added penalties for **swift camera-angle
  changes**, **wall collisions (−0.05)** and **distance travelled below a threshold (−0.01)** —
  hand-authored terms encoding human-like movement traits. Human gameplay data was used **only for
  evaluation**, never for training. Both baselines were themselves **deep-RL agents** (symbolic vs
  hybrid input), *not* hand-authored rule systems.
  *Why it matters, correctly stated:* it tests — and refutes — the assumption that a competent
  agent reads as human. It does **not** show that human-likeness requires learning from human data.
  It shows the opposite is achievable: **deliberate, hand-authored targeting of human-likeness
  passed a blind test.** That is the closest published analogue to "re-aim our dials at
  human-likeness instead of at strategic merit," and it is evidence for the *fix* side of the
  phase-3 gate, not against it.
- **Maia (chess human-move prediction).** Models trained on large human game corpora to predict
  the move a human *of a given rating band* would actually play, rather than the best move.
  Original: McIlroy-Young, Sen, Kleinberg, Anderson, *Aligning Superhuman AI with Human Behavior*,
  KDD 2020 — the abstract states Maia "predicts human moves at a much higher accuracy than
  existing engines." Grade **A** for that qualitative claim.
  https://arxiv.org/abs/2006.01855 · DOI 10.1145/3394486.3403219
  Maia-2 (Tang, Jiao, McIlroy-Young, Kleinberg, Sen, Anderson, 2024) unifies skill levels via a
  skill-aware attention mechanism. Grade **A** for identity/content. https://arxiv.org/abs/2409.20553
  ⚠️ **Correction applied (§6.1): the widely-quoted "5–15 percentage points better than Stockfish"
  figure could not be verified at either primary source and is carried at grade C, not A.**
  Follow-on, *Learning Models of Individual Behavior in Chess* (KDD 2022, DOI
  10.1145/3534678.3539367) extends this to **individual-player** rather than population modelling
  — the closest precedent for per-persona conditioning. Grade **C** (Codex, metadata only).
- **Behaviour cloning at real-time speed — Counter-Strike** (Pearce & Zhu, NeurIPS Offline RL
  Workshop 2021). A deep net trained by behaviour cloning on scraped human play — **5.5M frames /
  ~95 hours plus ~190k expert-demonstration frames per the current v2**; an earlier abstract
  version said ~4M, so cite the version. The paper requires the network to **"train and run in
  real-time."** Result: matches medium built-in-AI difficulty "whilst adopting a humanlike play
  style." Grade **A**. https://arxiv.org/abs/2104.04258
  ⚠️ **Speed caveat (§6.6):** it ran at ~16 FPS **on a gaming GPU**. This is evidence that behaviour
  cloning fits *a* real-time budget — not evidence about a laptop CPU at our throughput.
- **BotPrize (Unreal Tournament 2004).** Judges rate humanness 1–5 during 10-minute rounds. In
  2012 two bots (UT², using neuroevolution + behavioural adaptation; and MirrorBot) scored
  **above the human players** — ~52% versus an average human rating of ~40–41%. Grade **B**.
  https://en.wikipedia.org/wiki/Computer_game_bot_Turing_Test
  ⚠️ **Read the baseline before quoting this.** Real humans were rated non-human ~59–60% of the
  time. "Beating the Turing test" here means clearing a noisy, low bar — a caution that applies
  directly to how S6's detection pilot reports its own number.
- **Persona-conditioned policies.** *One Policy, Infinite NPCs* (Hong, arXiv 2605.23652,
  2026-05-22) conditions a single RL policy on persona embeddings, reporting **22× faster
  inference than an LLM-as-policy baseline** and sub-frame inference at 64 concurrent agents.
  Lead-verified as a real paper (§6.2) — but a **single-author, three-month-old preprint with no
  visible peer review, so carried at grade B, downgraded from the lane's A.** Do not let one
  preprint carry an architecture decision.
  MultiGAIL (Ahlberg, Sestini, Tollmar, Gisslén, CoG 2023, https://arxiv.org/abs/2308.07598) uses
  one discriminator per target playstyle as adversarial imitation reward models, steering one
  network across a spectrum of styles without hand-authoring a reward per style. Grade **A**.
- **Survey.** Świechowski & Ślęzak, *The Many Challenges of Human-Like Agents in Virtual Game
  Environments* (AAMAS 2025) — 13 challenges, plus an empirical bot-detector. It proposes that
  **the harder human-likeness is in a given game, the easier bot detection becomes in that game.**
  ⚠️ **The paper explicitly frames this as an OPEN HYPOTHESIS inviting validation or refutation,
  and its single tactical-game detector does not establish a cross-game relationship** (blind-review
  finding, accepted). Carry it into S6 as a **hypothesis to state and test, never as a prior backed
  by evidence.** Grade **A** for the paper; the relationship itself is **unestablished**.
  https://arxiv.org/abs/2505.20011
- **Believability-evaluation methodology (Codex lane, grade C — metadata only, directly relevant
  to S6's protocol design):** *A new design for a Turing Test for Bots* (10.1109/ITW.2010.5593336),
  *Studying believability assessment in racing games* (10.1145/3235765.3235797), *What makes
  virtual agents believable?* (10.1080/09540091.2015.1130021).

---

## 4. Poker-specific modelling of human styles

- **⭐ Teófilo & Reis, *Building a No Limit Texas Hold'em Poker Agent Based on Game Logs Using
  Supervised Learning* (AIS 2011, LNCS 6752, LIACC / University of Porto).** Builds an NLHE agent
  by treating past games between **human** players as a classification problem: game state → the
  action the human took. **This is behaviour cloning in our exact game.** The authors' own
  conclusion: the approach **alone is insufficient for a competitive agent, because the generated
  strategies are static and cannot adapt.** Grade **A** (retrieved via two independent routes,
  §6.4). https://link.springer.com/chapter/10.1007/978-3-642-21538-4_8 · open PDF:
  https://paginas.fe.up.pt/~niadr/PUBLICATIONS/LIACC_publications_2011_12/pdf/C55_Building_No_Limit_LFT_LPR.pdf
  **⚠️ This overturns the Claude lane's stated gap** ("no poker-specific behaviour-cloning
  precedent found") — it was surfaced only by the cross-family sweep. **Read the negative result
  on the right axis:** "static, cannot adapt" is a failure against *strength*, which is not our
  objective. A frozen, human-derived style is closer to a description of what we want than of what
  we fear. The transferable warning is narrower and real: **imitation gives you a fixed style, and
  humans visibly adjust** — so adaptivity must be designed in, not expected to emerge.
  **⚠️ Do not stop at the base result (blind-review finding, accepted).** The same paper continues
  past it: the authors **combined tactics drawn from different players** and report *greatly
  improved* performance against opponent-modelling adversaries. So static imitation is the paper's
  *starting point*, not its terminal architecture — **a mixture / strategy-selection layer over
  cloned styles is a hybrid option in its own right** and belongs in the architecture matrix (§7,
  candidate 7).
- **Teófilo & Reis, *Identifying Player's Strategies in No Limit Texas Hold'em Poker through the
  Analysis of Individual Moves* (arXiv 1301.5943, 2013).** Clusters real players by move-type
  frequency and finds **7 distinct style archetypes**. Grade **A**. https://arxiv.org/abs/1301.5943
  **The closest academic analogue to our own architecture** — a small number of discrete style
  buckets derived from move statistics. Two things it does *not* do: validate the clusters against
  human judges, or generate play. It is a classification result serving opponent modelling.
- **Codex additions, grade C (metadata only):** a Finnish thesis on neural prediction of a Hold'em
  player's next action (https://trepo.tuni.fi/handle/10024/78808), and *Opponent Modeling by
  Expectation–Maximization and Sequence Prediction in Simplified Poker*
  (10.1109/TCIAIG.2015.2491611).
- **Conspicuously absent:** no retrieved source clusters players **and** validates the clusters
  against human raters judging "does this look like a real person of style X."

---

## 5. How to measure human-likeness — reusable definitions

Directly transferable to the S3 realism score and the S6 detection protocol.

| Metric | What it is, plainly | Where it comes from | Grade |
|---|---|---|---|
| **Blind judge test** | Humans rate or label anonymised play; the standard is **statistical indistinguishability**, not a high score | BotPrize; "Navigates Like Me" | A/B |
| **Move-matching accuracy** | Fraction of decisions where the model's top-predicted action equals what the human actually did | Maia line; Ogawa/Hsueh/Ikeda ICAART 2023 | A/B |
| **Likelihood / perplexity** | The average probability the model assigns to the human's *actual* action — captures distribution match even when the top pick differs | Ogawa/Hsueh/Ikeda, ICAART 2023 (DOI 10.5220/0011804200003393) | B |
| **Discriminator accuracy** | Train a classifier to separate human from bot traces; **accuracy near chance = indistinguishable**. Usable both as a training signal and as an offline regression gate | MultiGAIL; Świechowski & Ślęzak | A |
| **Action-frequency distance** | Compare how often each action is taken across situations — the family our realism score already sits in | Implicit in Teófilo & Reis clustering | B (structural) |

⚠️ **Named gap:** no retrieved source applies a *specific formal distance metric* (KL divergence,
Wasserstein, Jensen-Shannon) to poker action-frequency distributions for a human-likeness
objective. S3 will be choosing its distance function without a poker precedent to cite.

**The structural finding that organises all of this:** *the poker literature measures strength;
the game-AI literature measures human-likeness; almost nothing does both, and nothing does both in
poker.* A pipeline that reports "our bots' win rates look right" says nothing about realism. The
two axes need separate instruments — which is exactly what the flywheel is building.

---

## 6. Lead verification record

| # | Claim as returned | Check | Outcome |
|---|---|---|---|
| 6.1 | "Maia predicts human moves 5–15 points better than Stockfish", cited to arXiv 2409.20553 | Fetched 2409.20553 **and** the original 2006.01855 | **Mis-cited and unverified.** 2409.20553 is Maia-2 and shows no such comparison; the original states the qualitative claim but no such figure on its abstract page. Qualitative claim kept at **A** on 2006.01855; the numeric figure demoted to **C** and must not be quoted as fact. |
| 6.2 | PCSP (arXiv 2605.23652) at grade A | Fetched the abstract page | **Real paper, claims accurate** — but single-author preprint dated 2026-05-22, no peer review evident. **Demoted A → B.** |
| 6.3 | "No poker-specific behaviour-cloning precedent exists" (Claude lane gap) | Codex sweep surfaced a candidate; Lead verified via DOI + independent title search | **Gap closed** — Teófilo & Reis 2011 is exactly that precedent. Grade **A**. *This is the cross-family sweep earning its cost.* |
| 6.4 | Pluribus hands characterised by Codex as "bot-play records" | Compared against the Claude lane's direct read of the supplementary file | **Codex imprecise** — 5 of 6 seats were human professionals per hand. Both lanes agree it is unusable as a modern human corpus (10,000 hands), so the conclusion is unaffected; the characterisation is corrected. |
| 6.5 | "Navigates Like Me" agent described as "purpose-trained toward human movement statistics", baseline as a "competent hand-built" agent | Blind review flagged both; Lead fetched the **full text** (the abstract does not disclose method) | **CONFIRMED WRONG, and it inverted a headline.** The agent is RL with **hand-designed reward shaping** (penalties for swift camera changes, wall collisions −0.05, distance-below-threshold −0.01); human data was used **for evaluation only**; both baselines were **deep-RL agents**, not rule systems. The surviving claim — competence-only training was detected, human-likeness-targeted training was not — is **strengthened**, but its direction changed: this is evidence that **hand-authored targeting works**. Bottom-line bullet 3, §1 and §3 rewritten. |
| 6.6 | "Small learned models comfortably meet ~500 hands/sec" | Blind review supplied the underlying numbers; Lead did the arithmetic (§7.1) | **Overclaimed.** No cited system benchmarks a laptop CPU at our throughput; the nearest CPU figure sits *inside our budget with no margin*. Downgraded to "plausible, unbenchmarked." |
| 6.7 | Architecture matrix omitted self-play poker policies | Blind review named Poker-CNN and AlphaHoldem | **Genuine gap, accepted.** Added as candidate 8 (§7). Their existence is what breaks the "all alternatives are corpus-gated" claim. |

**Blind cross-family review (GATE.md Tier 2)** returned NEEDS-WORK against a locked checklist;
rows 6.5–6.7 and the corrections marked "(blind-review finding, accepted)" throughout this dossier
are its adjudicated output. Findings were verified before folding, not auto-applied — full ledger
in `COMPLETION-NOTE.md` §7.

---

## 7. Candidate architectures, graded against the ~500 hands/sec constraint

**Revised after blind review.** The original version of this section made two claims that did not
survive: that speed is comfortably satisfied, and that *every* alternative needs human hand data.
Neither is true. The corrected discriminator is narrower: **which candidates need human
demonstrations, and which only need a human target to aim at.**

### 7.1 The speed budget, done as arithmetic rather than asserted

At **500 hands/sec**, six-handed, with roughly 8–15 villain decisions per hand, the engine must
serve about **4,000–7,500 villain decisions per second** — a budget of roughly **130–250 µs per
decision**, single-threaded, on a laptop CPU.

Against that: the CS:GO behaviour-cloning net ran at **~16 FPS on a gaming GPU**; PCSP reports
GPU batch-1 latency plus roughly **183–202 µs per CPU ONNX call** in a throttled engine test; and
AlphaHoldem reports **~2.9 ms per decision on a GPU** — an order of magnitude *outside* the budget.

**Conclusion: a small net is plausible but sits at the edge, not comfortably inside.** The PCSP
CPU figure lands *within* our band with essentially no headroom, and it is not our model, our
feature pipeline, or our hardware. **Any overhaul proposal must carry a representative CPU
microbenchmark — including decisions-per-hand — before throughput can be graded better than
"unresolved."** (Blind-review finding, accepted; the arithmetic above is mine.)

### 7.2 The matrix

| # | Architecture | Plainly | Data needed | Corpus-gated? | Speed | Grade |
|---|---|---|---|---|---|---|
| 1 | **Behaviour-cloned policy per style** (Maia / CS:GO / Teófilo-2011) | Train a small net to predict the action a human of style X would take | **Human hand histories tagged by style** | **Yes — blocked** | Plausible, unbenchmarked (§7.1) | **A** as a pattern; **A** for the poker precedent, whose own base result was "static, uncompetitive" *on strength* |
| 2 | **Persona-conditioned policy** (PCSP) | One network plus a style vector, instead of N rule sets | Human logs per persona **or** designer-authored persona descriptions + reward objectives | **No** — PCSP itself trains from authored personas | Plausible, unbenchmarked; the tightest published CPU figure | **B** (§6.2) |
| 3 | **Multi-discriminator adversarial imitation** (MultiGAIL) | Train one policy against several style-detectors instead of hand-writing a reward per style | Human demonstrations per style, **or** scripted expert trajectories as a bootstrap | **Partially** — degrades to authored experts | Training-time cost only | **A** in general game AI; no poker instance |
| 4 | **Empirically-derived archetypes** (Teófilo 2013) feeding 1–3 | Let clustering on real play *define* the personas rather than design intuition | A hand corpus with volume per bucket | **Yes — blocked** | Offline | **A** for the clustering precedent; not evidenced as sufficient alone |
| 5 | **Discriminator as a measurement layer** (not a policy) | A classifier that tries to tell our hands from human hands; chance accuracy = realistic | A labelled human sample + our own logs | **Weakly** — needs *some* humans, not a corpus | Offline; irrelevant | **A/B** — available now |
| 6 | **DeepStack-style per-decision re-solving** | Learned value function + game-tree re-solve every decision | Self-play | No | **Seconds per decision — DISQUALIFIED** | A (ruled out) |
| 7 | **Mixture / strategy-selection over cloned styles** (Teófilo 2011's own extension) | Combine tactics drawn from several players and select among them, instead of one frozen clone | Human logs, **or** authored style components | **Partially** | Same class as 1–2 | **B** — the paper reports "greatly improved" results but on *strength*, not realism |
| 8 | **Self-play learned policy** (Poker-CNN, arXiv 1509.06731; AlphaHoldem, AAAI 2022, DOI 10.1609/aaai.v36i4.20394) | Learn a poker policy from scratch by playing itself — no human data at all | **None** | **No — not corpus-gated at all** | AlphaHoldem: ~2.9 ms/decision on GPU — **~10–20× outside budget as published** | **B** — real and poker-specific, but optimises *strength*; **no evidence it produces human-likeness**, which is our actual objective |
| 9 | **Re-aim the existing dials at human-likeness** ("Navigates Like Me" pattern) | Keep the current architecture; change what the hand-authored terms *encode* — from strategic merit to human-behaviour traits | **None for training**; an external human target to aim at | **No** | Unchanged from today | **B** — the only candidate with a *blind-test success* behind its mechanism (§3), though in navigation, not poker |

### 7.3 The corrected coupling for phase 3

- **Corpus-gated (blocked by Dossier 3's NO-GO): candidates 1 and 4**, and partially 3 and 7.
- **Not corpus-gated: candidates 2, 8 and 9** — authored rewards, self-play, and re-aimed dials.
- **But candidate 8 optimises strength, and this dossier's central structural finding is that
  strength and human-likeness are disjoint objectives.** Self-play escapes the data blocker by
  aiming at the wrong target.
- **The residual, non-negotiable dependency:** every candidate — including 9 — needs an **external
  human target** to aim at and to be scored against. What this slice establishes is that the target
  can be **aggregate statistics** (Dossier 3, rung ii) rather than hands. That is a far cheaper
  dependency than a corpus, and it is obtainable.

**So the overhaul is not simply blocked by data.** It is narrowed: the demonstration-learning
branch is blocked, the self-play branch aims at the wrong objective, and the two live branches
(authored-reward learned policy, or re-aimed dials) are both **targeting** problems rather than
**data** problems. Candidate 9 in particular means the phase-3 gate is not a clean
"tune-versus-rebuild" binary — there is a third option that keeps the architecture and changes what
it optimises.

---

## 8. What works vs what fails

**Works:**
- **Target human-likeness explicitly, by whichever route is available** — either learn it from
  human decisions (Maia recipe, the most rigorously validated pattern retrieved) **or** hand-author
  reward terms that encode human-like traits ("Navigates Like Me", the only mechanism here with a
  blind-test pass behind it). Both work; only the first needs a corpus.
- Behaviour cloning fits *a* real-time budget in shipped/published systems (CS:GO, Drivatar) —
  though not one benchmarked against our CPU workload (§7.1).
- Condition **one** policy on a style vector rather than authoring N rule sets.
- Judge/discriminator evaluation, not internal statistics alone — internal metrics correlate with
  but do not guarantee indistinguishability.
- Variance-reduction estimators (DIVAT/AIVAT) for anything measured off noisy hand outcomes.

**Fails:**
- **Competence does not produce human-likeness.** Agents trained only to perform well were
  detected; the agent whose objective explicitly encoded human-like behaviour was not.
  *(Established for one navigation task, not for poker — do not overstate the reach.)*
- **Fixed architectures hit an adaptivity ceiling** — CPRG's own account of Poki.
- **Imitation alone yields a static style** (Teófilo 2011) — adaptivity must be designed in.
- **Opponent models built from sparse frequentist data are fragile** (RNR's documented weakness).
- **Low baselines masquerade as validation** — BotPrize's humans scored ~40%. Always report the
  baseline alongside any detection number. *(Directly applicable to S6.)*
- **A mature human-imitation system can still be pulled from production** — Forza dropped
  human-data-trained Drivatar in 2023 for fairness and quality reasons. "Trained on human data"
  is necessary, not sufficient.
- **Strength and style are measured by disjoint toolsets** — do not let one stand in for the other.

---

## 9. Open gaps (declared)

⚠️ **Scope of every negative below (blind-review finding, accepted):** these are **"not found in
this session's documented search, as of 2026-08"** — four lanes across web search, arXiv, DOI
resolution and vendor pages. They are **not** claims that no such work exists anywhere. Earlier
drafts phrased some of these as universal negatives ("no source anywhere"); that overstated what a
search can establish and has been corrected here and in the consumption map.

- **No poker study found that trains or evaluates against a human-rated believability metric.** The
  two literatures do not appear to intersect. This is the biggest single gap and it is why S6 has
  no protocol to copy wholesale.
- **No formal distributional-distance metric found applied to poker action frequencies for
  humanness.**
- **No direct statement found of the owner's exact negative result** — "a tuned dial architecture
  provably plateaus below a human-likeness threshold." Related evidence exists (Poki's adaptivity
  limit; BotPrize's weak baseline; the competence-≠-humanness result) but **the ceiling question
  cannot be answered from the literature. It has to be measured — which is what S5 is for.**
- **No style-labelled human hand-history dataset found newer than the 1995–2001 IRC corpus.**
- **No tabular-vs-neural comparison found for the human-likeness objective specifically.**
- **No CPU throughput benchmark found for any candidate at our workload** (§7.1) — the single
  most consequential unmeasured quantity for an overhaul proposal.
- Codex-surfaced sources at grade C were retrieved at metadata level only and are follow-up
  reading, not evidence. Poker-CNN and AlphaHoldem (candidate 8) entered via blind review and are
  graded B — abstract/metadata level, not read in full.
