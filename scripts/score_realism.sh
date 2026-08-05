#!/usr/bin/env bash
# One-command bridge: run the poker-analytics stub scorer against a local sim
# export from this repo.
#
# Usage: scripts/score_realism.sh [batch_dir] [scorer args...]
#   batch_dir defaults to docs/ai-dlc/research/persona-realism-artifacts/remeasure-2026-08-05/sim50k
#   and, if relative, is resolved against the invoking shell's cwd (not the
#   poker-analytics repo, which is where the scorer would otherwise resolve it).
#   To skip batch_dir and go straight to scorer args, use one of:
#     scripts/score_realism.sh "" --out FILE     # explicit empty placeholder
#     scripts/score_realism.sh -- --out FILE     # -- means "use default dir"
#     scripts/score_realism.sh --out FILE        # a leading flag also means "use default dir"
#   any args after batch_dir are passed through to score_stub.py (e.g. --out FILE)
#
# poker-analytics root resolution: $POKER_ANALYTICS_DIR if set and non-empty,
# else the sibling checkout <repo root>/../poker-analytics.
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"

ANALYTICS_DIR="${POKER_ANALYTICS_DIR:-}"
if [ -z "$ANALYTICS_DIR" ]; then
  ANALYTICS_DIR="$(cd "$REPO/.." && pwd)/poker-analytics"
fi

if [ ! -d "$ANALYTICS_DIR" ]; then
  echo "poker-analytics checkout not found at $ANALYTICS_DIR — set POKER_ANALYTICS_DIR to point at it" >&2
  exit 1
fi

PYTHON="$ANALYTICS_DIR/.venv/bin/python"
if [ ! -x "$PYTHON" ]; then
  echo "missing $PYTHON — run: cd $ANALYTICS_DIR && make venv" >&2
  exit 1
fi

SCORER="$ANALYTICS_DIR/scorer/score_stub.py"
if [ ! -f "$SCORER" ]; then
  echo "missing $SCORER — this poker-analytics checkout predates flywheel S1" >&2
  exit 1
fi

DEFAULT_DIR="$REPO/docs/ai-dlc/research/persona-realism-artifacts/remeasure-2026-08-05/sim50k"

if [ $# -eq 0 ]; then
  BATCH_DIR="$DEFAULT_DIR"
else
  case "$1" in
    "")  BATCH_DIR="$DEFAULT_DIR"; shift ;;   # explicit empty placeholder
    --)  BATCH_DIR="$DEFAULT_DIR"; shift ;;   # "--" also means "use default dir"
    -*)  BATCH_DIR="$DEFAULT_DIR" ;;          # leading flag: default dir, ALL args pass through
    *)   BATCH_DIR="$1"; shift ;;             # plain path
  esac
fi

# Normal cwd-relative resolution: a relative batch dir is relative to the
# invoking shell's cwd, not the poker-analytics repo (where the scorer would
# otherwise resolve a relative --dir).
case "$BATCH_DIR" in
  /*) : ;;
  *)  BATCH_DIR="$PWD/$BATCH_DIR" ;;
esac

exec "$PYTHON" "$SCORER" --dir "$BATCH_DIR" "$@"
