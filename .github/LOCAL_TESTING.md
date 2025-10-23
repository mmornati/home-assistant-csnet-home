# Local Workflow Testing Guide

This guide explains how to test GitHub Actions workflows locally before pushing to ensure they work correctly.

## Quick Start

```bash
# Run the test script
./scripts/test-workflows.sh
```

This will validate all workflows and ensure they're ready to be pushed.

## Required Tools

### 1. ActionLint (Required)

ActionLint validates GitHub Actions workflow files.

**Installation:**

```bash
# macOS (Homebrew)
brew install actionlint

# Linux/macOS (Direct download)
bash <(curl https://raw.githubusercontent.com/rhysd/actionlint/main/scripts/download-actionlint.bash)

# Verify installation
actionlint --version
```

### 2. yamllint (Required)

Validates YAML syntax and formatting.

**Installation:**

```bash
# Using pip
pip install yamllint

# macOS (Homebrew)
brew install yamllint

# Verify installation
yamllint --version
```

### 3. ShellCheck (Required)

Validates shell scripts in workflows.

**Installation:**

```bash
# macOS (Homebrew)
brew install shellcheck

# Ubuntu/Debian
sudo apt-get install shellcheck

# Verify installation
shellcheck --version
```

### 4. act (Optional)

Runs GitHub Actions workflows locally.

**Installation:**

```bash
# macOS (Homebrew)
brew install act

# Linux
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# Verify installation
act --version
```

**Note:** `act` is optional but highly recommended for testing workflows end-to-end.

## Testing Workflows

### Automated Testing (Recommended)

Use the provided test script:

```bash
./scripts/test-workflows.sh
```

This script will:
- ✅ Check all required dependencies
- ✅ Validate workflow YAML syntax
- ✅ Run ActionLint on all workflows
- ✅ Run YAML linting
- ✅ Check shell scripts
- ✅ Test zip creation
- ✅ Provide a summary of results

### Manual Testing

#### 1. Validate with ActionLint

```bash
# Check all workflows
actionlint -color -verbose .github/workflows/*.yaml

# Check specific workflow
actionlint -color .github/workflows/release.yaml
```

**Common Issues ActionLint Catches:**
- Invalid action versions
- Missing required inputs
- Incorrect if conditions
- Shell command issues
- Deprecated syntax

#### 2. Validate YAML Syntax

```bash
# Check all workflow files
yamllint .github/workflows/

# Check with custom config
yamllint -d "{extends: default, rules: {line-length: {max: 120}}}" .github/workflows/
```

#### 3. Check Shell Scripts

```bash
# Find and check all shell scripts
find .github scripts -name "*.sh" -exec shellcheck {} \;

# Check specific script
shellcheck scripts/test-workflows.sh
```

#### 4. Test Zip Creation

```bash
cd custom_components/csnet_home
zip -r test.zip . -x "*.git*" -x "*__pycache__*" -x "*.pyc"
ls -lh test.zip
zipinfo test.zip | head -20
rm test.zip
```

### Testing with Act (Advanced)

Run workflows locally with Docker:

```bash
# List available workflows
act -l

# Run a specific workflow (dry run)
act -n

# Run validation workflow
act pull_request -W .github/workflows/validate.yaml

# Run with specific event
act workflow_dispatch --input version=v1.4.3

# Run with secrets
act --secret-file .secrets
```

**Note:** Some workflows may not work perfectly with `act` due to limitations, but it's useful for catching most issues.

## Pre-Commit Testing

### Set up a Git Hook

Create `.git/hooks/pre-push`:

```bash
#!/bin/bash

# Run workflow tests before push
echo "Running workflow validation..."
./scripts/test-workflows.sh

if [ $? -ne 0 ]; then
    echo "❌ Workflow validation failed. Push aborted."
    exit 1
fi

echo "✅ All checks passed. Proceeding with push."
exit 0
```

Make it executable:

```bash
chmod +x .git/hooks/pre-push
```

## Continuous Validation

The repository includes a workflow validation workflow (`.github/workflows/workflow-validation.yaml`) that automatically runs on:
- Pull requests that modify workflows
- Pushes to main that modify workflows

This ensures workflows are validated in CI as well.

## Common Issues and Solutions

### Issue: ActionLint errors about unknown actions

**Solution:** Update action versions or check if the action exists.

```bash
# Example error:
# .github/workflows/release.yaml:109:23: could not find action "unknown/action@v1"

# Fix: Check GitHub for the correct action name and version
```

### Issue: YAML syntax errors

**Solution:** Use proper indentation and syntax.

```bash
# Check specific file
yamllint .github/workflows/release.yaml

# Common issues:
# - Mixed tabs and spaces (use spaces only)
# - Incorrect indentation (use 2 spaces)
# - Missing quotes around strings with special characters
```

### Issue: ShellCheck warnings in run commands

**Solution:** Fix shell script issues.

```bash
# Common issues:
# - Unquoted variables: Use "$VAR" instead of $VAR
# - Word splitting: Quote strings properly
# - Check exit codes: Use 'if' or 'set -e'
```

### Issue: act fails with Docker errors

**Solution:** Check Docker is running and you have sufficient permissions.

```bash
# Check Docker
docker ps

# Run with sudo if needed
sudo act pull_request
```

## Testing Checklist

Before pushing workflow changes:

- [ ] Run `./scripts/test-workflows.sh`
- [ ] All ActionLint checks pass
- [ ] YAML syntax is valid
- [ ] Shell scripts pass ShellCheck
- [ ] Zip creation works
- [ ] (Optional) Test with `act` if available
- [ ] Review the workflow diff
- [ ] Test in a fork if making major changes

## Best Practices

### 1. Test Incrementally

Make small changes and test frequently rather than large changes all at once.

### 2. Use Dry Runs

Always test with `act -n` (dry run) first before running full execution.

### 3. Check Action Versions

Regularly update action versions and test:

```bash
# Update checkout action
- uses: actions/checkout@v4.0.0  # Old
+ uses: actions/checkout@v5.0.0  # New
```

### 4. Validate Environment Variables

Test that all required environment variables and secrets are available:

```bash
# In workflow
- name: Check Required Variables
  run: |
    test -n "${{ secrets.GITHUB_TOKEN }}" || exit 1
    test -n "${{ github.ref_name }}" || exit 1
```

### 5. Test on Forks First

For major workflow changes:
1. Fork the repository
2. Test changes on the fork
3. Verify workflows work correctly
4. Create PR to main repository

## Troubleshooting

### ActionLint Shows False Positives

Create `.github/actionlint.yaml`:

```yaml
self-hosted-runner:
  labels: []
config-variables:
  - MY_VAR
```

### act Fails with "container not found"

Update act or use a different Docker image:

```bash
# Use specific image
act -P ubuntu-latest=ghcr.io/catthehacker/ubuntu:act-latest
```

### Workflows Work Locally but Fail in CI

Check for:
- Environment-specific issues
- Missing secrets/variables
- Different OS (Linux vs macOS)
- Timing issues

## Additional Resources

- [ActionLint Documentation](https://github.com/rhysd/actionlint)
- [act Documentation](https://github.com/nektos/act)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [yamllint Documentation](https://yamllint.readthedocs.io/)
- [ShellCheck Wiki](https://github.com/koalaman/shellcheck/wiki)

## Getting Help

If you encounter issues:
1. Check the error messages carefully
2. Review this documentation
3. Run `./scripts/test-workflows.sh` for detailed output
4. Open an issue with the `github_actions` label

## Examples

### Example: Testing Before Release

```bash
# 1. Make workflow changes
vim .github/workflows/release.yaml

# 2. Test locally
./scripts/test-workflows.sh

# 3. If all passes, commit and push
git add .github/workflows/release.yaml
git commit -m "fix: Update release workflow"
git push

# 4. Verify in GitHub Actions tab
```

### Example: Testing New Workflow

```bash
# 1. Create new workflow
cat > .github/workflows/new-workflow.yaml << 'EOF'
name: New Workflow
on: push
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5.0.0
EOF

# 2. Validate
actionlint .github/workflows/new-workflow.yaml

# 3. Test with act
act push -W .github/workflows/new-workflow.yaml -n

# 4. If OK, commit
git add .github/workflows/new-workflow.yaml
git commit -m "feat: Add new workflow"
```

---

**Remember:** Testing workflows locally saves time and prevents broken CI/CD pipelines!

