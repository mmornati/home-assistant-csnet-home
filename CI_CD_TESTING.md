# CI/CD Testing Documentation

This document describes the comprehensive testing infrastructure for the CSNet Home integration, including automated compatibility testing with multiple Home Assistant versions.

---

## Table of Contents

- [Overview](#overview)
- [Testing Workflows](#testing-workflows)
  - [Validation Workflow](#validation-workflow)
  - [Smoke Test](#smoke-test)
  - [Integration Test](#integration-test)
  - [Nightly Compatibility Check](#nightly-compatibility-check)
- [What Gets Tested](#what-gets-tested)
- [Home Assistant Version Compatibility](#home-assistant-version-compatibility)
- [Test Fixtures](#test-fixtures)
- [Running Tests Locally](#running-tests-locally)
- [Interpreting Test Results](#interpreting-test-results)
- [Troubleshooting](#troubleshooting)

---

## Overview

The CSNet Home integration uses a multi-layered testing approach to ensure compatibility across multiple Home Assistant versions and catch issues early:

```
┌─────────────────────────────────────────────────────────────┐
│                    Testing Pipeline                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Phase 1: Quick Validation (2-3 minutes)                    │
│  ├─ Code style checks (Black)                               │
│  ├─ Linting (Pylint)                                        │
│  ├─ Security scan (Bandit)                                  │
│  ├─ Hassfest validation                                     │
│  └─ HACS validation                                         │
│                                                               │
│  Phase 2: Unit Tests (5-10 minutes)                         │
│  ├─ pytest with multiple HA versions                        │
│  ├─ Python 3.11, 3.12 & 3.13                               │
│  ├─ HA 2025.6, 2025.8, 2025.10                             │
│  └─ Code coverage reporting                                 │
│                                                               │
│  Phase 3: Smoke Tests (2-3 minutes)                         │
│  ├─ Import validation                                        │
│  ├─ Manifest compatibility                                  │
│  ├─ API compatibility checks                                │
│  └─ 4 HA versions tested                                    │
│                                                               │
│  Phase 4: Integration Tests (10-15 minutes)                 │
│  ├─ Docker-based HA container                               │
│  ├─ Real integration loading                                │
│  ├─ Discovery verification                                  │
│  └─ Multiple HA versions                                    │
│                                                               │
│  Phase 5: Nightly Monitoring (Scheduled)                    │
│  ├─ Latest stable HA version                                │
│  ├─ HA dev branch (preview)                                 │
│  ├─ Multiple version smoke tests                            │
│  └─ Automatic issue creation on failure                     │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Testing Workflows

### Validation Workflow

**File**: `.github/workflows/validate.yaml`

**Triggers**:
- Push to main branch
- Pull requests
- Manual dispatch

**What it does**:
1. **Hassfest Validation** - Official Home Assistant integration validation
2. **HACS Validation** - HACS integration standards compliance
3. **Code Style** - Black formatting check
4. **Linting** - Pylint code quality analysis
5. **Unit Tests** - pytest with coverage across multiple HA versions
6. **Security Scan** - Bandit security vulnerability detection

**Matrix Testing**:
```yaml
Python versions: [3.11, 3.12, 3.13]
HA versions: [2025.6.0, 2025.8.0, 2025.10.0]
Total combinations: 9
```

**Example Output**:
```
✓ Hassfest: Passed
✓ HACS: Passed  
✓ Black: Code formatted correctly
✓ Pylint: No issues found
✓ Tests (Python 3.12 + HA 2025.10.0): 45 passed, coverage 87%
✓ Security: No vulnerabilities detected
```

---

### Smoke Test

**File**: `.github/workflows/smoke-test.yaml`

**Triggers**:
- Push to main
- Pull requests
- Manual dispatch

**Purpose**: Fast validation that integration loads without errors

**What it tests**:
1. Module imports work correctly
2. Manifest.json is valid
3. Home Assistant API compatibility
4. No import errors or syntax issues

**Speed**: ~2-3 minutes per version

**Matrix Testing**:
```yaml
Python versions: [3.11, 3.12, 3.13]
HA versions: [2025.4.0, 2025.6.0, 2025.8.0, 2025.10.0]
Total combinations: 12
```

**Example Output**:
```
Testing HA 2025.10.0 with Python 3.13:
✓ All modules imported successfully
✓ Manifest valid
✓ HA APIs compatible
✓ No syntax or import errors
```

---

### Integration Test

**File**: `.github/workflows/integration-test.yaml`

**Triggers**:
- Push to main
- Pull requests
- Manual dispatch (with custom HA version)

**Purpose**: Test integration in a real Home Assistant environment

**What it does**:
1. Starts Home Assistant in Docker container
2. Mounts integration code
3. Waits for HA to be ready
4. Verifies integration is discoverable
5. Checks logs for errors
6. Validates manifest in running environment

**Speed**: ~10-15 minutes per version

**Matrix Testing**:
```yaml
HA versions: [2025.9.0, 2025.10.0, latest]
```

**Example Output**:
```
✓ Home Assistant container started
✓ Integration files mounted
✓ Home Assistant ready (started in 45s)
✓ Integration manifest found and valid
✓ No import errors in logs
✓ Integration discoverable by HA
✓ All health checks passed
```

---

### Nightly Compatibility Check

**File**: `.github/workflows/nightly-compatibility.yaml`

**Triggers**:
- Scheduled: Every night at 2 AM UTC
- Manual dispatch

**Purpose**: Proactively detect compatibility issues with upcoming HA versions

**🔥 NEW: Dynamic Latest Version Testing**
- Automatically detects and tests the **absolute latest** HA version
- Checks both PyPI and GitHub for newest release
- **Zero maintenance** - no manual version updates needed
- Works with any future HA version (2025, 2026, 2027...)

**What it does**:
1. **Test Latest Stable**: Full test suite against **dynamically detected** latest HA release 🔥
   - Fetches from PyPI (usually most current)
   - Falls back to GitHub Releases
   - No manual updates needed!
2. **Test Dev Branch**: Tests against upcoming HA version (preview)
3. **Multi-Version Smoke**: Quick checks across 5 fixed + 1 dynamic version
   - Fixed: 2025.4.0, 2025.6.0, 2025.8.0, 2025.9.0, 2025.10.0
   - Dynamic: Whatever is latest on PyPI (changes automatically!)
4. **Generate Report**: Compatibility status report with version details
5. **Auto-Alert**: Creates GitHub issue if tests fail

**Notification Behavior**:
- Creates issue on first failure
- Updates existing issue on subsequent failures
- Comments when tests pass again after failure
- Issues labeled: `compatibility`, `automated`, `needs-investigation`

**Example Report**:
**Example Report**:
```markdown
# 🔍 Nightly Compatibility Check Report

**Date**: 2025-10-25 02:00:00 UTC

## Test Results

✅ **Latest Stable HA**: Tests Passed (2025.10.2)
⚠️ **HA Dev Branch**: Tests Failed (may indicate upcoming breaking changes)
✅ **Multi-Version Smoke Tests**: Passed

## Recommendations

- 🔧 Review upcoming Home Assistant changes
- 📝 Check HA dev branch changelog for breaking changes
- 🛠️ Consider updating integration code proactively
```

---

## What Gets Tested

### Unit Tests (pytest)

Located in `tests/` directory:

- ✅ **API Module** (`test_api.py`)
  - Login flow
  - Data parsing from `/data/elements`
  - Temperature scaling
  - Alarm code handling (including BCD formats)
  - Fan speed control
  - Silent mode
  - Installation data retrieval
  - Error handling

- ✅ **Climate Entity** (`test_climate.py`)
  - HVAC mode changes
  - Preset modes (comfort/eco)
  - Temperature control
  - State updates
  - Attribute reporting

- ✅ **Config Flow** (`test_config_flow.py`)
  - Initial setup wizard
  - Credential validation
  - Error handling

- ✅ **Coordinator** (`test_coordinator.py`)
  - Data refresh cycle
  - Error recovery
  - State management

- ✅ **Sensors** (`test_sensor.py`)
  - Sensor creation
  - Value updates
  - Alarm sensors

### Integration Tests (Docker)

- ✅ Integration loading
- ✅ Discovery by Home Assistant
- ✅ Manifest validation
- ✅ No import/syntax errors
- ✅ Frontend accessibility
- ✅ Log health checks

### Smoke Tests

- ✅ Module import checks
- ✅ Manifest structure validation
- ✅ HA API compatibility
- ✅ No critical errors

---

## Home Assistant Version Compatibility

### Currently Tested Versions

| Version | Unit Tests | Smoke Test | Integration Test | Nightly Check |
|---------|------------|------------|------------------|---------------|
| 2025.4.0 | ❌ | ✅ | ❌ | ✅ |
| 2025.6.0 | ✅ | ✅ | ❌ | ✅ |
| 2025.8.0 | ✅ | ✅ | ❌ | ✅ |
| 2025.9.0 | ❌ | ❌ | ✅ | ✅ |
| 2025.10.0 | ✅ | ✅ | ✅ | ✅ |
| latest (dynamic) 🔥 | ❌ | ❌ | ✅ | ✅ |
| dev | ❌ | ❌ | ❌ | ✅ |

**Note:** The "latest (dynamic)" version is automatically detected from PyPI every night. It could be 2025.10.2, 2025.11.0, or any future release - **no manual updates needed**!

### Version Selection Strategy

**Comprehensive Testing** (Unit tests):
- Mid-year stable (2025.6.0)
- Recent stable (2025.8.0)
- Latest stable (2025.10.0)

**Quick Validation** (Smoke tests):
- Includes older versions for backward compatibility
- 4 versions from 2025.4.0 to 2025.10.0

**Real Environment** (Integration tests):
- Recent stable versions
- Latest release
- 3 versions total (2025.9.0, 2025.10.0, latest)

**Proactive Monitoring** (Nightly):
- Latest stable release (🔥 **dynamically detected** from PyPI/GitHub, currently 2025.10.2)
- Development branch (preview future changes)
- 5 fixed versions + 1 dynamic latest for regression detection
- **Total: 6 versions tested** (automatically adjusts when new HA releases)

---

## Test Fixtures

### Location

`tests/fixtures/api_responses/`

### Available Fixtures

| Fixture | Description |
|---------|-------------|
| `elements_two_zones.json` | Standard 2-zone heating system |
| `elements_with_fan_speeds.json` | System with fan coil control |
| `installation_devices.json` | Temperature limits and system config |
| `installation_alarms.json` | Alarm data |

### Using Fixtures in Tests

```python
from tests.fixtures.conftest_fixtures import load_fixture

def test_with_fixture():
    # Load realistic API response
    data = load_fixture("api_responses/elements_two_zones.json")
    
    # Use in your test
    assert data["status"] == "success"
    assert len(data["data"]["elements"]) == 2
```

### Creating New Fixtures

See [`tests/fixtures/README.md`](../tests/fixtures/README.md) for detailed instructions on:
- Recording API responses from browser DevTools
- Sanitizing sensitive data
- Naming conventions
- Contributing fixtures

---

## Running Tests Locally

### Quick Start

```bash
# Install development dependencies
pip install -r custom_components/csnet_home/requirements-dev.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=custom_components --cov-report=html

# Run specific test file
pytest tests/test_api.py -v

# Run tests with specific HA version
pip install homeassistant==2025.10.0
pytest tests/ -v
```

### Test Different HA Versions Locally

```bash
# Create virtual environments for each version
python -m venv venv-2025.6
source venv-2025.6/bin/activate
pip install homeassistant==2025.6.0
pip install -r custom_components/csnet_home/requirements-dev.txt
pytest

# Test another version
python -m venv venv-2025.10
source venv-2025.10/bin/activate
pip install homeassistant==2025.10.0
pip install -r custom_components/csnet_home/requirements-dev.txt
pytest
```

### Run Integration Test Locally

```bash
# Using the existing integration test setup
make start        # Start HA in Docker
make logs         # Check logs
make stop         # Stop when done

# Or use the script directly
./scripts/integration-test.sh start
```

### Run Smoke Test Locally

```bash
# Install specific HA version
pip install homeassistant==2025.10.0

# Test imports
python -c "from custom_components.csnet_home import api, climate, sensor; print('✓ All imports successful')"

# Validate manifest
python -c "import json; manifest = json.load(open('custom_components/csnet_home/manifest.json')); print(f'✓ Manifest valid: {manifest[\"version\"]}')"
```

---

## Interpreting Test Results

### GitHub Actions Interface

1. **Go to the Actions tab** in GitHub repository
2. **Select a workflow** from the left sidebar
3. **Click on a run** to see results
4. **Expand job steps** to see detailed output

### Status Badges

The README displays real-time status:

```markdown
[![Validation](https://img.shields.io/.../validate.yaml)](link)
```

- 🟢 Green = All tests passing
- 🔴 Red = Tests failing
- 🟡 Yellow = Tests running
- ⚫ Gray = No recent runs

### Understanding Failures

#### Unit Test Failure

```
FAILED tests/test_api.py::test_login_success
```

**Action**: 
1. Check the test output for error message
2. Run test locally: `pytest tests/test_api.py::test_login_success -v`
3. Fix the code or update the test

#### Smoke Test Failure

```
✗ custom_components.csnet_home.api: ImportError
```

**Action**:
1. Check if module exists
2. Verify imports don't use unavailable HA APIs
3. Test with same HA version locally

#### Integration Test Failure

```
✗ Integration files not found in container
```

**Action**:
1. Check Docker mount configuration
2. Verify file paths are correct
3. Review container logs

#### Nightly Check Failure

```
⚠️ HA Dev Branch: Tests Failed
```

**Action**:
1. Review HA dev branch changelog
2. Check for breaking changes
3. Update integration code proactively
4. Comment on auto-created issue with findings

---

## Troubleshooting

### Common Issues

#### Tests Pass Locally But Fail in CI

**Possible causes**:
- Different Home Assistant version
- Missing dependencies
- Environment differences

**Solution**:
```bash
# Match CI environment locally
pip install homeassistant==2025.10.0  # Use version from CI
pytest -v
```

#### Smoke Test Imports Fail

**Possible cause**: Using HA APIs that don't exist in older versions

**Solution**:
- Use conditional imports
- Check HA version before using new APIs
- Maintain backward compatibility

```python
try:
    from homeassistant.new_api import NewFeature
    HAS_NEW_FEATURE = True
except ImportError:
    HAS_NEW_FEATURE = False
```

#### Integration Test Container Won't Start

**Possible causes**:
- Port 8123 already in use
- Docker not running
- Invalid configuration

**Solution**:
```bash
# Check if port is in use
lsof -i :8123

# Check Docker
docker ps

# View container logs
docker logs ha-test
```

#### Nightly Check Creates Too Many Issues

**Solution**:
- The workflow only creates ONE issue
- Subsequent failures update the existing issue
- Issue auto-closes when tests pass again

### Getting Help

1. **Check workflow logs** in GitHub Actions
2. **Review test output** for specific error messages
3. **Run tests locally** with same HA version
4. **Check recent HA changes** if dev branch fails
5. **Open an issue** with:
   - Workflow run link
   - Error messages
   - Expected vs actual behavior

### Useful Commands

```bash
# View all workflows
ls -la .github/workflows/

# Validate workflow syntax locally
# Install actionlint: brew install actionlint
actionlint

# Test workflow changes with act
# Install act: brew install act
act pull_request -W .github/workflows/validate.yaml

# Check Home Assistant version compatibility
pip install homeassistant==2025.10.0
python -c "import homeassistant; print(homeassistant.__version__)"
```

---

## Best Practices

### For Contributors

1. **Run tests locally** before pushing
2. **Test with multiple HA versions** if changing core functionality
3. **Add test fixtures** for new API responses
4. **Update tests** when adding features
5. **Check CI results** before merging PRs

### For Maintainers

1. **Monitor nightly check results** weekly
2. **Address dev branch failures** proactively
3. **Update tested HA versions** quarterly
4. **Review and close** auto-created compatibility issues
5. **Keep fixtures up-to-date** with API changes

### For Users

1. **Check workflow status** before installing from main branch
2. **Report compatibility issues** with your HA version
3. **Contribute test fixtures** for your device configuration
4. **Test preview builds** from PR artifacts

---

## Future Enhancements

Potential improvements to the testing infrastructure:

- [ ] Performance benchmarking
- [ ] Real API integration tests (with mock server)
- [ ] UI testing with Selenium
- [ ] Load testing for coordinator updates
- [ ] Multi-device configuration tests
- [ ] Automated changelog generation from test results

---

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [Home Assistant Testing](https://developers.home-assistant.io/docs/development_testing)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Documentation](https://docs.docker.com/)
- [Test Fixtures Guide](../tests/fixtures/README.md)
- [Integration Testing Guide](../INTEGRATION_TESTING.md)

---

**Last Updated**: 2025-10-25
**Maintained by**: @mmornati

