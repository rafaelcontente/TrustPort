.PHONY: install run-api run-mcp test lint clean help

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install project dependencies
	.venv/bin/pip install -e ".[dev]"
	.venv/bin/pip install "mcp>=1,<2"

run-api: ## Start the TrustPort API server (uvicorn)
	PYTHONPATH=src .venv/bin/python -m uvicorn trust_net_port.api:app --reload --host 127.0.0.1 --port 8000

run-mcp: ## Start the MCP server (for Claude Desktop)
	PYTHONPATH=src .venv/bin/python mcp_server.py

test: ## Run all tests with coverage
	PYTHONPATH=src .venv/bin/pytest tests/ --cov=src/trust_net_port --cov-fail-under=75 -q

lint: ## Run ruff linter and formatter
	.venv/bin/ruff check src/ tests/
	.venv/bin/ruff format --check src/ tests/

lint-fix: ## Auto-fix lint and format issues
	.venv/bin/ruff check --fix src/ tests/
	.venv/bin/ruff format src/ tests/

clean: ## Remove build artifacts
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .coverage htmlcov/
