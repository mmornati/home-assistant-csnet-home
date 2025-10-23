# Workflow Testing - Quick Start

Quick reference for testing GitHub Actions workflows locally.

## 🎯 Choose Your Testing Method

### Static Validation (Fast - No Docker Required)
**Use when:** Quick syntax checks, linting, basic validation  
**Time:** ~10 seconds  
**Requires:** actionlint, yamllint, shellcheck

```bash
./scripts/test-workflows.sh
```

✅ Best for: Quick feedback before commits

### Integration Testing (Comprehensive - Requires Docker)
**Use when:** Full workflow execution, testing actual job runs  
**Time:** 2-5 minutes per workflow  
**Requires:** act, Docker

```bash
act pull_request -W .github/workflows/validate.yaml
```

✅ Best for: Testing complete workflows before PRs

## 📦 Installation

### One-Time Setup
```bash
# Install all tools (macOS)
brew install actionlint yamllint shellcheck act

# Or install individually
brew install actionlint  # Required for static validation
brew install yamllint    # Required for static validation
brew install shellcheck  # Required for static validation
brew install act         # Optional for integration testing
```

## 🚀 Common Testing Workflows

### 1. Before Every Commit (Fast)
```bash
# Run static validation
./scripts/test-workflows.sh
```

### 2. Before Creating PR (Comprehensive)
```bash
# Static validation first
./scripts/test-workflows.sh

# Then integration test
act pull_request -W .github/workflows/validate.yaml
```

### 3. Testing Specific Workflows
```bash
# Test PR preview
act pull_request -W .github/workflows/pr-preview.yaml

# Test workflow validation
act pull_request -W .github/workflows/workflow-validation.yaml

# Test release (dry run)
act workflow_dispatch -W .github/workflows/release.yaml -n
```

### 4. Debug Failed Workflow
```bash
# Run with verbose output
act pull_request -W .github/workflows/validate.yaml -v

# Or run specific job only
act pull_request -j hassfest
```

## 📝 Test Event Payloads

Use pre-configured event payloads for realistic testing:

```bash
# Test with PR event
act pull_request -e .github/act-events/pull_request.json

# Test with workflow dispatch (release)
act workflow_dispatch -e .github/act-events/workflow_dispatch.json

# Test with push event
act push -e .github/act-events/push.json
```

## 🔍 Understanding Results

### Static Validation Results
```
✅ ActionLint passed         # Workflow syntax is valid
✅ YAML Lint passed           # YAML formatting is correct
✅ ShellCheck passed          # Shell scripts have no issues
✅ Zip creation successful    # Release artifact builds correctly
```

### Integration Test Results
```
[Validation/validate] 🚀  Start image=...
[Validation/validate]   🐳  docker pull image=...
[Validation/validate]   🐳  docker run image=...
...
[Validation/validate] ✅  Success - Main actions/checkout@v4
...
```

## 🆘 Quick Troubleshooting

### Static Validation Fails
```bash
# Check which tool failed and fix accordingly
# ActionLint errors → Fix workflow syntax
# YAML Lint errors → Fix indentation/formatting
# ShellCheck errors → Fix shell script issues
```

### Integration Test Fails
```bash
# Make sure Docker is running
docker ps

# Try with verbose output
act pull_request -W .github/workflows/validate.yaml -v

# Use dry run to see what would execute
act pull_request -W .github/workflows/validate.yaml -n
```

### Docker Not Found
```bash
# Start Docker Desktop (macOS/Windows)
# Or install Docker Engine (Linux)
# Verify: docker ps
```

## 📚 Full Documentation

- **[LOCAL_TESTING.md](LOCAL_TESTING.md)** - Complete guide to static validation
- **[INTEGRATION_TESTING.md](INTEGRATION_TESTING.md)** - Complete guide to `act` and Docker testing
- **[act-events/README.md](act-events/README.md)** - Event payload documentation

## 💡 Pro Tips

1. **Use static validation first** - It's faster and catches most issues
2. **Run integration tests before PR** - Catches issues early
3. **Use dry runs** - Preview what will execute: `act -n`
4. **Reuse containers** - Faster iteration: `act --reuse`
5. **Test incrementally** - Fix static issues before running integration tests

## 🎓 Learning Path

1. Start with static validation: `./scripts/test-workflows.sh`
2. Read error messages and fix issues
3. Once comfortable, install `act` and Docker
4. Run simple integration test: `act -l` (list workflows)
5. Try dry run: `act pull_request -n`
6. Run full workflow: `act pull_request`
7. Use verbose mode for debugging: `act pull_request -v`

## ✅ Recommended Workflow

```bash
# 1. Make changes to workflow file
vim .github/workflows/validate.yaml

# 2. Quick validation (10 seconds)
./scripts/test-workflows.sh

# 3. If passed, do integration test (2-5 minutes)
act pull_request -W .github/workflows/validate.yaml

# 4. If all passed, commit and push
git add .github/workflows/validate.yaml
git commit -m "Update validate workflow"
git push
```

Happy testing! 🚀

