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
