# Dossier 3 — NLHE human hand-history corpus: gate brief

Slice S2b (the research wave of `../../roadmap/bot-realism-flywheel.md`), PRD requirement R5.
Session R, 2026-08-05. **Docs-only session — no data was downloaded.**
Evidence trail: `_raw/lane-c-corpus-evidence.md` (sealed lane) + Lead verification recorded in §7.

---

## VERDICT: **PARTIAL**

**In one sentence:** we cannot legitimately obtain a modern corpus of actual human No-Limit
Hold'em *hands*, but we can obtain modern human NLHE *statistics* — published aggregate
numbers — which is what the target registry actually consumes, so the flywheel is not blocked;
what it needs from the owner is a provenance ruling, not a dataset.

The single word "PARTIAL" hides a split that matters, so state it as two answers:

| Question | Verdict | Confidence |
|---|---|---|
| Can we acquire a **licensing-clean corpus of human NLHE hands** (full action sequences, modern, large)? | **NO-GO** | High — the search was thorough and the blocker is structural, not a gap in effort |
| Can we acquire **modern human NLHE target statistics** (the per-stat numbers the registry needs)? | **PARTIAL — yes, with caveats and one owner ruling** | Medium — the best source is free and current but publishes no sample size or methodology |

**This corrects the sealed lane.** Lane C returned a flat NO-GO and ranked the
"modern population statistics" fallback rung as the *weakest* of four, on the finding that no
vendor publishes pool-wide statistics. Lead verification found a live, free, current source
that does exactly that (§7.4). The lane's hand-corpus reasoning survives intact and is adopted;
its fallback ranking does not.

> ⚠️ **What kind of NO-GO this is (revised after blind review).** The hand-corpus NO-GO is a
> **project-policy and ethics decision, not a legal ruling.** Nobody here is qualified to give
> one, and the legal picture is genuinely not automatic: breach of a collector's contract with a
> poker room, unauthorised-access law, copyright, and privacy are four separate questions with
> different answers, and a downstream *user* of data sits differently from the original collector.
> US authority cuts in more than one direction — public-web scraping has been held to fall outside
> the main unauthorised-access statute ([hiQ v. LinkedIn](https://cdn.ca9.uscourts.gov/datastore/opinions/2022/04/18/17-16783.pdf)),
> and facts as such are not copyrightable ([Feist](https://www.law.cornell.edu/supremecourt/text/499/340)).
> **Neither case resolves this** — poker hand data is arguably non-public and the situations are
> distinguishable — which is exactly why the honest framing is: *we decline this data on policy and
> ethics grounds, and a real answer would need qualified legal review we are not going to buy for a
> hobby project.* The practical outcome is unchanged; the justification is now the one we can
> actually defend.

---

## 1. Plain-language version (read this first)

**What we wanted.** The bots' targets — "a tight-aggressive player raises first-in about this
often, continuation-bets about this often" — currently come from numbers quoted in poker books
and coaching sites. We wanted to replace those with numbers measured from real humans playing
real online no-limit hold'em.

**Two different things we could have gone and got:**

1. **Hands** — the raw record of millions of individual decisions, which you would need if you
   wanted to *train* a model to imitate humans.
2. **Statistics** — somebody else already counted those hands and published the summary
   percentages, which is all you need if you only want *targets to aim at*.

**What we found.** Getting (1) legitimately is effectively impossible. Every large collection
of real human no-limit hands that exists traces back to "datamining" — software that sits at
online poker tables recording other people's hands without playing. Every major poker site's
terms of service explicitly bans this, by name. Some academic projects have re-published this
data under a clean open licence, but re-licensing somebody else's data does not undo how it was
originally collected. The two collections with genuinely clean paperwork are either tiny
(10,000 hands from one exhibition match) or contain no actual poker decisions at all (a
regulator-style research agreement that yielded deposit and session totals, not hands).

Getting (2) turned out to be much easier than the lane concluded. A free public site publishes
current player-pool averages for GGPoker across five stake levels — and, importantly, splits
them into *player categories* (everyone / the top 100 winners / regulars / recreational
players). Those categories map almost directly onto our bot archetypes, and the statistics
published are the exact ones our scorer wants.

**The catch, and the decision we need from you.** That site does not say where its data comes
from — and GGPoker's own rules ban the datamining that would be the obvious way to get it. So
we would be *reading published summary numbers whose upstream collection was probably against a
poker site's terms*. That is a meaningfully lighter act than downloading millions of scraped
hands ourselves: we would be citing a public webpage, not holding contraband data. But it is
still a judgment call that belongs to you, not to this research session. See §8.

**Jargon used below, defined once:** *hand history* = the full recorded action of one poker
hand · *datamining* = recording hands at tables you are not playing at · *ToS* = terms of
service, the contract a site's users agree to · *aggregate* = a summary number (an average or
percentage) computed over many hands, with the individual hands discarded · *VPIP / PFR /
WTSD / WWSF* = standard poker population statistics (how often a player voluntarily puts money
in preflop, raises first, reaches showdown, wins when they see the flop).

---

## 2. Why a clean hand corpus does not exist (the NO-GO half)

The lane checked the candidate list end to end. The blocker is the same at every branch.

**The one large, modern, full-action human NLHE dataset that exists in the open** is the human
core of the `uoftcprg/phh-dataset` project (University of Toronto Computer Poker Research
Group): **21,605,687 no-limit hold'em cash-game hands**, scraped 1–23 July 2009, stakes 25NL to
1000NL, across Absolute Poker, Full Tilt, iPoker, Ongame, PokerStars and PartyPoker. It is
archived on Zenodo under **CC BY 4.0** and the parser code is MIT-licensed — both look
completely clean in isolation.
*Verified independently by the Lead (§7.3): grade **A**.*
Source: https://github.com/uoftcprg/phh-dataset · https://zenodo.org/records/17136841 · as of 2026-08

**Its upstream is the problem.** That data came from **HandHQ**, a commercial datamining
vendor (now defunct). PokerStars' prohibited-activities terms ban, verbatim, "the practice of
datamining hands or private results," "the use of hands or private results acquired through
datamining," and "the mass sharing of hands, private results or playing statistics for the
purpose of analysis of opponents." GGPoker's help centre similarly bans Mass Data Analysis
tools and external result-sharing. **A downstream open licence does not cure an upstream terms
violation** — this is the trap, because the Zenodo licence page looks spotless on its own.
*Grade **B*** (the ToS text was retrieved via search-engine quotation; direct fetch returned 403).

**Everything else fails for a stated reason, not for lack of looking:**

| Candidate | Why it does not solve the problem | Grade |
|---|---|---|
| IRC Poker Database (U. Alberta) | Real human hands, but **1995–2001 and fixed-limit** — wrong era *and* wrong betting structure. No formal licence, only a bare copyright notice. | A (page), B (~9.48M hand count) |
| ACPC competition logs (620M+ hands) | Largest raw pool found and cleanly CC BY 4.0 — but **100% bot-versus-bot**. Cannot answer "how do humans play." | A |
| Pluribus vs. human pros (Science 2019) | Genuinely clean provenance, but **10,000 hands, 13 players, one artificial 6-max exhibition**. Reuse/redistribution terms **unresolved** (AAAS supplementary-materials rights not retrievable). | B |
| DeepStack human-study hands (~44–45k) | Secondary sources claim a public release; **no download location found** despite targeted search. Treat as unverified. | D |
| Kaggle / GitHub "poker hand dataset" listings | The widely-mirrored UCI set is **synthetic card combinatorics with no betting action at all** (verified). Others unverifiable. | A (UCI), D (others) |
| Active resellers (HHDealer, HHmailer, pokerenergy.net) | Currently trading, but all scrape in violation of site ToS; one advertises that ~60% of an entire network's hands are mined. **Paying does not cure it.** | B |
| PLOS ONE 2015 study (76.9M hands, 600k+ players, 2009–10) | Excellent peer-reviewed work — but the underlying data was **purchased from HHDealer**, same chain. Its *published numbers* are usable; its raw data is not ours to take. | A (paper), C (data licence) |
| Entain plc research agreement (PMC9325659) | **The one genuinely clean access pathway** — a formal data-sharing agreement with a licensed operator. But what it delivered was **daily financial/session aggregates, not hands or play-style stats**. Proves the route exists; does not prove it yields what we need. | A |
| UK Gambling Commission | Confirmed in the regulator's own FOI response: **"no information is currently held"** at individual level. | A |
| Absolute Poker leak / DOJ Black Friday | The leak is a security-breach artifact containing real IP addresses — **do not pursue**. No DOJ hand-level release found. | B |

**Privacy note (independent of licensing):** every human corpus here is keyed by screen name.
Screen names are pseudonymous but stable and tied to a real financial account, and these
datasets pair them with stake level and win/loss — which is more re-identifying than a bare
username. None of the sources documents a consent process meeting a modern research-ethics
standard; "anonymised" in this literature means identifiers were stripped *after* collection.

---

## 3. Paid options — priced, not recommended

Per the owner's ruling (assess, do not commit):

1. **Datamining resellers.** Active. Historical HandHQ pricing (stale, grade C): ~$0.99 per
   10,000 hands, ~$10 per 200,000, ~$32 per 1,000,000 — illustrative of the market's price
   point only. Current pricing unretrievable (403/523 errors). **Legal status unchanged by
   payment: still the prohibited bucket.**
2. **Operator data-sharing agreement.** No price list — a bespoke research partnership,
   realistically needing an academic affiliation and an ethics review. The one working
   precedent delivered financial aggregates, not play data.
3. **AAAS/Science supplementary reuse (Pluribus).** Free to read; a permissions question, not a
   price. Worth resolving regardless, cheaply, by asking AAAS.
4. **No vendor was found selling a licensed, ToS-clean aggregate-statistics product** — i.e.
   nothing of the form "buy our pool statistics with permission to republish."

---

## 4. Era-stability: what would even transfer

This matters because the fallback ladder's first rung proposes using 25-year-old limit-era data.

- **Direction of drift is agreed but never quantified.** Multiple secondary sources describe the
  2003–2006 boom pool as full of players who "barely knew the rules," and the late-2010s pool as
  solver-educated. **No source gives a trend line** ("pool VPIP fell from X% to Y%"). That is a
  real evidence gap, grade B/C.
- **One retrieved counter-example that some behaviour is era-stable:** the Entain study
  (2015–17) explicitly reports its involvement measures "were similar to those reported in
  LaPlante et al.'s 2009 study... despite numerous changes to the online poker environment."
  Grade **A**. That is about session/involvement patterns, not play style — but it establishes
  that "everything drifts" is not a safe assumption either.
- **Limit-to-no-limit transfer: no study found.** Reasoned position (flagged as *analysis, not
  evidence*): quantities driven by **positional information asymmetry** — e.g. the *ordering* of
  which seats enter pots most often — plausibly transfer as **shape/ordering only**. Quantities
  that depend on **bet-sizing freedom** — 3-bet sizing, c-bet sizing, stack-to-pot-ratio lines —
  are structurally meaningless in fixed-limit and **categorically cannot transfer**.

---

## 5. The fallback ladder, re-ranked

The roadmap pre-agreed four rungs. The lane ranked them (iii) > (iv) > (ii) > (i). **Lead
verification moves rung (ii) to the top.** Re-ranked, best first:

### Rung (ii) — modern published population aggregates · **NOW THE STRONGEST RUNG**

**What exists (Lead-verified, §7.4):** `bluffaces.com/calculators/mda/` (301-redirected from
`getcoach.poker`) publishes free aggregate statistics for the **GGPoker** player pool at
**NL25, NL50, NL100, NL200, NL500**, computed over "all the hands played in the last 12 months,"
broken out into four player categories: **all players · top-100 most-winning · regulars
(defined by VPIP and profitability thresholds) · recreationals (loose, losing)**. Statistics
exposed: win rate, VPIP, PFR, 3-bet, fold-to-3-bet, 4-bet, aggression frequency by street
(flop/turn/river), WTSD, W$SD, WWSF, c-bet, fold-to-c-bet.
Grade **B** — first-party page retrieved directly, but see the four caveats.
Source: https://bluffaces.com/calculators/mda/ · as of 2026-08

**Why this is the top rung:** it is the only rung giving **modern, segmented** numbers over the
project's own stat battery. No other rung comes close on either count.

⚠️ **But the segments are population strata, not play-style archetypes** (blind-review finding,
accepted — an earlier draft said they "map onto persona archetypes directly," which is wrong).
"All players" and "top-100 winners" are not styles at all; "regulars" and "recreationals" are
defined by **profitability and VPIP thresholds**, which does not identify TAG, LAG, nit, calling
station or maniac. The relationship is real but indirect: the recreational-versus-regular split
bounds the loose-passive-to-tight-aggressive axis. **That mapping is something S2a must construct
and justify, not read off** — any persona target derived this way is a modelled inference carrying
its own confidence grade.

**Four caveats that must travel with any number taken from it:**
1. **No sample size published.** "All hands in the last 12 months" is not a number. Any target
   derived from it carries unquantified uncertainty — which the S2a target registry must record
   as a low confidence grade, not launder into a point estimate.
2. **Single site, single pool.** GGPoker only. Population effects are site-specific.
3. **Rolling 12-month window ⇒ not reproducible.** The numbers move under you. **A retrieval date
   alone is not enough** (blind-review finding, accepted): the page is live and changing, so a date
   without the values cannot reproduce the evidence later. S2a must **record every consumed value
   and the exact filter combination it came from** (stake, segment, statistic) in the registry
   itself, or archive a dated snapshot. This is a direct hit on the PRD's reproducibility
   constraint and the mitigation is cheap — do it at first use, not later.
4. **No methodology or provenance statement anywhere on the site.** See §8 — this is the owner
   ruling.

**Checked and rejected as rung-(ii) sources:** `statname.net` — **per-player lookup only, not
pool aggregates**, and equally opaque about provenance (Lead-verified, grade B).
**Surfaced but not assessed:** MassBuster Pro and Hand2Note's pool-analysis feature both appear
to compute pool statistics *from a database the user supplies* — which puts the datamining
problem back on us, so they are not a route to published aggregates.

### Rung (iv) — literature bands as the floor · **weaker than assumed, but not worse than today**

Verified directly: the coaching-site numbers the project currently relies on are
**explicitly uncited**. SplitSuit's 3-bet-by-player-type figures are the author's own framework,
not tracking data (grade **A** — the page says so). This does not make the current registry
*worse* than believed; it confirms the original premise that the bands are soft. Keep as floor
and sanity-check only, never as a target of record.

### Rung (iii) — structured expert elicitation · **the credible way to fill genuine holes**

The **Sheffield Elicitation Framework (SHELF)** and the **Delphi method** are established
decision-science protocols for producing quantified probability distributions from expert
panels exactly when hard data is sparse — including the "roulette method" for building an
uncertainty histogram rather than a point estimate (grade **B**). Known weakness inherent to
all elicitation: anchoring and overconfidence, which the protocols mitigate but do not
eliminate. **Recommended use: only for stats where rung (ii) is silent** — running a panel to
re-derive numbers a public aggregate already publishes is wasted effort and adds bias.
Source: https://shelf.sites.sheffield.ac.uk · comparison paper https://arxiv.org/abs/2001.11365 · as of 2026-08

### Rung (i) — limit-era IRC data for era-stable shape parameters · **narrowest use only**

Admissible **only** for ordinal/shape claims with an explicit, mechanism-based justification per
parameter (e.g. "positional information advantage is structural, not era- or format-specific").
Never for magnitudes. Per §4, any bet-sizing-dependent statistic is disqualified outright.
The justification work has **not** been done — it is a task for whoever builds on this rung,
and the registry should refuse an unjustified parameter rather than accept it silently.

### The recommended combination

Build the S2a target registry on **rung (ii) snapshots as the primary modern source**, with
**peer-reviewed 2009–10 magnitudes** (the PLOS ONE study's *published numbers* — reading a
published paper's results is unencumbered, unlike its underlying data) as an independent
magnitude sanity check, **rung (iii) elicitation only for stats neither covers**, **rung (iv) as
the floor**, and **rung (i) for ordering claims only, each individually justified**. Every
target carries a confidence grade and a retrieval date. That is a materially stronger registry
than literature bands alone — which is the actual bar S2b had to clear.

---

## 6. What would change the verdict

To **GO** on hands:
1. A written data-use agreement with a licensed operator (or a tracker vendor with direct
   database access), **scoped in writing to hand-level or play-style data** — not just financial
   aggregates — with explicit rights to publish derived statistics. The Entain precedent shows
   the pathway is real; nobody has shown it yields play data.
2. Confirmation from AAAS of actual reuse terms for the Pluribus supplementary file. Cheap to
   ask; resolves an open licence question either way. (Still too narrow to be a target source on
   its own — 10,000 hands, 13 players.)
3. A public release location for the DeepStack human-study hands, if one genuinely exists.

To move rung (ii) from grade B to grade A: any published methodology or sample size from the
aggregate publisher, or a second independent pool-statistics publisher to cross-check against.

To **NO-GO** on statistics too: an owner ruling in §8 that rules out consuming aggregates of
unstated provenance. In that case the registry falls back to rungs (iii)+(iv), which is weaker
but still executable — **the flywheel is not blocked under any branch.**

---

## 7. Lead verification record (what I checked myself, and what changed)

Per the research protocol, where a conclusion is load-bearing the Lead checks the primary source
personally rather than deferring to lane rank.

| # | Claim as returned | What I did | Outcome |
|---|---|---|---|
| 7.1 | `phh-dataset` is "University of Toronto CPRG" | Suspected a mix-up with Alberta's CPRG; searched the repo | **Lane was right, my suspicion wrong** — the GitHub org is literally `uoftcprg`. Recorded so the correction is not re-litigated. |
| 7.2 | Human core = 21.6M NLHE hands, July 2009, HandHQ, 25NL–1000NL | Independent search retrieval | **Confirmed** to the exact figure (21,605,687) and date range. Upgraded to grade **A**. |
| 7.3 | Verdict NO-GO on a clean hand corpus | Reviewed the chain of reasoning against the retrieved ToS text | **Adopted unchanged.** The blocker is structural. |
| 7.4 | "No current population-wide play-style statistics from any named vendor"; rung (ii) is the weakest | Ran an independent search on pool/population statistics; found and fetched `bluffaces.com/calculators/mda/` (via a 301 from `getcoach.poker`) | **OVERTURNED.** A free, current, archetype-segmented GGPoker pool-statistics report exists with the project's stat battery. Rung (ii) promoted to strongest; headline verdict moved NO-GO → PARTIAL. |
| 7.5 | (new) Is `statname.net` a second such source? | Fetched directly | **No** — per-player lookup only, opaque provenance. Excluded. |

The lane checked GTO Wizard, PokerTracker, Hold'em Manager and Hand2Note and correctly found
none of them publish pool statistics; the source it missed is not a tracker vendor but a free
poker-education site, which is why the vendor-shaped search did not surface it.

---

## 8. ✅ Owner ruling — provenance of published aggregates (RESOLVED 2026-08-06)

> **RULING: Option (A) — use it, and disclose the limitation openly.** Owner, 2026-08-06.
>
> **What this authorises:** the S2a target registry may consume the published GGPoker pool
> aggregates (§5 rung ii). **Conditions that travel with the ruling, non-optional:**
> 1. Every consumed value is recorded in the registry **with its exact filter combination**
>    (stake · segment · statistic) and retrieval date — the source is a rolling window, so a date
>    alone cannot reproduce it (§5 caveat 3).
> 2. Every derived target carries a **low confidence grade**.
> 3. The strata→persona mapping is **constructed and justified**, never read off (§5 caveat, E1b).
> 4. The provenance limitation is stated **in the registry and in any public methodology
>    write-up** — "disclose" is the operative half of the ruling, not a footnote.
>
> The argument for the ruling is preserved below unchanged, as the record of why.

### The decision as it was put (retained for the record)

**Issue.** The strongest fallback rung (modern GGPoker pool statistics) comes from a publisher
that states nothing about where its data originates, and GGPoker's own terms prohibit the Mass
Data Analysis that is the obvious way to obtain it.

**Impact.** Determines whether the S2a target registry is built on modern archetype-segmented
numbers (rung ii) or on expert elicitation plus soft literature bands (rungs iii+iv). Affects
target quality, and — because the portfolio repo is intended to go public — the defensibility
of the methodology write-up.

**The distinction that makes this a real question rather than an obvious no:** we would be
reading **published summary percentages on a public educational webpage** and citing them. We
would not be downloading, holding, or redistributing anyone's hands. The terms that were
plausibly broken bind a dataminer to a poker room; they do not bind a reader of a public page.
Against that: if the public methodology write-up cites a source whose provenance we know to be
unstated, a skeptical reviewer can raise it — and that write-up is a hiring-manager-facing
artifact.

**Options.**
- **(A) Use it, disclose it.** Snapshot the numbers with retrieval dates, grade them
  low-confidence, and state the provenance limitation explicitly in the registry and in any
  public write-up. *Gain:* modern archetype-conditioned targets — by far the best available.
  *Cost:* a disclosed, permanent caveat in a portfolio artifact.
- **(B) Use it privately, exclude it from anything public.** Targets internally; public write-ups
  cite only rungs (iii)/(iv). *Gain:* keeps target quality. *Cost:* the public methodology no
  longer matches the actual method, which is its own credibility problem.
- **(C) Exclude it entirely.** Registry built on elicitation + literature bands.
  *Gain:* unimpeachable provenance. *Cost:* materially weaker targets, and S2b's practical
  contribution to the registry shrinks to "we confirmed the bands are soft."

**Recommendation: (A).** The act is reading a public page, the caveat is disclosable in one
sentence, and a methodology document that names its own weakest link reads as *more* rigorous to
a technical reviewer, not less. (C) trades real measurement quality for a purity that the
project's own literature bands do not have either — §5 rung (iv) verified that today's targets
are uncited author opinion, which is a *worse* provenance story than a disclosed aggregate.

**Decision needed from the owner:** A, B, or C — before S2a fixes the target registry.

---

## 9. What works vs what fails (method lessons, reusable)

**Works:**
- **Check licence at two levels — the redistributor's *and* the original collection's.** This is
  exactly how the CC-BY-over-a-ToS-violation trap was caught; checking only the Zenodo page
  would have passed it clean.
- **Official paper supplementary materials are the cleanest provenance trail** for human-vs-AI
  hand data — check the paper's own link before trusting any mirror.
- **Formal operator data-sharing agreements are a real, demonstrated route** — but scope the
  agreement explicitly to play-style data, since the working precedent delivered only financials.
- **Search by what publishes the thing, not by who you expect to publish it.** The rung-(ii)
  source was missed by a vendor-shaped search and found by a statistic-shaped one.

**Fails:**
- **Generic "poker hand dataset" names are unreliable** — several are relabelled copies of a
  synthetic card-classification set with zero betting action.
- **A downstream open licence does not cure an upstream terms violation** — and the mirror's
  licence page looks perfectly clean in isolation.
- **Coaching-site "typical stat" pages read as authoritative and frequently cite nothing.**
  Verified on a named example.
- **Site terms of service are not a fringe technicality here** — every major room checked has an
  explicit, current, enforced prohibition on precisely the activity every large commercial human
  corpus depends on.

---

## 10. Open gaps (declared, not papered over)

- No public download location found for the DeepStack human-study hands (~44–45k), despite
  targeted search.
- No quantified era-drift trend line for NLHE population statistics anywhere.
- No study comparing which specific NLHE statistics transfer between fixed-limit and no-limit.
- No sample size or methodology from the rung-(ii) publisher.
- Current pricing from active resellers unretrievable (403/523) — immaterial, since that bucket
  is excluded on terms grounds regardless.
- Kaggle listings other than the confirmed-synthetic UCI set remain unverified.
