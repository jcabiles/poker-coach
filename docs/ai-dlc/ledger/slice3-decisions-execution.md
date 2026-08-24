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
down in advance rather than fitted afterwards.
