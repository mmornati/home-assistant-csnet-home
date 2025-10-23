# Workflow Integration Testing with `act`

This guide explains how to run GitHub Actions workflows locally for full integration testing.

## What is `act`?

`act` is a tool that runs your GitHub Actions workflows locally using Docker. It simulates the GitHub Actions environment, allowing you to:
- ✅ Test workflows before pushing
- ✅ Debug workflow issues quickly
- ✅ Validate changes without creating commits
- ✅ Run workflows that require secrets (using local secrets file)

## Installation

### macOS (Homebrew)
```bash
brew install act
```

### Linux
```bash
curl -s https://raw.githubusercontent.com/nektos/act/master/install.sh | bash
```

### Verify Installation
```bash
act --version
```

## Docker Requirement

**Important:** `act` requires Docker to be running. Make sure Docker Desktop (or Docker engine) is installed and running before using `act`.

```bash
# Check Docker is running
docker ps
```

## Quick Start

### 1. List Available Workflows
```bash
# See all workflows and jobs
act -l
```

### 2. Run a Workflow (Dry Run)
```bash
# See what would run without actually running
act pull_request -n
```

### 3. Run Validation Workflow
```bash
# Run the complete validation workflow as if it's a PR
act pull_request -W .github/workflows/validate.yaml
```

## Common Use Cases

### Test Pull Request Validation
```bash
# Run validation workflow
act pull_request -W .github/workflows/validate.yaml

# With custom event data
act pull_request -W .github/workflows/validate.yaml -e .github/act-events/pull_request.json

# Verbose output for debugging
act pull_request -W .github/workflows/validate.yaml -v
```

### Test Workflow Validation
```bash
# Test the workflow validation itself
act pull_request -W .github/workflows/workflow-validation.yaml
```

### Test PR Preview Creation
```bash
# Test PR preview zip creation
act pull_request -W .github/workflows/pr-preview.yaml

# With event payload
act pull_request -W .github/workflows/pr-preview.yaml -e .github/act-events/pull_request.json
```

### Test Release Workflow
```bash
# Test manual release workflow
act workflow_dispatch -W .github/workflows/release.yaml --input version=v1.4.3

# With event file
act workflow_dispatch -W .github/workflows/release.yaml -e .github/act-events/workflow_dispatch.json
```

### Run All Push Workflows
```bash
# Run all workflows that trigger on push
act push
```

## Advanced Usage

### Using Secrets
Create a `.secrets` file (add to `.gitignore`):
```bash
# .secrets
GITHUB_TOKEN=your_test_token_here
OTHER_SECRET=value
```

Run with secrets:
```bash
act pull_request --secret-file .secrets
```

### Using Specific Docker Image
```bash
# Use medium-sized runner image (more tools available)
act pull_request -P ubuntu-latest=catthehacker/ubuntu:act-latest

# Use large image (closest to GitHub Actions)
act pull_request -P ubuntu-latest=catthehacker/ubuntu:full-latest
```

### Run Specific Job
```bash
# Run only a specific job
act pull_request -j validate
```

### Interactive Mode
```bash
# Run with interactive shell on failure
act pull_request -W .github/workflows/validate.yaml --verbose --debug
```

### Reuse Containers
```bash
# Reuse containers for faster iteration
act pull_request --reuse
```

## Testing Workflow

### Recommended Testing Flow

1. **First, run static validation** (fast, no Docker needed):
   ```bash
   ./scripts/test-workflows.sh
   ```

2. **Then, run integration tests** (slower, requires Docker):
   ```bash
   # Dry run first to see what will execute
   act pull_request -W .github/workflows/validate.yaml -n
   
   # Run the actual workflow
   act pull_request -W .github/workflows/validate.yaml
   ```

3. **Debug if needed**:
   ```bash
   # Run with verbose output
   act pull_request -W .github/workflows/validate.yaml -v
   ```

### Example: Testing Your Changes

```bash
# 1. Make changes to workflow
vim .github/workflows/validate.yaml

# 2. Quick validation (static)
./scripts/test-workflows.sh

# 3. Integration test (with Docker)
act pull_request -W .github/workflows/validate.yaml

# 4. If successful, commit and push
git add .github/workflows/validate.yaml
git commit -m "Update validation workflow"
git push
```

## Troubleshooting

### Issue: Docker not found
**Error:** `Cannot connect to the Docker daemon`

**Solution:**
```bash
# Start Docker Desktop (macOS/Windows)
# Or start Docker service (Linux)
sudo systemctl start docker
```

### Issue: Container size errors
**Error:** `Image too large` or slow downloads

**Solution:** Use smaller images:
```bash
# Use micro image (smallest, fastest)
act pull_request -P ubuntu-latest=node:16-buster-slim
```

### Issue: GitHub token required
**Error:** `Unauthorized` or rate limiting

**Solution:** Create a personal access token and use it:
```bash
# Create .secrets file
echo "GITHUB_TOKEN=ghp_your_token_here" > .secrets

# Run with secrets
act pull_request --secret-file .secrets
```

### Issue: Workflow runs differently than on GitHub
**Reason:** Different Docker images, environment variables, or permissions

**Solution:**
- Use full-size images: `catthehacker/ubuntu:full-latest`
- Check environment differences
- Review `act` documentation for known limitations

## Limitations

`act` has some limitations compared to real GitHub Actions:

1. **Different runner images**: May not have all tools available
2. **No GitHub context**: Some GitHub-specific features may not work
3. **Secrets**: Need to be provided manually
4. **Caching**: May work differently than in GitHub Actions
5. **Matrix builds**: Can be slower locally

## Best Practices

1. ✅ **Always run static validation first** with `./scripts/test-workflows.sh` (faster)
2. ✅ **Use dry runs** (`-n`) to preview what will execute
3. ✅ **Start with small workflows** before testing complex ones
4. ✅ **Use reuse flag** (`--reuse`) for faster iteration during development
5. ✅ **Keep secrets in `.secrets` file** and add it to `.gitignore`
6. ✅ **Test locally before pushing** to catch issues early

## Event Payloads

Test event payloads are available in `.github/act-events/`:
- `pull_request.json` - Simulates PR events
- `workflow_dispatch.json` - Simulates manual workflow trigger
- `push.json` - Simulates push events

See `.github/act-events/README.md` for usage examples.

## Resources

- [act GitHub Repository](https://github.com/nektos/act)
- [act Documentation](https://nektosact.com/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Event Webhook Payloads](https://docs.github.com/en/webhooks/webhook-events-and-payloads)

## Summary

Integration testing with `act` provides:
- 🚀 **Fast feedback loop** - Test locally without pushing
- 🔍 **Better debugging** - Run workflows with verbose output
- 💰 **Save CI minutes** - Catch issues before using GitHub Actions
- 🔒 **Test with secrets** - Use local secrets safely
- 📦 **Complete workflows** - Test entire workflow including all jobs

Use this in combination with static validation (`./scripts/test-workflows.sh`) for comprehensive workflow testing!

