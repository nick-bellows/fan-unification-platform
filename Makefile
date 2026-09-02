# POSIX convenience targets; Windows users run the scripts/*.ps1 equivalents.

.PHONY: check test up down demo

PREFECT_API_URL ?= http://127.0.0.1:4200/api
export PREFECT_API_URL

demo: ## full local run: generate -> init-db -> pipeline -> evaluate
	fanuni generate
	fanuni init-db
	fanuni pipeline
	fanuni evaluate

check:
	ruff check .
	ruff format --check .
	mypy src tests
	pytest

test:
	pytest

up:
	docker compose up -d --build

down:
	docker compose down
