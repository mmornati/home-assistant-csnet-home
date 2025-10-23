# Release Process Documentation

## Overview

This repository uses an automated release workflow that ensures version consistency and creates release artifacts automatically.

## Safety Features

The release workflow is designed to be **idempotent** and safe to re-run:

- ✅ **Smart Version Updates**: Only commits manifest changes if the version is different
- ✅ **Tag Protection**: Handles existing tags gracefully, won't fail if tag exists
- ✅ **Release Protection**: Checks for existing releases, won't duplicate
- ✅ **No Git Conflicts**: Two-stage process prevents non-fast-forward errors
- ✅ **Safe Re-runs**: You can safely re-run the workflow for the same version

## How to Create a New Release

### Option 1: Manual Workflow Dispatch (Recommended)

This is the **recommended** approach as it ensures everything happens in the correct order:

1. Go to **Actions** tab in GitHub
2. Select **"Release Workflow"** from the left sidebar
3. Click **"Run workflow"** button
4. Enter the version number (e.g., `v1.4.3`)
5. Click **"Run workflow"**

The workflow will automatically:
- ✅ Update the version in `manifest.json`
- ✅ Commit the change to `main` branch
- ✅ Create and push the git tag
- ✅ Create a GitHub release with release notes
- ✅ Build and upload the zip file

### Option 2: Manual Release (Advanced)

If you prefer to create releases manually:

1. **Update manifest version first:**
   ```bash
   # Update version in custom_components/csnet_home/manifest.json
   git add custom_components/csnet_home/manifest.json
   git commit -m "Updating to version v1.4.3"
   git push origin main
   ```

2. **Create and push tag:**
   ```bash
   git tag v1.4.3
   git push origin v1.4.3
   ```

3. **Create GitHub release:**
   - Go to Releases → Draft a new release
   - Select the tag you just created
   - Enable "Generate release notes"
   - Publish the release

4. The workflow will automatically build and upload the zip file

## Re-running Failed Releases

Thanks to the workflow's idempotent design, you can safely re-run a release for the same version:

### Scenario 1: Workflow Failed After Manifest Update

If the workflow failed after updating the manifest but before creating the tag:

1. Go to **Actions** → **Release Workflow**
2. Click **"Run workflow"**
3. Enter the **same version number** (e.g., `v1.4.2`)
4. Click **"Run workflow"**

The workflow will:
- ✅ Detect the version is already correct in manifest
- ✅ Skip the commit step (no git conflicts!)
- ✅ Create and push the tag
- ✅ Create the release
- ✅ Build and upload the zip

### Scenario 2: Tag Exists but Release Failed

If the tag was created but the release creation failed:

1. Re-run the workflow with the same version
2. The workflow will:
   - ✅ Skip manifest update (already correct)
   - ✅ Detect tag exists and continue
   - ✅ Check if release exists, create if needed
   - ✅ Build and upload the zip

### Scenario 3: Complete Re-run

Even if everything partially succeeded, you can always re-run:

```bash
# The workflow handles all these cases automatically:
# - Manifest already has correct version → Skip commit
# - Tag already exists → Continue without error
# - Release already exists → Skip creation, upload artifact
```

**No manual cleanup needed!** The workflow is smart enough to handle all scenarios.

## Release Workflow Details

### Job 1: prepare_release (Manual Trigger Only)

Runs when you use "Run workflow" button. This job:
- Updates the manifest.json with the new version
- Commits and pushes to main
- Creates and pushes the tag
- Creates the GitHub release

### Job 2: build_and_upload_zip (Automatic on Release)

Runs when a release is published. This job:
- Verifies the manifest version matches the tag
- Creates the zip archive
- Uploads it to the GitHub release
- Stores it as an artifact

## Version Numbering

Follow Semantic Versioning:
- **Major** (v2.0.0): Breaking changes
- **Minor** (v1.5.0): New features, backward compatible
- **Patch** (v1.4.3): Bug fixes, backward compatible

## Troubleshooting

### Issue: Manifest version doesn't match tag

**Symptom:** Workflow fails with "Manifest version does not match tag version"

**Solution:**
1. Check out the tag: `git checkout v1.4.3`
2. Verify manifest.json has the correct version
3. If incorrect, update manually and move the tag:
   ```bash
   # Update manifest.json
   git add custom_components/csnet_home/manifest.json
   git commit -m "Fix manifest version"
   git tag -f v1.4.3
   git push -f origin v1.4.3
   ```

### Issue: Tag already exists

**Symptom:** "tag 'vX.X.X' already exists"

**Solution:**
```bash
# Delete local and remote tag
git tag -d v1.4.3
git push --delete origin v1.4.3
# Recreate using the workflow
```

## Security Improvements

### 1. No More Force Pushes
- The old workflow used `git push -f -f` which is dangerous
- New workflow uses proper git operations

### 2. Verified Operations
- Manifest version is verified before creating artifacts
- Clear error messages if something is wrong

### 3. Modern Actions
- Uses maintained, official GitHub actions
- No deprecated third-party actions
- Regular Dependabot updates

### 4. Better Permissions
- Minimal required permissions
- Uses built-in GITHUB_TOKEN (no PAT needed)

## Best Practices

1. **Always test in a feature branch first**
2. **Use the manual workflow for releases** (most reliable)
3. **Don't create tags manually unless necessary**
4. **Review the generated release notes before publishing**
5. **Keep manifest.json version in sync with tags**

## Migration from Old Workflow

The old workflow had issues:
- ❌ Created commits after tags were created
- ❌ Used deprecated actions
- ❌ Used force pushes
- ❌ Had race conditions

The new workflow:
- ✅ Creates commits before tags
- ✅ Uses modern, maintained actions
- ✅ No force operations
- ✅ Deterministic and reliable

## Examples

### Creating a patch release
```
Version: v1.4.3
Type: Bug fix release
Steps: Use workflow dispatch with version "v1.4.3"
```

### Creating a minor release
```
Version: v1.5.0
Type: New feature release
Steps: Use workflow dispatch with version "v1.5.0"
```

### Creating a major release
```
Version: v2.0.0
Type: Breaking changes
Steps: 
1. Update documentation about breaking changes
2. Use workflow dispatch with version "v2.0.0"
3. Mark as pre-release if needed for testing
```

## Questions?

If you encounter any issues not covered here, please open an issue on GitHub.

