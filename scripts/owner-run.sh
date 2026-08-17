#!/usr/bin/env bash
# S5 — THE continue_ref PROBE. Six short waves, about 45 minutes in total.
#
#   bash ~/Documents/Github/poker-coach/scripts/owner-run.sh
#
# WHAT THIS IS, in plain terms. Stage 1 tried 730 different bot settings and
# none of them played close enough to a human while still behaving like its own
# character. The dial that mattered most — how readily a bot calls — was already
# pushed as far as it is allowed to go in every persona's best result, so there
# is nothing left to squeeze inside the space we searched. This run tests the one
# dial stage 1 was never allowed to touch, to find out whether it moves the
# result at all. If it does not, the ceiling is real and diagnosed; if it does,
# it is a lead worth following, not an answer.
#
# WHAT IT DOES. Six waves, one per persona, six simulations each: one at the
# starting point, then five with the frozen dial set across its full permitted
# range. Same runner, same checks and same bookkeeping as the stage-1 waves — it
# only points at a different set of configs.
#
# COST. 42 runs. The study goes from 758 to 800 of its 1,500-run cap.
#
# THIS IS SHORT ENOUGH TO WATCH. Roughly 45 minutes, not an overnight run. Keep
# the machine plugged in and leave it otherwise idle: the speed check that
# decides whether a batch is trustworthy is sensitive to other programs
# competing for the processor. Closing the lid is safe. Ctrl-C is not — a wave
# has no resume point, so interrupting one throws away its work and re-spends
# those runs.
#
# IF SOMETHING GOES WRONG. Re-running this exact command is always safe: it
# reads what is already on disk and picks up at the next unfinished wave. A wave
# that cannot finish is marked blocked, its evidence is left untouched, and the
# remaining waves still run. Tell Claude when it finishes either way.
set -euo pipefail

# The wave runner needs bash 4 or newer; macOS ships bash 3.2 as /bin/bash.
exec /opt/homebrew/bin/bash \
  -c 'STAGE=probes exec bash "$1"' _ \
  "$HOME/Documents/Github/poker-coach/docs/ai-dlc/research/persona-realism-artifacts/reachability-s5/owner-run-sweep.sh"
