import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import {
  getSession,
  leaveSession,
  postHeroAction,
  postNextHand,
  postSimulateSession,
} from "../api/client";
import type { ActionType, SessionView } from "../api/types";
import SimActionBar from "./simulate/SimActionBar";
import SimEventLog from "./simulate/SimEventLog";
import SimLedger from "./simulate/SimLedger";
import SimShowdown from "./simulate/SimShowdown";
import SimSpeedPicker, { type SimSpeed } from "./simulate/SimSpeedPicker";
import SimTable from "./simulate/SimTable";

// Simulate S9 — the playable, persistent table. Hero acts via predetermined
// -sizing buttons; bots resolve instantly (server-side, within each request),
// so every rendered view sits at a hero-decision boundary or hand-over. Stacks
// carry over, a per-seat net-BB ledger tracks P&L, and a browser reload
// restores the exact live decision point via a persisted session_id.
//
// PokerTable stays the drill/quiz render primitive; the felt here is the
// simulate-scoped SimTable (same room, richer per-seat data S9 owns). No
// villain hole cards ever render except at showdown (structural on the wire —
// re-checked in SimTable/SimShowdown).

const STORAGE_KEY = "simulate.session_id";
const SPEED_KEY = "simulate.speed";

// The client's json<T>() throws Error("<url> -> <status>") on non-2xx, so a
// lost/ended session surfaces as a message ending "-> 404".
function isSessionNotFound(err: unknown): boolean {
  return err instanceof Error && / -> 404$/.test(err.message);
}

// ── Client-side pacing (S11) ────────────────────────────────────────────────
// The server resolves every bot action synchronously and returns them in one
// `events` batch; there is no server pacing hook. Pacing is a pure client-side
// replay: a shared `stagedIndex` counts how many of the batch's events are
// "revealed" so far, and drives BOTH the log (which lines are visible) and the
// felt (which seats show their resolved fold/all-in/chips state). The index
// walks up on a timer whose per-step delay depends on the speed setting.

// Base bot delay window at "normal" (ms). Each step picks a uniform-random
// value in [MIN, MAX] so the table's rhythm reads human, never metronomic.
const NORMAL_MIN = 500;
const NORMAL_MAX = 1500;
// "fast" runs the same window proportionally quicker; "instant" = no delay.
const FAST_FACTOR = 0.4;

function readSpeed(): SimSpeed {
  try {
    const v = window.localStorage.getItem(SPEED_KEY);
    if (v === "normal" || v === "fast" || v === "instant") return v;
  } catch {
    /* private-mode storage — fall through to default */
  }
  return "normal";
}

function prefersReducedMotion(): boolean {
  try {
    return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  } catch {
    return false;
  }
}

// Delay before revealing the NEXT staged event, given the effective speed.
// reduced-motion collapses to instant regardless of the stored setting.
function stepDelayMs(speed: SimSpeed): number {
  if (speed === "instant" || prefersReducedMotion()) return 0;
  const span = NORMAL_MAX - NORMAL_MIN;
  const base = NORMAL_MIN + Math.random() * span;
  return speed === "fast" ? base * FAST_FACTOR : base;
}

export default function SimulateView() {
  const [view, setView] = useState<SessionView | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false); // any in-flight action/deal
  const busyRef = useRef(false); // sync guard against click bursts
  const sessionIdRef = useRef<string | null>(null);

  // Speed setting (client-only, localStorage). Drives the pacing delays. Held
  // in a ref too so the running playback timer reads the LIVE speed on each step
  // — a mid-batch change takes effect on the next reveal without rewinding.
  const [speed, setSpeed] = useState<SimSpeed>(readSpeed);
  const speedRef = useRef<SimSpeed>(speed);
  const changeSpeed = useCallback((next: SimSpeed) => {
    speedRef.current = next;
    setSpeed(next);
    try {
      window.localStorage.setItem(SPEED_KEY, next);
    } catch {
      /* private-mode storage — setting still applies this session */
    }
  }, []);

  // Pacing state: how many of the current batch's events are revealed. The felt
  // (SimTable) and the log (SimEventLog) both read this so a seat never shows
  // its resolved state before the log narrates that seat's action. Held in a
  // ref too so the recursive step timer reads the live value without re-arming.
  const [stagedIndex, setStagedIndex] = useState(0);
  const stagedRef = useRef(0);
  const timerRef = useRef<number | null>(null);

  const setStaged = useCallback((n: number) => {
    stagedRef.current = n;
    setStagedIndex(n);
  }, []);

  const clearTimer = useCallback(() => {
    if (timerRef.current != null) {
      window.clearTimeout(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  const events = view?.hand?.events ?? null;
  const eventCount = events?.length ?? 0;

  // Playback engine: whenever a new batch arrives, replay it one event at a time
  // on the speed-scaled timer. A fresh batch (new view) restarts from 0; the
  // timer walks stagedIndex up to eventCount, then stops. instant/reduced-motion
  // yields a 0ms first step so the whole batch reveals in one frame. Any new
  // batch or unmount clears the pending timer (no interval leaks).
  useEffect(() => {
    clearTimer();
    if (eventCount === 0) {
      setStaged(0);
      return;
    }

    // Instant / reduced-motion: reveal the whole batch in one commit — no
    // per-step timer, and no one-frame flash of the pre-reveal (all-live) felt.
    if (stepDelayMs(speedRef.current) === 0) {
      setStaged(eventCount);
      return;
    }

    setStaged(0);
    const step = () => {
      const next = stagedRef.current + 1;
      setStaged(next);
      if (next < eventCount) {
        timerRef.current = window.setTimeout(step, stepDelayMs(speedRef.current));
      } else {
        timerRef.current = null;
      }
    };
    timerRef.current = window.setTimeout(step, stepDelayMs(speedRef.current));

    return clearTimer;
    // Restart the batch only when a NEW events array arrives (fresh object
    // identity per view). Speed is read live from speedRef inside `step`, so a
    // mid-batch speed change takes effect on the next step WITHOUT rewinding —
    // that's why `speed` is deliberately not a dependency of this effect.
  }, [events, eventCount, clearTimer, setStaged]);

  const playing = eventCount > 0 && stagedIndex < eventCount;

  // Lockstep map for the felt: position → the 1-based staged-index threshold at
  // or above which that seat's LAST action in this batch has been narrated. A
  // seat reveals its resolved status (fold-dim / all-in / chips-in-front) only
  // once stagedIndex reaches its threshold — so the felt never shows a seat's
  // final state before the log line that explains it. Positions absent from the
  // batch (hero, seats settled before it) get no entry → revealed immediately.
  const revealAt = useMemo(() => {
    const m = new Map<string, number>();
    if (events) events.forEach((e, i) => m.set(e.position, i + 1));
    return m;
  }, [events]);

  // Adopt a session view: hold its id (both in a ref for callbacks and in
  // localStorage for reload restore) and render its hand.
  const adopt = useCallback((res: SessionView) => {
    sessionIdRef.current = res.session_id;
    try {
      window.localStorage.setItem(STORAGE_KEY, res.session_id);
    } catch {
      // Private-mode / disabled storage: play still works this session, only
      // reload-restore is lost. Non-fatal.
    }
    setView(res);
  }, []);

  const clearStored = useCallback(() => {
    sessionIdRef.current = null;
    try {
      window.localStorage.removeItem(STORAGE_KEY);
    } catch {
      /* non-fatal */
    }
  }, []);

  // Create a fresh session and adopt its first hand.
  const startSession = useCallback(async () => {
    adopt(await postSimulateSession());
  }, [adopt]);

  // Mount: try to restore a stored session; on 404 (missing/ended) clear it and
  // deal a fresh one. StrictMode double-invokes effects in dev; the cancelled
  // flag keeps the later resolve from clobbering state.
  useEffect(() => {
    let cancelled = false;
    setError(null);
    const stored = (() => {
      try {
        return window.localStorage.getItem(STORAGE_KEY);
      } catch {
        return null;
      }
    })();

    const boot = async () => {
      if (stored) {
        try {
          const res = await getSession(stored);
          if (!cancelled) adopt(res);
          return;
        } catch (e) {
          if (!isSessionNotFound(e)) throw e;
          // Stale/ended session — fall through to a fresh one.
          clearStored();
        }
      }
      if (!cancelled) await startSession();
    };

    boot().catch((e) => {
      if (!cancelled) setError(e instanceof Error ? e.message : String(e));
    });
    return () => {
      cancelled = true;
    };
  }, [adopt, clearStored, startSession]);

  // Shared runner for hero actions / deals: a sync ref guard (state is async —
  // a same-tick burst would slip past a state-only check), 404 recovery, and
  // error surfacing. `op` returns the new view (or starts fresh on a lost
  // session).
  const run = useCallback(
    async (op: (id: string) => Promise<SessionView>) => {
      if (busyRef.current) return;
      const id = sessionIdRef.current;
      if (!id) {
        // No live session (first-visit race) — create one instead.
        busyRef.current = true;
        setBusy(true);
        setError(null);
        try {
          await startSession();
        } catch (e) {
          setError(e instanceof Error ? e.message : String(e));
        } finally {
          busyRef.current = false;
          setBusy(false);
        }
        return;
      }
      busyRef.current = true;
      setBusy(true);
      setError(null);
      try {
        try {
          adopt(await op(id));
        } catch (e) {
          if (isSessionNotFound(e)) {
            clearStored();
            await startSession();
          } else {
            throw e;
          }
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
      } finally {
        busyRef.current = false;
        setBusy(false);
      }
    },
    [adopt, clearStored, startSession],
  );

  const decide = useCallback(
    (action: ActionType, sizeBb?: number | null) => {
      // Hero-fold shortcut: the hero has no more decisions this hand, so there
      // is nothing to pace for them — skip the bot playback entirely and deal
      // the next hand in the same turn. Cancel any residual timer first so a
      // fold mid-playback of a prior batch can't leave a stray reveal running.
      if (action === "fold") {
        clearTimer();
        void run(async (id) => {
          await postHeroAction(id, { action });
          return postNextHand(id);
        });
        return;
      }
      void run((id) =>
        postHeroAction(id, sizeBb != null ? { action, size_bb: sizeBb } : { action }),
      );
    },
    [run, clearTimer],
  );

  const nextHand = useCallback(() => {
    // Dealing a fresh hand after hand_over must cancel any residual playback
    // timer from the just-finished hand's final batch before the new view lands.
    clearTimer();
    void run((id) => postNextHand(id));
  }, [run, clearTimer]);

  // Leave the table: end it server-side, clear storage, deal a fresh session so
  // the tab keeps working. A lost session (already 404) is treated as success.
  const leaveTable = useCallback(async () => {
    if (busyRef.current) return;
    busyRef.current = true;
    setBusy(true);
    setError(null);
    const id = sessionIdRef.current;
    try {
      if (id) {
        try {
          await leaveSession(id);
        } catch (e) {
          if (!isSessionNotFound(e)) throw e;
        }
      }
      clearStored();
      await startSession();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      busyRef.current = false;
      setBusy(false);
    }
  }, [clearStored, startSession]);

  const hand = view?.hand ?? null;

  return (
    <section className="simulate">
      <div className="sim-topbar">
        <h1 className="sim-heading">Simulate</h1>
        {view && (
          <div className="sim-topbar-controls">
            <SimSpeedPicker speed={speed} onChange={changeSpeed} />
            <button
              type="button"
              className="btn sim-leave-btn"
              onClick={leaveTable}
              disabled={busy}
            >
              Leave table
            </button>
          </div>
        )}
      </div>

      {error && (
        <div className="panel bad-bg">
          Error: {error}. Is the backend running on :8008?
        </div>
      )}

      {hand ? (
        <div className="sim-layout">
          <div className="sim-main">
            <SimTable hand={hand} stagedIndex={stagedIndex} revealAt={revealAt} />

            {hand.is_hero_turn && (
              <SimActionBar
                legalActions={hand.legal_actions}
                disabled={busy || playing}
                onDecide={decide}
              />
            )}

            {hand.hand_over && (
              <SimShowdown
                showdown={hand.showdown}
                seats={hand.seats}
                onNextHand={nextHand}
                dealing={busy || playing}
              />
            )}

            {!hand.is_hero_turn && !hand.hand_over && (
              <p className="sim-waiting" role="status">
                Waiting on the table…
              </p>
            )}
          </div>

          <aside className="sim-side">
            <SimEventLog events={hand.events} stagedIndex={stagedIndex} />
            <SimLedger seats={hand.seats} />
          </aside>
        </div>
      ) : (
        !error && (
          <div className="panel simulate-empty" role="status">
            Taking a seat…
          </div>
        )
      )}
    </section>
  );
}
