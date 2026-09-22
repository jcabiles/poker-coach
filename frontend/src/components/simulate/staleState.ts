// P4 — the client half of the state token, alone in a module so it can be
// pinned. No React, no fetch; same shape of module as `handCount.ts`.
//
// WHY THIS IS A MODULE AND NOT TWO EXPRESSIONS IN THE VIEW. Both halves decide
// whether a write the player already pressed is allowed to land. `isStaleState`
// is the one status the view recovers from by refetching rather than by showing
// an error, and `withStateToken` is the only thing that puts the observed state
// on the wire — a token dropped or double-encoded here reads as a mismatch, and
// the server answers every mismatch with a refusal. Neither is observable from
// a green build, so both are tested directly.

/**
 * The status out of a `json<T>` rejection, or null when the error is not one.
 *
 * The client's `json<T>()` throws Error("<url> -> <status>") on non-2xx and
 * keeps nothing else — the body is dropped (finding ledger B20) — so the status
 * is only recoverable as a suffix of the message. One reader for it, rather
 * than a regex per caller.
 */
export function errorStatus(err: unknown): number | null {
  const m = err instanceof Error ? / -> (\d{3})$/.exec(err.message) : null;
  return m ? Number(m[1]) : null;
}

/**
 * A write refused because the client acted on a state the server has moved on
 * from — another device (or another tab) got there first. The recovery is to
 * refetch and tell the player, never to retry the write on their behalf: the
 * spot they decided at no longer exists.
 */
export function isStaleState(err: unknown): boolean {
  return errorStatus(err) === 409;
}

/**
 * Put the observed state token on a request path as a query parameter.
 *
 * It is a query parameter and not a body field because the action body is
 * `Decision`, domain core shared with Practice grading. The token is encoded
 * (it is server-derived today, but a path that only works for the shapes the
 * server happens to mint now is a trap), and an existing query string is kept
 * rather than replaced.
 */
export function withStateToken(path: string, token: string): string {
  const sep = path.includes("?") ? "&" : "?";
  return `${path}${sep}state_token=${encodeURIComponent(token)}`;
}
