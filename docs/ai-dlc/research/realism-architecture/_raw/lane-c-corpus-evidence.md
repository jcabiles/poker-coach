# Lane C — Human NLHE Hand-History Corpus: Gate Brief

**VERDICT: NO-GO** on acquiring a modern, licensing-clean, full-action-sequence human NLHE hand-history corpus as a direct replacement for the literature-band target statistics — at least not this session, and probably not without a purchased/negotiated data-use agreement no one has priced-and-committed to yet. Every human-play corpus of real size that this research located traces its origin to hand-history **datamining performed in violation of the originating poker rooms' terms of service** (a practice this brief was instructed to treat as out of bounds). The two exceptions that are unambiguously clean — the Pluribus vs. human-professionals dataset and an operator-agreement dataset from Entain plc — are either too small/narrow (10,000 hands, one bespoke 6-max AI-exhibition match) or contain no play-style action data at all (daily financial/session aggregates only, no hands). See Part 6 for full reasoning and what would flip this.

---

## Part 1 — Candidate corpora

### 1. IRC Poker Database (background / given)
University of Alberta Computer Poker Research Group (CPRG). Real human play, IRC-based online poker games, **1995–2001**, **limit** hold'em (per the CPRG's own page; the "no-limit" gap is exactly why this lane exists). A third-party parser repo describes the extracted total as **9,478,019 hands** (grade B — not stated on the primary CPRG page itself). Hosted at `http://poker.cs.ualberta.ca/IRC/IRCdata.tgz`.
- Format: limit hold'em only (also some 7-card stud/Omaha subsets per community lore, not verified this session).
- Era/years: 1995–2001.
- Human or bot: human.
- Full action sequences: yes, text-based hand logs.

### 2. Annual Computer Poker Competition (ACPC) logs
Run 2006–2017 by the University of Alberta CPRG and partners; agents (AI programs) play **each other**, not humans. Logs are consolidated in the "phh-dataset" project (see #3): **341,172,750** fixed-limit heads-up/3-player hands and **278,842,225** no-limit heads-up hands (hand counts include duplicates from repeated deals). This is the largest raw hand-count pool found in this research, and it is **100% bot-vs-bot** — it cannot answer "how do humans play." Useful only as an engine/format testbed, not a human-realism source.
- Format: both fixed-limit and no-limit heads-up/3-player.
- Era: 2006–2017 (agent strength, not human population, evolves across these years).
- Human or bot: **bot vs bot**.
- Full action sequences: yes (PHH format).

### 3. "A Dataset of Poker Hand Histories" (University of Toronto CPRG, `uoftcprg/phh-dataset`)
The modern aggregator/umbrella project. Combines, in one standardized "Poker Hand History" (PHH) format:
- The ACPC bot logs above (bot-vs-bot).
- **21,605,687 no-limit hold'em hands, human play**, "anonymized hand history logs scraped from July 1st to July 23, 2009," sourced from a commercial dataminer, **HandHQ** — split across Absolute Poker (1,270,658), Full Tilt Poker (1,299,503), iPoker Network (5,996,345), Ongame Network (1,647,765), PokerStars (3,092,698), PartyPoker (8,298,718 hands); stakes 25NL–1000NL, cash games.
- 83 televised hands from the 2023 WSOP Event #43 final table (human, tournament, full sequence, but n is trivially small).
- 10,000 Pluribus hands (see #4).
- A handful of curated historical/novelty hand selections.
- Repo: `https://github.com/uoftcprg/phh-dataset` (code, MIT license). Dataset itself archived on Zenodo, e.g. `https://zenodo.org/records/13997158` and a newer copy `https://zenodo.org/records/17136841` (data, **CC BY 4.0**). Both retrieved and read directly this session.
- **This is the only realistically "large, modern-ish, full-action human NLHE" candidate found — and its human core (item 4 below) has a legally murky root, discussed in Part 2.**

### 4. The HandHQ-sourced 2009 scrape (embedded in #3)
Treated separately because its legal status differs from the rest of the aggregator. **What it is:** a commercial datamining vendor's product, resold and later donated/mirrored into an academic aggregator. **HandHQ's own stated legal position** (reported via a PokerStrategy.com forum thread, grade C) is that it "never agreed to the Terms and Conditions of the poker rooms and therefore has no legal problem mining and selling hand histories" — i.e., a self-serving legal theory, not a court-tested one, and irrelevant to whether the *poker rooms* consented (they did not — see Part 2). HandHQ.com itself is now defunct (domain parked for sale, confirmed this session).

### 5. Pluribus vs. human professionals (Brown & Sandholm, *Science* 2019)
**Official, primary-source release.** 10,000 hands, 6-player no-limit hold'em, Pluribus playing 67 games against 13 distinct human opponents described as professionals (~149 hands/game on average). Published as Data File S1 in the paper's official supplementary materials: `https://noambrown.com/papers/19-Science-Superhuman_Supp.pdf` (redirect from `noambrown.github.io`, confirmed live this session) and the AAAS mirror `science.sciencemag.org/cgi/content/full/science.aay2400/DC1` (cited via secondary sources, not independently re-fetched — grade B for that specific URL). Full action sequences, in a compact custom notation (e.g. `STATE:42:r200fcffc/cr650cf/cr3000f:8c6h|7hJs|...:...`). Community parsers exist (`VitamintK/pluribus-hand-parser`, `dbur/pluribus-parser`) and it's also mirrored inside `phh-dataset`.
- Format: no-limit hold'em, 6-max.
- Era: 2019.
- Human or bot: mixed — 5 of 6 seats human, 1 seat AI, every hand.
- **License: UNRESOLVED.** This is a *Science*/AAAS journal supplementary file; I could not retrieve AAAS's supplementary-materials terms-of-reuse page this session (403 on the editorial-policies URL). Do not assume CC-BY or public-domain status without checking AAAS's licence terms directly before any reuse.
- Size caveat: 10,000 hands from 13 players in one artificial 6-max AI-exhibition format is far too small and non-representative to be a *target-statistics* source on its own.

### 6. DeepStack vs. human professionals (Moravčík et al., *Science* 2017)
The underlying study is real and well documented: 44,000 hands, heads-up no-limit hold'em, DeepStack vs. professional players recruited through the International Federation of Poker (December 2016). Secondary sources (not independently verified this session) claim "45,037-hand logs were publicly released," including "45 thousand hands played by self-identified professional players" as part of a larger ~150k-hand pool of DeepStack vs. various opponents. **I could not locate an actual public download location for this data in this session** — the natural candidate repo (`lifrordi/DeepStack-Leduc`) only contains the *Leduc toy-game* implementation, not the NLHE human-study hands. Treat the "publicly released" claim as **UNVERIFIED-RECALL** until a primary URL is retrieved.

### 7. Slumbot
Live heads-up no-limit bot with a public HTTP API (built by Eric Jackson, CFR-based). No downloadable corpus of prior hands was found; the API lets you *generate* new hand histories by playing against it (bot-vs-caller data, not human-vs-human, and of unknown ToS status for bulk use). **No information found** on any released Slumbot hand corpus.

### 8. Kaggle datasets
Searched several: the "UCI Poker Hand Dataset" mirror (also on Kaggle) is **not gameplay data at all** — confirmed directly from the UCI ML Repository page (`archive.ics.uci.edu/dataset/158/poker+hand`): it is a synthetic enumeration of 5-card combinations (1,025,010 rows) labeled by poker hand rank (pair, flush, etc.), built for classification-algorithm benchmarking, with zero betting action or player identity. Other Kaggle listings found by title (`joogollucci/poker-hands-dataset`, `hosseinah1/poker-game-dataset`, `smeilz/poker-holdem-games`) could not be inspected this session (WebFetch returned only page titles, no body content) — their true provenance is **UNRESOLVED**, and given how the UCI set gets relabeled and re-uploaded under generic "poker hand dataset" names, do not assume any Kaggle listing titled this way is real hand-history data without checking its description and source citation directly.

### 9. GitHub — general search
Beyond `phh-dataset`, GitHub surfaced mostly **hand-history parsers/tools** (`HHSmithy/PokerHandHistoryParser`, `stw-developer/HandHistoryParser`, `galetahub/poker_history`, etc.) that operate on hands *you* supply — not corpora themselves. No additional standalone human-hand corpora of consequence were found beyond what's in #3/#4.

### 10. Commercial hand-history marketplaces / datamining resellers
These are **currently active** (checked this session): `hhdealer.com` ("HHDealer," fetch blocked by 403 but confirmed listed and referenced across multiple sources as active and selling PokerStars/WPT Global/network hands), `hhmailer.com` ("a leading online service in data mining PokerStars hand histories" per its own marketing, fetch failed with a 523 error this session so pricing could not be directly confirmed), and `pokerenergy.net`'s iPoker datamining page (claims "60% of all hands on the iPoker Network were being mined" as of a May-2025 reference). **HandHQ.com itself is now defunct** — domain parked for sale (confirmed via WHOIS-style search this session). Historical HandHQ pricing (grade C, stale, from a 2009-era third-party review site): ~$0.99 for a 10,000-hand sample, ~$10 for 200,000 hands, ~$32 for 1,000,000 hands.
- **All of these operate by scraping/datamining hands from poker rooms, which those rooms' own terms of service explicitly prohibit** (see Part 2). This is precisely the "scraping a site against its terms" category the brief instructs to treat as out of bounds, regardless of whether money changes hands.

### 11. Tracking-software vendors (PokerTracker, Hold'em Manager, GTO Wizard "GTO Reports")
These tools compute statistics **only on hands the individual user has personally played/imported** — they are not licensable population-wide datasets. GTO Wizard's "GTO Reports" feature, read directly this session, explicitly compares *a user's own uploaded stats* to solver benchmarks; the only "sample size" language on that page is an internal low-sample warning threshold (<200 hands) for a single player's own history, not a population statistic. **No public, sourced, population-wide aggregate statistics product from any tracking-software vendor was found this session.**

### 12. Academic papers built on licensed/agreement-based real operator data
Two were found and fetched directly:
- **Potter van Loon, van den Assem & van Dolder (2015), "Beyond Chance? The Persistence of Performance in Online Poker," PLoS ONE 10(3): e0115479.** Data: purchased from **HHDealer** (same datamining-vendor lineage as #4/#10) — 76.9 million hands, 456.1 million player-hand observations, 600,000+ distinct players, **October 2009–September 2010**, NLHE cash games at three stake tiers ($0.25/$2/$10 big blind). This is the single largest, best-documented, peer-reviewed human NLHE dataset found this session by a wide margin — but its ultimate source is the same ToS-violating datamining chain, so it does not escape the Part 2 legal concerns even though the *paper* is legitimate academic work.
- **"Second Session at the Virtual Poker Table" (PMC9325659).** Data: a formal, de-identified, secure-transfer data-sharing arrangement with **Entain plc** (formerly GVC Holdings), a licensed, regulated operator. Feb 2015–Jan 2017, 2,489 players (filtered from 72,494 registrants). **This is the one genuinely clean, operator-authorized access route found this session** — but the data granted was **daily aggregates of financial/session activity** (spend, session count, deposits), **not hand-level play data or VPIP/PFR-style statistics**. It demonstrates the access *pathway* exists (a research-purpose data-sharing agreement with a licensed operator), not that such an agreement would yield play-style hand data.

### 13. Government / regulator data
Checked the UK Gambling Commission directly (`gamblingcommission.gov.uk`, FOI response page fetched this session): confirmed, in the regulator's own words, that **"no information is currently held"** at the individual level — only aggregate market/financial statistics are published. A future pilot ("ROCD," Regular Feed of Operator Core Data) might eventually produce more granular data but "is not yet being received by the Commission." **No individual- or hand-level regulator dataset exists today.**

### 14. Litigation-released data
The 2007–2008 Absolute Poker/UltimateBet "superuser" cheating scandal did produce a real leaked master hand-history file (containing hole cards and IP addresses of all players in the implicated tournaments) — but this was an **accidental leak to a single player, used as forensic evidence**, not a structured, intentionally published research dataset, and it contains serious personally-identifying information (IP addresses). No packaged, downloadable version of it was found this session, and it should not be pursued even if found (see Part 2 privacy flag). The 2011 DOJ "Black Friday" seizures of PokerStars/Full Tilt/Absolute Poker produced financial forfeiture settlements; **no hand-history data release by DOJ or a bankruptcy trustee was found**.

### 15. Format infrastructure (not a corpus)
`hh-specs.handhistory.org` ("Open Hand History," OHH) is an open **file-format specification** for encoding hand histories, backed by industry (PokerTracker et al.). It defines *how* to represent a hand, not a source *of* hands. Worth knowing about if the project ever needs a standard schema, irrelevant to the acquisition question itself.

---

## Part 2 — Licensing and terms assessment

**I am not a lawyer; this is a report of what the primary/secondary sources say, not legal advice.**

| Bucket | Candidate | Basis |
|---|---|---|
| **(a) Clearly permitted** | ACPC bot-vs-bot logs (via `phh-dataset`, CC BY 4.0) | Own competition's data, no human subjects, explicit open licence. Does not answer the human-stats question though. |
| **(a) Clearly permitted** | Pluribus 10,000-hand dataset, *as an official Science supplementary file* — for the *research uses the paper itself demonstrates* | Official AAAS/author release. **But** general redistribution/republication rights are UNRESOLVED (see Part 1 §5) — treat as (a) for "read and analyze," (b)/UNRESOLVED for "redistribute or republish aggregates broadly." |
| **(b) Requires permission / data-use agreement** | An Entain-style operator data-sharing agreement (per PMC9325659's precedent) | Demonstrably obtainable in principle (one team got it for a different research question); would need to be independently negotiated for hand-level or play-style data, which has not been shown to be grantable at that pathway. |
| **(b) Requires permission / data-use agreement** | IRC Poker Database | No formal licence text on the CPRG's own page — only an informal "may be useful to researchers and hobbyists" plus a bare copyright notice. Decades of tacit academic reuse suggest low practical risk, but there is no explicit grant of redistribution or aggregate-publication rights. Recommend requesting written confirmation from CPRG rather than assuming permission. |
| **(c) Prohibited / legally murky** | The HandHQ-sourced 2009 human hands (whether accessed via the original vendor, via `phh-dataset`'s CC-BY relabeling, or via the PLOS ONE paper's underlying data) | The originating poker rooms' own terms of service **explicitly prohibit** this. PokerStars' prohibited-activities page (quoted via search-engine retrieval this session, not independently re-fetched due to a 403 — grade B) states verbatim: *"the practice of datamining hands or private results (observing games without playing in order to build up a database of hand histories for future reference); the use of hands or private results acquired through datamining; the mass sharing of hands, private results or playing statistics for the purpose of analysis of opponents"* are all prohibited. GGPoker's help center (fetched via search synthesis) similarly blocks "Mass Data Analysis" tools and sharing results externally. **A third party (HandHQ, or downstream `phh-dataset`) applying its own CC-BY licence to this data does not cure the fact that the data was extracted from the originating platforms in violation of those platforms' own terms.** This is exactly the "scraping a site against its terms" scenario the brief instructs to treat as out of bounds. |
| **(c) Prohibited / legally murky** | Current active resellers HHDealer, HHmailer, pokerenergy.net iPoker mining | Same underlying ToS violation as above, ongoing and current (2025–2026), one vendor openly states ~60% of an entire network's hands are being mined. Paying for this does not change its legal character. |
| **(c) Prohibited / legally murky** | The Absolute Poker leaked master hand-history file | Contains hole cards and real player IP addresses — a serious personal-data exposure from a security breach, not a licensed dataset. Should not be sought even if a packaged copy surfaces. |
| **UNRESOLVED (cannot verify)** | Kaggle listings other than the confirmed-synthetic UCI set | Could not retrieve descriptions this session; do not treat as clean until checked individually. |

**Privacy note:** every human corpus discussed here uses pseudonymous screen names, not real-world identities — but screen names are still personal data under most privacy frameworks (they are stable, re-identifiable pseudonyms tied to a real financial account), and several of these datasets pair screen names with stake level and win/loss, which is more re-identifying than a bare username. None of the sources reviewed this session included a documented anonymization/consent process meeting a modern research-ethics standard (e.g., IRB-reviewed informed consent) — the "anonymized" language used by HandHQ-lineage sources describes stripping/hashing identifiers after the fact, not obtaining consent before collection.

**Terms of service, generally:** every major site whose terms I could retrieve (PokerStars, GGPoker; 888poker referenced via secondary source) prohibits third parties from building databases of other players' hands without those players' direct participation, and separately prohibits exporting/selling/redistributing hand data obtained this way. This is a consistent, industry-wide position, not one outlier site.

---

## Part 3 — Paid options (assessed, not recommended)

Per the owner's ruling, this is pricing/terms information only — **nothing below is a purchase recommendation**.

1. **Datamining resellers (HHDealer, HHmailer, pokerenergy.net).** Currently active. Historical HandHQ pricing (now-defunct vendor, grade C, stale): ~$0.99/10,000 hands, ~$10/200,000 hands, ~$32/1,000,000 hands — illustrative of the price point this market has historically operated at, not a current quote. Current pricing for HHDealer/HHmailer could not be retrieved this session (403/523 errors on their sites). **Legal status: bucket (c), see Part 2 — buying does not cure the ToS problem.**
2. **Operator data-sharing agreement (Entain-style).** No published price list exists; this is a bespoke research partnership, arranged directly with a licensed operator, presumably requiring an academic affiliation, an IRB-style ethics review, and a formal agreement. No cost figure was found or could be found (not the kind of thing operators publish).
3. **AAAS/*Science* supplementary-data reuse (Pluribus).** Free to access; reuse/redistribution terms UNRESOLVED (Part 1 §5) — would need direct confirmation from AAAS's rights office, not a "price," but a permissions question.
4. No evidence was found of any *modern* vendor selling a **licensed, ToS-clean, aggregate-statistics** product (as opposed to raw scraped hands) — i.e., nothing like "we sell you our internally-collected pool VPIP/PFR distribution with permission to publish it." If such a product exists, it was not surfaced by this session's searches.

---

## Part 4 — Era-stability evidence

- **Qualitative consensus (grade B/C, multiple independent secondary sources) that pools have gotten dramatically tougher since the mid-2000s "boom" era.** The 2003–2006 boom period saw the online player pool reportedly doubling annually, described as full of players who "barely knew the rules," ending with the 2006 UIGEA. By contrast, sources describing the 2010s consistently cite the rise of HUD tracking, then GTO solver study, as having become "the cornerstone of serious poker education" by the late 2010s. No single rigorously quantified trend line (e.g., "pool-average VPIP fell from X% in 2006 to Y% in 2022") was located this session — this is a **real evidence gap**, not filled by any source retrieved.
- **One directly relevant, retrieved data point that behavioral involvement measures can be surprisingly STABLE across a decade:** PMC9325659 (fetched directly), comparing its 2015–2017 Entain-plc cohort against LaPlante et al.'s 2009 study, explicitly reports: *"results were similar to those reported in LaPlante et al.'s 2009 study... suggesting that players' levels of involvement are similar to those from ten years ago despite numerous changes to the online poker environment."* This is about session/involvement patterns, not VPIP/PFR-style playstyle stats, but it is genuine evidence that **not every online-poker behavioral quantity drifts** — some are era-stable and some (skill/toughness) plausibly are not, and the sourced literature does not tell us which specific play-style numbers fall in which bucket.
- **Limit-vs-no-limit transferability: no dedicated study was found this session.** This is a genuine gap. Reasoned (not sourced — flag this as analysis, not evidence) expectation: quantities driven by *positional information asymmetry* (e.g., the ordinal ranking of "how often does UTG vs. BTN voluntarily enter the pot" — tightest to loosest by seat) plausibly reflect strategic logic common to both formats and may transfer as **shape/ordering**, not as point values. Quantities that depend on *bet-sizing freedom* (3-bet sizing, c-bet sizing, all-in frequency, stack-to-pot-ratio-dependent lines) are structurally meaningless in fixed-limit hold'em, where bet sizes are fixed by the stake — these categorically **cannot** transfer from IRC-era limit data.

---

## Part 5 — Fallback ladder

**(i) Limit-era IRC data for era-stable SHAPE parameters.**
What it can deliver: relative *ordering* of positional looseness (which seats enter pots more/less often than others), and possibly qualitative calling-station vs. aggressive-player archetypes as shapes. What it cannot deliver: any point-estimate percentage (VPIP magnitude, 3-bet frequency, c-bet sizing) — 1995–2001 limit-format, boom-adjacent-but-earlier human pools are neither the right era nor the right betting structure for magnitudes. Justification for each parameter proposed to survive the gap must be explicit and mechanism-based (e.g., "positional information advantage is structural, not era- or format-specific") — none of that justification work was done in this lane; it is a task for whoever builds on this rung.

**(ii) Modern tracker-site population statistics as published aggregates.**
The strongest thing this session actually found and fetched is 15+ years stale (HHDealer/PLOS ONE data, Oct 2009–Sep 2010) and traces to ToS-violating collection at the root (Part 2). No current (2023–2026), sourced, methodology-disclosed, population-wide play-style statistics report from any named tracking-software vendor (PokerTracker, Hold'em Manager, GTO Wizard, Hand2Note) was located — GTO Wizard's "GTO Reports" was checked directly and confirmed to be personal-stats-only, not population-wide. Poker-training-site "typical VPIP" claims (SplitSuit, Red Chip Poker, Upswing) were checked directly and at least one (SplitSuit) **explicitly cites no source** — "the author's own framework," not tracking data. **This rung is currently the weakest, not the strongest, of the four** — the premise that vendors publish rigorous pool-wide numbers was not borne out by this session's search.

**(iii) Structured expert or LLM elicitation panels.**
The **Sheffield Elicitation Framework (SHELF)**, University of Sheffield's own methodology (`shelf.sites.sheffield.ac.uk`, found this session, not independently re-fetched — grade B), and the related **Delphi method**, are established, peer-documented decision-science protocols for eliciting quantitative probability distributions from expert panels, specifically designed for exactly this situation ("hard data are sparse... difficult policy decisions"). A retrieved comparison paper (arXiv:2001.11365, grade B) directly compares SHELF against the "classical method" of aggregating expert priors. Known strengths: structured facilitation, group discussion to surface disagreement, explicit uncertainty quantification (e.g., via the "roulette method" of histogram-building). Known weakness inherent to all expert-elicitation approaches (general decision-science knowledge, not independently re-sourced this session beyond the SHELF background): anchoring and overconfidence biases, which formal protocols like SHELF are specifically built to mitigate but not eliminate.

**(iv) Literature bands as the floor.**
What's actually out there: poker-training-site pages (SplitSuit, Red Chip Poker, Upswing, PokerCoaching) citing numbers like "22–28% VPIP for a winning 6-max regular" or "solid regulars 19/17–25/23." Checked directly: **these are consistently uncited, author's-experience numbers**, not sourced from any published dataset. This confirms, rather than resolves, the project's original problem — the literature bands the project already relies on are exactly this same tier of evidence, no better-sourced than what a determined web search turns up.

**Ranking, and what to build on:** (iii) and (iv) together, cross-checked against (ii)'s one legitimate finding (the aging-but-real 2009–2010 academic numbers, as a magnitude sanity-check only, not a target) and (i) for ordinal/shape confirmation only. Concretely: run a SHELF- or Delphi-style elicitation with strong current NLHE players/coaches to produce quantified target distributions (not point estimates) for the specific statistics the project needs; use the 2009–2010 HHDealer/PLOS-ONE numbers and the existing literature bands as priors/sanity checks for magnitude, not as ground truth; use position-ordering logic (not magnitudes) from IRC-era data only where the mechanism argument is explicit and format-independent. Do **not** build on any of the datamined corpora in Part 1/2's bucket (c).

---

## Part 6 — The verdict

**NO-GO** on acquiring a modern, licensing-clean, full-action-sequence human NLHE hand-history corpus, because every candidate of adequate size and recency traces to ToS-violating datamining at its root, and the two exceptions that are clean are either too small and narrow (Pluribus, 10,000 hands, one artificial AI-exhibition format) or contain no play-style data at all (the Entain operator agreement, financial aggregates only).

**Reasoning:** This research checked the natural candidate list end to end — university/AI-research releases (ACPC is bot-only; DeepStack's human-study data could not be located publicly; Pluribus's human data is real but tiny and license-unresolved), commercial marketplaces (all currently-active ones scrape in violation of site ToS, confirmed against the sites' own prohibited-activities pages), Kaggle/GitHub (mostly synthetic or unverifiable), government/regulator sources (UK Gambling Commission confirmed, in writing, that no individual-level data exists today), and litigation (no hand-level release found; the one leaked dataset that exists is a security-breach artifact carrying real IP addresses, not a usable or ethical source). The one legitimate access *pathway* that clearly works — a formal data-sharing agreement with a licensed operator — has a working precedent (Entain/PMC9325659) but that precedent delivered financial aggregates, not play-style hand data, so it is not proven to be able to deliver what this project needs even if pursued.

**What would change this verdict to PARTIAL or GO:**
1. A confirmed, written data-use agreement with a licensed operator (or a tracking-software vendor with direct database access) that is scoped, in writing, to include hand-level or play-style aggregate statistics — not just financial/session data — and that explicitly grants rights to publish derived aggregate statistics.
2. Confirmation from AAAS of the actual reuse/redistribution terms for the Pluribus supplementary data, if the project's needs could be met by a 10,000-hand, 6-max, human-vs-AI dataset (probably too narrow on its own, but worth resolving the licence question regardless).
3. Discovery of a corpus this session did not surface — in particular, the DeepStack human-study hands, if a genuine public release location exists, would be worth chasing down (era: Dec. 2016, still fairly old but more recent than 2009–2010, and reportedly ~45,000 hands with a claimed public release that this session could not verify).
4. An explicit owner decision to accept the legal/reputational risk of building on ToS-violating datamined data (e.g., the `phh-dataset` mirror of the 2009 HandHQ hands) — this is a policy call outside this lane's remit; it is flagged, not recommended.

---

## Candidate table

| corpus | format/era | human or bot | size | licence | may publish aggregates? | bucket | grade | URL | as of |
|---|---|---|---|---|---|---|---|---|---|
| IRC Poker Database | Limit, 1995–2001 | Human | ~9.48M hands (grade B count) | No formal licence; bare copyright + informal "useful to researchers" note | Unclear — not stated | (b) | A (page itself), B (hand count) | https://poker.cs.ualberta.ca/irc_poker_database.html | 2026-08 |
| ACPC logs (bot-vs-bot) | Fixed-limit + no-limit, 2006–2017 | Bot | 341.2M FL + 278.8M NL hands (incl. dupes) | CC BY 4.0 (Zenodo) / MIT (repo code) | Yes | (a) | A | https://zenodo.org/records/13997158 ; https://github.com/uoftcprg/phh-dataset | 2026-08 |
| phh-dataset human core (HandHQ 2009 scrape) | No-limit hold'em cash, July 2009 | Human | 21,605,687 hands, 6 sites | CC BY 4.0 as relicensed by uoftcprg — but original scrape violated site ToS | Legally UNRESOLVED despite the stated licence | (c) | B/C for provenance; A for the relicensor's own stated terms | https://zenodo.org/records/13997158 | 2026-08 |
| Pluribus vs. human pros | No-limit hold'em 6-max, 2019 | Mixed (5 human / 1 bot per hand) | 10,000 hands, 13 players | Science/AAAS supplementary file; general reuse terms UNRESOLVED | UNRESOLVED | (a) for the paper's own use; UNRESOLVED for republication | B | https://noambrown.com/papers/19-Science-Superhuman_Supp.pdf | 2026-08 |
| DeepStack vs. human pros | Heads-up no-limit, 2016 | Human vs bot | ~44,000–45,037 hands (claimed) | Unknown — no primary download located | Unknown | UNRESOLVED | D (public release claim unverified) | none retrieved | 2026-08 |
| Slumbot | Heads-up no-limit, live | Bot (API only) | No corpus found | N/A | N/A | UNRESOLVED | — | https://www.slumbot.com (not independently confirmed this session) | 2026-08 |
| UCI "Poker Hand" dataset (incl. Kaggle mirrors) | Synthetic, N/A | Neither (synthetic combinatorics) | 1,025,010 rows | UCI ML Repository terms | N/A — not gameplay data | N/A | A | https://archive.ics.uci.edu/dataset/158/poker+hand | 2026-08 |
| Other Kaggle "poker hand(s) dataset" listings | Unknown | Unknown | Unknown | Unknown | Unknown | UNRESOLVED | D | https://www.kaggle.com/datasets/joogollucci/poker-hands-dataset ; https://www.kaggle.com/datasets/hosseinah1/poker-game-dataset | 2026-08 |
| HHDealer / HHmailer / pokerenergy.net (active resellers) | No-limit cash, current | Human | Unknown current volume | No licence; ToS-violating datamining | No — sites explicitly prohibit redistribution | (c) | B (existence/activity); pricing not independently verified this session | https://hhdealer.com/ ; https://hhmailer.com/ ; https://pokerenergy.net/ipoker-hand-histories | 2026-08 |
| HandHQ.com (defunct) | No-limit cash, historical | Human | Historical vendor, now closed | N/A (site gone) | N/A | (c), historical | B | (domain now for sale) | 2026-08 |
| Entain plc operator data-sharing agreement | N/A — financial/session aggregates only, 2015–2017 | Human | 2,489 players (of 72,494 registrants) | Formal data-sharing agreement (bespoke) | Yes, in aggregate, as demonstrated by the published paper | (b) | A | https://pmc.ncbi.nlm.nih.gov/articles/PMC9325659/ | 2026-08 |
| PLOS ONE (Potter van Loon et al. 2015) academic dataset | No-limit cash, Oct 2009–Sep 2010 | Human | 76.9M hands, 456.1M player-hand obs, 600k+ players | Underlying data from HandHQ (see above); paper itself is peer-reviewed and open access | Yes, aggregate findings already published; raw redistribution rights rest with HandHQ's chain, not the authors | (b)/(c) mixed | A (paper), C (underlying data licence) | https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0115479 | 2026-08 |
| UK Gambling Commission | N/A | N/A | None currently held | N/A | N/A | N/A — data does not exist yet | A | https://www.gamblingcommission.gov.uk/about-us/freedomofinformation/print/individual-level-online-gambling-data | 2026-08 |
| Absolute Poker leaked master hand-history file | No-limit/tournament, 2007–2008 | Human | Unknown scope | None — security-breach artifact, contains real IPs | No — do not pursue | (c) | B | (no packaged public copy found) | 2026-08 |
| DOJ Black Friday seizures | N/A | N/A | No hand-level release found | N/A | N/A | N/A | B (negative finding) | https://www.justice.gov/usao-sdny/pr/former-full-tilt-poker-ceo-pleads-guilty-and-sentenced-manhattan-federal-court | 2026-08 |

---

## Claims table (non-corpus claims)

| claim | grade | source | as of |
|---|---|---|---|
| Poker rooms' ToS (PokerStars) explicitly prohibit datamining, use of datamined hands, and mass sharing of hands/stats | B (search-engine-quoted primary text; direct fetch returned 403) | pokerstarsnj.com/poker/room/prohibited (redirects to poker.fanduel.com) | 2026-08 |
| GGPoker prohibits Mass Data Analysis tools (PokerTracker, Hold'em Manager, Hand2Note) and result-sharing | B | help.ggpoker.com/article/Can-I-share-my-results-or-data-online | 2026-08 |
| GTO Wizard "GTO Reports" is personal-stats-only, not population-wide | A (fetched directly) | blog.gtowizard.com | 2026-08 |
| SplitSuit's cited 3-bet-frequency-by-player-type numbers are explicitly uncited/author's-own-experience | A (fetched directly) | splitsuit.com/understanding-3-bet-ranges | 2026-08 |
| SHELF (Sheffield Elicitation Framework) is an established multi-expert probability-elicitation protocol | B | shelf.sites.sheffield.ac.uk (found via search, not independently re-fetched) | 2026-08 |
| Player involvement measures (session patterns) were similar in a 2015–2017 cohort vs. a 2009 baseline study | A (fetched directly) | pmc.ncbi.nlm.nih.gov/articles/PMC9325659 | 2026-08 |
| UK Gambling Commission holds no individual-level online gambling data as of this FOI response | A (fetched directly) | gamblingcommission.gov.uk FOI page | 2026-08 |
| 2003–2006 online poker "boom" era characterized by rapid pool growth and weak average player skill | B/C (Wikipedia + secondary strategy-site sources) | en.wikipedia.org/wiki/Poker_boom and others | 2026-08 |
| UCI "Poker Hand" dataset is synthetic 5-card enumeration, not gameplay | A (fetched directly) | archive.ics.uci.edu/dataset/158/poker+hand | 2026-08 |

---

## What works vs. what fails

**Best practices found:**
- Official paper supplementary materials (Pluribus/Science) are the cleanest provenance trail available for any human-vs-AI hand data — always check the paper's own supplementary-materials link before trusting a mirror.
- Formal operator data-sharing agreements (Entain/PMC9325659 precedent) are a real, working access route for research-purpose data — worth pursuing directly with a licensed operator if the project ever wants to go this route, but scope the agreement explicitly to include play-style/hand-level data, since the one working precedent found delivered financial aggregates only.
- Cross-checking a claimed dataset's licence at two levels (the redistributor's stated licence AND the original data's provenance) surfaces problems that checking only the redistributor's licence page would miss — this is exactly how the `phh-dataset` CC-BY-vs-HandHQ-ToS conflict was caught.

**Pitfalls found:**
- Generic "poker hand dataset" names on Kaggle/GitHub are unreliable — several likely just relabel the synthetic UCI classification set, which contains zero actual gameplay or betting action. Always check the description for "5 cards, hand rank label" language before assuming it's a hand-history corpus.
- A downstream open licence (CC-BY, MIT) applied by an aggregator/mirror does not cure an upstream ToS violation at the point of original collection — this is easy to miss because the *mirror's* licence page looks completely clean in isolation.
- Training-site "typical stat" pages read as authoritative but frequently cite no source at all (confirmed directly for SplitSuit); do not treat a plausible-sounding number on a coaching site as sourced data without checking.
- Poker sites' terms of service are not a fringe technicality here — every major site checked (PokerStars, GGPoker) has an explicit, current, enforced prohibition on exactly the datamining/redistribution activity that every commercially available large human-hand corpus in this space depends on.

---

## UNVERIFIED-RECALL — not retrieved this session

- General background belief that PokerStars operates a public "hand replayer" showing some played hands on its own site — plausible but not checked this session, and even if true it would likely fall under the same scraping-prohibition analysis as everything else in bucket (c).
- General background belief that solver-vendor training products (PioSolver, GTO+, and GTO Wizard's core solving product, as distinct from its "GTO Reports" personal-stats feature checked directly this session) publish baseline GTO ranges widely used as informal literature-band references — not independently re-verified with a specific citation and numbers this session.
- General background belief that PokerStars historically held a dominant (~50–70%) share of global online poker traffic in the mid-2000s to mid-2010s — relevant only as color for "which site's data would be most representative," not independently sourced this session.

## NO INFORMATION FOUND ON

- A public, working download location for the DeepStack human-study hand histories (44,000–45,037 hands), despite multiple targeted searches.
- A structured, downloadable, research-usable copy of the Absolute Poker leaked master hand-history file (only incident narratives were found).
- Any DOJ or bankruptcy-trustee release of hand-level poker data from the 2011 Black Friday enforcement actions.
- A current (2023–2026), named, methodology-disclosed, large-sample population statistics report published by any poker tracking-software vendor (PokerTracker, Hold'em Manager, Hand2Note) — as opposed to personal-stats tools.
- Any dedicated academic or industry study directly comparing which specific NLHE behavioral statistics do vs. do not transfer meaningfully from fixed-limit to no-limit betting structures.
- Current, verified pricing from any active hand-history datamining reseller (HHDealer, HHmailer) — both sites returned errors (403/523) to direct fetch this session.
