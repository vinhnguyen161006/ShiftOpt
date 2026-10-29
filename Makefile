.PHONY: install conventions lint typecheck test openapi up down

install:
	cd engine && uv sync --locked
	cd backend && uv sync --locked
	cd frontend && npm ci

conventions:
	python scripts/check_conventions.py

lint:
	cd engine && uv run --locked ruff format --check . && uv run --locked ruff check .
	cd backend && uv run --locked ruff format --check . && uv run --locked ruff check .
	cd frontend && npm run lint

typecheck:
	cd engine && uv run --locked mypy src tests benchmarks
	cd backend && uv run --locked mypy src tests migrations/env.py scripts
	cd frontend && npm run typecheck

test:
	cd engine && uv run --locked pytest -q --cov=shiftopt --cov-fail-under=80
	cd backend && uv run --locked pytest -q

openapi:
	cd backend && uv run --locked python -m scripts.export_openapi
	cd frontend && npm run gen:api

up:
	docker compose up -d --build

down:
	docker compose down
