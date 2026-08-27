import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import {
  getReveal,
  getSession,
  getVillainRange,
  leaveSession,
  postHeroAction,
  postNextHand,
  postSimulateSession,
} from "../api/client";
import type {
  ActionType,
  GradeView,
  HandReplayView,
  RevealedSeatView,
  SessionView,
  SimMode,
  VillainRangeView,
} from "../api/types";
import HandReplay from "./simulate/HandReplay";
import SimActionBar from "./simulate/SimActionBar";
import SimEventLog from "./simulate/SimEventLog";
import SimGradingToggle from "./simulate/SimGradingToggle";
import SimLabelsToggle from "./simulate/SimLabelsToggle";
import SimLedger from "./simulate/SimLedger";
import SimModeChoice from "./simulate/SimModeChoice";
import SimPostflopChart from "./simulate/SimPostflopChart";
import SimRangeChart from "./simulate/SimRangeChart";
import SimRecap from "./simulate/SimRecap";
import SimShowdown from "./simulate/SimShowdown";
import SimSpeedPicker, { type SimSpeed } from "./simulate/SimSpeedPicker";
import SimWatchToggle from "./simulate/SimWatchToggle";
import SimStreetReport from "./simulate/SimStreetReport";
import SimTable from "./simulate/SimTable";
import SimVillainRange from "./simulate/SimVillainRange";
import { stagedTableState } from "./simulate/simPlayback";

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
const WATCH_KEY = "simulate.watch";
const COACH_KEY = "simulate.coachMode";

// ── Two-mode Simulate (T7) ──────────────────────────────────────────────────
// Completed hands a Challenge table plays before the blind check bars the deal,
// which is what the "Hand N / 200" counter counts towards. This is the client's
// OWN copy of the backend's `BLIND_CHECK_HAND_GATE`
// (backend/app/services/sim_session.py) — the threshold is deliberately not on
// the wire, because the approved contract names exactly two new session fields
// and a third would be an unapproved deviation (finding ledger B11). Divergence
// between the two literals is cosmetic: the dialog is driven by the server
// refusing to deal, never by this counter. Defined once here; no site repeats
// the number.
const BLIND_CHECK_HAND_GATE = 200;

// The Labels toggle is TAB-LOCAL (spec para 23) and namespaced by session id so
// it re-arms at a new table — unlike the four keys above, which are settings
// that outlive any one session and are deliberately not namespaced.
function labelsKey(sessionId: string): string {
  return `simulate.labels.${sessionId}`;
}

// Labels-shown preference for one session. They RETURN at the unlock (spec
// para 18), so anything but an explicit "hidden" shows them.
function readLabelsShown(sessionId: string): boolean {
  try {
    return window.localStorage.getItem(labelsKey(sessionId)) !== "hidden";
  } catch {
    return true;
  }
}

function writeLabelsShown(sessionId: string, shown: boolean): void {
  try {
    window.localStorage.setItem(labelsKey(sessionId), shown ? "shown" : "hidden");
  } catch {
    /* private-mode storage — setting still applies this session */
  }
}

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

// Watch-folded-hands setting (client-only, localStorage). ON (default) plays the
// villains out to showdown after a hero fold; OFF skips straight to the next
// hand. Absent/garbage storage ⇒ default ON.
function readWatch(): boolean {
  try {
    return window.localStorage.getItem(WATCH_KEY) !== "off";
  } catch {
    return true;
  }
}

// In-hand grading visibility (client-only, localStorage). Coach mode (true)
// shows the live hero verdict badge + end-of-hand recap; Real play (false,
// default) hides both — grading is still computed + recorded either way.
// Absent/garbage storage ⇒ default false (real-play/hidden).
function readCoachMode(): boolean {
  try {
    return window.localStorage.getItem(COACH_KEY) === "on";
  } catch {
    return false;
  }
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

  // ── Sit-down gate (two-mode-simulate T6) ──────────────────────────────────
  // The mode is fixed for a session, so a session may only ever be created by an
  // explicit choice. `awaitingMode` raises the two-room sit-down screen; it is
  // set by every path that used to create a Training session silently (spec
  // para 4: first boot, the 404 recovery in `run`, and Leave table) and cleared
  // only once a chosen session has been adopted. Restoring a stored session
  // never sets it, so a mid-session reload lands straight back at the table.
  // `pendingMode` is the room whose session is in flight — it drives the
  // screen's loading state and is null whenever nothing is being created.
  const [awaitingMode, setAwaitingMode] = useState(false);
  const [pendingMode, setPendingMode] = useState<SimMode | null>(null);

  // Focus handoff. Sitting down disables the card mid-press; leaving the table
  // removes the button that was pressed. Either way the focused element stops
  // existing and the browser drops focus to <body>, which puts the theme switch
  // and seven navigation tabs between a keyboard user and the screen that just
  // appeared. So each swap names the element to move focus to, and the effect
  // below does it once the new view has rendered.
  //
  // A FAILED create needs the same handoff and for the same reason: the card
  // was disabled while the request was in flight, so focus was already dropped
  // to <body>, and re-enabling it does not bring focus back. That case aims at
  // the error panel rather than a heading — it is above the still-pickable
  // rooms, so it both reads out what went wrong and leaves Tab pointing at the
  // choice again.
  //
  // All three targets carry tabIndex={-1}: they are focus TARGETS, never tab
  // stops. app.css scopes its outline suppression to that attribute.
  const modeHeadingRef = useRef<HTMLHeadingElement>(null);
  const tableHeadingRef = useRef<HTMLHeadingElement>(null);
  const errorPanelRef = useRef<HTMLDivElement>(null);
  const focusAfterSwap = useRef<"none" | "sit-down-screen" | "table" | "error">("none");

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

  // Watch-folded-hands toggle. Held in a ref too because `decide` reads it at
  // fold-CLICK time (a mid-playout flip must not retroactively change the hand
  // in flight — it takes effect on the NEXT fold).
  const [watch, setWatch] = useState<boolean>(readWatch);
  const watchRef = useRef<boolean>(watch);
  const changeWatch = useCallback((next: boolean) => {
    watchRef.current = next;
    setWatch(next);
    try {
      window.localStorage.setItem(WATCH_KEY, next ? "on" : "off");
    } catch {
      /* private-mode storage — setting still applies this session */
    }
  }, []);

  // Grading-visibility toggle (Coach ↔ Real play). Read at render time — no
  // ref needed, unlike watch/speed, because it only gates what renders below,
  // not a click-time decision branch.
  const [coachMode, setCoachMode] = useState<boolean>(readCoachMode);
  const changeCoachMode = useCallback((next: boolean) => {
    setCoachMode(next);
    try {
      window.localStorage.setItem(COACH_KEY, next ? "on" : "off");
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

  // ── S10 grading state ─────────────────────────────────────────────────────
  // The just-taken decision's verdict, shown as a seal on the hero pod. The hero
  // acts by their own click (not part of the bot playback), so the badge may
  // appear immediately — but it's cleared the moment the next action starts and
  // whenever a fresh hand deals, so it never bleeds onto a later decision.
  const [heroBadge, setHeroBadge] = useState<GradeView | null>(null);

  // Tier accumulation (refuter reality): persisted recap rows carry NO
  // verdict/reasoning text — only the live `last_grade` on each action response
  // does. So we stash each hand's live grades by ordinal here and merge them
  // back into the hand-over recap, so mistakes/blunders show their "why" on the
  // live path. Reset per hand (a new hand_no). A ref (not state): it's read at
  // render time from the current view and never needs to trigger its own render.
  const tiersByOrdinal = useRef<Map<number, GradeView>>(new Map());
  // "session_id#hand_no" keys — session-scoped so a 404-recovery into a fresh
  // session (which restarts at hand 1) can't reuse the previous hand's state.
  const gradedHandNo = useRef<string | null>(null);
  // The hand we've already refetched the report for, so a restore/re-render
  // of an already-finished hand doesn't refetch on every adopt.
  const reportedHandNo = useRef<string | null>(null);

  // Bumped whenever a hand completes so the all-time per-street report refetches
  // its aggregate. Also nudged on mount by the report's own effect.
  const [reportKey, setReportKey] = useState(0);

  // ── Villain-range (V2) ──────────────────────────────────────────────────────
  // Cumulative narrated-action bookkeeping for the range endpoint's lockstep
  // `through_action` param (the WHOLE-hand count of non-POST actions narrated so
  // far — hero's own + every villain's). The endpoint maps it to the domain's
  // POST-inclusive index (`domain_index = 2 + through_action`), so an off-by-one
  // here shows up as a chart one action ahead of / behind the log.
  //
  // `narratedBase` = the count of narrated actions BEFORE the current batch's
  // staged events; `narratedCount = narratedBase + stagedIndex`. Within one hand
  // every re-adopt is a hero action (next-hand/initial deal start a new
  // hand_no), and the hero's own action is itself exactly one narrated row that
  // precedes this batch's events — so the recurrence is: new hand ⇒ base 0;
  // same-hand hero action ⇒ base = prevBase + prevEventCount + 1. Held in a ref
  // (read at fetch time) plus mirrored context for reset detection.
  const narratedBaseRef = useRef(0);
  const narratedHandRef = useRef<string | null>(null);
  const prevEventCountRef = useRef(0);

  // Which villain seat's estimated-range panel is open (one at a time), plus the
  // resolved estimate + its fetch status. openRangeSeat drives the SimTable
  // button pressed-state and the panel mount; the rest is the panel's data.
  const [openRangeSeat, setOpenRangeSeat] = useState<number | null>(null);
  const [villainRange, setVillainRange] = useState<VillainRangeView | null>(null);
  const [rangeLoading, setRangeLoading] = useState(false);
  const [rangeErrored, setRangeErrored] = useState(false);

  // R1 reveal-after-fold: which reveal button is active (null = none clicked
  // yet) and the villain cards the server returned. Reset on every hand
  // transition (in adopt) so a reveal never bleeds onto the next hand.
  const [revealScope, setRevealScope] = useState<"last-in" | "all" | null>(null);
  const [revealedSeats, setRevealedSeats] = useState<RevealedSeatView[]>([]);

  // "Replay last hand" (T7): the just-completed hand opened in the stepped
  // replayer. The live wire carries no sim_hand_id — only session_id + hand_no —
  // so we resolve the replay through the (session_id, hand_no) endpoint. Null =
  // the live table is showing; a resolved view swaps the replayer in over it.
  const [replay, setReplay] = useState<HandReplayView | null>(null);
  const [replayLoading, setReplayLoading] = useState(false);
  const [replayError, setReplayError] = useState<string | null>(null);

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

    // S10 grade bookkeeping. A new (session, hand_no) pair resets the per-hand
    // tier accumulator — hand_no ALONE is not a safe key: every session starts
    // at hand 1, so a mid-hand-1 404 recovery into a fresh session would
    // otherwise bleed session A's "why" text into session B's recap (final-gate
    // refuter med-1). Then stash this response's live grade (if any) by ordinal
    // so the hand-over recap can merge in the tiers the persisted rows lack,
    // and surface it as the hero-pod badge.
    const hand = res.hand;
    const gradeKey = `${res.session_id}#${hand.hand_no}`;
    if (gradedHandNo.current !== gradeKey) {
      tiersByOrdinal.current = new Map();
      gradedHandNo.current = gradeKey;
    }
    const grade = hand.last_grade ?? null;
    if (grade) tiersByOrdinal.current.set(grade.ordinal, grade);
    setHeroBadge(grade);

    // A finished hand's decisions have persisted — refetch the all-time report
    // (once per hand, so a reload of an already-over hand doesn't re-fetch).
    if (hand.hand_over && reportedHandNo.current !== gradeKey) {
      reportedHandNo.current = gradeKey;
      setReportKey((k) => k + 1);
    }

    // Villain-range narrated-count bookkeeping (see the refs' comment). A fresh
    // hand resets the base to 0; a same-hand re-adopt is always a hero action,
    // whose single narrated row precedes this batch's events — so the new base
    // is the previous batch's fully-revealed total (prevBase + prevEventCount)
    // plus that one hero row. The count is only ever CONSUMED while playback is
    // active (see `rangeThrough`); on a settled/restored turn the full history
    // is requested instead, so a mid-hand reload (events=[], no hero action)
    // never needs an accurate base.
    const newBatch = res.hand.events?.length ?? 0;
    if (narratedHandRef.current !== gradeKey) {
      narratedHandRef.current = gradeKey;
      narratedBaseRef.current = 0;
      // Any hand transition closes an open villain-range panel — including
      // hand endings whose hand_over view was never adopted (the hero-fold
      // shortcut jumps straight to the next deal; without this a panel open on
      // a NON-folding villain silently carried across the hand boundary —
      // villain-range refuter med-1).
      setOpenRangeSeat(null);
      // R1: a new hand clears any reveal from the previous hand (fold-path FE
      // state bled 3× historically — reset it on the same boundary as the range
      // panel so revealed cards can't carry onto the next dealt hand).
      setRevealScope(null);
      setRevealedSeats([]);
    } else {
      narratedBaseRef.current = narratedBaseRef.current + prevEventCountRef.current + 1;
    }
    prevEventCountRef.current = newBatch;
    // Reset the staged index ATOMICALLY with the base bump: the playback
    // effect also resets it, but that runs a flush later — in between,
    // rangeThrough would read newBase + the OLD batch's terminal stagedIndex
    // and fire one inflated lockstep request (refuter low-1).
    setStaged(0);

    setView(res);
  }, [setStaged]);

  const clearStored = useCallback(() => {
    sessionIdRef.current = null;
    try {
      window.localStorage.removeItem(STORAGE_KEY);
    } catch {
      /* non-fatal */
    }
  }, []);

  // Hand the table back to the player instead of creating one for them. Every
  // path that used to deal a session eagerly calls this: the mode is fixed for
  // the session, so silently minting a Training table is exactly how a
  // Challenge player would lose the room they chose without being told (spec
  // para 4). Clearing `view` unmounts the felt so the sit-down screen is the
  // whole page, and drops any stale hand from the session just lost/left.
  // `handoff` says whether a focused control was destroyed getting here. After
  // Leave table or a lost session the player was mid-interaction and their
  // control has just gone, so focus moves to the sit-down heading. On first
  // boot nobody has interacted yet — stealing focus then would be its own
  // failure, so focus is left where the browser put it.
  const askForMode = useCallback((handoff: "move-focus" | "leave-focus") => {
    if (handoff === "move-focus") focusAfterSwap.current = "sit-down-screen";
    setView(null);
    setPendingMode(null);
    setAwaitingMode(true);
  }, []);

  // Create the session the player asked for and adopt its first hand. This is
  // the ONLY place a session is created. A failure leaves the sit-down screen
  // up with the error panel above it, so the player can pick again.
  const chooseMode = useCallback(
    async (mode: SimMode) => {
      if (busyRef.current) return;
      busyRef.current = true;
      setBusy(true);
      setPendingMode(mode);
      setError(null);
      try {
        adopt(await postSimulateSession(mode));
        // The card that was just pressed is about to unmount — hand focus to
        // the table's own heading, which announces the room and the hand.
        focusAfterSwap.current = "table";
        setAwaitingMode(false);
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
        // The pressed card went disabled and took focus with it; both rooms are
        // about to be pickable again, so hand focus to the error panel above
        // them rather than leaving the keyboard user on <body>.
        focusAfterSwap.current = "error";
      } finally {
        setPendingMode(null);
        busyRef.current = false;
        setBusy(false);
      }
    },
    [adopt],
  );

  // Deliver the focus handoff the swap asked for. Deliberately has no
  // dependency array: it must run after EVERY render, because the render that
  // mounts the new view is the first moment its heading exists. The ref is
  // cleared as it fires, so a later unrelated render never re-steals focus.
  useEffect(() => {
    const target = focusAfterSwap.current;
    if (target === "none") return;
    focusAfterSwap.current = "none";
    const el =
      target === "sit-down-screen"
        ? modeHeadingRef.current
        : target === "table"
          ? tableHeadingRef.current
          : errorPanelRef.current;
    el?.focus();
  });

  // Mount: try to restore a stored session; on 404 (missing/ended) clear it and
  // ask which room to sit in. StrictMode double-invokes effects in dev; the
  // cancelled flag keeps the later resolve from clobbering state.
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
          // Restore keeps the session's stored mode and never re-asks
          // (spec para 3) — `awaitingMode` is left false.
          if (!cancelled) adopt(res);
          return;
        } catch (e) {
          if (!isSessionNotFound(e)) throw e;
          // Stale/ended session — fall through to the sit-down screen.
          clearStored();
        }
      }
      if (!cancelled) askForMode("leave-focus");
    };

    boot().catch((e) => {
      if (!cancelled) setError(e instanceof Error ? e.message : String(e));
    });
    return () => {
      cancelled = true;
    };
  }, [adopt, clearStored, askForMode]);

  // Shared runner for hero actions / deals: a sync ref guard (state is async —
  // a same-tick burst would slip past a state-only check), 404 recovery, and
  // error surfacing. `op` returns the new view (or starts fresh on a lost
  // session).
  const run = useCallback(
    async (op: (id: string) => Promise<SessionView>) => {
      if (busyRef.current) return;
      const id = sessionIdRef.current;
      if (!id) {
        // No live session (first-visit race) — raise the sit-down screen rather
        // than minting a table the player never asked for.
        askForMode("move-focus");
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
            // The session was lost mid-play. Ask for the room again rather than
            // dropping the player into a Training table they did not pick.
            clearStored();
            askForMode("move-focus");
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
    [adopt, clearStored, askForMode],
  );

  const decide = useCallback(
    (action: ActionType, sizeBb?: number | null) => {
      // Hero-fold skip (Watch OFF only): the hero has no more decisions this
      // hand, so with watching disabled there is nothing to pace — skip the bot
      // playback entirely and deal the next hand in the same turn. Cancel any
      // residual timer first so a fold mid-playback of a prior batch can't leave
      // a stray reveal running. Read from the ref so a mid-playout toggle only
      // affects the NEXT fold. With Watch ON we fall through to the normal path
      // below, which adopts the fold response so the villains narrate to
      // showdown (+ recap) exactly like a hand played out.
      if (action === "fold" && !watchRef.current) {
        clearTimer();
        void run(async (id) => {
          // The fold response ends the hand but is never adopted (we jump
          // straight to the next deal) — without the bump here the per-street
          // report went stale after every fold-ended hand (final-gate refuter
          // high-1: adopt() only sees the NEXT hand, whose hand_over is false).
          const folded = await postHeroAction(id, { action });
          const foldedKey = `${folded.session_id}#${folded.hand.hand_no}`;
          if (folded.hand.hand_over && reportedHandNo.current !== foldedKey) {
            reportedHandNo.current = foldedKey;
            setReportKey((k) => k + 1);
          }
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

  // Open the just-completed hand in the stepped replayer. The live wire has no
  // sim_hand_id, so resolve by the unique (session_id, hand_no) pair the FE holds
  // (SessionView.session_id + hand.hand_no) via the replay alias endpoint. This is
  // purely additive — it never touches the live session state, so play is unchanged.
  const openLastReplay = useCallback(async (sessionId: string, handNo: number) => {
    setReplayLoading(true);
    setReplayError(null);
    setReplay(null);
    try {
      const r = await fetch(
        `/api/v1/simulate/replay?session_id=${encodeURIComponent(sessionId)}&hand_no=${handNo}`,
      );
      if (!r.ok) throw new Error(`${r.url} -> ${r.status}`);
      setReplay((await r.json()) as HandReplayView);
    } catch (e) {
      setReplayError(e instanceof Error ? e.message : String(e));
    } finally {
      setReplayLoading(false);
    }
  }, []);

  const closeReplay = useCallback(() => {
    setReplay(null);
    setReplayError(null);
  }, []);

  // Leave the table: end it server-side, clear storage, and return to the
  // sit-down screen. Sitting down again is the only way to change room, so this
  // path must ask rather than re-deal. A lost session (already 404) is treated
  // as success.
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
      askForMode("move-focus");
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      busyRef.current = false;
      setBusy(false);
    }
  }, [clearStored, askForMode]);

  const hand = view?.hand ?? null;

  // ── The display gate (two-mode-simulate T7) ────────────────────────────────
  // ONE boolean for all five archetype display sites — the seat plate and its
  // tooltip, the range button, the ledger's Player column, the range panel's
  // header, and the preflop exploit note. It is computed here and threaded down
  // precisely so the five cannot drift apart; a component deciding for itself is
  // how one of them ends up still rendering.
  //
  // Training always names its opponents. Challenge withholds every label from
  // hand 1 until the blind check has been answered OR skipped (a skip stores a
  // result too, spec para 15 — `submitted` is true either way), and follows the
  // player's toggle from then on.
  //
  // Nothing here touches the data: `persona_type` rides the wire in both modes
  // and stays in the record, which is what keeps history, replay and the
  // analytics export attributable (spec constraint (c)).
  const challenge = view?.mode === "challenge";
  const labelsUnlocked = view?.blind_check?.submitted === true;

  // The stored preference is per-session and tab-local, so it is DERIVED during
  // render rather than restored by an effect: an effect renders one frame under
  // the previous value first, which on a reload means flashing the labels of a
  // player who had chosen to hide them. `labelsPref` carries the session it
  // belongs to, so a new table falls back to that table's stored value instead
  // of inheriting the last one's.
  const sessionId = view?.session_id ?? null;
  const storedLabelsShown = useMemo(
    () => (sessionId == null ? true : readLabelsShown(sessionId)),
    [sessionId],
  );
  const [labelsPref, setLabelsPref] = useState<{
    sessionId: string;
    shown: boolean;
  } | null>(null);
  const labelsShown =
    labelsPref?.sessionId === sessionId ? labelsPref.shown : storedLabelsShown;

  const labelsVisible = !challenge || (labelsUnlocked && labelsShown);
  // Absent before the unlock, never present-and-disabled (spec para 20): a
  // disabled control advertises that something is being withheld. Training gets
  // no toggle at all — it is the app as it stands, plus its stamp.
  const showLabelsToggle = challenge && labelsUnlocked;

  // Hiding again must CLOSE an open range panel: the panel is mounted
  // independently of the button, so gating the button alone would leave the
  // panel and its archetype header on screen (spec para 21). Closing it is also
  // what discards an in-flight range response — clearing `openRangeSeat` runs
  // the fetch effect's cleanup, whose existing stale-response guard drops the
  // late reply. No second guard is added beside it.
  const changeLabelsShown = useCallback((forSession: string, next: boolean) => {
    setLabelsPref({ sessionId: forSession, shown: next });
    writeLabelsShown(forSession, next);
    if (!next) setOpenRangeSeat(null);
  }, []);

  // Completed hands, from the wire (spec para 11): hand 200 counts only once it
  // settles, so this reads 199 while it is live. `hand_no - 1` alone would fire
  // a hand late and show "Hand 201 / 200". Drives the counter's progress only —
  // the deal is barred by the server, not by this number.
  const completedHands = hand != null ? hand.hand_no - (hand.hand_over ? 0 : 1) : 0;
  // Percent of the way to the check, or null once there is nothing to count
  // towards — after the unlock the `/ 200` and the bar both go (spec para 19).
  const gateProgress =
    challenge && !labelsUnlocked
      ? Math.min(100, (completedHands / BLIND_CHECK_HAND_GATE) * 100)
      : null;

  const tableState = useMemo(
    () =>
      hand
        ? stagedTableState({
            startStreet: hand.last_grade?.street,
            finalStreet: hand.street,
            finalBoard: hand.board,
            events: hand.events,
            stagedIndex,
          })
        : null,
    [hand, stagedIndex],
  );

  // Merge the finished hand's persisted recap with the live tiers we accumulated
  // this hand (persisted rows lack verdict/reasoning text; the live grades carry
  // it). Match by ordinal; the live entry wins where present so misses show
  // their "why" on the live path. On a mid-session reload the accumulator is
  // empty, so this degrades to the numbers-only persisted rows — accepted v1.
  const mergedRecap = useMemo<GradeView[]>(() => {
    const rows = hand?.recap ?? [];
    return rows.map((r) => tiersByOrdinal.current.get(r.ordinal) ?? r);
    // hand?.recap identity changes per view; the accumulator is a ref read live.
  }, [hand?.recap]);

  // Pacing gate (S11 lockstep philosophy — nothing on screen may lead the log):
  // during staged bot playback the hand may already be hand_over server-side,
  // but the recap and the felt's final grades must stay hidden until playback
  // completes. The hero's OWN badge is exempt — the hero acted by their own
  // click, not the bot playback, so it may show immediately.
  const revealHandEnd = !playing;

  // Enter or Space deals the next hand once the hand has settled — the topbar
  // button can sit above the fold, but the key saves the reach entirely. Skipped
  // when focus is on an interactive control so we never hijack a key meant for
  // another button (Watch, reveal, etc.) — a focused button still gets its
  // native Space/Enter click; busyRef is the same sync guard run() uses, so a
  // stray double-fire (global handler + a focused button's own key) can't deal
  // twice.
  useEffect(() => {
    // Also suppressed while the stepped replayer is open — a background Enter/Space
    // must never deal a new live hand under the replay overlay (additive promise).
    if (!hand?.hand_over || !revealHandEnd || replay) return;
    const onKey = (e: KeyboardEvent) => {
      if ((e.key !== "Enter" && e.key !== " ") || e.repeat || e.metaKey || e.ctrlKey || e.altKey) return;
      const target = e.target as HTMLElement | null;
      if (
        target?.closest(
          'button, a, input, textarea, select, [role="button"], [contenteditable="true"]',
        )
      ) {
        return;
      }
      if (busyRef.current) return;
      e.preventDefault();
      nextHand();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [hand?.hand_over, revealHandEnd, nextHand, replay]);

  // ── R1 reveal-after-fold ────────────────────────────────────────────────────
  // Did the hero fold this hand? Only then are the villains withheld (face-down)
  // and the reveal buttons meaningful; a hero-in showdown auto-reveals instead.
  const heroFolded = hand?.hand_over
    ? hand.seats.some((s) => s.is_hero && s.status === "folded")
    : false;
  // Fetch the requested reveal set and flip those seats on the felt. Availability
  // is a 200 body — an unavailable reveal (capability off / not a hero fold) just
  // leaves the felt face-down. Only a dead session errors; swallow it (reveal is
  // an optional affordance, never blocks play).
  const onReveal = useCallback(async (scope: "last-in" | "all") => {
    const id = sessionIdRef.current;
    if (!id) return;
    try {
      const res = await getReveal(id, scope);
      if (res.available) {
        setRevealScope(scope);
        setRevealedSeats(res.seats);
      }
    } catch {
      /* non-fatal: reveal is optional */
    }
  }, []);
  // seat_index → revealed hole cards, consumed by SimTable to flip the felt.
  const revealedBySeat = useMemo(
    () => new Map(revealedSeats.map((s) => [s.seat_index, s.hole_cards] as const)),
    [revealedSeats],
  );

  // ── Villain-range panel: open/close + lockstep fetch (V2) ───────────────────
  // The narrated count that gates the estimate. While playback runs, it's the
  // per-hand cumulative count of narrated actions the log has revealed so far
  // (base + stagedIndex) — passed as `through_action` so the chart conditions on
  // exactly the visible prefix and NEVER leads the log. When NOT playing the log
  // is fully caught up (or this is a restored/settled turn), so we request the
  // full history (undefined) — which also sidesteps a mid-hand reload's
  // untracked base.
  const narratedCount = narratedBaseRef.current + stagedIndex;
  const rangeThrough = playing ? narratedCount : undefined;

  // The open seat's live SeatView (server truth) and its STAGED reveal state —
  // the same staged-fold computation SimTable's button uses, so the panel closes
  // in lockstep with the fold narration, not the instant server-truth flips.
  const openSeat =
    openRangeSeat != null ? hand?.seats.find((s) => s.seat_index === openRangeSeat) : undefined;
  const openSeatStagedFolded =
    openSeat != null &&
    (() => {
      const threshold = revealAt.get(openSeat.position);
      const revealed = threshold == null || stagedIndex >= threshold;
      return revealed && openSeat.status === "folded";
    })();

  const toggleRange = useCallback((seatIndex: number) => {
    setOpenRangeSeat((prev) => (prev === seatIndex ? null : seatIndex));
  }, []);
  const closeRange = useCallback(() => setOpenRangeSeat(null), []);

  // Auto-close: the open villain's staged fold narrates, or the hand ends
  // (hand_over reveals real cards — an estimate beside the truth is noise). Both
  // are lockstep-aware: hand_over's felt reveal is itself gated behind playback,
  // and the fold uses the staged computation above.
  useEffect(() => {
    if (openRangeSeat == null) return;
    if (hand?.hand_over || openSeat == null || openSeatStagedFolded) {
      setOpenRangeSeat(null);
    }
  }, [openRangeSeat, hand?.hand_over, openSeat, openSeatStagedFolded]);

  // Fetch on open + REFETCH as the narrated count advances while open (lockstep
  // narrowing). Stale-response guard mirrors SimRangeChart: each request is
  // stamped with the (seat, through) live at fire time; a late response for a
  // superseded stamp is discarded. Fire-and-forget — never blocks the table.
  const rangeStampRef = useRef<string>("");
  useEffect(() => {
    if (openRangeSeat == null || view == null) return;
    const stamp = `${view.session_id}#${openRangeSeat}#${rangeThrough ?? "full"}`;
    rangeStampRef.current = stamp;
    let cancelled = false;
    setRangeLoading(true);
    setRangeErrored(false);
    getVillainRange(view.session_id, openRangeSeat, rangeThrough)
      .then((res) => {
        if (cancelled || rangeStampRef.current !== stamp) return;
        setVillainRange(res);
        setRangeLoading(false);
      })
      .catch(() => {
        if (cancelled || rangeStampRef.current !== stamp) return;
        setVillainRange(null);
        setRangeErrored(true);
        setRangeLoading(false);
      });
    return () => {
      cancelled = true;
    };
    // Refetch on: open seat change, count advance (lockstep narrowing), or a
    // 404-recovery into a fresh session (session_id).
  }, [openRangeSeat, rangeThrough, view]);

  // Drop stale panel data the instant the open seat changes / closes, so the
  // next open never flashes the previous villain's grid before its fetch lands.
  useEffect(() => {
    setVillainRange(null);
    setRangeErrored(false);
  }, [openRangeSeat]);

  return (
    <section className="simulate">
      <div className="sim-topbar">
        <h1 className="sim-heading" ref={tableHeadingRef} tabIndex={-1}>
          Simulate
          {view && (
            // Which room this session is in (T6). A stamp on the session's
            // paperwork, never a control: the mode is fixed once the player has
            // sat down, so there is nothing here to switch.
            <span className={`sim-mode-stamp sim-mode-stamp-${view.mode}`}>
              <span className="sim-sr-only">Table: </span>
              {view.mode === "challenge" ? "Challenge" : "Training"}
            </span>
          )}
          {hand && (
            // Per-session hand counter — orients you on the live table. Same
            // `hand_no` the replayer titles a hand by; History numbers hands
            // its own way, so this is a live-table cue, not a History key.
            // On a Challenge table still short of its blind check it also names
            // the target and draws the distance travelled (T7, spec para 10);
            // both go at the unlock (para 19).
            <span className="sim-hand-progress">
              <span className="sim-hand-no">
                Hand <span className="num">{hand.hand_no}</span>
                {gateProgress != null && (
                  <>
                    {" / "}
                    <span className="num">{BLIND_CHECK_HAND_GATE}</span>
                  </>
                )}
              </span>
              {gateProgress != null && (
                // Decorative on purpose: the counter beside it already states
                // both numbers, and an aria-label here would be folded into
                // this heading's own accessible name and read out with it.
                <span className="sim-hand-bar" aria-hidden="true">
                  {/* Nothing is drawn at zero: the fill carries a minimum width
                      so early progress is visible, and that floor must not
                      claim a hand the player has not finished. */}
                  {gateProgress > 0 && (
                    <span
                      className="sim-hand-bar-fill"
                      style={{ width: `${gateProgress}%` }}
                    />
                  )}
                </span>
              )}
            </span>
          )}
        </h1>
        {view && (
          <div className="sim-topbar-controls">
            {/* Primary next-step lives here, first in the cluster and above the
                fold — the old home in SimShowdown sat below the tall felt and
                needed a scroll every hand. Present only once the hand has
                settled (same gate the result panel uses); Enter/Space deal too. */}
            {hand?.hand_over && revealHandEnd && !replay && (
              <button
                type="button"
                className="btn btn-primary sim-next-btn"
                onClick={nextHand}
                disabled={busy}
              >
                {busy ? "Dealing…" : "Next hand →"}
              </button>
            )}
            {/* Replay last hand (T7) — shown once the hand has settled. Resolves
                the just-played hand by (session_id, hand_no) and opens it in the
                stepped replayer. Additive: it never touches live session state. */}
            {hand?.hand_over && revealHandEnd && view && !replay && (
              <button
                type="button"
                className="btn sim-replay-btn"
                onClick={() => void openLastReplay(view.session_id, hand.hand_no)}
                disabled={busy || replayLoading}
              >
                {replayLoading ? "Opening…" : "Replay last hand"}
              </button>
            )}
            <SimWatchToggle watch={watch} onChange={changeWatch} />
            <SimGradingToggle coachMode={coachMode} onChange={changeCoachMode} />
            {/* Labels: Shown / Hidden (T7) — mounted only after the blind check
                has been answered, so before the unlock it is absent from the
                document rather than present and disabled. */}
            {showLabelsToggle && (
              <SimLabelsToggle
                shown={labelsShown}
                onChange={(next) => changeLabelsShown(view.session_id, next)}
              />
            )}
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

      {/* role="alert" because this panel also appears on paths that hand focus
          to nothing at all — a failed restore on boot, a failed action at the
          table — and without a live region those failures are silent to a
          screen reader. Matches the replay panel below. The focus move on the
          failed-create path is deliberately kept on TOP of the alert: a focus
          change can pre-empt a live-region announcement, so reading the panel
          out because focus landed on it is the guarantee, and the alert is the
          cover for the paths where focus does not move. */}
      {error && (
        <div className="panel bad-bg" role="alert" ref={errorPanelRef} tabIndex={-1}>
          Error: {error}. Is the backend running on :8008?
        </div>
      )}

      {replayError && (
        <div className="panel bad-bg" role="alert">
          Couldn’t open the replay: {replayError}.{" "}
          <button type="button" className="sim-replay-dismiss" onClick={closeReplay}>
            Dismiss
          </button>
        </div>
      )}

      {replay ? (
        <HandReplay key={replay.sim_hand_id} replay={replay} onClose={closeReplay} />
      ) : hand ? (
        <div className="sim-layout">
          <div className="sim-main">
            <SimTable
              hand={hand}
              board={tableState?.board ?? hand.board}
              street={tableState?.street ?? hand.street}
              stagedIndex={stagedIndex}
              revealAt={revealAt}
              playbackComplete={!playing}
              lastGrade={coachMode ? heroBadge : null}
              openRangeSeat={openRangeSeat}
              onToggleRange={toggleRange}
              revealedBySeat={revealedBySeat}
              labelsVisible={labelsVisible}
            />

            {/* Villain-range panel (V2) — one open villain at a time, keyed by
                the open seat so a seat switch remounts a fresh grid. Sits under
                the felt so it doesn't crowd the seat pods. Auto-closes on the
                villain's staged fold / hand_over (effects above).
                T7: the panel's header is an archetype display site of its own,
                and this file mounts it, so the label gate belongs here — with
                the labels hidden the panel never exists to leak. Hiding also
                clears `openRangeSeat` (see changeLabelsShown), which is what
                stops the fetch and keeps a re-show from popping it back. */}
            {labelsVisible && openSeat && !openSeatStagedFolded && !hand.hand_over && (
              <SimVillainRange
                key={openSeat.seat_index}
                position={openSeat.position}
                range={villainRange}
                loading={rangeLoading}
                errored={rangeErrored}
                onClose={closeRange}
              />
            )}

            {hand.is_hero_turn && (
              <SimActionBar
                legalActions={hand.legal_actions}
                disabled={busy || playing}
                onDecide={decide}
              />
            )}

            {/* Point-of-need baseline range chart (C2). Preflop hero turns only,
                and never during bot playback (pacing). The identity key must
                change PER DECISION POINT, not per hand: two hero preflop turns
                in one hand (open → villain 3-bets → hero faces it) would
                otherwise share a key and keep the FIRST decision's chart on
                screen for the second (chart refuter high-1). pot_bb strictly
                grows between consecutive preflop hero decisions, so it is the
                per-decision discriminator; is_hero_turn added nothing (always
                true when mounted). */}
            {hand.is_hero_turn && hand.street === "preflop" && !playing && view && (
              <SimRangeChart
                sessionId={view.session_id}
                identityKey={`${view.session_id}#${hand.hand_no}#${hand.pot_bb}`}
                heroCards={hand.hero.hole_cards}
                labelsVisible={labelsVisible}
              />
            )}

            {/* Postflop action-mix chart (R5) — the grader's own baseline for
                the current postflop decision, same point-of-need contract as
                the preflop chart above. identityKey adds street + pot_bb: pot
                strictly grows between hero turns on one street and the street
                itself advances otherwise, so every postflop decision point in
                a hand gets a distinct key (stale-guard discriminator). */}
            {hand.is_hero_turn && hand.street !== "preflop" && !playing && view && (
              <SimPostflopChart
                sessionId={view.session_id}
                identityKey={`${view.session_id}#${hand.hand_no}#${hand.street}#${hand.pot_bb}`}
              />
            )}

            {/* Hand-over surfaces gate on playback: the recap and settlement
                slip appear only once the bot playback finishes (revealHandEnd),
                so nothing leads the log. */}
            {hand.hand_over && revealHandEnd && (
              <>
                <SimShowdown
                  showdown={hand.showdown}
                  seats={hand.seats}
                  heroFolded={heroFolded}
                  revealScope={revealScope}
                  onReveal={onReveal}
                />
                {coachMode && (
                  <SimRecap
                    recap={mergedRecap}
                    sessionId={sessionIdRef.current}
                    heroCards={hand.hero.hole_cards}
                    board={hand.board}
                  />
                )}
              </>
            )}

            {!hand.is_hero_turn && !hand.hand_over && (
              <p className="sim-waiting" role="status">
                Waiting on the table…
              </p>
            )}
          </div>

          <aside className="sim-side">
            <SimEventLog events={hand.events} stagedIndex={stagedIndex} board={hand.board} />
            <SimStreetReport refreshKey={reportKey} />
            <SimLedger seats={hand.seats} labelsVisible={labelsVisible} />
          </aside>
        </div>
      ) : awaitingMode ? (
        // The sit-down screen (T6). Rendered even when `error` is set, so a
        // failed create leaves the player a way back in — the error panel above
        // says what went wrong and both rooms stay pickable.
        <div className="sim-empty-shell">
          <SimModeChoice
            pending={pendingMode}
            onChoose={(m) => void chooseMode(m)}
            headingRef={modeHeadingRef}
          />
          {/* The all-time report is session-independent — it stays beside the
              door, exactly as it does in the restoring state below. */}
          <aside className="sim-side sim-side-empty">
            <SimStreetReport refreshKey={reportKey} />
          </aside>
        </div>
      ) : (
        !error && (
          <div className="sim-empty-shell">
            <div className="panel simulate-empty" role="status">
              Restoring your table…
            </div>
            {/* The all-time report is session-independent — show it even before
                the first hand adopts (spec: visible with or without a live
                session). */}
            <aside className="sim-side sim-side-empty">
              <SimStreetReport refreshKey={reportKey} />
            </aside>
          </div>
        )
      )}
    </section>
  );
}
