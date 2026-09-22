# Browser walk-through r2 — P4 diff (design-reviewer with Playwright, Opus, 2026-09-22)

Returned inline (review-only agent) and saved verbatim by the Director. Run against an isolated
stack from the worktree on ports 8125/7781 with its own database; the owner's stack on 8008/7777
was never touched. Screenshots were deleted after the run; nothing entered the repo.

VERDICT: FAIL — one blocking defect. Spec items 8–12 otherwise verified and correct.

1. **blocking** — The stale notice survives leaving the table and reappears on a brand-new session. Observed: notice up → press Leave table (HTTP 204, clean leave) → sit-down screen → take a seat → the line "Acted elsewhere — table refreshed." is rendered on session `f7ae7a92…`, hand 1, first decision, with no 409 anywhere in the backend log after the leave. Cause: `setNotice(null)` exists only in `run`'s success path (`SimulateView.tsx:699`); `leaveTable` (`:806-833`), `clearStored` (`:538-547`) and `askForMode` (`:564-569`) never clear it. Fix: clear it in the teardown path every table exit already calls.
2. **pass** — Current-session boot: with localStorage cleared (a second device), reload landed on the same table — session `5c256ad8…`, hand 1, A♦4♣, SB 103.62bb — and rewrote the storage key; `/session/current` is 404 with no session and is not shadowed by `/session/{id}`.
3. **pass** — Stale-write recovery end to end: `POST …/action?state_token=1.6` → 409, table refreshed to the post-fold state, `<p class="sim-stale-notice" role="status">Acted elsewhere — table refreshed.</p>`, and the notice cleared on the next successful write (deal, hand 1 → 2).
4. **pass** — Watch-off fold path, the case that would refuse its own deal: `action?state_token=2.5` → 200, then the chained `hand?state_token=2.7` → 200, i.e. the deal carried the fold response's token; hand advanced 2 → 3, no 409, no error panel.
5. **pass** — Leave semantics: stale `leave?state_token=3.4` → 409 with the session still active (`/session/current` still 200) and the notice shown, not ended; second Leave → 204, sit-down screen, storage cleared; the other device's next action then → 404 (session-not-found recovery).
6. **pass** — Phone 915×412: dock and both buttons measured identical with and without the notice (dock `y=351 h=61`; buttons `y=360 h=44`); notice fixed at `y=241…280`, fully inside the viewport, `pointer-events: none` (hit-test at its centre returns the element beneath), no overlap, no horizontal scroll. All 13 writes carried `state_token` (zero tokenless), exactly 3 × 409, all intentional. Notice contrast 16.07:1 night / 15.24:1 day (AA needs 4.5:1). No JavaScript console errors.

Servers NOT stopped by the reviewer: the sandbox denies `kill`, `ps` and `pgrep`, so `scripts/serve.sh stop` could not signal anything. Left listening: backend uvicorn PIDs 59019 (reloader) and 59023 (worker) on :8125, frontend vite PID 59027 on :7781.
