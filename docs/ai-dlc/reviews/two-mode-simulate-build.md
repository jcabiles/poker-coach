# Build review record — Two-mode Simulate (Training / Challenge)

One entry per hand-off barrier between the eight tickets of this slice. The plan is
`../plans/two-mode-simulate.md`; the tickets are `../tickets/two-mode-simulate.md`. Every entry
records which deterministic checks ran, who reviewed, and what the verdict was — because a
barrier that leaves no record is indistinguishable from a barrier that was skipped.

## The worktree's test baseline is not the main checkout's

Measured 2026-08-26 on this branch's base commit. The main checkout runs `2 failed, 2189
passed`; this worktree runs **`2189 passed, 2 skipped, 0 failed`**. The difference is entirely
benign and worth stating once so nobody reads it as a masked regression: the two
`test_detection_probe.py` tests that fail in the main checkout **skip** here, because they read
a machine-local data file that is deliberately not tracked by git and so was never copied into
the worktree. Their own skip message says so: `local S6 deck / owner DB not present`.

The practical consequence is good: inside this worktree, **any failure at all is ours**.

---

## Barrier after ticket T1 — the two session columns and migration `0015`

**Ticket in plain terms.** T1 is the database groundwork: it adds two columns to the Simulate
session table — `mode`, which records whether the player chose Training or Challenge, and
`blind_check_json`, which will later hold the result of the hand-200 opponent-identification
quiz — plus the Alembic migration that adds them to an existing database. It builds no
behaviour.

**Worker:** `implementer`, Sonnet, medium effort (the agent's pinned effort).
**Reviewer:** `refuter`, Sonnet, high effort (pinned). Fresh context; did not see the
implementer's reasoning.
**Verdict: APPROVE.** No blocking issues.

**Deterministic checks — re-run independently by the reviewer, not taken from the worker's
report:**

| Check | Result |
|---|---|
| Full backend suite (`pytest -q`) | `2190 passed, 2 skipped`, zero failures |
| `tests/test_db.py` | 1 passed |
| The new migration test | 1 passed |
| Selection `-k "db or migrat or sim_session or sim_replay or sim_grading"` | 94 passed |
| `ruff check .` | clean |

The passing count rose by exactly one, which is the one test T1 added. Nothing was lost.

**The new test was proved non-vacuous rather than assumed to be.** The reviewer moved the
migration file out of the versions directory, cleared the compiled-bytecode cache, and re-ran:
the test failed with `OperationalError: no such column: mode`. Restoring the file made it pass
again. So the test genuinely exercises the migration and does not merely re-assert its own
setup.

**The one design question, adjudicated.** The specification says both columns are nullable with
`NULL` read as Training, but the implementation types the Python field as a plain non-optional
string. The reviewer settled it: SQLite's `ALTER TABLE ... ADD COLUMN ... DEFAULT 'training'`
writes the literal default into every pre-existing row at migration time rather than leaving
them null, and the only place that constructs a session row in Python never omits the field, so
no null can reach a reader through any path that exists. The type annotation is therefore
truthful, and the absence of a read-time fallback is correctly unnecessary rather than a defect.
This matches the golden path it was told to copy, `DrillAttempt.source`, which also carries no
per-instance guard.

**One thing carried forward to T2, which is the ticket that adds the first reader.** If a null
ever did reach the column, the schema field T2 is about to add — a literal union of exactly
`"training"` and `"challenge"` — would raise a validation error rather than quietly fall back to
Training. T2's brief therefore instructs it to normalise at the read boundary. The gain is that
a hand-rolled or future write path cannot turn a missing mode into a 500 error; the cost is one
extra line in the view assembly.

---

## Barrier after ticket T2 — the mode accepted at creation and carried on every response

**Ticket in plain terms.** T2 makes session creation accept the player's Training-or-Challenge
choice and makes every response carry it back, together with whatever hand-200 quiz result is
stored. It builds no gate, no scoring and no user interface.

**Worker:** `implementer`, Sonnet, medium effort (pinned).
**Reviewer:** `refuter`, Sonnet, high effort (pinned). Fresh context.
**Verdict: APPROVE WITH FINDINGS**, two of them Major. Both were fixed by the original
implementer before this barrier closed, and the fixes were verified by the Director.

**Deterministic checks — re-run by the reviewer independently, then again by the Director after
the fixes:**

| Check | Result |
|---|---|
| Full backend suite | `2195 passed, 2 skipped`, zero failures — exactly the five tests T2 added |
| Selection `-k "sim or simulate"` after the fixes | 148 passed (146 plus the two regression tests) |
| The ticket's own test module after the fixes | 7 passed |
| `ruff check .` | clean |

**All five original tests were proved load-bearing**, not merely present. The reviewer broke the
specific code each one guards and confirmed the test failed, then restored every file and checked
it byte-for-byte against the original. The test that matters most — that villain archetypes
survive in the database in Challenge mode, the one constraint in this slice that must not bend —
was attacked twice, including a version that nulls the archetype *after* the session is dealt so
that the assertion itself has to catch it rather than an incidental engine crash. It did.

**The two Major findings, both reproduced as real HTTP 500 responses.** They share one shape:
`_view()` is the single point where every Simulate response is assembled, so anything that raises
inside it takes down not one field but the whole session — restore, dealing, and acting alike,
with no recovery short of hand-written SQL.

1. **An unrecognised stored mode.** The normalisation guarded only null and empty values, so a
   non-empty junk string passed into the two-value literal union and failed response validation.
   The reasoning that justified handling null applies identically to an unrecognised value: both
   are reachable by exactly the same hand-rolled write. Fixed by validating against the permitted
   values rather than testing truthiness.

2. **A malformed stored blind check.** The stored-result parse was unguarded. Fixed with a
   commented fallback that drops the field and lets play continue — the case the engineering
   standard carves out when it allows "a deliberate fallback [that] states its reason in a
   comment". The specification's own framing settles it: the blind check is "a keepsake for the
   player, not a measurement", so core play must not depend on it parsing. The finding was latent,
   because nothing writes that column until T4, but T2 owns the read path that will inherit
   whatever T4 writes.

A third, minor finding: the `# type: ignore` comment suppressed nothing, because this repository
runs no static type checker in any of its gate commands. It was removed.

**Why no second review round.** The two fixes were specified by the reviewer, not invented by the
implementer; the implementer proved each new regression test fails against a mechanically
reverted copy of the file; and the Director read the final diff and re-ran the checks. A third
agent re-reviewing two reviewer-designed edits would have cost another full review pass to
re-confirm what two parties had already established. Recorded here so the decision is visible
rather than implied.

---

## Barrier after ticket T3 — the completed-hand count and the server-side deal barrier

**Ticket in plain terms.** T3 counts how many hands the player has finished and stops the deal
once a Challenge session reaches 200 of them with the opponent-identification quiz unanswered.
It is the correctness-critical ticket of the slice: an off-by-one at this exact boundary is the
defect that forced the specification to be rewritten before it was approved.

**Worker:** `heavy-worker`, Opus, high effort (pinned).
**Reviewer:** `refuter`, Opus, high effort (pinned). Fresh context.
**Verdict: APPROVE WITH FINDINGS** — six, all Minor, all real. Four were code and were fixed by
the original implementer before this barrier closed; two were documents and were fixed by the
Director.

**Deterministic checks:**

| Check | Result |
|---|---|
| Full backend suite, before the fixes | `2210 passed, 2 skipped`, zero failures — exactly the thirteen tests T3 added |
| Full backend suite, after the fixes | `2213 passed, 2 skipped`, zero failures |
| The two modules the name-based selection hides | 46 passed |
| `ruff check .` | clean |

**The boundary was settled by the reviewer from first principles, not checked against the
implementer's answer.** It derived the count at four states independently and then compared:

| State | Hands finished | Deal barred? |
|---|---|---|
| Hand 199 live | 198 | No |
| Hand 199 settled | 199 | No |
| Hand 200 live | **199** | No |
| Hand 200 settled | **200** | **Yes** |

The deal must be barred at exactly one of those four and nowhere earlier. The implementation
bars there and only there, confirmed by execution rather than by reading: a probe reproduced all
four states, called the deal, then re-read the session **on a separate database connection** and
found the hand counter unmoved, the button seat unmoved, and no new hand row written. That is a
stronger check than the in-test assertion it replaced.

**The most consequential finding is a sentence, not a line of code.** The acceptance criterion
*"the derivation returns 200 both while hand 200 is live and after it settles"* is false under
the formula the same documents mandate — a live hand 200 gives 199. The implementer found it in
the ticket and implemented the formula rather than the sentence, which was the right call. The
reviewer found the **same sentence repeated verbatim in the specification's own verification
list**, which the implementer had missed. Both are now corrected. Left standing, a frontend
worker reading it literally would have opened the dialog mid-hand — the rev-2 defect,
reintroduced from the document rather than from the code.

**Three findings were fixed here rather than deferred, and one of the deferrals was re-routed.**
The implementer had sent the dropped end-of-hand recap to ticket T8. That was the right instinct
and the wrong destination: T8 owns only frontend files, and the recap is assembled on the server,
so T8 could not have fixed it. It came back to T3, which owned the file at that moment.

**One fix removed code rather than adding it.** The gate and the response had disagreed about
what counts as a stored quiz result — one tested whether the column was non-empty, the other
whether it parsed — so a corrupt value let play run past the gate while the browser kept
re-showing its dialog. Both now call one shared predicate, and the earlier inline parse was
deleted rather than left beside it. Exactly one parse site now exists in the module.

**Mutation testing, by both parties.** The implementer ran seven mutations; the reviewer ran nine
independently, including one the implementer had not tried — injecting a mutation *inside* the
barred branch, which is what proves the "nothing is mutated" assertions are load-bearing rather
than decorative. Every behaviour-changing mutation was caught. One mutation survived and was
reported honestly as a genuine equivalence rather than dressed up as a gap: moving the barrier
above the live-hand early return is behaviourally identical, because both branches build the same
response from the same row.

**A process defect that nearly hid the whole ticket.** The name-filtered test selection used as
this slice's de-facto done condition matches the *module filename*. The implementer's first
filename contained neither "sim" nor "simulate", so the run deselected every new test and
reported the unchanged baseline — green, while executing none of the work. They caught it only
because the number had not moved. The reviewer reproduced the mechanism in an isolated project
and found a second, permanent instance: the same selection hides a test module that drives more
than two thousand hands through the changed function, past the gate. **The barrier now runs the
full suite for every remaining backend ticket**, at ten minutes a run instead of thirteen seconds.

**Why no second review round.** As at the previous barrier: the fixes were reviewer-specified
rather than implementer-invented, the implementer proved each new test fails against a
mechanically reverted copy, the mutation battery was re-run afterwards with the file restored
byte-identical, and the Director read the final diff and re-ran the full suite. Recorded so the
decision is visible rather than implied.

---

## Barrier after ticket T4 — the blind-check endpoint, and the end of the backend

**Ticket in plain terms.** T4 builds the quiz that unlocks the opponents' names: the server picks
three seats from the session identifier, the player names each one's playing style, the server
scores the answers against what those seats actually were and stores the result once. It is the
last backend ticket; everything after it is the browser.

**Worker:** `heavy-worker`, Opus, high effort (pinned).
**Reviewer:** `refuter`, Opus, high effort (pinned). Fresh context.
**Verdict: APPROVE WITH FINDINGS** — two Minor, both fixed before this barrier closed.

**Deterministic checks:**

| Check | Result |
|---|---|
| Full backend suite, before the fixes | `2236 passed, 2 skipped`, zero failures — exactly the 23 tests T4 added |
| Full backend suite, after the fixes | `2239 passed, 2 skipped`, zero failures |
| `ruff check .` | clean |

**Eighteen mutations, zero survivors.** The reviewer copied the worktree elsewhere and mutated the
copy rather than the tree, so the working tree is provably untouched. Mutations covered the
scoring arithmetic, the seat pick's determinism, sampling without replacement, hero exclusion,
the threshold comparison, the mode condition, each error status, first-write-wins, persistence,
and two aimed squarely at the information leak. One of those killed the worker's own doubt: the
mutation that fills the pre-submission offer with the real archetypes was caught by three tests,
so that guard is load-bearing rather than decorative.

**Cross-process determinism was measured, not argued.** Four separate interpreters at four
different hash seeds produced the same triples. More usefully, the reviewer **wrote its own
implementation from the specification text alone** and confirmed it reproduces both pinned
triples — which is what rules out the failure where a test's hard-coded expectation was written
to match a buggy implementation. It then checked the arithmetic by hand.

**The disclosed sampling bias was quantified exactly rather than waved through:** 0.56% total
variation distance from uniform, all 56 possible triples reachable, worst-case per-seat deviation
0.36 percentage points. The reviewer then gave a better reason than the specification's for why
it does not matter — the archetypes are shuffled onto seats by a generator statistically
independent of the session identifier, so bias in *which seat* is asked induces no bias in *which
archetype* is asked about.

**The orchestrator was wrong once, and the structure caught it.** The worker's brief demanded a
test proving no archetype appears anywhere in the pre-submission response. That is unsatisfiable
against the approved specification, which deliberately lets every seat's archetype ride the wire
in both modes and records that nulling it breaks two frontend consumers. The worker followed the
specification over the brief, said so plainly, and scoped its assertion to the quiz object — where
the real leak channel is. The reviewer confirmed the ruling and verified nothing had been nulled
or hidden to satisfy the instruction. This is recorded as ledger entry B15 rather than left in a
transcript, because a review structure that only ever catches workers is not doing its job.

**One reviewer recommendation was overruled.** It judged the concurrent-submission race
carry-forward-able because the application is local and single-user. The Director overruled: the
ticket's own acceptance criterion states first-write-wins as a property, the specification
explicitly contemplates two browser tabs, and T4 is the last backend ticket — no remaining ticket
owns the file, so deferring meant never. The fix is a conditional write that lands only while the
column still holds what the read observed, compared null-safely against the **observed value**
rather than against emptiness, so that the corrupt-value rule from ledger entry B10 survives: a
value that does not parse is still replaceable by a genuine first write.

**A test that passed against broken code nearly shipped as proof that it did not.** The worker's
first concurrency reproduction asserted on a row re-fetched from the database session instead of
one held in a local variable. The identity map holds weak references, so the row was collected,
the second caller silently re-read after the first had committed, and the test passed against the
unfixed code. The worker found this themselves and rewrote the test to hold both rows — and to
assert its own reproduction is still valid before exercising it, so a future library change makes
it fail loudly rather than pass while testing nothing. Recorded because it is the most instructive
thing that happened at this barrier.

---

## Barrier after ticket T5 — the browser learns the server's shapes

**Ticket in plain terms.** T5 is the hinge between the finished backend and the three interface
tickets. It hand-writes the TypeScript types for the two new response fields and the quiz
objects, and gives the client its two new calls. It builds no interface.

**Worker:** `implementer`, Sonnet, medium effort (pinned).
**Reviewer:** `refuter`, Sonnet, high effort (pinned). Fresh context.
**Verdict: APPROVE WITH FINDINGS** — one Minor, fixed by the Director at this barrier.

**This ticket had no test suite and no runtime validation.** The types are hand-maintained, there
is no code generation, and the generated-types file in the tree is unwired. A green compiler
proves the types are self-consistent, not that they are *true* — so the review was the only thing
standing between a mistyped field and a runtime failure three tickets later.

**Deterministic checks:**

| Check | Result |
|---|---|
| `npm run typecheck` | clean |
| `npm run build` | 72 modules, built |
| Full backend suite | `2239 passed, 2 skipped`, zero failures |

**The types were checked against real serialised JSON, not against the Python source.** The
implementer could not do this — another session holds port 8008 — and fell back to reading the
models field by field, which was sanctioned but is the weaker check. The reviewer took the route
that needs no port at all: the in-process test client this repository already uses in its own boot
probe. It captured actual JSON for a session created with no body, in each mode, restored, at the
open gate before submission, after an answered submission, and after a skipped one, plus the three
error bodies. **No divergence anywhere** — including the two cases most likely to bite, the quiz
object arriving as `null` rather than absent before the gate, and its guess list arriving empty
rather than absent.

**The compiler-enforcement decision was tested rather than assumed.** The session-creation call
takes a required mode rather than an optional one defaulting to Training, because the
specification names silently creating a Training session as how a Challenge player loses their
mode without being told. The reviewer removed the argument, confirmed the typecheck fails, then
restored the file and checked its hash matched.

**The one finding overturned the implementer's stated rationale using the file's own history.**
The incoming scored guess was typed as a bare string "to mirror the Python". The reviewer found
seven existing places where this same file deliberately tightens a closed-set backend string into
a literal union, and pointed out that the actual archetype is one of six *by construction* because
the table composition is a fixed multiset. Narrowed at this barrier; typecheck and build re-run
clean.

**One thing was correctly left alone and carried forward instead.** The new client call cannot
distinguish the quiz endpoint's three refusal statuses, because the shared response helper
discards the body and throws with only the status. That is the file's uniform convention and
imitating it was right; T8 needs to know going in, and its brief carries it.

---

## Barrier after ticket T6 — the sit-down screen, and the first thing a player sees

**Ticket in plain terms.** T6 builds the screen where a player choosing to sit down picks between
two rooms — Training, which names the opponents from the first hand, and Challenge, which withholds
those names for 200 hands — and reroutes every path that used to create a table without asking.

**Worker:** `ux-ui-designer`, Opus, high effort (pinned), across two rounds; the second round used a
fresh agent because the first's transcript was evicted after running over an hour.
**Reviewers:** `refuter`, Sonnet, high effort, on the control flow; `design-reviewer`, Opus, high
effort, with a real browser, on the visuals and accessibility. Three review passes.
**Verdict: code review APPROVE with no findings; design review FAIL, then PASS, then a plain pass on
the residuals.**

**Deterministic checks:** typecheck clean, build clean, backend suite unaffected.

**The code review was clean and did more than it was asked.** It independently verified the fourth
session-creation path the worker had found, then went looking for a fifth and established there is
exactly one call of the session-creation client function in the whole frontend. It confirmed there
is no flash of the chooser before a restore resolves by tracing the initial state values rather than
only the effect, and confirmed the double-submit guard is a synchronous check rather than a
cosmetic disabled attribute. It also confirmed the old eager-creation helper was deleted rather than
left as dead code.

**The design review is why this barrier was worth its cost.** It found eight issues, seven of them
this ticket's, none of which a typecheck or a code reviewer could have seen — and it found them by
measuring rendered pixels rather than reading tokens. The one that mattered most was an acceptance
failure rather than a matter of taste: the mode stamp behaves correctly, but was styled in the
application's own "this control is ON" idiom, with the same fill, ink and radius as the pressed
toggle sitting beside it in the same band. The specification says the stamp never becomes a switch.

**Two findings were rendering geometry, not colour.** A one-pixel line landing on a fractional
coordinate never resolves to its token value — which was silently costing one of the four
non-colour cues that distinguish the two rooms, and, once the cards' borders were raised, was
costing half of each card's perimeter too.

**The reviewer's own first framing of that second one was wrong, and the designer corrected it.**
The vertical edges were not safe, they were lucky: they pass at even viewport widths and collapse at
odd ones, so the defect was four edges rather than two. The designer also established the whole
defect is device-pixel-ratio dependent, and flagged that a re-measure at ratio 2 would show
pass-before-and-after and should not be read as a refutation — handing the next reviewer the very
thing that would make the designer look wrong. The reviewer tested both claims and upheld both,
explicitly correcting its own earlier report.

**The Director's brief was wrong once here too.** It relayed an inset-ring fix that would have had
to be repeated across five box-shadow declarations, all inside a transition, and would therefore
have animated on hover. The designer rejected it with that reason and doubled the border instead.

**Two defects were closed by deleting something.** The screen's own background wash was both
darkening text to within one hundredth of its floor and rendering as the panel box its comment said
it was not. Removing it fixed both. The reviewer's judgment on that is worth keeping: the wash was
not carrying atmosphere, it was carrying a second rectangle, and by lightening the ground it was
flattening the very shadows meant to create depth.

**A comment that asserted something false was fixed rather than annotated**, per the standard. It
claimed the shell already paints a glow behind every route; the shell paints nothing. The deletion
it justified was still correct, for a measurable reason the comment now states instead.

**One item was correctly attributed away from this ticket.** The application shell overflows
horizontally at phone widths. The worker said so, and the reviewer verified it by reproducing the
identical overflow on a route this slice never touches rather than accepting the claim.
