# The one gate: `make check` runs format check + lint + type check + tests for both halves.
# CI runs the same two halves (check-backend, check-frontend). `make fix` applies the formatters.
# Backend commands run from backend/ with PYTHONPATH=. so a worktree checks its own source,
# not the main checkout the shared venv was installed from.

.DEFAULT_GOAL := check

BACKEND  := backend
FRONTEND := frontend
VENV     := $(BACKEND)/.venv/bin
NPMBIN   := $(FRONTEND)/node_modules/.bin

.PHONY: check check-backend check-frontend fix \
        fmt-check-backend lint-backend typecheck-backend test-backend \
        fmt-check-frontend lint-frontend typecheck-frontend test-frontend build-frontend

check: check-backend check-frontend

check-backend: fmt-check-backend lint-backend typecheck-backend test-backend
check-frontend: fmt-check-frontend lint-frontend typecheck-frontend test-frontend build-frontend

# --- backend ---------------------------------------------------------------
fmt-check-backend:
	cd $(BACKEND) && .venv/bin/ruff format --check .

lint-backend:
	cd $(BACKEND) && .venv/bin/ruff check .

typecheck-backend:
	cd $(BACKEND) && PYTHONPATH=. .venv/bin/mypy app

# pytest plus the live boot probe (alembic upgrade + route probes). Never run two at once:
# the probe migrates backend/data/poker_coach.db.
test-backend:
	./scripts/verify.sh

# --- frontend --------------------------------------------------------------
fmt-check-frontend:
	cd $(FRONTEND) && node_modules/.bin/biome format src

lint-frontend:
	cd $(FRONTEND) && node_modules/.bin/biome ci src

typecheck-frontend:
	cd $(FRONTEND) && node_modules/.bin/tsc --noEmit

test-frontend:
	cd $(FRONTEND) && node_modules/.bin/vitest run

build-frontend:
	cd $(FRONTEND) && node_modules/.bin/vite build

# --- autofix ---------------------------------------------------------------
fix:
	cd $(BACKEND) && .venv/bin/ruff format . && .venv/bin/ruff check --fix .
	cd $(FRONTEND) && node_modules/.bin/biome check --write src

# --- agent tickets ---------------------------------------------------------
MAIN := $(patsubst %/,%,$(dir $(shell git rev-parse --path-format=absolute --git-common-dir)))
BASE ?= main

# Claim an agent ticket: `make ticket ID=<id>` creates .worktrees/<id> on branch ticket/<id>
# from $(BASE). An existing branch means another session already claimed it. Values reach the
# shell as environment variables, never as recipe text, and a missing tool folder stops the claim.
# Tool folders installed in the main checkout, linked into each ticket worktree.
LINK_DIRS := backend/.venv frontend/node_modules

.PHONY: ticket
ticket: export TICKET_ID = $(ID)
ticket: export TICKET_BASE = $(BASE)
ticket: export TICKET_MAIN = $(MAIN)
ticket: export TICKET_LINKS = $(LINK_DIRS)
ticket:
	@case "$$TICKET_ID" in "") echo "usage: make ticket ID=<ticket id> [BASE=<branch>]"; exit 2 ;; -* | .* | *[!A-Za-z0-9._-]*) echo "ticket id may use only letters, digits, dot, dash and underscore"; exit 2 ;; esac; \
	case "$$TICKET_BASE" in "" | -*) echo "BASE must name a branch"; exit 2 ;; esac; \
	for d in $$TICKET_LINKS; do test -e "$$TICKET_MAIN/$$d" || { echo "not claimed: $$d is missing in the main checkout; install dependencies there first"; exit 1; }; done; \
	if git show-ref --verify --quiet "refs/heads/ticket/$$TICKET_ID"; then echo "ticket $$TICKET_ID is already claimed (branch ticket/$$TICKET_ID exists)"; exit 1; fi; \
	set -e; git -C "$$TICKET_MAIN" worktree add -b "ticket/$$TICKET_ID" "$$TICKET_MAIN/.worktrees/$$TICKET_ID" "$$TICKET_BASE"; \
	for d in $$TICKET_LINKS; do ln -s "$$TICKET_MAIN/$$d" "$$TICKET_MAIN/.worktrees/$$TICKET_ID/$$d"; done; \
	echo "claimed: $$TICKET_MAIN/.worktrees/$$TICKET_ID"
