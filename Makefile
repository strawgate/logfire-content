# Makefile for logfire-cli development
# =============================================================================

.PHONY: help install install-dev sync lint lint-check lint-fix format typecheck test test-coverage ci check docs docs-serve clean build publish

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
	@echo ""
	@echo "Testing:"
	@echo "  test             Run tests"
	@echo "  test-coverage    Run tests with coverage report"
	@echo ""
	@echo "CI/CD:"
	@echo "  ci               Run all CI checks (lint, typecheck, test)"
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
	uv sync --no-dev

install-dev:
	uv sync --group docs

sync:
	uv sync --group docs

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
	uv run basedpyright

# =============================================================================
# Testing
# =============================================================================

test:
	uv run pytest

test-coverage:
	uv run pytest --cov --cov-report=term-missing --cov-report=html

# =============================================================================
# CI/CD
# =============================================================================

ci: lint-check typecheck test
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
