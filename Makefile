# Makefile for GTMind

install:
	poetry install --no-root

lock:
	poetry lock --no-update

update:
	poetry update

check:
	poetry run ruff check src tests
	poetry run mypy src

check-fix:
	poetry run ruff check src tests --fix

test:
	poetry run pytest -q --tb=short --disable-warnings

coverage:
	poetry run coverage run -m pytest
	poetry run coverage report --show-missing
	poetry run coverage html

clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage

format:
	poetry run ruff format src tests
