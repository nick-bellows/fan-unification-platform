# POSIX convenience targets; Windows users run the scripts/*.ps1 equivalents.

.PHONY: check test up down

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
