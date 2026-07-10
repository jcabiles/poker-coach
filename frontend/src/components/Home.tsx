import { useEffect, useState } from "react";

import { getCalendar, getRecap } from "../api/client";
import type {
  CalendarDay,
  LeakStat,
  Mode,
  RecapResponse,
  ReviewPlanResponse,
} from "../api/types";
import { formatHash } from "../lib/hashRoute";

// N7 — mastery thresholds. Named constants (not silent magic numbers) and
// surfaced verbatim in the "Learning path" key below.
export const MASTERY_ACCURACY_THRESHOLD = 0.8; // "solid" needs >= this accuracy...
export const MASTERY_ATTEMPTS_THRESHOLD = 20; // ...and >= this many attempts.

type Mastery = "new" | "learning" | "solid";

interface PathNode {
  title: string;
  mode: Mode;
  leakCategories: number[]; // app/domain/leaks.py LeakCategory ints this node exercises
}

// N7 — single ordered learning path (no branching skill tree; see roadmap
// §N7 no-gos). Each preflop node deals its own family via a per-node-context
// `/drill/next` mode (backend _FAMILY_CTX); postflop/exploit nodes use their
// existing modes.
const LEARNING_PATH: PathNode[] = [
  { title: "RFI", mode: "rfi", leakCategories: [100, 101, 102, 103, 104] },
  { title: "vs RFI", mode: "vs_rfi", leakCategories: [112] },
  { title: "Blind defense", mode: "blind_defense", leakCategories: [110] },
  { title: "vs Limpers", mode: "vs_limpers", leakCategories: [150] },
  { title: "vs 3-bet", mode: "vs_3bet", leakCategories: [120, 121] },
  { title: "C-bet", mode: "postflop", leakCategories: [200] },
  { title: "Facing c-bet", mode: "vs_cbet", leakCategories: [201] },
  { title: "Facing check-raise", mode: "vs_check_raise", leakCategories: [202] },
  { title: "Exploits", mode: "exploit", leakCategories: [300, 301, 302, 303] },
];

// Mastery is computed from the EXISTING /stats/leaks response (attempts +
// accuracy per leak_category bucket) — no new stats surface.
function masteryFor(leakCategories: number[], leaks: LeakStat[]): Mastery {
  const matching = leaks.filter((l) => leakCategories.includes(l.category));
  const attempts = matching.reduce((sum, l) => sum + l.attempts, 0);
  if (attempts === 0) return "new";
  const accuracy = matching.reduce((sum, l) => sum + l.attempts * l.accuracy, 0) / attempts;
  return accuracy >= MASTERY_ACCURACY_THRESHOLD && attempts >= MASTERY_ATTEMPTS_THRESHOLD
    ? "solid"
    : "learning";
}

const MASTERY_TONE: Record<Mastery, string> = {
  new: "neutral",
  learning: "warn",
  solid: "good",
};

const MASTERY_LABEL: Record<Mastery, string> = {
  new: "New",
  learning: "Learning",
  solid: "Solid",
};

function goTo(hash: string) {
  window.location.hash = hash;
}

// T9 — heat intensity. The calendar renders 5 steps (empty + l1–l4). A day's
// step is chosen by its attempt count (a session's worth of reps deepens the
// foil). Thresholds are deliberately coarse — attendance, not precision.
function calStep(attempts: number): 0 | 1 | 2 | 3 | 4 {
  if (attempts <= 0) return 0;
  if (attempts < 8) return 1;
  if (attempts < 16) return 2;
  if (attempts < 28) return 3;
  return 4;
}

// T9 — format a "YYYY-MM-DD" date for a title/aria-label without pulling in a
// date lib or risking a timezone shift (the string is already the local day).
function prettyDate(iso: string): string {
  const [y, m, d] = iso.split("-");
  const months = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
  ];
  const mi = Number(m) - 1;
  return `${months[mi] ?? m} ${Number(d)}, ${y}`;
}

// N7 — home/curriculum hub: "the evening's card" (the due SM-2 queue) + "the
// curriculum" (a single ordered learning path). Below the fold: the attendance
// heat calendar + the House Recap. `plan` is null when its fetch hasn't
// resolved or failed (best-effort like stats); the calendar/recap are fetched
// here on mount, also best-effort — each hides gracefully on failure.
export default function Home({
  plan,
  leaks,
}: {
  plan: ReviewPlanResponse | null;
  leaks: LeakStat[];
}) {
  const dueItems = plan?.items ?? [];
  const dueCount = plan?.due_count ?? 0;

  // T9 — calendar + recap are Home-local, fetched on mount, fire-and-forget.
  // `null` means "not loaded / failed" for both — the cards hide (calendar) or
  // empty-state (recap) rather than blocking the view.
  const [calendar, setCalendar] = useState<CalendarDay[] | null>(null);
  const [recap, setRecap] = useState<RecapResponse | null>(null);

  useEffect(() => {
    let cancelled = false;
    getCalendar(8)
      .then((c) => {
        if (!cancelled) setCalendar(c);
      })
      .catch(() => {
        if (!cancelled) setCalendar(null);
      });
    getRecap()
      .then((r) => {
        if (!cancelled) setRecap(r);
      })
      .catch(() => {
        if (!cancelled) setRecap(null);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="home">
      {/* --- upper fold: the evening's card + the curriculum --- */}
      <div className="home-grid">
        <section className="panel card--deco home-section">
          <header className="home-head">
            <div>
              <span className="home-eyebrow">The Evening&apos;s Card</span>
              <h2 className="home-section-title">Today&apos;s plan</h2>
            </div>
          </header>
          {dueCount > 0 ? (
            <>
              <p className="home-due-count">
                <b className="home-due-num">{dueCount}</b>
                <span className="home-due-word">
                  spots due for
                  <br />
                  review tonight
                </span>
              </p>
              <ul className="mix home-due-list">
                {dueItems.map((item) => (
                  <li key={item.signature}>
                    <span className="home-due-name">
                      <span className="home-due-pip" aria-hidden="true" />
                      {item.label}
                    </span>
                    <span className="home-due-date">due {item.due_date}</span>
                  </li>
                ))}
              </ul>
              <button
                type="button"
                className="btn btn-primary"
                onClick={() => goTo(formatHash("drill", "review"))}
              >
                Start reviews
              </button>
            </>
          ) : (
            <p className="home-empty">
              Nothing due —{" "}
              <button
                type="button"
                className="btn"
                onClick={() => goTo(formatHash("drill", "random"))}
              >
                drill something new
              </button>
            </p>
          )}
        </section>

        <section className="panel card--deco home-section">
          <header className="home-head">
            <div>
              <span className="home-eyebrow">The Curriculum</span>
              <h2 className="home-section-title">Learning path</h2>
            </div>
            <span className="home-path-key">
              Solid ≥{Math.round(MASTERY_ACCURACY_THRESHOLD * 100)}% ·{" "}
              {MASTERY_ATTEMPTS_THRESHOLD}+ reps
            </span>
          </header>
          <ol className="home-path">
            {LEARNING_PATH.map((node) => {
              const mastery = masteryFor(node.leakCategories, leaks);
              return (
                <li key={node.title}>
                  <button
                    type="button"
                    className="btn home-path-node"
                    onClick={() => goTo(formatHash("drill", node.mode))}
                  >
                    <span className="home-path-title">{node.title}</span>
                    <span className={`badge mastery ${MASTERY_TONE[mastery]}`}>
                      {MASTERY_LABEL[mastery]}
                    </span>
                  </button>
                </li>
              );
            })}
          </ol>
        </section>
      </div>

      {/* --- lower fold: attendance heat calendar + the House Recap --- */}
      <div className="home-lower">
        {calendar && calendar.length > 0 && (
          <section className="panel card--deco home-section home-cal">
            <header className="home-head">
              <div>
                <span className="home-eyebrow">Attendance</span>
                <h3 className="home-section-title">Streak calendar</h3>
              </div>
              <span className="new-tag" aria-hidden="true">
                New
              </span>
            </header>
            {/* 7 weekday rows (Mon-aligned), weeks flow down the columns —
                grid-auto-flow: column fills top-to-bottom then left-to-right,
                matching the Monday-aligned array order (index i → weekday i%7,
                week ⌊i/7⌋). Each cell carries its own text alternative. */}
            <div className="cal-grid" role="list" aria-label="Practice attendance, last 8 weeks">
              {calendar.map((d) => {
                const step = calStep(d.attempts);
                const acc = Math.round(d.accuracy * 100);
                const label =
                  d.attempts > 0
                    ? `${d.attempts} spots on ${prettyDate(d.date)} (${acc}% accuracy)`
                    : `No practice on ${prettyDate(d.date)}`;
                return (
                  <span
                    key={d.date}
                    role="listitem"
                    className={`cal-cell l${step}`}
                    title={label}
                    aria-label={label}
                  />
                );
              })}
            </div>
            <div className="cal-legend">
              <span>Less</span>
              <span className="cal-cell l0" aria-hidden="true" />
              <span className="cal-cell l1" aria-hidden="true" />
              <span className="cal-cell l2" aria-hidden="true" />
              <span className="cal-cell l3" aria-hidden="true" />
              <span className="cal-cell l4" aria-hidden="true" />
              <span>More</span>
              <span className="cal-legend-note">last 8 weeks</span>
            </div>
          </section>
        )}

        <section className="panel card--deco home-section home-recap">
          <header className="home-head">
            <div>
              <span className="home-eyebrow">The House Recap</span>
              <h3 className="home-section-title">Last session</h3>
            </div>
            <span className="new-tag" aria-hidden="true">
              New
            </span>
          </header>
          {recap && recap.day ? (
            <>
              <dl className="recap-stats">
                <div className="recap-stat">
                  <dd className="recap-figure">{recap.hands}</dd>
                  <dt className="recap-label">Hands played</dt>
                </div>
                <div className="recap-stat">
                  <dd className="recap-figure">
                    {Math.round(recap.accuracy * 100)}
                    <span className="recap-pct">%</span>
                  </dd>
                  <dt className="recap-label">Accuracy</dt>
                </div>
                <div className="recap-stat">
                  <dd className="recap-figure loss">−{recap.bb_given_up.toFixed(1)}</dd>
                  <dt className="recap-label">bb given up · approx.</dt>
                </div>
              </dl>
              {recap.biggest_miss ? (
                <div className="recap-miss">
                  <span className="recap-miss-badge">Biggest miss</span>
                  <div className="recap-miss-body">
                    <span className="recap-miss-label">{recap.biggest_miss.label}</span>
                    <span className="recap-miss-cost mono">
                      cost ≈ {recap.biggest_miss.ev_loss_bb.toFixed(1)}bb · approx.
                    </span>
                  </div>
                </div>
              ) : (
                <p className="recap-clean">No costly misses — a clean session.</p>
              )}
            </>
          ) : (
            <p className="home-empty recap-empty">
              No sessions yet —{" "}
              <button
                type="button"
                className="btn"
                onClick={() => goTo(formatHash("drill", "random"))}
              >
                play your first hands
              </button>
            </p>
          )}
        </section>
      </div>
    </div>
  );
}
