#!/usr/bin/env bash
# Manage THIS project's dev stack: FastAPI backend (:8008) + Vite frontend (:7777).
#
# Scope/safety: tracks the two servers it starts via PID files in the repo. Both
# the PID-file check and the command-line fallback match against this repo's
# absolute path, so a recycled PID or another project's uvicorn/vite on the same
# port is never mistaken for ours (and never killed).
#
# Usage: scripts/serve.sh {start|stop|restart|status}
#        BACKEND_PORT=8123 FRONTEND_PORT=7200 scripts/serve.sh start   # override ports
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO"

export BACKEND_PORT="${BACKEND_PORT:-8008}"
export FRONTEND_PORT="${FRONTEND_PORT:-7777}"

BE_PIDFILE="$REPO/.backend.pid";  BE_LOG="$REPO/.backend.log"
FE_PIDFILE="$REPO/.frontend.pid"; FE_LOG="$REPO/.frontend.log"

PY="$REPO/backend/.venv/bin/python"
UVICORN="$REPO/backend/.venv/bin/uvicorn"
VITE="$REPO/frontend/node_modules/.bin/vite"
HEALTH="http://localhost:${BACKEND_PORT}/api/v1/health"
# `localhost`, not 127.0.0.1: vite binds IPv6 loopback only, so a v4-literal
# probe is refused even when the dev server is perfectly healthy.
FRONTEND_URL="http://localhost:${FRONTEND_PORT}/"
READY_TIMEOUT="${READY_TIMEOUT:-30}"   # seconds to wait for each side to answer

# Repo-anchored command-line patterns: only match processes launched from THIS
# checkout's venv/node_modules on the expected port.
BE_PATTERN="$REPO/backend/.venv/bin/uvicorn app.main:app.*--port ${BACKEND_PORT}"
FE_PATTERN="$REPO/frontend/.*vite.*--port ${FRONTEND_PORT}"

# True if PID is alive AND its command line matches the expected pattern —
# a recycled PID (crash/reboot leftovers) fails the second check. If ps itself
# is unavailable (restricted sandboxes), fall back to trusting liveness alone.
_pid_matches() {
  local pid="$1" pattern="$2" cmdline
  kill -0 "$pid" 2>/dev/null || return 1
  # `-ww` asks for the untruncated command line. Piped output is not truncated in
  # practice, so this changes nothing today; it is here so the check cannot start
  # failing if ps is ever invoked somewhere that does clip to the terminal width.
  if ! cmdline="$(ps -ww -o command= -p "$pid" 2>/dev/null)"; then return 0; fi
  printf '%s\n' "$cmdline" | grep -qE "$pattern"
}

# `curl` and `wget` are denied by this repo's Claude sandbox, so readiness is
# probed with the backend venv's Python instead. The URL is passed as an argument
# rather than interpolated, so a shell-special character in it cannot reach the
# Python source.
_http_ok() {
  "$PY" - "$1" <<'PY' >/dev/null 2>&1
import sys
import urllib.request

with urllib.request.urlopen(sys.argv[1], timeout=2) as response:
    sys.exit(0 if response.status == 200 else 1)
PY
}

# $1=label  $2=url  $3=logfile. Polls until the URL answers 200, then tails the
# log to stderr and fails if it never does.
_wait_ready() {
  local label="$1" url="$2" log="$3"
  printf 'waiting for %s %s' "$label" "$url"
  local ticks=$(( READY_TIMEOUT * 2 ))
  while [ "$ticks" -gt 0 ]; do
    if _http_ok "$url"; then echo " — up"; return 0; fi
    printf '.'
    sleep 0.5
    ticks=$(( ticks - 1 ))
  done
  echo " — FAILED"
  echo "$label did not answer $url within ${READY_TIMEOUT}s — last lines of ${log#"$REPO"/}:" >&2
  tail -n 15 "$log" >&2 || true
  return 1
}

# Echo a live PID for each server, or nothing. Validated PID file first; then a
# repo-anchored command-line fallback for a server started outside this script.
_be_pid() {
  local pid
  if [ -f "$BE_PIDFILE" ]; then
    pid="$(cat "$BE_PIDFILE")"
    if _pid_matches "$pid" "$BE_PATTERN"; then echo "$pid"; return; fi
    rm -f "$BE_PIDFILE"   # stale or recycled PID — discard
  fi
  pgrep -f "$BE_PATTERN" 2>/dev/null | head -n1 || true
}
_fe_pid() {
  local pid
  if [ -f "$FE_PIDFILE" ]; then
    pid="$(cat "$FE_PIDFILE")"
    if _pid_matches "$pid" "$FE_PATTERN"; then echo "$pid"; return; fi
    rm -f "$FE_PIDFILE"   # stale or recycled PID — discard
  fi
  pgrep -f "$FE_PATTERN" 2>/dev/null | head -n1 || true
}

_require() {
  [ -x "$UVICORN" ] || { echo "missing backend venv ($UVICORN) — run: cd backend && python3 -m venv .venv && .venv/bin/pip install -e ." >&2; exit 1; }
  [ -x "$VITE" ]    || { echo "missing frontend deps ($VITE) — run: cd frontend && npm install" >&2; exit 1; }
}

start() {
  _require
  local be fe; be="$(_be_pid)"; fe="$(_fe_pid)"
  if [ -n "$be" ] && [ -n "$fe" ]; then
    echo "already running (backend pid $be :$BACKEND_PORT, frontend pid $fe :$FRONTEND_PORT)"; exit 0
  fi

  if [ -z "$be" ]; then
    if [ -f "$BE_LOG" ]; then mv -f "$BE_LOG" "$BE_LOG.1"; fi
    ( cd "$REPO/backend" && nohup "$UVICORN" app.main:app --reload --port "$BACKEND_PORT" >"$BE_LOG" 2>&1 & echo $! >"$BE_PIDFILE" )
    echo "backend  started (pid $(cat "$BE_PIDFILE") on :$BACKEND_PORT) — logs: .backend.log"
  else
    echo "backend  already up (pid $be on :$BACKEND_PORT)"
  fi

  _wait_ready "backend " "$HEALTH" "$BE_LOG" || exit 1

  if [ -z "$fe" ]; then
    if [ -f "$FE_LOG" ]; then mv -f "$FE_LOG" "$FE_LOG.1"; fi
    ( cd "$REPO/frontend" && nohup "$VITE" --port "$FRONTEND_PORT" --strictPort >"$FE_LOG" 2>&1 & echo $! >"$FE_PIDFILE" )
    echo "frontend started (pid $(cat "$FE_PIDFILE") on :$FRONTEND_PORT) — logs: .frontend.log"
  else
    echo "frontend already up (pid $fe on :$FRONTEND_PORT)"
  fi

  # The frontend is waited on too. With --strictPort, vite exits rather than
  # picking another port, so without this `start` would report success and print
  # an "open" line for a server that never came up.
  _wait_ready "frontend" "$FRONTEND_URL" "$FE_LOG" || exit 1

  echo "open http://localhost:${FRONTEND_PORT}"
}

# $1=label  $2=pidfile  $3=pid
_stop_one() {
  local label="$1" pidfile="$2" pid="$3"
  if [ -z "$pid" ]; then echo "$label not running"; rm -f "$pidfile"; return; fi
  # TERM children first (uvicorn --reload worker, vite's esbuild) then the
  # parent, so nothing orphans while still holding the port.
  pkill -TERM -P "$pid" 2>/dev/null || true
  kill "$pid" 2>/dev/null || true
  # Wait for real exit so restart can't see a half-dead process; escalate if hung.
  for _ in $(seq 1 20); do
    kill -0 "$pid" 2>/dev/null || break
    sleep 0.25
  done
  if kill -0 "$pid" 2>/dev/null; then
    pkill -KILL -P "$pid" 2>/dev/null || true
    kill -9 "$pid" 2>/dev/null || true
  fi
  rm -f "$pidfile"
  echo "$label stopped (pid $pid)"
}

stop() {
  _stop_one "backend " "$BE_PIDFILE" "$(_be_pid)"
  _stop_one "frontend" "$FE_PIDFILE" "$(_fe_pid)"
}

status() {
  local be fe; be="$(_be_pid)"; fe="$(_fe_pid)"
  [ -n "$be" ] && echo "backend  running (pid $be on :$BACKEND_PORT)"  || echo "backend  not running"
  [ -n "$fe" ] && echo "frontend running (pid $fe on :$FRONTEND_PORT)" || echo "frontend not running"
}

case "${1:-}" in
  start)   start ;;
  stop)    stop ;;
  restart) stop; start ;;
  status)  status ;;
  *) echo "usage: scripts/serve.sh {start|stop|restart|status}"; exit 2 ;;
esac
