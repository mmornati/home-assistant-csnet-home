---
description: Run tests and validate code quality
---

# Run Tests Workflow

This workflow guides you through running tests and validation checks for the home-assistant-csnet-home integration.

## Unit Tests

### Run all tests
// turbo
```bash
cd /Users/mmornati/Projects/home-assistant-csnet-home
pytest
```

### Run specific test file
```bash
cd /Users/mmornati/Projects/home-assistant-csnet-home
pytest tests/test_api.py
```

### Run with verbose output
// turbo
```bash
cd /Users/mmornati/Projects/home-assistant-csnet-home
pytest -v
```

## Coverage Reports

### Terminal coverage report
// turbo
```bash
cd /Users/mmornati/Projects/home-assistant-csnet-home
pytest --cov=custom_components/csnet_home --cov-report term-missing
```

### HTML coverage report
// turbo
```bash
cd /Users/mmornati/Projects/home-assistant-csnet-home
pytest --cov=custom_components/csnet_home --cov-report html
```

After running, open the report:
```bash
open htmlcov/index.html  # macOS
# or: xdg-open htmlcov/index.html  # Linux
```

## Integration Testing

### Start Home Assistant with the integration
```bash
cd /Users/mmornati/Projects/home-assistant-csnet-home
./scripts/integration-test.sh start
```

### View integration test logs
```bash
cd /Users/mmornati/Projects/home-assistant-csnet-home
./scripts/integration-test.sh logs
```

### Restart after code changes
```bash
cd /Users/mmornati/Projects/home-assistant-csnet-home
./scripts/integration-test.sh restart
```

### Stop integration testing
```bash
cd /Users/mmornati/Projects/home-assistant-csnet-home
./scripts/integration-test.sh stop
```

## Workflow Validation

### Validate GitHub Actions workflows
// turbo
```bash
cd /Users/mmornati/Projects/home-assistant-csnet-home
./scripts/test-workflows.sh
```

### Test with act (requires Docker and act installed)
```bash
cd /Users/mmornati/Projects/home-assistant-csnet-home
act pull_request -W .github/workflows/validate.yaml
```

## Quick Commands (Make)

```bash
cd /Users/mmornati/Projects/home-assistant-csnet-home

# Start integration test environment
make start

# View logs
make logs

# Restart (after code changes)
make restart

# Stop
make stop

# Clean all test data
make clean
```

## Pre-commit Checks

The following run automatically on commit via pre-commit hooks:

- **black** - Code formatting
- **isort** - Import sorting
- **pylint** - Linting
- **yamllint** - YAML validation

Manual execution:
```bash
cd /Users/mmornati/Projects/home-assistant-csnet-home
pre-commit run --all-files
```
