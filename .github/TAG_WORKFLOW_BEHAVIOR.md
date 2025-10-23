# How GitHub Actions Uses Workflow Files with Tags

## Important Concept

⚠️ **When a workflow is triggered by a tag or release event, GitHub Actions uses the workflow file FROM THAT TAG'S COMMIT, not from the main branch.**

## Why This Matters

### Example: The v1.4.2 Issue

**Timeline:**
1. v1.4.2 tag created pointing to commit `75ca797` (had old broken workflow)
2. Workflow improvements committed to main (`310fdac`, `220f6a1`, `2d4bced`, `ae0efc0`)
3. Release triggered for v1.4.2 → **Uses OLD workflow from commit `75ca797`** ❌
4. Tag moved to commit `8a265bc` (has new improved workflow)
5. New release triggered for v1.4.2 → **Uses NEW workflow from commit `8a265bc`** ✅

## How to Check Which Workflow File a Tag Uses

```bash
# Show the workflow file from a specific tag
git show v1.4.2:.github/workflows/release.yaml | head -30

# Check which commit a tag points to
git log --oneline -1 v1.4.2

# Compare tag commit with main
git log --oneline v1.4.2..main
```

## Signs You're Using an Old Workflow

If you see these in your GitHub Actions run:

### Old Workflow Indicators:
- ❌ Job name: `update_version_and_create_zip`
- ❌ Uses: `actions-js/push@master`
- ❌ Uses: `thedoctor0/zip-release@0.7.6`
- ❌ Single-stage process

### New Workflow Indicators:
- ✅ Job names: `prepare_release` and `build_and_upload_zip`
- ✅ Uses: `actions/checkout@v5.0.0`
- ✅ Uses: `softprops/action-gh-release@v2`
- ✅ Two-stage process
- ✅ Idempotent (safe to re-run)

## How to Fix a Tag with Old Workflow

### Option 1: Move the Tag (Recommended for existing releases)

```bash
# Move tag to current main (or any commit with new workflow)
git tag -f v1.4.2
git push -f origin v1.4.2
```

**Important:** This requires force push! Only do this if:
- The release hasn't been widely distributed yet
- You need to fix a broken workflow
- You understand the implications

### Option 2: Create a New Version (Recommended for production)

```bash
# Create a new version instead
git tag v1.4.3
git push origin v1.4.3
```

This is safer because:
- ✅ Doesn't rewrite history
- ✅ Clear version progression
- ✅ Old releases remain untouched

## Best Practices

### 1. Test Workflows Before Tagging

```bash
# Ensure workflow is tested and working on main
# Then create the tag
git tag v1.4.3
git push origin v1.4.3
```

### 2. Use Manual Workflow Dispatch for Releases

Instead of relying on tag creation to trigger releases:

1. Commit and push all changes to main
2. Test the workflow
3. Use manual workflow dispatch: Actions → Release Workflow → Run workflow
4. The workflow creates the tag AND the release

This ensures the tag always points to the correct commit with the correct workflow.

### 3. Verify Tag Before Publishing

```bash
# Before creating a release, verify the tag has the right workflow
git show v1.4.3:.github/workflows/release.yaml | grep -A 5 "^name:"
git show v1.4.3:.github/workflows/release.yaml | grep -E "^  [a-z_]+:"
```

## Workflow Triggers and File Sources

| Trigger Type | Workflow File Source |
|--------------|---------------------|
| `push` to branch | HEAD of that branch |
| `pull_request` | HEAD of PR branch |
| `workflow_dispatch` (manual) | Branch selected in UI (usually main) |
| `release: published` | **Commit the tag points to** ⚠️ |
| Tag push | **Commit the tag points to** ⚠️ |

## Common Questions

### Q: I updated the workflow on main, why isn't my release using it?

**A:** Because the release is triggered by a tag, and that tag points to a commit that doesn't have your updates.

**Solution:** Either move the tag (force push) or create a new version.

### Q: Can I test a release workflow without creating a tag?

**A:** Yes! Use `workflow_dispatch` (manual trigger):
1. Go to Actions → Release Workflow
2. Click "Run workflow"
3. Enter version number
4. The workflow will create the tag for you

### Q: How do I know if my workflow changes are included in a tag?

**A:** 
```bash
# Check the workflow file at the tag
git show v1.4.2:.github/workflows/release.yaml

# Compare with main
diff <(git show v1.4.2:.github/workflows/release.yaml) <(git show main:.github/workflows/release.yaml)
```

### Q: What's the safest way to release?

**A:** Use the two-stage workflow with manual dispatch:

1. **All changes on main** (including workflow improvements)
2. **Test locally** with `./scripts/test-workflows.sh`
3. **Manual trigger** from GitHub UI
4. **Workflow handles everything** (manifest, tag, release, zip)

This ensures:
- ✅ Tag is created AFTER workflow is finalized
- ✅ Tag always points to a commit with the correct workflow
- ✅ No need to move tags later

## For This Project

Our current release workflow is designed to handle all these complexities:

### Safe Release Process:
1. Ensure main has all changes (including workflow)
2. Go to: https://github.com/mmornati/home-assistant-csnet-home/actions/workflows/release.yaml
3. Click "Run workflow"
4. Enter version (e.g., `v1.4.3`)
5. Let the workflow handle everything

The workflow will:
- ✅ Update manifest (if needed)
- ✅ Create and push tag (from current main commit)
- ✅ Create GitHub release
- ✅ Build and upload zip

### To Fix v1.4.2:
1. Delete the v1.4.2 release: https://github.com/mmornati/home-assistant-csnet-home/releases
2. Run workflow manually with `v1.4.2`
3. Tag already points to correct commit (we moved it)
4. Workflow will recreate everything correctly

## Summary

🔑 **Key Takeaway:** Tags are snapshots. They capture not just your code, but also your workflow files. Always ensure your tag points to a commit that has the workflow you want to use.

📚 **For More:** See [RELEASE_PROCESS.md](RELEASE_PROCESS.md) for the complete release guide.

