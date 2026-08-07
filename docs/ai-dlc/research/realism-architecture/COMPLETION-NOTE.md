# Session R — S2b completion note

Slice S2b of `../../roadmap/bot-realism-flywheel.md` (research wave), PRD requirement R5.
Session R, 2026-08-05. **Docs-only session. No git commands were run, no code or sims were
executed, nothing outside this directory was modified, and no dataset was downloaded.**

Per the working agreement §5, the director session reviews this and commits accepted dossiers.
**Session R has not committed anything.**

---

## 1. Files delivered

| File | One-line summary |
|---|---|
| `01-academic-prior-art.md` | The Alberta/CPRG lineage optimises *strength*, never human-likeness; the answer lives in chess/FPS/navigation research, where human-likeness must be targeted deliberately — by learning from human data **or** by hand-authoring behaviour terms, the latter being the one mechanism here with a blind-test pass behind it. |
| `02-commercial-practice.md` | No commercial product discloses a realism method (the one that does calls itself a study aid, not realism); poker bot detection is real, decision-level, and entirely self-reported; no blind human-vs-bot poker experiment exists publicly. |
| `03-nlhe-corpus-gate-brief.md` | **Verdict PARTIAL** — NO-GO on a licensing-clean corpus of human NLHE *hands*, but modern archetype-segmented human *statistics* are freely available, which is what the target registry actually consumes; one owner ruling required. |
| `04-consumption-map.md` | All 53 conclusions routed to scorer / sweep / detection / estimand contract / architecture gate / corpus decision / explicitly-rejected, each with an evidence grade and the specific change it should cause. |
| `_raw/lane-a-academic-evidence.md` | Sealed Claude lane — full academic evidence trail, claims table, six candidate architectures. |
| `_raw/lane-b-commercial-evidence.md` | Sealed Claude lane — full commercial evidence trail with every detection method tagged input-level vs decision-level. |
| `_raw/lane-c-corpus-evidence.md` | Sealed Claude lane — full corpus/licensing evidence trail, 15 candidates assessed, permitted/agreement/prohibited buckets. |
| `_raw/lane-d-codex-sweep.md` | Cross-family (Codex Terra) breadth sweep — source inventory, "most likely missed" list, contradictions. |
| `COMPLETION-NOTE.md` | This file. |

**On `_raw/`:** these are worker outputs, kept as the audit trail behind the four dossiers. The
director may commit them for traceability or drop them as working material — the dossiers are
self-contained without them. They are **not** duplicate deliverables.

**Pass/fail against the roadmap:** three dossiers ✅ · gate brief ends in an explicit
GO/PARTIAL/NO-GO with licensing assessment ✅ · fallback ladder (i)–(iv) each evaluated with
evidence, since the verdict is PARTIAL ✅ · consumption map with evidence grades ✅.

---

## 2. Method (so the director can weigh the output)

Four research lanes, one wave, ungated per GATE.md (no Opus workers, ≤5 workers, no external side
effects, no irreversible actions, no foreman):

- Three sealed Claude lanes (`general-purpose`, pinned `model: sonnet`) — academic, commercial,
  corpus. Each named its source hierarchy from SOURCES.md rather than improvising criteria.
- One Codex Terra sweep (`model_reasoning_effort=medium`) for cross-family breadth — chosen
  specifically because this slice exists after prior planning missed a whole research lineage.
- Owner decisions taken up front: strictest evidence bar (every citation retrieved this session,
  URL + `as of` date, no memory-sourced claims), paid corpus options priced but not recommended,
  commercial lane run at full depth rather than pre-cut.
- Adjudication, primary-source verification, and authoring of all four dossiers: this session.

**The Codex lane earned its cost once, decisively** — it surfaced Teófilo & Reis 2011, a
behaviour-cloning NLHE agent trained on human game logs, which the Claude academic lane had
explicitly reported as a gap ("no poker-specific behaviour-cloning precedent found"). That single
find changes the architecture picture in `01` and `04`.

---

## 3. Lead corrections to lane output (adjudicated, not auto-folded)

Reviewer and worker output is a report, never gospel. Five claims were checked against primary
sources personally and four were changed:

| # | Lane claim | Outcome |
|---|---|---|
| 1 | Rung (ii) of the fallback ladder is "essentially empty — no vendor publishes pool statistics" | **OVERTURNED.** Found and fetched a free, current, archetype-segmented GGPoker pool-statistics source. Rung (ii) promoted from weakest to strongest; **the headline corpus verdict moved NO-GO → PARTIAL.** |
| 2 | "Maia predicts human moves 5–15 points better than Stockfish," cited to arXiv 2409.20553 | **Mis-cited and unverified.** That ID is Maia-2 and shows no such comparison; the original paper states the qualitative claim without that figure. Qualitative claim kept at grade A on the correct paper; the number demoted to C. |
| 3 | PCSP (arXiv 2605.23652) graded A | **Real paper, claims accurate**, but a single-author preprint from 2026-05 with no visible peer review. **Demoted A → B.** |
| 4 | "No poker-specific behaviour-cloning precedent exists" | **Refuted** by the cross-family sweep and confirmed by the Lead via two independent retrievals. Grade A. |
| 5 | `phh-dataset` attributed to "University of Toronto CPRG" | **Lane was right, my suspicion was wrong** — the GitHub org is literally `uoftcprg`. Recorded so it is not re-litigated. Hand counts independently confirmed, upgraded to grade A. |

---

## 4. ⚠️ Items requiring the owner (surfaced, not silently reconciled)

Per the tripwire rule in `.claude/CLAUDE.md`, research that undercuts a planned slice's premise
goes to the owner rather than being quietly absorbed.

**OWNER-1 — provenance ruling. ✅ RESOLVED 2026-08-06: option (A), use it and disclose openly.**
The S2a target registry may consume the published GGPoker pool aggregates. **Four binding
conditions travel with the ruling** (full text in `03-nlhe-corpus-gate-brief.md` §8): record every
consumed value with its exact filter combination (stake · segment · statistic) plus retrieval date,
since the source is a rolling window and a date alone cannot reproduce it; grade every derived
target low-confidence; construct and justify the strata→persona mapping rather than reading it off;
and state the provenance limitation in the registry **and** in any public methodology write-up.
Disclosure is half the ruling, not a footnote.

**OWNER-2 — roadmap re-scope. ✅ RESOLVED 2026-08-06: re-scope approved and applied.** The NEXT item
is now **"Population-statistics ingestion + target-registry upgrade"**; the acquire-hands framing is
closed, with a formal operator data-sharing agreement retained as the only credible route back to
hands (listed, deliberately not pursued). ⚠️ **Boundary note for the director:** this edit touches
`../../roadmap/bot-realism-flywheel.md`, which is outside session R's docs-only scope and is
normally single-owner (director). It was made on the owner's explicit instruction, and is flagged
here rather than left silent so the ownership exception is visible at fan-in.

**Not a conflict, recorded for completeness:** nothing in these findings contradicts the roadmap or
PRD. The roadmap pre-agreed the fallback ladder precisely in case of this outcome, and its
sequencing is *validated* by finding A8 — no literature answers the ceiling question, so it has to
be measured, which is what S5 exists to do.

---

## 5. Three findings that change downstream work

*(Revised after blind review — finding 1 is the post-correction version. See §7.)*

1. **The phase-3 gate has a third option, and it is the best-evidenced mechanism here**
   (`04` → ARCH A11 + A2). The only experiment in this research where an agent actually passed a
   blind human-vs-machine test achieved it through **hand-authored reward terms encoding human-like
   traits** — penalties for swinging the camera around, bumping walls, standing still — with human
   data used only to *evaluate*, never to train. **Our dial architecture is hand-authored terms;
   they just encode strategic merit instead of human-likeness.** So "keep the engine, re-aim what it
   optimises" belongs in the decision matrix alongside fix and rebuild. It is not corpus-gated, not
   speed-gated, and reuses the existing engine.
   The related data picture: **some** rebuild branches are blocked by the corpus NO-GO (behaviour
   cloning, empirical archetype clustering); **others are not** (persona-conditioned policies from
   authored personas, self-play). But the ones that escape the data blocker mostly optimise
   *strength*, and strength and human-likeness are disjoint objectives. **The one dependency that
   is universal is a human *target* to aim at — which after this slice is aggregate statistics, not
   hands.**
2. **Cross-persona similarity is a detection surface we create by construction** (`04` → DETECTION
   D4/D5). The oldest documented commercial detection technique is finding groups of accounts that
   play too similarly to be chance. Seven personas generated from one dial engine over one merit
   table is structurally that. **No per-persona distance metric can see this** — S6 needs a
   cross-persona statistic, and the roadmap's Goodhart guard on archetype separation turns out to
   be an anti-detection requirement, not only a coaching-value floor.
3. **The speed budget is tighter than assumed and is unmeasured** (`04` → ARCH A4). At 500 hands/sec
   with ~8–15 villain decisions per hand, the budget is roughly **130–250 µs per decision,
   single-threaded, on a laptop CPU**. The nearest published CPU figure for a persona-conditioned
   net is ~183–202 µs — *inside the band with no headroom* — and a published self-play poker policy
   is ~2.9 ms on a GPU, an order of magnitude outside. **Any overhaul proposal owes a representative
   CPU microbenchmark before throughput can be claimed.**

---

## 6. Declared gaps and limits

- **No source states the exact negative result the ceiling question needs.** The literature cannot
  settle whether a tuned dial architecture can reach human-band behaviour. This is a finding, not a
  failure of searching — and it means S5's measurement is load-bearing rather than confirmatory.
- **No blind human-vs-bot poker experiment exists publicly.** S6 designs a protocol; it does not
  reproduce one. That should be stated in S6's write-up.
- **No formal distributional-distance metric has ever been applied to poker action frequencies for
  a human-likeness objective.** S3 chooses without precedent and must argue the choice.
- **No quantified era-drift trend line** for NLHE population statistics, and **no study** of which
  statistics transfer between fixed-limit and no-limit.
- The rung-(ii) statistics source publishes **no sample size and no methodology**, and uses a
  rolling 12-month window — targets from it must be snapshotted with retrieval dates or the
  registry silently drifts.
- Codex-surfaced sources graded **C** were retrieved at metadata (DOI/title) level only. They are
  follow-up reading, not evidence for any conclusion.
- Several first-party pages were unreachable during research (partypoker's method post 403,
  PokerSnowie's own weaknesses page 404, reseller sites 403/523). Each is recorded inline as a
  retrieval gap rather than filled in from memory.
- Commercial evidence is genuinely thin, as the roadmap anticipated when it named this lane the
  first scope cut. It was run at full depth anyway and its detection half — not its realism half —
  is what justified that.

---

## 7. Blind cross-family review (GATE.md Tier 2) — findings ledger

**Reviewer:** Codex Sol (`gpt-5.6-sol`, `model_reasoning_effort=high`), fresh context, given only
the four dossiers and a **locked checklist** — fabricated/misread sources · unsupported leaps ·
missing counter-evidence · staleness. Cross-family by design: the artifact was authored by Claude.

**Verdict returned: NEEDS-WORK.** Thirteen findings. **All thirteen adjudicated as accepted**, two
after the Lead independently verified them against primary sources first (reviewer output is a
report, never gospel — but here it was right, including about the dossier's own headline).

| # | Sev | Finding | Adjudication |
|---|---|---|---|
| 1 | HIGH | "Navigates Like Me" agent described as trained on human data, baseline as hand-built | **ACCEPTED — Lead-verified from the paper's full text.** It is RL with hand-designed reward shaping; human data was evaluation-only; both baselines were deep-RL agents. **This inverted a headline conclusion** — corrected in `01` §1/§3/§6.5 and `04` §2.4 |
| 2 | HIGH | `04` A1: "every alternative architecture requires human training data" | **ACCEPTED.** PCSP trains from authored personas; "Navigates Like Me" used no human traces. Claim was false as a universal. Split into corpus-gated vs not (A1), with the genuinely universal dependency isolated as A1b |
| 3 | HIGH | `04` A2 overclaims — a navigation result does not compare dial tuning against imitation learning | **ACCEPTED.** Scoped to "competence alone is insufficient in this navigation task" |
| 4 | HIGH | Missing counter-evidence: self-play poker policies (Poker-CNN, AlphaHoldem) need no human corpus | **ACCEPTED — genuine gap.** Added as A13 / candidate 8, with the caveat that they optimise strength, not human-likeness |
| 5 | HIGH | `02` uses the Dec-2020 EA filing without the outcome | **ACCEPTED — Lead-verified.** Case voluntarily dismissed 2021-02-11 after plaintiffs met EA's engineers; EA states the system was never in FIFA/Madden/NHL. Rewritten in `02` bottom-line/§1/§2.3/§5 — **the corrected lesson is about judges being confidently wrong, which is now DETECTION D10** |
| 6 | MED | AAMAS 2025 "harder⇒easier detection" promoted to a grade-A prior; the paper calls it an open hypothesis | **ACCEPTED.** Relabelled as an untested hypothesis in `01` §3 and `04` D8 |
| 7 | MED | `04` A4 speed claim unbenchmarked for this workload | **ACCEPTED.** Downgraded; `01` §7.1 now does the arithmetic explicitly (~130–250 µs/decision budget vs ~183–202 µs nearest CPU figure) |
| 8 | MED | Bluffaces segments described as mapping to persona archetypes "directly" | **ACCEPTED.** They are population strata; mapping must be constructed and justified (`03` §5, `04` E1b) |
| 9 | MED | Discriminator "modest human sample incl. owner's own hands" unsupported | **ACCEPTED.** Single-player confounds identity/stake/session; now requires multiple humans, held-out-player evaluation, matched conditions, power analysis (`04` S3) |
| 10 | MED | Universal negatives ("no source anywhere") laundered from search outcomes | **ACCEPTED.** Restored to "not found in this session's documented search, as of 2026-08" in `01` §9 and `04` D1/S4/A8 |
| 11 | MED | Teófilo 2011 reduced to "static imitation"; the paper's mixture extension omitted | **ACCEPTED.** Added as a hybrid architecture branch (`01` candidate 7, `04` A12) |
| 12 | MED | ToS provenance treated as a settled legal conclusion | **ACCEPTED.** Recast as a **project-policy/ethics NO-GO pending qualified legal review**, with the hiQ/Feist caveats stated (`03` verdict banner, `04` C1b). Practical outcome unchanged |
| 13 | LOW×3 | CS:GO frame count (5.5M in v2, not 4M); IRC hand count (CPRG says ">10 million", 9.48M is a third-party parser figure); rolling-window values need pinning, not just a date | **ALL ACCEPTED** and corrected in place |

**Reviewer's VERIFIED-CLEAN list** (checked and held up): all seven arXiv identifiers exist with
matching titles/authors; the Springer DOI supports the human-game-log classification claim and its
static-strategy limitation; arXiv 1301.5943's seven clusters; `phh-dataset`'s 21,605,687 HandHQ
NLHE hands with the stated sites, stakes, date range and CC BY 4.0; Bluffaces' free GGPoker
statistics with the stated stakes, four segments, rolling window and statistic families; GTO
Wizard's virtual-incentive mechanism and psychology disclaimer; EA's patent wording; Cicero's
40-game/82-human figures.

**Not examined by the reviewer:** metadata-only grade-C papers, proprietary operator detector
accuracy, exact IRC archive contents (downloading was prohibited), and a jurisdiction-specific
legal opinion.

**Honest assessment of what this review cost and bought.** It overturned one headline conclusion,
corrected a stale precedent that had been given prominence, closed a real prior-art gap, and
tightened five overstatements. The corrections **improved** the phase-3 picture rather than
damaging it — the third gate option (§5 finding 1) exists only because the review forced a re-read
of the mechanism behind this research's single strongest result. **No finding was rejected**, which
is itself worth noting: on a first-authored research artifact, that suggests the pre-review draft
was over-confident in exactly the places a maker cannot see.

**Residual risk the director should weigh:** the four dossiers have now been through one blind
review and the corrections were folded by the same session that wrote the originals. A second
opinion on the *corrected* text has not been run, and per the review-loop stop condition that would
need a new question, method or counterexample to justify — not simply another pass.
