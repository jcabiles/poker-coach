# Poker Coach — local NLHE trainer

A local web app to drill and train live No-Limit Texas Hold'em strategy, tailored
for the $1/$2 → $2/$3 climb. Simplified-but-sound (not pure GTO), preflop first.

Plan: `docs/ai-dlc/roadmap.md` · Strategy research: `docs/research/` · Spec/tickets: `docs/ai-dlc/`.

## Quickstart
After cloning, run these once — then `poker-coach` launches the app from anywhere in the repo:
```bash
# 1. one-time setup (Python ≥ 3.12, Node ≥ 20)
cd backend  && python -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]" && cd ..
cd frontend && npm install && cd ..

# 2. install direnv (the tool that exposes the `poker-coach` command), once per machine
brew install direnv                             # macOS; see direnv.net for other OSes
echo 'eval "$(direnv hook zsh)"' >> ~/.zshrc     # or ~/.bashrc for bash — then restart the shell

# 3. trust this repo's .envrc (once per clone)
direnv allow .

# 4. run it
poker-coach            # start backend :8008 + frontend :7777 in the background
poker-coach stop       #   stop / restart / status also work
```
Open <http://localhost:7777>. No direnv? Use `./scripts/serve.sh start` instead — same launcher. Full details below.

## Layout
```
backend/   FastAPI API + pure domain core + SQLite/Alembic
frontend/  React + Vite
content/   strategy content packs + JSON schema
docs/      research, roadmap, specs, tickets
bin/       poker-coach  (global launcher, via direnv)
scripts/   serve.sh, verify.sh
```

## Architecture (why it scales)
- **Pure domain core** (`backend/app/domain/`) — Spot, Decision, EvaluationResult,
  content packs, SRS, leaks. No web/DB imports (enforced by a test).
- **Swappable `StrategyProvider`** — grading is one async interface. Today a
  heuristic provider; a solver-table provider drops in later with no rebuild.
- **Strategy as versioned data** — ranges live in content packs, not code.
- **Freq + EV results, never boolean** — feedback/SRS/leaks all consume the rich shape.

## Screenshots
| Preflop trainer | Facing aggression | Exploit archetypes | Postflop equity |
| --- | --- | --- | --- |
| ![Preflop trainer](docs/assets/preflop-trainer.png) | ![Facing aggression](docs/assets/facing-aggression.png) | ![Exploit archetypes](docs/assets/exploit-archetypes.png) | ![Postflop equity](docs/assets/postflop-equity.png) |

## Setup & run

Install and run steps live in [Quickstart](#quickstart) above — venv + `pip install -e ".[dev]"`,
`npm install`, direnv, then `poker-coach` (or `./scripts/serve.sh start` without direnv).

API health: `http://localhost:8008/api/v1/health` · interactive docs at `/docs`.

> Override ports with `BACKEND_PORT=8123 FRONTEND_PORT=5200 poker-coach`. Logs
> stream to `.backend.log` / `.frontend.log` at the repo root.

Or run separately (two terminals):
```bash
# backend — API on :8008
cd backend && uvicorn app.main:app --port 8008 --reload
# frontend — UI on :7777
cd frontend && npm run dev
```

**Checks — one gate, same locally and in CI:**
```bash
make check            # format check + lint + type check + tests, both halves
make check-backend    # ruff format --check · ruff check · mypy app · ./scripts/verify.sh
make check-frontend   # biome format · biome ci · tsc --noEmit · vitest run · vite build
make fix              # apply ruff format, ruff check --fix, biome check --write
```
Backend deps are locked in `backend/uv.lock` (`cd backend && uv sync --extra dev` creates
`.venv`; `pip install -e ".[dev]"` still works). Commit hooks: `backend/.venv/bin/pre-commit install`.

### Play from your phone

Start the stack with the `--lan` flag, through either entry point:
```bash
./scripts/serve.sh start --lan
# or, with direnv set up:
poker-coach start --lan
```

> `--lan` makes the frontend dev server listen on the home wifi instead of only on the Mac. The
> script prints the address to open on the phone once the stack is ready. Type that printed
> address exactly, as a raw IP (for example `http://192.168.1.42:7777`) — the dev server refuses
> hostnames it does not recognise, so `http://mac.local:7777` returns "Blocked request. This host
> is not allowed."
>
> On the phone, open that address in Chrome, then use Chrome's menu → **Add to Home screen** to
> get an app-like icon.
>
> The phone only works while the Mac is running the stack — closing the laptop lid or running
> `stop` takes the phone with it. The router can also hand the Mac a new address later (after a
> reboot or a long idle period), which breaks the saved home-screen shortcut until it is recreated
> from the newly printed address. The first time `--lan` runs, macOS may prompt to allow incoming
> network connections for Node — allow it, or the phone cannot reach the server.
>
> **The honest boundary.** The backend's own port (8008) stays bound to the Mac and is never
> reachable from another device, `--lan` or not. But the frontend port (7777) forwards every
> request under `/api` to that backend regardless of which network interface it arrived on — so
> while `--lan` is on, the *entire unauthenticated API* is reachable from anything on the home
> wifi, not just the trainer's UI. That is acceptable here because the home network is trusted and
> this app has no user accounts, but it is a real exposure, not a cosmetic one: don't run `--lan`
> on a network you don't trust. The flag is off by default — a plain `start` (or `poker-coach`
> with no arguments) listens on loopback only — and `status` reports which of the two states the
> running server is in.

### Always on

Install the login agent once, in a plain terminal:
```bash
./scripts/always_on_install.sh
```

> This writes a launchd user agent (macOS's own "run this for me" mechanism) to
> `~/Library/LaunchAgents/com.poker-coach.serve.plist` and loads it. From then on macOS runs
> `scripts/serve.sh --lan start` at login and again every five minutes. The launcher is a no-op
> when the stack is already up, so the repeat costs nothing and is exactly what brings the stack
> back after the Mac sleeps, after a crash, or after a stray `stop` — within five minutes, without
> you touching a terminal.
>
> Its output lands in `local/always-on/launchd.log` (both streams, appended). launchd will not
> create that directory; the installer does — so re-run the installer if you ever delete `local/`.
> Re-running it is safe at any time and is also how you pick up an edited plist.
>
> Remove it with `./scripts/always_on_uninstall.sh`. That unloads the agent and deletes the plist
> but leaves a running stack alone; stop that yourself with `scripts/serve.sh stop`.
>
> **Four things to know before you install.**
> 1. Run the installer from your main checkout (`~/Documents/Github/poker-coach`), not from a
>    worktree — a worktree is deleted when its branch merges, and the agent would then fire at a
>    path that no longer exists. The installer refuses a worktree for that reason.
> 2. Start the stack by hand once with `scripts/serve.sh --lan start` before installing, so you are
>    at the keyboard for macOS's "allow incoming connections for Node" prompt. The agent's first run
>    can raise it with nobody there to click it, and until it is accepted the phone cannot connect.
> 3. If you hand-start the stack *without* `--lan`, the agent cannot fix it: every five minutes the
>    launcher exits 1 with "already running, but frontend is loopback only", and the phone stays
>    locked out until you run `scripts/serve.sh restart --lan` yourself.
> 4. A backend started by the agent has no `ANTHROPIC_API_KEY` — the plist carries only `PATH`, and
>    a key is never written into a plist — so the coach falls back to its template prose for as long
>    as that backend process lives. A stack you start by hand from a shell that loaded the key keeps
>    the live coach.
>
> **What you are accepting.** The agent always starts with `--lan`, so with it installed the
> entire unauthenticated API is reachable from anything on the home wifi whenever the Mac is awake
> — not just while you remember you started it. See **The honest boundary** above for exactly what
> that exposes. Don't install this on a Mac that joins networks you don't trust.

## Status
**Phase 0** (foundations) complete & verified. **Phase 1a** (real preflop trainer) built:
research-backed ranges for RFI / facing-an-open / blind defense / vs-limpers, frequency-tolerant
grading, SM-2 spaced repetition, auto leak tracking, drill modes (random / review / leak-focus),
and a lean React UI (multi-action bar, mode selector, colored 13×13 grid, stats strip).
**Phase 1b** adds facing-aggression (vs-3-bet 4bet/call/fold, vs-4-bet jam/call/fold) + a
betting-line display + light stack-depth variety. **Phase 1c** adds exploit / villain-archetype drills
(calling station / nit / LAG / fish) with a GTO-vs-exploit contrast on high-leverage nodes.

**Phase 2a — first postflop slice — built & verified (128 backend tests green):** a pure-Python
equity engine (7-card evaluator + Monte-Carlo `equity_vs_range` with dead-card filtering), a
rule-based board-texture classifier, a dedicated flop **c-bet grader** (texture + positional
range-advantage heuristic, *not* equity-backed — that's 2b), a `CompositeProvider` routing by street
(preflop → heuristic, flop → postflop), a flop-c-bet drill mode, and two foundational quizzes
(board-texture classification, equity estimation) with tolerance-band grading. Postflop spots get a
texture/SPR-bucketed signature; preflop hashes are byte-identical to before. No new DB migration.

**Phase 2b — facing a flop c-bet (defense) — built & verified (141 backend tests green):** the other
side of the 2a spot — hero (BB) defends vs a flop c-bet with **fold / call / raise (check-raise)**,
graded by a defender-perspective range-advantage rule + `grade_vs_cbet` (texture + range advantage +
pot-odds/MDF + a bet-size term), a `vs_cbet` spot builder + drill mode, and a **faced-bet bucket** in
the postflop signature so small vs big c-bets stay in separate SRS items. Still not equity-backed; no
new DB migration.

**Phase 2c — postflop SRS review — built & verified (148 backend tests green; migration 0004):** the
flop **c-bet** and **vs-c-bet** spots now re-surface in `mode=review` via SM-2, keyed on their
texture/SPR/faced-bet archetype. `srs_item` gains 4 nullable postflop columns; `record_attempt`
persists + backfills them; `_rebuild_postflop` reconstructs a due archetype from the 2a/2b builders; a
`Spot.srs_signature` override guarantees the due row graduates even when reconstruction is approximate.
This closes the core *surface → drill → re-surface until mastered* loop for postflop.

**Phase 2d — equity-backed range advantage — investigated, then deferred to Phase 3.** A bounded
Monte-Carlo over the simplified ranges can't recover a stable range-advantage signal (mean equity is
flat ~0.5; combo-share is range-width-biased; top-of-range strength is noisy/counterintuitive) — real
range advantage is a solver/EV property. The stable positional+texture heuristic was kept; the swap to
solver-backed range advantage lands in Phase 3 behind the existing `StrategyProvider`. (FeedbackPanel
polish — per-action sizes — shipped.)

**Phase 2e-0 — foundational fixes — built & verified (163 backend tests green):** paydown before
turn/river. There was no street-level dispatch past preflop — a turn/river spot would be silently
graded as a flop. Fixed: the postflop provider now street-gates to the flop (turn/river →
`NOT_FOUND`); `faced_bet_bucket` is raise-aware (reads the current `CALL`, subtracting hero's prior
street investment) instead of scanning history for a max bet; `_hand_category` now detects made
straights/flushes AND demotes plain top pair from `strong` to `weak_made` (a live bug that had
`grade_vs_cbet` recommending "never fold" with a marginal top pair); all `texture.classify()` call
sites slice `board[:3]` explicitly. No new migration.

**Phase 2e-1 — facing a flop check-raise — built & verified (183 backend tests green):** hero c-bet,
the defender check-raised, and hero (the original aggressor) decides **fold / call / raise (sized
4-bet)**. `grade_vs_check_raise` encodes the live-$1/$2 read that *check-raises are rarely bluffs* as a
markedly higher fold baseline than the c-bet-defense grader — modulated (not overridden) by texture, so
air still folds on dry boards. A `build_check_raise_spot` builder (with the correct *incremental* call
size — `raise_to − cbet`, not the raw raise total), a `vs_check_raise` drill mode + SRS-review
reconstruction, leak `VS_CHECK_RAISE=202`, and a frontend mode + a street-scoped betting-line fix (a
flop check-raise no longer mislabels as a preflop "3-bet"). Closes the flop c-bet loop. No new migration.

Next: turn play (2nd barrel, needs street-aware texture) → facing a turn bet → river value/bluff →
facing a river bet → multiway → full-hand mode. Sequenced one-epic-per-session in `docs/ai-dlc/roadmap.md`
(§ Phase 2), with the contract scan in `docs/ai-dlc/contracts/postflop-turn-river.md`.

## How this was built
Developed with an AI-assisted, spec-first workflow: each phase started from written research and a
delta spec (`docs/`), was broken into tickets, then implemented and verified against tests before the
next phase. The architecture (pure domain core, swappable strategy provider, content-as-data) was
chosen up front so later phases extend rather than rewrite.
