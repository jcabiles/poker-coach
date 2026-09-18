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
