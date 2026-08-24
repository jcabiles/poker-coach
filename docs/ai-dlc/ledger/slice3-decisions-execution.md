# Finding ledger — slice3-decisions-execution (spec review round 1, 2026-08-24)

**Bottom line.** Dual review (Claude refuter on Sonnet + Codex gpt-5.6-terra), both
APPROVE-WITH-FIXES, findings convergent. Four findings, all ACCEPTED and folded into the spec
the same day. Raw reports: `../reviews/slice3-decisions-execution-r1-terra.md`; the refuter
report is reproduced in the session transcript (key claims re-verified inline below).

| # | Source | Severity | Finding | Adjudication |
|---|---|---|---|---|
| 1 | both (Terra 1, refuter 1) | HIGH | Consistency sweep conflicts with the engine-edit exclusion: `personas_postflop.py:323-370, 1742-1748` asserts the withdrawn 2026-08-19 per-bucket ruling as settled law and names the deleted tests as its enforcement | ACCEPTED — verified against source. Spec amended: comment-only corrections in `personas_postflop.py` permitted as an explicit adjudicated exception; zero behavioral diff, suite green is the proof |
| 2 | both (Terra 2, refuter 2) | MEDIUM | Filed-15's rule is prospective but §11 is a retrospective reviewer checklist; landing it as a bare checklist item weakens it to an after-the-fact question | ACCEPTED — spec amended: item 16 written in the W3R-1 dual pattern (binding prospective rule + pass/fail reviewer check), amendment block states it binds before ship |
| 3 | refuter 3 | MEDIUM | Narrator comment block `test_personas_postflop.py:980-1034` describes the deleted tripwire as "filed for owner ruling"; not on the spec's per-symbol deletion list, so a literal implementer orphans it. Surviving docstring `:8421-8428` also asserts the withdrawn ruling | ACCEPTED — both added to the spec's deletion/correction list |
| 4 | refuter 4 | LOW | Contract map used "Session-F", a label appearing nowhere in the poker-analytics working agreement | ACCEPTED — contract map corrected with a dated note |

**Verified-clean claims worth keeping** (refuter's deterministic checks): all cited line
ranges in spec + contract map exact · deleting the three tests + two helpers orphans nothing
surviving (`test_t3_river_damp_moves_only_the_ace_high_call_leg` depends only on
`_t3_allin_river_dist` + the damp constant) · Filed 14's engine claim is TRUE (position
multiplier applied after multiway — `personas_postflop.py:1501,1822,1874`, bluff path
`:1792`) · `test_contract_provenance.py` inspects only the §5a→§6 span, so §3/§4/§7/§9/§11
edits cannot trip it · baseline suite state 395 passed / 6 xfailed (all 6 = the
persona-parametrized ceiling test) · `ruff` clean · `make scorer-test` 119/119 green.

**Process note.** First Codex invocation failed on a sandbox write-denial creating
`~/.codex-ai-org` (not auth, not nested-Seatbelt); relocating `CODEX_HOME` to
`~/.codex/ai-org-home` (inside the sandbox's writable `~/.codex`) fixed it. Worth carrying
into the recipe if it recurs.

---

# Build round — `/ai-org:build`, Lane A + Lane B, 2026-08-24

**Bottom line.** Every wave was reviewed by a fresh agent that had not seen the worker's
reasoning. Findings below are listed with what the orchestrator decided about each; none was
folded automatically. One of them is a defect in the approved spec rather than in anyone's
build work, and one is an item that now needs the owner's confirmation.

Scope note: the owner's build invocation authorized **Lane A + Lane B only** — chain 1,
tickets E1 through E3, all inside poker-coach. Chain 2 (tickets P1–P4, the poker-analytics
publication-readiness lane, which the spec calls Lane C) was not authorized and is unbuilt.

| # | Wave | Source | Severity | Finding | Adjudication |
|---|---|---|---|---|---|
| B1 | E1 | build reviewer | HIGH | The paragraph recording ruling D2 (the value-side commitment slope is in scope for the future re-anchor slice) also asserted, inside a paragraph headed as an owner ruling, that the slope's engine work "lands in a separate pull request inside the same slice, ahead of the calibration one" — a reading of pre-existing ratified amendment A6, not something the owner ruled. | **ACCEPTED; kept in substance, re-marked.** Striking it was rejected: A6 opens by calling the re-anchor slice "calibration and hand-off only" while D2 puts engine work inside that slice, so the tension is real and a worker who cannot see it will hit it unwarned. The reading now sits in its own paragraph under the file's existing `⚠️ Provenance … not itself owner-ratified text` convention. **This is a new item awaiting owner confirmation.** |
| B2 | E1 | build reviewer | MEDIUM | "Amendment A10" was cited four times but never defined; amendments A1 through A9 are each a headed, dated block. | **ACCEPTED; label removed rather than a heading invented,** because the rule structurally is a reviewer-checklist item, not a block in §3, §4a or §7 like every real A-letter. It is now cited as "§11 item 16, owner-ratified 2026-08-24", which keeps its authority visible. |
| B3 | E2 | worker, orchestrator-verified | MEDIUM | **Defect in the approved spec, not in the build.** The spec directs a docstring correction at `test_fold_to_bet_respects_alpha_ceiling`, lines 8421–8428. Those lines belong to a different test, `test_bluff_catcher_alpha_contract_untouched_at_multiple_opponents` (defined at `:8072`), whose docstring is the one asserting the withdrawn ruling and citing a now-deleted test. | **Line numbers are right, the name is wrong.** Verified independently against `HEAD`: the named test's docstring is about the one-pair bluff-catcher range and the α ceiling as a ceiling-not-a-floor, and never asserts the per-bucket reading — so it needed no correction and got none. The worker corrected the block the line numbers point at, which was the correct call. Recorded here so a later reader does not "fix" the spec's name and re-open the wrong docstring. |
| B4 | E2 | worker, disclosed | LOW | A roughly 7-line section-header comment not named on the ticket's deletion list was deleted along with the block it introduced. | **ACCEPTED as correct.** The build reviewer confirmed it was a genuine orphan: it introduced only content being removed in full, it asserted the withdrawn ruling as settled fact, and nothing still referenced by surviving code went with it. Keeping it would have left a factually wrong header with nothing underneath. |

| B5 | E3 | build reviewer (Opus) | MEDIUM | The roadmap's verification claim that "every derived target is graded LOW confidence throughout" is contradicted by three of the sister repository's registry rows, and the entry was marked satisfied without disclosing that two of its own four candidate approaches are incomplete. | **ACCEPTED.** Confirmed independently by the orchestrator against `poker-analytics:data/targets/registry-v2.json`: 49 rows labelled `LOW`, 3 labelled `C-grade literature (unchanged)` — `flop_cbet`, `fold_to_cbet`, `af`. Condition (2) narrowed to targets *derived from the ingested aggregates*, and a fourth residual added recording that the swap off the literature bands is partial and no expert-elicitation panel was run — a disclosed limitation, not a work item. **This is the finding that justified routing the wave-3 reviewer to Opus.** |
| B6 | E3 | build reviewer | LOW | One contract map asserted "nothing occupies those line numbers now" while the other contract map edited in the same change said a live test begins exactly there. | **ACCEPTED.** Two contract maps contradicting each other inside one change defeats the purpose of a contract map. Corrected to name the cross-persona ordering test that now occupies those lines. |
| B7 | E3 | build reviewer | LOW | A ledger note placed the new reduction-floor rule "alongside §5a's obligations"; §5a holds exactly two obligations and this is neither — both halves live in §11 item 16. | **ACCEPTED, ledger note only.** The theory contract's own wording was checked and is correct (it claims the same dual *form*, which is true), so E1's committed text needed no change. |
| B8 | E3 | build reviewer | LOW | The close packet the roadmap links as its close record still instructs the owner to "rule on the filed decisions", done on 2026-08-24. | **ACCEPTED; narrow scope exception granted.** Dated reports in `research/slice3-calldown/` are normally not edited. One appended dated paragraph, no body change; the play session, genuinely still outstanding, untouched. Gain: the linked record stops handing the owner a completed task. Cost: one more file in the diff, and a small precedent for annotating dated records. |
| B9 | E3 | build reviewer | LOW | A research measurement script under `docs/` still opens by stating the withdrawn ruling as its reason for existing. | **ACCEPTED; narrow scope exception granted.** The worker self-restricted because the ticket forbids touching code, but the boundary it was given names `backend/`, `frontend/`, `content/` and `scripts/`, and this file is in none of them. Confirmed standalone with no importers and still parsing after a docstring-only banner. |
| B10 | E3 | build reviewer | LOW | The ledger's summary block compressed parked, deferred and closed into one clause and stated one closure more flatly than its own note did. | **ACCEPTED.** The per-item notes were already correct and distinct; the summary is the first thing read and is where a uniform stamp creeps back in. |

**Wave-2 review outcome: APPROVE, zero findings** (`../reviews/slice3-decisions-execution-build-e2.md`).
The reviewer re-ran the syntax-tree comparison and the persona test file itself rather than reading
the worker's transcript; both matched. Residue sweep found no surviving line in either file that
asserts the withdrawn per-bucket rule as live.

**Independently reproduced by the orchestrator, not taken on a worker's word.** The engine
file `personas_postflop.py` has a **byte-identical abstract syntax tree before and after**
E2 — that is a proof of zero behaviour change, stronger than reading the diff for lines
beginning with a hash · all five symbols the ticket deletes are absent and all three that
must survive are present · the pre-work baseline was registered before any worker started
(whole suite 2191 passed / 2 skipped / 6 expected-failures; the persona test file alone
collecting 401), so the predicted post-deletion figures of 2189 / 2 / 0 and 393 were written
down in advance rather than fitted afterwards · both finding ledgers touched by E3 are
strictly append-only (231 and 10 lines added, **zero deleted**), so no past entry's recorded
finding was revised · the registry confidence counts behind B5 were re-derived from
`registry-v2.json` itself rather than accepted from the review · the measurement script in B9
was confirmed to parse and to have no importers before the exception was granted.

**Wave-3 review outcome: APPROVE-WITH-FIXES, six findings, all accepted and fixed pre-commit**
(`../reviews/slice3-decisions-execution-build-e3.md`). The wave-3 reviewer was routed to Opus
rather than the Sonnet used for waves 1 and 2, because that diff is the largest, edits the
governing roadmap, and makes a claim about another repository's state. B5 is what that
routing bought.

## Still owed by the owner when this build lands

Two items came out of this build and neither can be closed from a branch.

1. **Confirm or overrule one interpretation** (finding B1). The theory contract now carries a
   paragraph reconciling the ruling that the commitment slope is in scope for the re-anchor
   slice with amendment A6, which opens by calling that slice "calibration and hand-off only".
   The reading offered is that A6's prohibition binds the calibration pull request, so the
   slope lands in a separate pull request inside the same slice. **It is marked as an
   agent-adjudicated clarification and explicitly not owner-ratified text**, and a worker
   reaching the re-anchor slice while it is unconfirmed is instructed to raise the tension
   rather than pick a reading.
2. **Correct a document that no branch can reach.**
   `docs/ai-dlc/research/persona-realism-audit-2026-07-24.md` is listed in `.git/info/exclude`,
   so it is untracked and exists only in the main checkout. Its §10.2 still gives the
   superseded order for the engine's aggression multipliers — position before multiway —
   while the engine applies position **last** and the theory contract now says so. Theory
   contract §11 item 12 sends reviewers to that §10.2 for exactly this ordering, so the
   pointer currently resolves to superseded text. The fix is a one-line dated correction in
   the owner's own copy.
