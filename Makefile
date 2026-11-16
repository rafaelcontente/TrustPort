.PHONY: install test lint bench demo clean

install:
	python3 -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -e ".[dev]"

test:
	.venv/bin/pytest tests/ -v --tb=short

lint:
	.venv/bin/ruff check src/ tests/ benchmarks/
	.venv/bin/mypy src/

bench:
	bash benchmarks/reproduce.sh

demo:
	.venv/bin/python examples/01_basic_validation.py

clean:
	rm -rf .venv __pycache__ .pytest_cache *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
