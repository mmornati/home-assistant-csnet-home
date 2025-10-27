# GitHub Workflows Documentation

This document describes all GitHub Actions workflows in this repository and their security measures.

## Workflows Overview

> **Note on Version Testing**: As of 2025, all CI workflows use dynamic version detection from PyPI to ensure tests run against current, relevant Home Assistant versions. No more hardcoded 2024 versions!

### 1. Release Workflow (`release.yaml`)

**Purpose:** Automate the release process with proper version management

**Triggers:**
- Manual workflow dispatch (recommended)
- Release published event

**Security Measures:**
- ✅ Minimal permissions (contents: write, id-token: write)
- ✅ Uses official GitHub actions only
- ✅ No force operations
- ✅ Version verification before publishing
- ✅ Proper commit ordering (manifest before tag)

**Key Features:**
- Automatic manifest version updates
- Release notes generation
- Zip artifact creation
- Artifact retention (90 days)

[See RELEASE_PROCESS.md for detailed usage instructions]

### 2. Validate Workflow (`validate.yaml`)

**Purpose:** Comprehensive code quality and testing

**Triggers:**
- Push to main branch
- Pull requests

**Security Measures:**
- ✅ Read-only permissions
- ✅ Dependency caching
- ✅ Security scanning (Bandit, Safety)
- ✅ Matrix testing (Python 3.11, 3.12)

**Jobs:**
- **validate**: Home Assistant integration validation
- **hacs_validation**: HACS compliance check
- **style**: Code formatting (Black)
- **lint**: Static analysis (Pylint)
- **pytest**: Unit tests with coverage
- **security**: Security vulnerability scanning

### 3. PR Preview Workflow (`pr-preview.yaml`)

**Purpose:** Generate preview artifacts for pull requests

**Triggers:**
- PR opened, synchronized, reopened, or ready for review
- Only when custom_components files change

**Security Measures:**
- ✅ Minimal permissions (contents: read, pull-requests: write)
- ✅ Only runs on non-draft PRs
- ✅ 30-day artifact retention
- ✅ Comment updates instead of spam

**Key Features:**
- Automatic ZIP creation for testing
- Helpful PR comments with installation instructions
- Updates existing comments to avoid spam

### 4. Stale Workflow (`stale.yaml`)

**Purpose:** Manage stale issues and PRs

**Triggers:**
- Scheduled (daily)

**Security Measures:**
- ✅ Minimal permissions
- ✅ No external dependencies

### 5. Smoke Test Workflow (`smoke-test.yaml`)

**Purpose:** Quick import and basic compatibility validation

**Triggers:**
- Push to main branch
- Pull requests
- Manual workflow dispatch

**Security Measures:**
- ✅ Read-only permissions
- ✅ Dynamic version detection from PyPI
- ✅ Automatic Python version selection

**Key Features:**
- 🚀 **Fast Testing**: Tests latest version from last 3 months (month-based selection)
- 🐍 **Smart Python Detection**: Auto-selects Python 3.12 or 3.13 based on HA requirements
- ✅ Module import validation
- ✅ Manifest validation
- ✅ HA API compatibility checks
- 💨 Runs on every PR for quick feedback
- 📅 **Year-Agnostic**: Works in any year automatically

**Why Last 3 Months?**
Smoke tests are meant to be fast. Testing the latest version from each of the last 3 months provides good coverage of recent releases without slowing down PR feedback. If there are multiple patches in a month (e.g., 2025.10.1, 2025.10.2, 2025.10.4), only the latest is tested.

### 6. Integration Test Workflow (`integration-test.yaml`)

**Purpose:** Full Docker-based integration testing with real Home Assistant

**Triggers:**
- Push to main branch
- Pull requests
- Manual workflow dispatch (with optional version override)

**Security Measures:**
- ✅ Read-only permissions
- ✅ Isolated Docker containers
- ✅ Dynamic version detection

**Key Features:**
- 🐳 **Real HA Environment**: Tests in actual Home Assistant Docker containers
- 🎯 **Month-Based Selection**: Tests latest version from last 2 months + "latest"
- ✅ Integration loading verification
- ✅ Manifest validation in container
- ✅ Log analysis for errors
- 📦 Artifact collection on failure
- 🔄 Always includes "latest" to catch breaking changes early
- 📅 **Year-Agnostic**: Works across year boundaries automatically

**Why Docker?**
Docker testing is the most accurate way to test integrations, as it runs in the actual Home Assistant environment with all dependencies and the real loading mechanism.

**Why Last 2 Months + Latest?**
Docker tests are slower than smoke tests. Testing the latest version from each of the last 2 months plus the "latest" Docker image provides thorough coverage without excessive CI time. The "latest" image ensures we catch breaking changes immediately.

### 7. Labeler Workflow (`labeler.yaml`)

**Purpose:** Auto-label PRs based on changed files

**Triggers:**
- Pull requests

**Security Measures:**
- ✅ Read-only for contents
- ✅ Write for PRs only

### 8. Nightly Compatibility Check (`nightly-compatibility.yaml`)

**Purpose:** Test integration compatibility with multiple Home Assistant versions

**Triggers:**
- Scheduled (nightly at 2 AM UTC)
- Manual workflow dispatch

**Security Measures:**
- ✅ Minimal permissions (contents: read, issues: write)
- ✅ Dynamic version detection from PyPI
- ✅ Automatic Python version selection based on HA requirements
- ✅ Proper error handling for failed installations
- ✅ Continue-on-error for non-critical failures

**Key Features:**
- 🎯 **Month-Based Version Selection**: Automatically fetches latest version from the last 4 months (by major release)
- 🐍 **Smart Python Detection**: Detects Python requirements for each HA version and uses the correct Python version
  - Python 3.12 for HA versions up to 2025.5.x
  - Python 3.13 for HA versions 2025.6.0+
- ✅ Tests against latest stable HA version with full test suite
- 🔬 Tests against HA dev branch for upcoming breaking changes
- 💨 Smoke tests across multiple recent HA versions (import verification)
- 📊 Skips tests for versions that fail to install (version not available)
- 🚨 Creates GitHub issues on failure (scheduled runs only)
- 📝 Generates comprehensive compatibility report with recommendations
- 📅 **Year-Agnostic**: Uses current date, works in 2025, 2026, 2027+

**Why Month-Based Selection?**
Instead of testing arbitrary version counts, the workflow selects the latest version from each of the last N months:
- **October 2025**: Tests 2025.10.x, 2025.9.x, 2025.8.x, 2025.7.x (latest patch from each)
- **January 2026**: Tests 2026.1.x, 2025.12.x, 2025.11.x, 2025.10.x (handles year boundaries)
- Always current and relevant
- Adapts to HA's monthly release cadence
- Handles multiple patches per month (takes latest)
- Proper Python version matching for each release

## Testing Strategy Overview

The repository uses a multi-layered testing approach for Home Assistant compatibility:

| Workflow | Trigger | HA Versions Tested | Speed | Purpose |
|----------|---------|-------------------|-------|---------|
| **Smoke Test** | Every PR/Push | Last 3 months (latest per month) | ⚡ Fast | Quick import validation |
| **Integration Test** | Every PR/Push | Last 2 months + "latest" | 🐳 Medium | Real Docker environment |
| **Nightly Check** | Scheduled | Last 4 months + dev branch | 🌙 Comprehensive | Full compatibility scan |

### Version Selection Philosophy

All workflows now use **month-based dynamic version detection** to ensure relevance:

1. **Month-Based Selection**: Selects latest version from each of the last N months
   - Example (Oct 2025): 2025.10.4, 2025.9.3, 2025.8.2
   - Adapts to current date automatically
   - Works across year boundaries (Jan 2026 → Dec 2025, Nov 2025, etc.)
2. **Year-Agnostic**: Uses `date +%Y` - works in 2025, 2026, 2027+ without changes
3. **Patch-Smart**: If there are multiple patches (2025.10.1, 2025.10.2, 2025.10.4), picks the latest
4. **Python Version Matching**: Automatically uses Python 3.12 or 3.13 based on HA requirements
5. **Fail Gracefully**: Skips versions that can't be installed rather than failing

### When to Use Each Test

- **Smoke Test**: Fast feedback on PRs, basic compatibility check
- **Integration Test**: Validates integration loads in real HA (most important)
- **Nightly Check**: Comprehensive compatibility testing including dev branch

## Security Best Practices

### 1. Minimal Permissions

All workflows use the principle of least privilege:
```yaml
permissions:
  contents: read  # Only what's needed
  pull-requests: write  # When necessary
```

### 2. Dependency Pinning

- Actions are pinned to specific versions
- Regular Dependabot updates configured
- No unmaintained or deprecated actions

### 3. Secret Management

- Uses built-in `GITHUB_TOKEN` (no PATs)
- Secrets are only used where necessary
- No secrets in logs or outputs

### 4. Input Validation

- Release version inputs are validated
- Manifest versions are verified
- Failure modes are explicit

### 5. Artifact Security

- Limited retention periods
- Proper exclusions (no `.git`, `__pycache__`)
- Clear naming conventions

## Common Issues and Solutions

### Release Workflow Issues

**Issue:** "Manifest version does not match tag version"
```bash
# Solution: Manually update and re-tag
git checkout v1.4.3
# Update manifest.json
git commit -am "Fix manifest version"
git tag -f v1.4.3
git push -f origin v1.4.3
```

**Issue:** "Tag already exists"
```bash
# Solution: Delete and recreate
git tag -d v1.4.3
git push --delete origin v1.4.3
# Then use workflow dispatch
```

### Validate Workflow Issues

**Issue:** Style check fails
```bash
# Solution: Run Black locally
black .
git commit -am "Apply Black formatting"
git push
```

**Issue:** Tests fail
```bash
# Solution: Run tests locally
pytest tests/
# Fix issues, commit, push
```

### PR Preview Issues

**Issue:** Artifact not generated
- Check if PR is in draft mode (drafts are skipped)
- Check if changed files include custom_components
- Review workflow run logs

### Nightly Compatibility Issues

**Issue:** Tests fail with "No module named 'homeassistant'"
```bash
# This usually means Python version mismatch
# The workflow now automatically detects and uses the correct Python version
# Check the "Determine Python Version" step in the workflow logs
# HA 2025.6+ requires Python 3.13, earlier versions use 3.12
```

**Issue:** All smoke tests show "SKIPPED (version not available)"
```bash
# This is normal if PyPI temporarily has issues
# The workflow will automatically skip unavailable versions
# Check PyPI status: https://status.python.org/
# Or verify versions exist: curl -s https://pypi.org/pypi/homeassistant/json | jq '.releases | keys'
```

**Issue:** Tests pass on old versions but fail on latest
```bash
# This indicates a breaking change in the latest Home Assistant release
# Review the compatibility report artifact for details
# Check Home Assistant release notes for breaking changes
# Update the integration to support the new HA API changes
```

**Issue:** Want to test against specific older versions
```bash
# The workflow now dynamically tests the 5 most recent stable versions
# To add specific versions, modify get-versions-to-test job
# Or run integration tests locally with specific HA versions:
pip install homeassistant==2025.9.0
pytest tests/
```

## Workflow Maintenance

### Regular Updates

1. **Dependencies:** Dependabot updates actions automatically
2. **Python versions:** Update matrix when new versions release
3. **Security scans:** Review Bandit and Safety results

### Testing Changes

Before modifying workflows:
1. Test in a fork first
2. Use `workflow_dispatch` for manual testing
3. Review logs carefully
4. Document changes in PR

### Monitoring

- Check workflow run history regularly
- Review failed runs promptly
- Keep security advisories enabled

## Migration from Old Workflows

### What Changed

**Old Release Workflow:**
- ❌ Used `actions-js/push` (unmaintained)
- ❌ Force-pushed changes
- ❌ Created commits after tags
- ❌ Had race conditions

**New Release Workflow:**
- ✅ Uses official GitHub actions
- ✅ Proper git operations
- ✅ Commits before tags
- ✅ Deterministic and reliable

### Breaking Changes

⚠️ **Important:** The new release workflow requires using workflow dispatch for creating releases. The old automatic approach has been removed for safety.

**Old process:**
1. Create tag
2. Create release
3. Workflow updates manifest (fails!)

**New process:**
1. Run workflow dispatch with version
2. Workflow updates manifest, creates tag, creates release
3. Workflow builds and uploads zip

## Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Security Hardening Guide](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions)
- [Home Assistant Developer Docs](https://developers.home-assistant.io/)

## Questions?

For issues or questions about workflows:
1. Check this documentation
2. Review workflow run logs
3. Open an issue with the `github_actions` label

