---
description: Format code and sort imports
---

# Code Formatting Workflow

This workflow ensures code follows the project's style guidelines using black and isort.

## Format Python Code

### Format all code (automatic fix)
// turbo
```bash
cd /Users/mmornati/Projects/home-assistant-csnet-home
black custom_components/csnet_home tests
```

### Check formatting without changes
// turbo
```bash
cd /Users/mmornati/Projects/home-assistant-csnet-home
black --check custom_components/csnet_home tests
```

## Sort Imports

### Sort all imports (automatic fix)
// turbo
```bash
cd /Users/mmornati/Projects/home-assistant-csnet-home
isort custom_components/csnet_home tests
```

### Check import sorting without changes
// turbo
```bash
cd /Users/mmornati/Projects/home-assistant-csnet-home
isort --check-only custom_components/csnet_home tests
```

## Quick Format Script

Use the included script to format everything at once:
// turbo
```bash
cd /Users/mmornati/Projects/home-assistant-csnet-home
./format-code.sh
```

## Pre-commit Hooks

Pre-commit hooks automatically format code before commits. To run manually:
// turbo
```bash
cd /Users/mmornati/Projects/home-assistant-csnet-home
pre-commit run --all-files
```

## Format Specific Files

```bash
cd /Users/mmornati/Projects/home-assistant-csnet-home

# Format single file
black custom_components/csnet_home/api.py
isort custom_components/csnet_home/api.py

# Format directory
black custom_components/csnet_home/
isort custom_components/csnet_home/
```

## Configuration

Formatting configuration is defined in:
- **black:** `pyproject.toml` or `.black` config
- **isort:** `setup.cfg` or `.isort.cfg`
- **pre-commit:** `.pre-commit-config.yaml`
