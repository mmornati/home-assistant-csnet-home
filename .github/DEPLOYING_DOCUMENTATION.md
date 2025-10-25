# Deploying Documentation

This guide explains how to deploy the documentation to GitHub Pages using the automated workflow.

## Overview

The documentation is automatically built and deployed to GitHub Pages using:
- **MkDocs** - Static site generator optimized for documentation
- **Material for MkDocs** - Beautiful, responsive theme
- **GitHub Actions** - Automated build and deployment

## 📋 Table of Contents

- [Overview](#overview)
- [Preview Documentation (PRs)](#preview-documentation-prs)
- [Automated Deployment](#automated-deployment)
- [Local Development](#local-development)
- [Troubleshooting](#troubleshooting)

---

## 📖 Preview Documentation (PRs)

Before merging documentation changes, you can preview the built site!

### Automatic PR Previews

When you open a PR that modifies documentation files, the **Documentation Preview** workflow automatically:

1. ✅ Builds the complete documentation site
2. ✅ Uploads it as a downloadable artifact
3. ✅ Posts a comment on the PR with download link
4. ✅ Updates automatically on each new commit

### How to View a Preview

#### Step 1: Download the Preview

After the workflow completes, you'll see a comment on your PR:

1. Click the **"Download Documentation Preview"** link in the PR comment
2. Scroll to the **Artifacts** section at the bottom of the workflow run page
3. Download the `documentation-preview-pr###` artifact (ZIP file)
4. Extract the ZIP file to a folder

#### Step 2: View Locally

**Option A: Local HTTP Server (Recommended)**

```bash
# Navigate to the extracted 'site' folder
cd site

# Start a local server (choose one):

# Python 3
python3 -m http.server 8000

# Node.js
npx serve

# PHP (if installed)
php -S localhost:8000
```

Then open **http://localhost:8000** in your browser.

**Option B: Direct File Access**

Simply open `site/index.html` in your browser.

> ⚠️ **Note:** Search and some interactive features require a local HTTP server (Option A).

### Preview Workflow Details

**Workflow File**: `.github/workflows/docs-preview.yaml`

**Triggers on PR changes to**:
- `docs/wiki/**` - All documentation pages
- `docs/images/**` - Documentation images
- `mkdocs.yml` - Site configuration
- `docs/requirements.txt` - Python dependencies

**What's Included**:
- ✅ Fully built static site
- ✅ All pages and navigation
- ✅ Images and assets
- ✅ Search functionality
- ✅ Dark/light theme
- ✅ Responsive design

---

## Automated Deployment

### How It Works

1. **Trigger**: Workflow runs when:
   - You push changes to `docs/wiki/` folder on `main` branch
   - You modify `mkdocs.yml` configuration
   - You manually trigger the workflow

2. **Build**: GitHub Actions:
   - Checks out the repository
   - Installs Python and MkDocs
   - Builds the documentation site
   - Creates static HTML files

3. **Deploy**: Automatically:
   - Publishes to GitHub Pages
   - Updates the live documentation site
   - Available at: `https://mmornati.github.io/home-assistant-csnet-home`

### Setup Steps

#### 1. Enable GitHub Pages

1. Go to your repository on GitHub
2. Click **Settings** → **Pages**
3. Under **Build and deployment**:
   - **Source**: Select "GitHub Actions"
4. Click **Save**

#### 2. Configure Repository Permissions

The workflow needs write permissions:

1. Go to **Settings** → **Actions** → **General**
2. Scroll to **Workflow permissions**
3. Select **Read and write permissions**
4. Check **Allow GitHub Actions to create and approve pull requests**
5. Click **Save**

#### 3. Verify Workflow File

Ensure `.github/workflows/deploy-docs.yaml` exists with correct permissions:

```yaml
permissions:
  contents: write
  pages: write
  id-token: write
```

#### 4. Test Deployment

1. Make a small change to any file in `docs/wiki/`
2. Commit and push to `main` branch
3. Go to **Actions** tab on GitHub
4. Watch the "Deploy Documentation to GitHub Pages" workflow run
5. Once complete, visit your GitHub Pages URL

### Workflow Details

**Workflow File**: `.github/workflows/deploy-docs.yaml`

**Triggers**:
```yaml
on:
  push:
    branches:
      - main
    paths:
      - 'docs/wiki/**'
      - 'mkdocs.yml'
      - '.github/workflows/deploy-docs.yaml'
  pull_request:
    paths:
      - 'docs/wiki/**'
      - 'mkdocs.yml'
  workflow_dispatch:  # Manual trigger
```

**Jobs**:
1. **Build**: Compiles documentation to static site
2. **Deploy**: Publishes to GitHub Pages (only on push to main)

**Pull Request Behavior**:
- Builds documentation to verify no errors
- Does NOT deploy (preview only)
- Shows any build errors in PR checks

---

## MkDocs Configuration

### Configuration File

**File**: `mkdocs.yml` (in repository root)

### Key Settings

```yaml
site_name: Hitachi CSNet Home Integration
site_url: https://mmornati.github.io/home-assistant-csnet-home
repo_url: https://github.com/mmornati/home-assistant-csnet-home

theme:
  name: material
  palette:
    # Light/dark mode toggle
  features:
    - navigation.instant
    - navigation.tracking
    - search.suggest
    - content.code.copy
```

### Customizing the Site

Edit `mkdocs.yml` to customize:

**Site Information**:
```yaml
site_name: Your Site Name
site_description: Your description
site_author: Your Name
```

**Theme Colors**:
```yaml
theme:
  palette:
    - scheme: default
      primary: blue  # Change to: indigo, teal, green, etc.
      accent: light blue
```

**Navigation Structure**:
```yaml
nav:
  - Home: wiki/Home.md
  - Getting Started:
    - Installation: wiki/Installation-Guide.md
    - Configuration: wiki/Configuration-Guide.md
  # Add or reorder pages
```

**Features**:
```yaml
theme:
  features:
    - navigation.tabs          # Top-level tabs
    - navigation.tabs.sticky   # Sticky tabs
    - navigation.expand        # Expand sections
    - search.suggest          # Search suggestions
    - content.code.copy       # Copy code button
```

### Adding New Pages

1. Create markdown file in `docs/wiki/`
2. Add to navigation in `mkdocs.yml`:
```yaml
nav:
  - Your New Page: wiki/Your-New-Page.md
```
3. Commit and push - automatic deployment!

---

## Local Development

### Prerequisites

Install MkDocs and theme:

```bash
pip install mkdocs-material
pip install mkdocs-minify-plugin
pip install mkdocs-redirects
```

Or use the provided script:

```bash
pip install -r docs/requirements.txt
```

### Build and Serve Locally

**Start development server**:
```bash
mkdocs serve
```

Then open: http://127.0.0.1:8000

**Features**:
- Live reload on file changes
- Preview exactly as it will appear on GitHub Pages
- Test navigation and search
- Verify code highlighting

**Build static site**:
```bash
mkdocs build
```

Output in `site/` directory.

**Strict mode** (fail on warnings):
```bash
mkdocs build --strict
```

### Local Testing Workflow

1. Edit documentation in `docs/wiki/`
2. Run `mkdocs serve` to preview
3. Test navigation, search, formatting
4. Fix any issues
5. Commit and push when satisfied
6. GitHub Actions deploys automatically

---

## Adding Features

### Enable Mermaid Diagrams

Already configured! Use in markdown:

````markdown
```mermaid
graph LR
    A[User] --> B[Home Assistant]
    B --> C[CSNet Manager]
    C --> D[Heat Pump]
```
````

### Enable LaTeX Math

Already configured! Use inline:

```markdown
Einstein's equation: $E = mc^2$
```

Or block:

```markdown
$$
\frac{n!}{k!(n-k)!} = \binom{n}{k}
$$
```

### Add Custom CSS

1. Create `docs/stylesheets/extra.css`
2. Add custom styles
3. Reference in `mkdocs.yml`:
```yaml
extra_css:
  - stylesheets/extra.css
```

### Add Custom JavaScript

1. Create `docs/javascripts/extra.js`
2. Add functionality
3. Reference in `mkdocs.yml`:
```yaml
extra_javascript:
  - javascripts/extra.js
```

---

## Adding Images

### Method 1: In Repository

1. Place images in `docs/images/` or `images/`
2. Reference in markdown:
```markdown
![Description](../images/your-image.png)
```

### Method 2: External URLs

```markdown
![Description](https://example.com/image.png)
```

### Method 3: GitHub Assets

Upload to GitHub Issues/Discussions, use generated URL:

```markdown
![Description](https://user-images.githubusercontent.com/...)
```

### Image Best Practices

- **Format**: PNG for screenshots, SVG for diagrams
- **Size**: Optimize before committing (<500KB)
- **Alt text**: Always include descriptive alt text
- **Path**: Use relative paths for portability

---

## Troubleshooting Deployment

### Build Fails

**Check workflow logs**:
1. Go to **Actions** tab
2. Click on failed workflow run
3. Expand failed step
4. Read error message

**Common issues**:
- Broken markdown links
- Missing files referenced in `mkdocs.yml`
- Invalid YAML in `mkdocs.yml`
- Markdown syntax errors

**Fix**:
1. Test locally with `mkdocs build --strict`
2. Fix errors shown
3. Commit and push again

### Deployment Succeeds But Site Not Updating

**Wait a few minutes**: GitHub Pages can take 1-5 minutes to update

**Clear browser cache**: Hard refresh (Ctrl+Shift+R or Cmd+Shift+R)

**Check GitHub Pages settings**:
- Ensure source is "GitHub Actions"
- Verify branch is correct

### 404 Errors on Site

**Check navigation in `mkdocs.yml`**:
- Ensure all paths are correct
- Paths relative to repository root
- Use `wiki/Page-Name.md` format

**Check file names**:
- Must match exactly (case-sensitive)
- No spaces (use hyphens)

### Workflow Not Triggering

**Check trigger paths**:
```yaml
paths:
  - 'docs/wiki/**'
```

**Ensure files are in correct directory**:
- Must be in `docs/wiki/` folder
- Commit must be to `main` branch

**Manual trigger**:
1. Go to **Actions** tab
2. Select "Deploy Documentation to GitHub Pages"
3. Click **Run workflow**

---

## Advanced Configuration

### Versioning

Use `mike` for documentation versioning:

```bash
pip install mike

# Deploy version
mike deploy --push --update-aliases 2.1 latest

# Set default version
mike set-default --push latest
```

### Search Optimization

Configure search in `mkdocs.yml`:

```yaml
plugins:
  - search:
      separator: '[\s\-,:!=\[\]()"/]+|(?!\b)(?=[A-Z][a-z])|\.(?!\d)|&[lg]t;'
      lang: 
        - en
```

### Analytics

Add Google Analytics:

```yaml
extra:
  analytics:
    provider: google
    property: G-XXXXXXXXXX
```

### Social Cards

Auto-generate social media cards:

```yaml
plugins:
  - social:
      cards_layout_options:
        background_color: "#0066CC"
```

---

## Maintenance

### Keeping Dependencies Updated

Update MkDocs and plugins:

```bash
pip install --upgrade mkdocs-material
pip install --upgrade mkdocs-minify-plugin
pip install --upgrade mkdocs-redirects
```

### Monitoring Deployment

Set up notifications:
1. Go to **Settings** → **Notifications**
2. Enable "Actions" notifications
3. Get notified of failures

### Regular Checks

Periodically verify:
- All links work (use link checker)
- Images load correctly
- Search functions properly
- Mobile display looks good
- No console errors

---

## Migration from GitHub Wiki

If you previously used GitHub Wiki:

### Export Wiki Content

```bash
git clone https://github.com/mmornati/home-assistant-csnet-home.wiki.git
```

### Convert to MkDocs Format

1. Copy markdown files to `docs/wiki/`
2. Update internal links (remove `.md` extensions not needed in MkDocs)
3. Update `mkdocs.yml` navigation
4. Test locally
5. Deploy

### Redirect Old Wiki

Add to `mkdocs.yml`:

```yaml
plugins:
  - redirects:
      redirect_maps:
        'old-page.md': 'wiki/New-Page.md'
```

---

## Benefits of This Setup

✅ **Automated**: Push changes → Documentation updates automatically  
✅ **Beautiful**: Material theme is modern and responsive  
✅ **Searchable**: Full-text search built-in  
✅ **Fast**: Static site, loads instantly  
✅ **Version Controlled**: All changes tracked in git  
✅ **Preview**: PR builds test documentation before merge  
✅ **Free**: GitHub Pages hosting at no cost  
✅ **Professional**: Looks like enterprise documentation  

---

## Getting Help

**MkDocs Documentation**: https://www.mkdocs.org  
**Material Theme**: https://squidfunk.github.io/mkdocs-material  
**GitHub Pages**: https://docs.github.com/en/pages  
**GitHub Actions**: https://docs.github.com/en/actions  

**Issues with deployment?**  
Open an issue: https://github.com/mmornati/home-assistant-csnet-home/issues

---

## Quick Reference

### Common Commands

```bash
# Install dependencies
pip install mkdocs-material mkdocs-minify-plugin mkdocs-redirects

# Serve locally
mkdocs serve

# Build site
mkdocs build

# Build strictly (fail on warnings)
mkdocs build --strict

# Deploy manually (not needed with GitHub Actions)
mkdocs gh-deploy
```

### File Structure

```
repository/
├── .github/
│   └── workflows/
│       └── deploy-docs.yaml       # Deployment workflow
├── docs/
│   ├── wiki/                      # Documentation pages
│   │   ├── Home.md
│   │   ├── Installation-Guide.md
│   │   └── ...
│   ├── images/                    # Images
│   └── stylesheets/               # Custom CSS (optional)
├── mkdocs.yml                     # MkDocs configuration
└── site/                          # Built site (generated, gitignored)
```

---

**Ready to deploy?** Just push your changes to the `main` branch! 🚀

