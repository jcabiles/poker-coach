# N6 — LLM coach: on-demand "Explain this" (spec)

_Epic 3 · supersedes R7. Interview locked 2026-07-18 (see `simulate-n6-n7-decisions` memory)._

## Goal

Turn a graded Simulate decision into a plain-language **concept + fix**. An on-demand
"Explain this" button on each recap row calls a **swappable `CoachProvider`**: an Anthropic
Claude API when a key is configured, else a deterministic **templated fallback** built from the
already-authored `content/` rationale. Explanation is **live-per-request only** — no persistence,
no migration (matches R7's stated no-go on reload-durable reasoning).

## Interview decisions (locked)

- **Engine:** Claude API behind a `CoachProvider` seam + templated fallback. Fallback is the
  default when `ANTHROPIC_API_KEY` is unset, so tests + offline both work.
- **Trigger:** on-demand button per graded decision in the recap (not auto). Bounded cost, no
  mid-hand latency; lives inside the N2 coach-mode surface (SimRecap only renders in coach mode).
- **Privacy:** the prompt is built from **hero-only** context (hero hole cards, public board,
  the grade). The guarantee is **field-selection, not FE-state absence**: at `hand_over` the FE's
  `hand` object *does* hold villain showdown cards (same render scope as SimRecap), so the payload
  must be assembled by **explicitly picking** hero-only fields (`street`, `chosen_action`,
  `hero_cards`, `board`, …) — **never by spreading `hand`**. `CoachExplainRequest`/`CoachContext`
  have **no villain slot**, so villain cards have no channel into the prompt regardless of what the
  parent holds. A pinned-fields comment at the call site guards against a future payload widening.

## Design

### Backend seam — `app/services/coach.py` (new)

Coach is inherently an I/O concern (outbound HTTP) ⇒ it lives in **services**, not `app/domain/`
(domain-purity invariant). Mirrors the `StrategyProvider` singleton discipline
(`sim_session._grading_provider()`): one instance, lazy getter.

- `CoachContext` — frozen dataclass carrying hero-only fields:
  `street, chosen_action, correctness, sizing_correctness, ev_loss_bb, coverage, node_context,
  position, facing_position, verdict, reasoning, hero_cards: tuple[str,str] | None,
  board: tuple[str, ...]`. **No villain field exists** (privacy by construction).
- `CoachProvider` Protocol: `name: str`; `async def explain(self, ctx: CoachContext) -> str`.
- `TemplateCoach` — pure, deterministic. **Does not depend on `ctx.reasoning`** — it is `None` for
  every row after any reload (documented `restore_session`/`_grade_view` behavior) and for optimal
  rows on the live path, so the fallback must stand on the always-present structured fields.
  Composes a "**Concept** … **Fix** …" paragraph from `correctness` + `node_context`/street +
  `chosen_action` + `position`/`facing_position` + `ev_loss_bb` (a correctness-keyed scaffold:
  optimal → why the line is standard here; mistake/blunder → the leak + the corrective action).
  When `ctx.reasoning` **is** present it is folded in as an extra sentence (enrichment, not the
  spine), so the fallback never contradicts the live verdict. Non-tautological in all cases,
  including `reasoning=None`. `name="template"`.
- `AnthropicCoach` — `name="anthropic"`. Builds a system + user prompt from `ctx`, POSTs to
  `https://api.anthropic.com/v1/messages` via **stdlib `urllib.request`** (no new dependency —
  `httpx`/`anthropic`-SDK would be ask-first) inside `asyncio.to_thread` (blocking call off the
  event loop). Reads `ANTHROPIC_API_KEY` and optional `ANTHROPIC_MODEL` (default
  `claude-haiku-4-5-20251001` — cheap, short outputs; user overrides for quality) from
  `os.environ`. Timeout (~15s). Any failure (no key mid-call, network, non-200, parse) **raises**.
- `get_coach() -> CoachProvider` — singleton: `AnthropicCoach` iff `ANTHROPIC_API_KEY` is set,
  else `TemplateCoach`.
- `async def explain_decision(ctx) -> tuple[str, str]` — calls `get_coach().explain(ctx)`; on any
  exception falls back to `TemplateCoach().explain(ctx)`. Returns `(text, source)` where source ∈
  `{"anthropic","template"}`. **Always returns usable text** — the button never hard-errors.

Prompt discipline: EV framing stays "≈ approximate (heuristic)", never solver-grade; asks for
≤~120 words, plain language, one concept + one concrete fix. Hero-only facts only.

### Endpoint — `app/api/v1/simulate.py`

`POST /simulate/{session_id}/explain` → `CoachExplainView`. Mirrors the reveal/chart endpoints:
404 reserved for `SessionNotFound`; everything else is a 200 body. Adds a small
`sim_session.assert_session_active(db, session_id, owner_id) -> None` (raises `SessionNotFound`,
reuses the private `_get_session`) so the router keeps the established `except SessionNotFound`
idiom instead of an ad-hoc None-check. The endpoint needs **no current hand** — it grades from the
request body, so a session between hand transitions is still a 200. Builds `CoachContext` from the
request, returns `CoachExplainView(explanation, source)`.

- `CoachExplainRequest` (schema) — the hero-only grade context the FE is displaying:
  `street, chosen_action, correctness, sizing_correctness, ev_loss_bb, coverage, node_context,
  position, facing_position, verdict, reasoning, hero_cards, board`.
- `CoachExplainView` — `explanation: str`, `source: str`.

### Frontend

- `SimRecap.tsx` — add an "Explain this" button per row (coach-mode already gates the component).
  On click: POST the row's context (+ hero cards + board from the parent SessionView) → render the
  returned text in an expandable `<p className="sim-recap-explain">` with loading + error states.
  Button available on any row (miss or not — "why was this optimal" is valid). One row's request
  in flight at a time per row; result cached in component state until the hand changes.
- `SimulateView.tsx` — pass `heroCards` + `board` into `SimRecap`; reset explain-state on the same
  hand-transition boundary the recap already resets on.
- `api/client.ts` + `api/types.ts` — add `explainDecision(...)` client fn + `CoachExplainRequest`/
  `CoachExplainView` interfaces (hand-maintained, both sides synced).
- Tokens-only CSS for the button + explanation block; AA contrast + visible focus both themes.

## Pass / fail

1. With **no `ANTHROPIC_API_KEY`**, the endpoint returns a non-empty explanation with
   `source="template"` for a graded decision (offline-deterministic test).
2. `explain_decision` **falls back to template** when the primary coach raises (monkeypatch
   `AnthropicCoach.explain`/`urlopen` to raise → source flips to `"template"`, text still returned).
3. `get_coach()` returns `TemplateCoach` when the key is unset and `AnthropicCoach` when set
   (monkeypatch `os.environ`).
4. **Privacy:** `CoachExplainRequest`/`CoachContext` carry **no villain-card field**; a test asserts
   the prompt string built by `AnthropicCoach` from a populated context contains hero cards/board
   but no villain hole cards (there is no channel for them).
5. Endpoint 404s only on a missing/ended session; a valid session returns 200 with text.
6. Template fallback text is **non-tautological** — references the node/action/correctness (not
   just "good decision"), **including when `reasoning=None`** (the reload/optimal-row default):
   a test builds a `CoachContext` with `reasoning=None` and asserts the output names the
   node_context + chosen_action + correctness.
6b. FE call site assembles the payload by **explicit field-picking** from `hand`/grade (pinned by a
   comment), never spreading `hand`; the picked fields carry no villain slot.
7. FE: coach mode shows an "Explain this" button per recap row; click renders coaching text;
   loading + error states exist; AA + focus both themes; typecheck + build green.
8. `verify.sh` green; **no migration, no new dependency, no `spot_signature()` / grader / pin
   change** (coach never touches grading).

## No-gos

- No persistence of explanations (no migration, no `sim_decision` column) — live per request.
- No new top-level dependency (stdlib `urllib` only; `anthropic`/`httpx` runtime = ask-first).
- No villain hole cards in any prompt/payload.
- No solver claims; EVs stay approximate-labeled.
- Coach never mutates grading, signatures, or content packs — read-only over the grade context.
- No auto-fire; no per-street/global coach toggle beyond the existing N2 coach-mode gate.
