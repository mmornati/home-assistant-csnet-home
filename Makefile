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

install-dev:
	@echo "Creating virtual environment (.venv) if needed..."
	python3 -m venv .venv
	@echo "Installing development dependencies inside .venv..."
	. .venv/bin/activate && pip install --upgrade pip
	. .venv/bin/activate && pip install -r custom_components/csnet_home/requirements-dev.txt
	. .venv/bin/activate && pre-commit install
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
	pytest tests/ -v --cov=custom_components.csnet_home --cov-report=html --cov-report=term

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
