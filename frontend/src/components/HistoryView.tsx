import { useCallback, useEffect, useMemo, useState } from "react";

import type { HandReplayView, HistoryListItemView, HistoryListView } from "../api/types";
import HandReplay from "./simulate/HandReplay";
import { tierOf } from "./simulate/simGrade";

// Simulate Hand-History + Replay (T5) — the hand register. A day-ruled ledger of
// every completed Simulate hand, newest-first, grouped by UTC calendar day. Each
// day is a page: a gilt date rule, then one line per hand carrying its engraved
// per-day ordinal, hero seat/position, and a worst-tier chip. A "mistakes only"
// toggle filters (client-side) to hands that hold a {mistake, blunder} decision —
// the review shortlist. Selecting a hand opens the stepped replayer (T6).
//
// This view fetches the two read-only endpoints directly with the app's /api/v1
// base + the same "url -> status" error shape the client helper uses, so it needs
// no change to the shared client module.

const BASE = "/api/v1";

async function fetchJson<T>(url: string): Promise<T> {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`${r.url} -> ${r.status}`);
  return (await r.json()) as T;
}

// Group the flat (already newest-first) item list into contiguous day pages,
// preserving order. Items share a `day`; the server pre-sorted, so a simple
// contiguous-run group keeps newest days first and newest hands first within.
interface DayGroup {
  day: string;
  items: HistoryListItemView[];
}

function groupByDay(items: HistoryListItemView[]): DayGroup[] {
  const out: DayGroup[] = [];
  for (const it of items) {
    const last = out[out.length - 1];
    if (last && last.day === it.day) last.items.push(it);
    else out.push({ day: it.day, items: [it] });
  }
  return out;
}

// "2026-07-22" → "Tue · Jul 22, 2026" — a legible page header. Parse as UTC so
// the label matches the server's UTC day bucket (a local-midnight parse could
// shift the date across a timezone). Falls back to the raw string if unparseable.
function formatDay(day: string): string {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(day);
  if (!m) return day;
  const d = new Date(Date.UTC(Number(m[1]), Number(m[2]) - 1, Number(m[3])));
  if (Number.isNaN(d.getTime())) return day;
  return d.toLocaleDateString(undefined, {
    weekday: "short",
    month: "short",
    day: "numeric",
    year: "numeric",
    timeZone: "UTC",
  });
}

export default function HistoryView() {
  const [list, setList] = useState<HistoryListView | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [mistakesOnly, setMistakesOnly] = useState(false);

  // The open replay (fetched by id on select) + its load state. Null = the list
  // is showing. A per-select fetch keeps the wire lean (the list carries no steps).
  const [replay, setReplay] = useState<HandReplayView | null>(null);
  const [replayLoading, setReplayLoading] = useState(false);
  const [replayError, setReplayError] = useState<string | null>(null);

  const loadList = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setList(await fetchJson<HistoryListView>(`${BASE}/simulate/history`));
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadList();
  }, [loadList]);

  const openHand = useCallback(async (id: number) => {
    setReplayLoading(true);
    setReplayError(null);
    setReplay(null);
    try {
      const view = await fetchJson<HandReplayView>(`${BASE}/simulate/hand/${id}/replay`);
      setReplay(view);
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

  const items = list?.items ?? [];
  const filtered = useMemo(
    () => (mistakesOnly ? items.filter((it) => it.has_mistake) : items),
    [items, mistakesOnly],
  );
  const groups = useMemo(() => groupByDay(filtered), [filtered]);
  const mistakeCount = useMemo(() => items.filter((it) => it.has_mistake).length, [items]);

  // The stepped replayer takes over the view when a hand is open. `key` remounts
  // it per hand so its internal cursor resets to the first step.
  if (replay) {
    return (
      <section className="history">
        <HandReplay key={replay.sim_hand_id} replay={replay} onClose={closeReplay} />
      </section>
    );
  }

  return (
    <section className="history">
      <header className="history-head">
        <div className="history-titleblock">
          <h1 className="history-title">Hand history</h1>
          <p className="history-sub">Every completed hand, newest first — step back through any of them.</p>
        </div>
        {items.length > 0 && (
          <button
            type="button"
            className={"btn history-filter" + (mistakesOnly ? " on" : "")}
            aria-pressed={mistakesOnly}
            onClick={() => setMistakesOnly((v) => !v)}
          >
            Mistakes only
            <span className="history-filter-count num">{mistakeCount}</span>
          </button>
        )}
      </header>

      {replayError && (
        <div className="panel bad-bg history-replay-error" role="alert">
          Couldn’t open that hand: {replayError}.{" "}
          <button type="button" className="history-retry-link" onClick={closeReplay}>
            Dismiss
          </button>
        </div>
      )}

      {loading ? (
        <HistorySkeleton />
      ) : error ? (
        <div className="panel bad-bg" role="alert">
          Couldn’t load your history: {error}. Is the backend running on :8008?{" "}
          <button type="button" className="history-retry-link" onClick={() => void loadList()}>
            Retry
          </button>
        </div>
      ) : items.length === 0 ? (
        <div className="panel history-empty" role="status">
          <p className="history-empty-lead">No hands to review yet.</p>
          <p className="history-empty-note">
            Play a few hands at the table and they’ll be filed here, day by day.
          </p>
          <a className="btn btn-primary history-empty-cta" href="#/simulate">
            Go to the table
          </a>
        </div>
      ) : filtered.length === 0 ? (
        <div className="panel history-empty" role="status">
          <p className="history-empty-lead">No mistakes in this window — clean play.</p>
          <button type="button" className="btn history-empty-cta" onClick={() => setMistakesOnly(false)}>
            Show all hands
          </button>
        </div>
      ) : (
        <ol className="history-days">
          {groups.map((g) => (
            <li key={g.day} className="history-day">
              <h2 className="history-day-head">
                <span className="history-day-date">{formatDay(g.day)}</span>
                <span className="history-day-count num">{g.items.length}</span>
              </h2>
              <ul className="history-hand-list">
                {g.items.map((it) => (
                  <li key={it.sim_hand_id} className="history-hand-row">
                    <button
                      type="button"
                      className="history-hand-btn"
                      onClick={() => void openHand(it.sim_hand_id)}
                      disabled={replayLoading}
                      aria-label={`Replay hand ${it.day_ordinal}, hero ${it.hero_position}${
                        it.has_mistake ? ", contains a mistake" : ""
                      }`}
                    >
                      <span className="history-hand-ord">
                        <span className="history-hand-ord-word">Hand</span>
                        <span className="history-hand-ord-no num">{it.day_ordinal}</span>
                      </span>
                      <span className="history-hand-hero">{it.hero_position}</span>
                      <span className="history-hand-dec num">
                        {it.n_decisions} {it.n_decisions === 1 ? "decision" : "decisions"}
                      </span>
                      <span className="history-hand-tier">
                        <WorstTierChip tier={it.worst_tier} />
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}

// The hand's worst graded verdict as a chip — same tier vocabulary/tone classes
// as the live badge + recap. A null tier is "no baseline" (muted), never faked.
function WorstTierChip({ tier }: { tier: HistoryListItemView["worst_tier"] }) {
  const meta = tierOf(tier);
  return (
    <span className={"sim-badge sim-badge-inline sim-tier-" + meta.tone}>
      <span className="sim-badge-word">{meta.label}</span>
    </span>
  );
}

// Skeleton — two day pages of placeholder rows, shaped like the real list so the
// content doesn't jump on load. Decorative; hidden from the accessibility tree.
function HistorySkeleton() {
  return (
    <div className="history-skeleton" aria-hidden="true">
      {[0, 1].map((d) => (
        <div key={d} className="history-day">
          <div className="history-day-head">
            <span className="history-skel-bar history-skel-date" />
          </div>
          <div className="history-hand-list">
            {[0, 1, 2].map((r) => (
              <div key={r} className="history-hand-row">
                <span className="history-skel-bar history-skel-row" />
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
