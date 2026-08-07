# Dossier 2 — Commercial practice: human-like agents and bot detection

Slice S2b of `../../roadmap/bot-realism-flywheel.md`, PRD requirement R5.
Session R, 2026-08-05. Evidence trail: `_raw/lane-b-commercial-evidence.md` +
`_raw/lane-d-codex-sweep.md`.

The roadmap names this dossier as the first scope cut if appetite runs out. The owner elected to
run it at full depth. **That was the right call for one reason: this is the only lane that speaks
to the north-star metric (blind bot-detection rate), because bot detection is a real commercial
discipline with a public record.** The realism half is thin — as expected — and this dossier says
so rather than inflating marketing copy into method.

---

## Bottom line

1. **No commercial product discloses a rigorous method for opponent realism.** The one with real
   technical detail — GTO Wizard's Player Profiles — is solver-tree bias injection, and the vendor
   explicitly disclaims that it represents real player psychology.
2. **Industry "human-like" means "fun and fair to play against," not "undetectable."** Every named
   system found pursued believability through *tactical competence*, or trained on human data and
   then bolted on a hand-tuned layer to suppress what it learned.
3. **Deliberate imperfection is standard practice, and players' *suspicion* of it is costly even
   when the suspicion is wrong.** EA's difficulty-adjustment patent states the design goal is to be
   "undetectable by a user," and a 2020 class action alleged it was in use — **but the plaintiffs
   voluntarily dismissed on 2021-02-11 after EA gave them technical information and engineer
   access, and EA states the technology was never in FIFA, Madden or NHL.** *(Corrected after blind
   review — the earlier draft cited only the filing and called this a documented system failure. It
   is not. What survives is a weaker but still real lesson about player suspicion, stated in §2.3.)*
4. **Poker bot detection is overwhelmingly decision-level, which is the good news for us** —
   timing consistency, bet-size consistency, statistical clustering across accounts. Device-level
   checks are stacked on top in real deployments but are not available to, or needed by, us.
5. **Almost no detection accuracy number in this space is independently audited.** Every figure
   found is self-reported. Treat the commercial record as evidence of *which signals work*, never
   as calibration for how well.
6. **No blind human-vs-bot labelling experiment for poker exists publicly.** The strongest verified
   precedent is Meta's Cicero — in Diplomacy, with a dialogue channel. **S6 has no protocol to
   copy; it is building one.**

---

## 1. Plain-language version (read this first)

**Two questions this dossier asks.** First: how do companies that ship simulated opponents
actually make them feel human? Second: how do real poker sites catch bots — because "can a judge
tell a bot from a human" is our north-star metric, and poker rooms have been doing exactly that
for money, for fifteen years.

**On making opponents feel human, the honest answer is: nobody publishes how.** Poker training
products sell "realistic opponents" but describe no method. The single exception is GTO Wizard,
which explains its opponent types clearly — and the explanation is that it takes a mathematically
perfect strategy and adds small artificial bonuses and penalties to particular actions, so the
engine behaves *as if* calling were slightly rewarded, producing a "calling station." Their own
blog says plainly that this is not a claim about real human psychology. That is essentially the
same family of technique as our dials — which is worth knowing: **our approach is not naive, it is
the state of the disclosed commercial art.** It is also, by the vendor's own admission, not
realism.

**Video games have a longer, better-documented history, and the lesson is a warning.** Forza's
"Drivatar" learned to drive from real player data — and learned to ram other cars, because real
players do. The studio had to add a manual layer to suppress what the human data taught it.
Separately, EA patented a system for secretly adjusting difficulty, describing the goal in the
patent as "undetectable by a user." Players believed it was in FIFA and sued. **The case was
dropped in February 2021 after the plaintiffs met EA's engineers, and EA says the technology was
never shipped in those games.** So this is not a story about a system that failed — it is a story
about *thousands of players becoming convinced they could detect one that (by the best available
account) was never there.* The recurring pattern across both examples: *faithful imitation of
humans produces behaviour studios have to correct, and in a domain where users study patterns
obsessively, the belief that they are being manipulated is costly on its own.*

**On detection, the news is more useful.** Poker rooms catch bots mainly by looking at *decisions*,
not at mouse movements: how consistent someone's timing is, how consistent their bet sizes are,
and — the oldest documented technique, from 2010 — finding *groups* of accounts playing too
similarly to be coincidence. That last one is directly relevant to us, because our seven personas
are generated from one engine and could plausibly cluster the same way a bot farm does. Sites also
lean on players reporting each other, which is a form of exactly the blind human judgment our
north star measures.

**What nobody has done publicly is our actual experiment**: show judges anonymised poker seats and
ask which are human. The closest real result is Meta's Cicero, which played 40 online Diplomacy
games against 82 people and was not detected — but Diplomacy involves *talking*, which poker does
not, so the protocol does not transfer.

**Jargon, defined once.** *Solver / GTO* = a computed mathematically-unexploitable strategy ·
*DDA (dynamic difficulty adjustment)* = software that secretly makes a game easier or harder based
on how you are doing · *rubber-banding* = the visible version of that ("the AI catches up") ·
*RTA (real-time assistance)* = a human consulting solver software mid-hand, which sites treat like
botting · *behavioural biometrics* = identifying people by *how* they physically interact — mouse,
keystrokes, timing · *false positive* = flagging an innocent player.

---

## 2. Making agents human-like — what industry actually does

### 2.1 Poker products

**GTO Wizard "Player Profiles" — the only disclosed method in the category.** Profiles work by
adding **virtual incentives** to actions: "at each decision, the engine treats these incentives as
if they carried a small bonus or penalty," e.g. "+5% pot incentive to calling" produces
calling-station behaviour. Eight defaults ship (GTO-savvy, fish, calling station, maniac, TAG reg,
LAG reg, nit, "Glass Cannon") plus a custom builder. The vendor's own caveat: *"we aren't claiming
this simple 'Fish Profile' perfectly represents every recreational player. Human psychology is way
more complex than a couple of tree-level incentives."* Grade **A**.
https://blog.gtowizard.com/profiles_explained_modeling_exploitable_opponents/ · as of 2026-08

> **Read this against our own architecture.** Bias injection over a strategy baseline, with a
> small set of named archetypes, is *the disclosed commercial state of the art* — and its own
> vendor scopes it as a study aid, not as realism. That is simultaneously reassuring (we are not
> doing something amateurish) and confirmatory of the ceiling question (nobody claims this family
> of technique produces believable people).

**Everything else discloses nothing.** Optima Poker Trainer ships archetype settings (Loose, Tight,
GTO, …) with no method disclosure (grade C). Advanced Poker Training markets an "opponent
simulation engine" and "machine learning" with no architecture, training data or validation
described (grade C). PokerSnowie is described by third parties as self-play neural networks and is
positioned as a study tool, not a realistic opponent — **and its own first-party "Weaknesses" page
returns HTTP 404** (grade A for the 404 itself; the disappearance of a vendor's own limitations
page is itself a finding about how thin durable documentation is here). GTOBase / InstaGTO /
GTO LAB train the user against solved strategy, not against a population model.

**Category pattern:** every product that discloses any mechanism frames opponent types as
**bias injection on a solved baseline**. **No product claims or documents passing a blind
human-vs-bot test. No product publishes a population-tendencies dataset or cites where its numbers
come from.**

### 2.2 Video games — three named systems, one repeated lesson

- **Forza "Drivatar."** Bayesian neural networks per player modelling behaviour across "12 turn
  types" from speed, steering angle and per-corner consistency; data discarded for any segment the
  player rewound. Turn 10's creative director on the tension: player-derived AI "will sometimes
  learn to take corners badly — just like you, they might even spin out," and early builds
  **learned to ram other cars**, forcing a hand-tuned override layer. Later versions moved toward
  population-level rather than individual mimicry. Grade **B**.
  https://www.gamedeveloper.com/design/how-forza-s-drivatar-actually-works
- **F.E.A.R. — Goal-Oriented Action Planning** (Orkin, GDC 2006). Believability came from *tactical
  adaptivity and coordination* — suppression fire, call-outs, replanning when the player slams a
  door — not from injected randomness or error. Grade **B**.
  https://www.gamedeveloper.com/design/building-the-ai-of-f-e-a-r-with-goal-oriented-action-planning
- **Left 4 Dead "AI Director"** (Booth, Valve, GDC 2009). Stated goals: "robust and believable
  behavior," acting as "competent proxies for human players." Believability defined at the level of
  *pacing and challenge*. Grade **B** (first-party PDF located but returned unparsed binary;
  wording is from corroborating summaries — recorded honestly rather than upgraded).

**Pattern:** none of the three aimed at "indistinguishable from a specific human." Two achieved
believability through competence and adaptivity; the one that trained on human data needed a
correction layer. **This is the same finding Dossier 1 reaches from the academic side, arrived at
independently** — imitation of humans produces behaviour that needs curation.

### 2.3 Deliberate imperfection, and the sharpest cautionary precedent

Practitioner framing distinguishes visible rubber-banding from invisible DDA: "for DDA to be most
successful, it should be invisible… if they feel that the game is 'cheating' or artificially
manipulating the difficulty, they will quickly lose trust and engagement" (grade B).

**EA's DDA patent and the 2020 class action — including how it ended.** EA holds a patent (filed
2016) for difficulty adjustment the patent text itself says is meant to be **"undetectable by a
user."** In November 2020 three plaintiffs filed a class action alleging EA used it in FIFA, Madden
and NHL to push microtransactions. A FIFA coach quoted in the coverage: "Having recorded and
studied hundreds of my own games… I've drawn too many comparisons to just pass this off as merely
nonsense." Grade **A** for the patent language; **B** for the community-skepticism framing.
https://slate.com/technology/2020/12/electronic-arts-fifa-madden-nhl-lawsuit-dynamic-difficulty-adjustment.html

⚠️ **How it ended (blind-review finding, accepted; Lead-verified).** The plaintiffs **voluntarily
dismissed** the case in the US District Court for the Northern District of California on
**2021-02-11**, after EA provided detailed technical information and access to its engineers. EA's
own statement says there is no DDA or scripting in Ultimate Team modes, that the patented
technology "never was in FIFA, Madden or NHL, and never will be," and that it will not use DDA to
advantage or disadvantage players in online multiplayer. Grade **A**.
https://www.ea.com/news/fair-play-and-dynamic-difficulty-adjustment ·
https://www.pcgamer.com/fifa-dynamic-difficulty-lawsuit-dropped-after-plaintiffs-talk-to-eas-engineers/

**What this precedent does and does not show.** The earlier draft of this dossier used the filing
alone and presented it as a documented case of manipulation being detected. **That reading was
stale and wrong, and the correction cuts against the dossier's own argument** — so state the
weaker version honestly:

- It is **not** evidence that an intentionally-imperfect agent was caught. By the best available
  account the system was never deployed.
- It **is** evidence that **a large, motivated player base can convince itself it detects
  manipulation that is not there**, sustain that belief against a first-party denial, and take it
  to federal court. The FIFA coach's "hundreds of recorded games" is pattern-matching that produced
  a confident false positive.
- **The transferable lesson for us is about our own north star, and it points at judges rather than
  at bots.** Our detection pilot asks humans to label seats as human or bot. This case is a
  documented instance of exactly that kind of human judgment being confidently wrong at scale —
  which is an argument for the S6 protocol's blinding and for reporting how often judges
  misclassify the *human* class, not just the bot class.

---

## 3. Bot detection — the north star's real-world analogue

Every method below is tagged for applicability. Only decision-level signals are available to us.

| Source | Method disclosed | Applicability | Grade |
|---|---|---|---|
| **Poker Table Rankings** (2010, Dave Martin, named) | "Human Robot Score" = composite of session length, standard deviation of lengths, times played, schedule consistency, scored 0–100. Separately, a **grouping algorithm over 400+ stats finding "groups of 10 or more players playing exactly the same."** Explicitly a triage signal, human-interpreted — not proof | **DECISION-LEVEL — applicable.** The oldest and most concretely documented method found | B |
| **PokerStars** | "Data scientists, programmers and former professional players"; "patterns and anomalies across billions of hands"; claims **95%** of caught bots come from its own team. Methods kept deliberately secret | Mixed — "hardware and software" is not decomposed; disclosure is ambiguous | B (self-reported) |
| **888poker** | "Continuously enhanced our AI and data capabilities… deducing playing patterns that indicate abnormal behaviour." 161 accounts blocked, **$362,893 refunded to 4,068 players in 2023** (+26% YoY). Credits **player community reports** as an important input | DECISION-LEVEL — applicable | B |
| **partypoker** | Publishes annual statistics consistently (291 accounts, $71,771 redistributed in 2024) — the most transparent operator found. Its own method post returned **403** on fetch | DECISION-LEVEL per secondary description | B |
| **GGPoker** | Official statement on an integrity breach discloses **zero technical detail** ("our monitoring system and hand analysis identify suspicious activity"). Separately, a "Poker Integrity Council" of internal security plus external pros reviewing hand histories reportedly banned 42 accounts, seized $1.2M, citing "human-mimicking" AI | Human expert review of hand histories = **DECISION-LEVEL — applicable, and notable: they use expert humans as judges** | A (statement, thin) / C (the PIC figures) |
| **GeoComply** | DLL/injection detection, process-disguise detection ("solvers renamed to calculator.exe"), VM/emulator detection, location-spoof piercing | **INPUT/DEVICE-LEVEL — not applicable here** | A (method) / C (its "0 false positives" claim) |
| **PokerBot.com** | "Collusion graphs, timing biometrics, hand-history statistical consistency, network/device fingerprinting"; claims reliable flagging within a few hundred to ~1,000 hands | Mixed — timing + hand-history stats applicable; fingerprinting not | C (snippet-level) |
| **SEON / BioCatch** | Mouse, keystroke, touch and sensor baselines | Largely INPUT-LEVEL — not applicable | C |

**Two things worth carrying into S6 and S5:**

- **"Groups playing too similarly to be chance" is a detection method that our own roster is
  exposed to.** Seven personas generated from one dial engine over one merit table is precisely the
  structure that grouping algorithms are built to catch. This is a *realism* risk the current
  architecture creates by construction, and it argues for a detection statistic that looks at
  **cross-persona similarity**, not only per-persona distance from human bands. It also sharpens
  the roadmap's Goodhart guard from the other direction: archetype separation is not just a
  coaching-value floor, it is an *anti-detection* requirement.
- **Operators use expert humans reviewing hand histories as judges** (GGPoker's Integrity Council;
  888poker's community reports). That is the S6 protocol, already running commercially. It is
  weak evidence that the protocol design is sound, and zero evidence about calibration.

**The evidence quality warning.** PokerStars' 95%, GeoComply's "0 false positives," BioCatch's
"40% reduction" — all self-reported, none independently audited, none with published methodology
or sample size. **Use this record to choose which signals to compute; never to set a target.**

---

## 4. Blind human-vs-bot experiments

**Meta AI's Cicero — the strongest verified precedent, and it is not poker.** Meta's own research
page states Cicero "played 40 games, against 82 anonymous human competitors," sending an average
of 130 messages per game, "achieved more than 2x the average score of its opponents," and ranked
"in the top 10% of participants who played more than one game." Grade **A** for those numbers.
https://ai.meta.com/research/cicero/diplomacy/
Secondary reporting adds that no in-game message indicated players suspected an AI. **The official
page does not itself state players were blind to the possibility of facing a bot** — that detail is
secondary-source only, grade **B**. A later (2024) study reportedly used a design where players
knew in advance a bot might be present; its primary source was not retrieved, so no numbers from it
are reported here.

**Why it does not transfer cleanly:** Diplomacy is a negotiation game whose primary channel is
*natural-language dialogue*. Cicero's undetectability is substantially a claim about text. Poker
has no dialogue channel — detection rests entirely on decisions, timing and sizing, which is a
much narrower and arguably harder surface to hide in.

**No public account of a blind human-vs-bot labelling experiment for online poker was found.**
Declared as a genuine gap. S6 is not reproducing an established protocol; it is designing one, and
should say so in its write-up.

---

## 5. What works vs what fails

**Works (documented practice):**
- **Bias injection over a solved baseline** for opponent "types" — cheap, fast, transparent, and
  explicitly scoped by its own vendor as a study aid rather than realism.
- **Population-scale statistical clustering for detection** — the longest continuously documented
  technique (2010→2026) and directly applicable to our north star.
- **Tactical adaptivity as the believability lever, not injected noise** (F.E.A.R., L4D).
- **A correction layer over learned behaviour** (Drivatar) — when human-derived behaviour reads as
  broken, studios hand-patch rather than trusting the learned signal end to end.
- **Human judges reviewing hand histories** as a detection input — commercially in use today.

**Fails (documented pitfalls):**
- **Human judges pattern-matching for manipulation can be confidently wrong at scale** — the EA
  case, where a motivated player base sued over a system that by the best available account was
  never shipped, and dropped the case after seeing the engineering. Read as a caution about
  *judges*, not about bots (§2.3).
- **Raw imitation of human data produces behaviour that reads as wrong, not human** — early
  Drivatar's ramming.
- **Vendor and operator accuracy claims are never independently audited.**
- **Marketing routinely blurs input-level and decision-level detection** — expect real-world claims
  to overstate what pure behavioural profiling alone achieves, because deployments stack device
  checks underneath.
- **First-party transparency does not persist** — a vendor's own "weaknesses" page is now a 404.

---

## 6. Open gaps (declared)

- No blind human-vs-bot labelling experiment for poker, anywhere public.
- No independently audited accuracy or false-positive rate for any commercial poker bot detector.
- partypoker's own method post unreachable (403); only trade-press paraphrase available.
- No primary regulatory document on bot-detection requirements retrieved — all regulator claims are
  snippet-level, grade C, and should not be cited as regulatory fact.
- No single named GDC talk framing "human tells" (timing, mistakes, tilt) as a deliberate NPC design
  checklist; the pattern was reconstructed across adjacent systems.
- Competitive-shooter bot-believability practice is thinner than the racing and horror examples.
