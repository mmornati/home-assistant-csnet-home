# Makefile for CSNet Home Custom Component Development

.PHONY: help test test-unit test-integration start stop restart logs clean format lint install-dev package

help:
	@echo "CSNet Home Development Commands"
	@echo "================================"
	@echo ""
	@echo "Development:"
	@echo "  make install-dev      Install development dependencies"
	@echo "  make format           Format code with black and isort"
	@echo "  make lint             Run linters (pylint, mypy)"
	@echo "  make package          Build a distributable zip for manual testing"
	@echo ""
	@echo "Testing:"
	@echo "  make test             Run all tests"
	@echo "  make test-unit        Run unit tests only"
	@echo "  make test-integration Start integration testing environment"
	@echo ""
	@echo "Integration Testing:"
	@echo "  make start            Start Home Assistant for testing"
	@echo "  make stop             Stop Home Assistant"
	@echo "  make restart          Restart Home Assistant"
	@echo "  make logs             Show Home Assistant logs"
	@echo "  make clean            Clean all test data"
	@echo ""

PYTHON_BIN ?= python3

install-dev:
	@if ! command -v $(PYTHON_BIN) >/dev/null 2>&1; then \
		echo "❌ $(PYTHON_BIN) not found. Please install Python 3.13 and try again (or run 'make install-dev PYTHON_BIN=python3.13')."; \
		exit 1; \
	fi
	@if ! $(PYTHON_BIN) -c "import sys; sys.exit(0 if sys.version_info[:2] == (3, 13) else 1)" >/dev/null 2>&1; then \
		echo "❌ $(PYTHON_BIN) must point to Python 3.13.x (found $$($(PYTHON_BIN) -V 2>&1))."; \
		echo "   Override with 'make install-dev PYTHON_BIN=python3.13' if you have multiple Python versions installed."; \
		exit 1; \
	fi
	@if [ -d .venv ] && [ -f .venv/pyvenv.cfg ] && ! grep -q "version = 3\.13" .venv/pyvenv.cfg; then \
		echo "Detected virtual environment with incorrect Python version. Recreating..."; \
		rm -rf .venv; \
	fi
	@echo "Creating virtual environment (.venv) with $(PYTHON_BIN)..."
	$(PYTHON_BIN) -m venv .venv
	@echo "Installing development dependencies inside .venv..."
	. .venv/bin/activate && pip install --upgrade pip
	. .venv/bin/activate && pip install -r custom_components/csnet_home/requirements-dev.txt
	. .venv/bin/activate && python -m pip install --upgrade --force-reinstall pre-commit
	. .venv/bin/activate && python -m pip install "PyYAML==6.0.2"
	@HOOKS_PATH=$$(git config --get core.hooksPath || true); \
	if [ -n "$$HOOKS_PATH" ]; then \
		echo "⚠️ Git config 'core.hooksPath' is set to '$$HOOKS_PATH'. Skipping pre-commit hook installation."; \
		echo "   Run 'git config --unset core.hooksPath' (or '--global') and re-run 'make install-dev' to install hooks automatically."; \
	else \
		. .venv/bin/activate && pre-commit install; \
	fi
	@echo "✅ Environment ready. Activate it with: source .venv/bin/activate"

format:
	@echo "Formatting code..."
	black custom_components/csnet_home/
	black tests/
	isort custom_components/csnet_home/
	isort tests/

lint:
	@echo "Running linters..."
	pylint custom_components/csnet_home/
	mypy custom_components/csnet_home/

test: test-unit
	@echo "All tests completed!"

test-unit:
	@echo "Running unit tests..."
	@if [ ! -d .venv ]; then \
		echo "❌ Virtualenv (.venv) not found. Run 'make install-dev' first."; \
		exit 1; \
	fi
	. .venv/bin/activate && python -m pytest tests/ -v --cov=custom_components.csnet_home --cov-report=html --cov-report=term

test-integration:
	@echo "Starting integration testing environment..."
	./scripts/integration-test.sh start

start:
	./scripts/integration-test.sh start

stop:
	./scripts/integration-test.sh stop

restart:
	./scripts/integration-test.sh restart

logs:
	./scripts/integration-test.sh logs

status:
	./scripts/integration-test.sh status

clean:
	./scripts/integration-test.sh clean
	@echo "Cleaning Python cache..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "Cleaning coverage reports..."
	rm -rf htmlcov/ .coverage 2>/dev/null || true

package:
	@echo "Creating development zip package..."
	mkdir -p dist
	rm -f dist/hass-custom-csnet-home.zip
	cd custom_components && \
	zip -r ../dist/hass-custom-csnet-home.zip csnet_home \
		-x "*.git*" \
		-x "*__pycache__*" \
		-x "*.pyc" \
		-x "*.pyo" \
		-x "*.DS_Store" \
		-x "*.pytest_cache*"
	@echo "✅ Package created at dist/hass-custom-csnet-home.zip"
