.PHONY: install test lint format bench demo clean

install:
	pip install -e ".[dev]"

test:
	pytest tests/ -q --cov=src --cov-report=term-missing

lint:
	ruff check src/ tests/ benchmarks/
	mypy src/

format:
	ruff format src/ tests/ benchmarks/

bench:
	@echo "Running benchmarks (seeds fixed for reproducibility)..."
	python benchmarks/run.py || echo "(Placeholder: create benchmarks/run.py with fixed seeds)"

demo:
	@echo "Starting TrustPort API..."
	uvicorn trust_net_port.api:app --reload

clean:
	rm -rf .pytest_cache .coverage htmlcov/ *.db __pycache__/
	find . -type d -name __pycache__ -exec rm -rf {} +
