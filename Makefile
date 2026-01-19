# Makefile for logfire-cli development
# =============================================================================

.PHONY: help install install-dev sync lint lint-check lint-fix format typecheck test test-coverage test-integration test-integration-update ci check docs docs-serve clean build publish markdownlint markdownlint-fix yamlfix yamlfix-check

# Default target
help:
	@echo "Logfire CLI Development Commands"
	@echo "================================="
	@echo ""
	@echo "Setup:"
	@echo "  install          Install production dependencies"
	@echo "  install-dev      Install with development dependencies"
	@echo "  sync             Sync all dependencies (recommended)"
	@echo ""
	@echo "Quality:"
	@echo "  lint             Run linting (alias for lint-check)"
	@echo "  lint-check       Check code with ruff (no fixes)"
	@echo "  lint-fix         Auto-fix linting issues"
	@echo "  format           Format code with ruff"
	@echo "  typecheck        Run type checking with basedpyright"
	@echo "  markdownlint     Check Markdown files with markdownlint"
	@echo "  markdownlint-fix Auto-fix Markdown linting issues"
	@echo "  yamlfix          Format YAML files with yamlfix"
	@echo "  yamlfix-check    Check YAML files without modifying"
	@echo ""
	@echo "Testing:"
	@echo "  test             Run tests"
	@echo "  test-coverage    Run tests with coverage report"
	@echo "  test-integration Run integration tests (requires LOGFIRE_* env vars)"
	@echo "  test-integration-update Update integration test snapshots"
	@echo ""
	@echo "CI/CD:"
	@echo "  ci               Run all CI checks (lint, typecheck, markdownlint, yamlfix, test)"
	@echo "  check            Alias for ci"
	@echo ""
	@echo "Documentation:"
	@echo "  docs             Build documentation"
	@echo "  docs-serve       Serve documentation locally"
	@echo ""
	@echo "Build:"
	@echo "  build            Build package"
	@echo "  clean            Clean build artifacts"
	@echo "  publish          Publish to PyPI (requires auth)"

# =============================================================================
# Setup
# =============================================================================

install:
	uv sync --no-group dev --no-group docs

install-dev:
	uv sync --group dev --group docs

sync:
	uv sync --group dev --group docs

# =============================================================================
# Code Quality
# =============================================================================

lint: lint-check

lint-check:
	uv run ruff check src tests
	uv run ruff format --check src tests

lint-fix:
	uv run ruff check --fix src tests
	uv run ruff format src tests

format:
	uv run ruff format src tests

typecheck:
	@echo "Running type checking..."
	@uv run basedpyright --outputjson > /tmp/pyright.json 2>&1 || true
	@uv run basedpyright || true
	@python3 -c "import json, sys; data = json.load(open('/tmp/pyright.json')); errors = [d for d in data.get('generalDiagnostics', []) if d.get('severity') == 'error']; warnings = [d for d in data.get('generalDiagnostics', []) if d.get('severity') == 'warning']; print(f'\nType checking: {len(warnings)} warnings, {len(errors)} errors'); sys.exit(1 if (errors or warnings) else 0)" || exit 1

markdownlint:
	@command -v markdownlint >/dev/null 2>&1 || { echo "Error: markdownlint not found. Install with: npm install -g markdownlint-cli"; exit 1; }
	markdownlint "**/*.md" --ignore node_modules

markdownlint-fix:
	@command -v markdownlint >/dev/null 2>&1 || { echo "Error: markdownlint not found. Install with: npm install -g markdownlint-cli"; exit 1; }
	markdownlint "**/*.md" --fix --ignore node_modules

yamlfix:
	@find . -name "*.yaml" -o -name "*.yml" | grep -v node_modules | grep -v ".venv" | grep -v ".pytest_cache" | xargs uv run yamlfix

yamlfix-check:
	@find . -name "*.yaml" -o -name "*.yml" | grep -v node_modules | grep -v ".venv" | grep -v ".pytest_cache" | grep -v ".github/workflows" | xargs uv run yamlfix --check

# =============================================================================
# Testing
# =============================================================================

test:
	uv run pytest

test-coverage:
	uv run pytest --cov --cov-report=term-missing --cov-report=html

test-integration:
	uv run pytest -m integration -v tests/test_integration.py tests/test_client_integration.py

test-integration-update:
	uv run pytest -m integration --inline-snapshot=update tests/test_integration.py tests/test_client_integration.py

# =============================================================================
# CI/CD
# =============================================================================

ci: lint-check typecheck markdownlint yamlfix-check test
	@echo ""
	@echo "All CI checks passed!"

check: ci

# =============================================================================
# Documentation
# =============================================================================

docs:
	uv run --group docs mkdocs build

docs-serve:
	uv run --group docs mkdocs serve

# =============================================================================
# Build & Release
# =============================================================================

build: clean
	uv build

clean:
	rm -rf build dist *.egg-info
	rm -rf .pytest_cache .ruff_cache .coverage htmlcov
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

publish: build
	uv publish
