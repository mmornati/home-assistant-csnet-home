# CSNet Home (unofficial, for Hitachi) Integration - Wiki Documentation

This directory contains comprehensive user documentation for the CSNet Home (unofficial, for Hitachi) integration for Home Assistant.

## 📚 Documentation Structure

All documentation is organized as wiki pages ready to be deployed to GitHub Wiki.

### Core Documentation Pages

1. **[Home.md](Home.md)** - Main landing page with overview and navigation
2. **[Installation-Guide.md](Installation-Guide.md)** - Complete installation instructions (HACS, manual, from source)
3. **[Configuration-Guide.md](Configuration-Guide.md)** - Initial setup and configuration
4. **[Climate-Control.md](Climate-Control.md)** - Controlling climate entities and zones
5. **[Water-Heater-Control.md](Water-Heater-Control.md)** - DHW (Domestic Hot Water) management
6. **[Sensors-Reference.md](Sensors-Reference.md)** - Complete sensor catalog and reference
7. **[Advanced-Features.md](Advanced-Features.md)** - Silent mode, fan control, OTC, extended attributes
8. **[Multi-Zone-Configuration.md](Multi-Zone-Configuration.md)** - C1/C2 circuit setup and management
9. **[Troubleshooting.md](Troubleshooting.md)** - Common issues and solutions
10. **[FAQ.md](FAQ.md)** - Frequently asked questions

## 🎯 Quick Links

### For New Users
- Start with [Installation-Guide.md](Installation-Guide.md)
- Then follow [Configuration-Guide.md](Configuration-Guide.md)
- Check [FAQ.md](FAQ.md) for common questions

### For Existing Users
- [Climate-Control.md](Climate-Control.md) - Learn all climate features
- [Sensors-Reference.md](Sensors-Reference.md) - Find specific sensors
- [Advanced-Features.md](Advanced-Features.md) - Explore advanced capabilities

### When You Have Issues
- [Troubleshooting.md](Troubleshooting.md) - Find solutions
- [FAQ.md](FAQ.md) - Quick answers

## 📋 Documentation Features

Each page includes:
- ✅ Clear step-by-step instructions
- ✅ Code examples (YAML, service calls, automations)
- ✅ Configuration examples
- ✅ Lovelace UI examples
- ✅ Troubleshooting sections
- ✅ Cross-references to related pages
- ✅ Best practices and tips
- ✅ Placeholder markers for screenshots

## 🖼️ About Image Placeholders

Throughout the documentation, you'll see markers like:

```
**[PLACEHOLDER: Screenshot of integration search]**
```

These indicate where screenshots would be helpful. You can:
1. **Replace with actual screenshots** from your Home Assistant installation
2. **Generate mock images** that look like Home Assistant UI
3. **Leave as placeholders** for community contributions

Recommended screenshots:
- Integration search dialog
- Configuration form
- Climate entity card
- Water heater controls
- Sensor lists
- Dashboard examples
- HACS installation steps

## 📖 Deploying to GitHub Wiki

### Option 1: Manual Upload (Recommended for GitHub Wiki)

1. Go to your repository's Wiki on GitHub
2. Create a new page for each .md file
3. Copy the content from each file
4. Adjust internal links if needed (remove .md extension)

### Option 2: Using git-wiki

If using a wiki repository:

```bash
# Clone wiki repository
git clone https://github.com/mmornati/home-assistant-csnet-home.wiki.git

# Copy documentation files
cp docs/wiki/*.md home-assistant-csnet-home.wiki/

# Commit and push
cd home-assistant-csnet-home.wiki
git add *.md
git commit -m "Add comprehensive user documentation"
git push
```

### Option 3: Wiki Sidebar

Create a `_Sidebar.md` file with navigation:

```markdown
### Documentation

**Getting Started**
- [[Home]]
- [[Installation Guide]]
- [[Configuration Guide]]

**Features**
- [[Climate Control]]
- [[Water Heater Control]]
- [[Sensors Reference]]
- [[Advanced Features]]

**Configuration**
- [[Multi Zone Configuration]]

**Help**
- [[Troubleshooting]]
- [[FAQ]]
```

## 🎨 Styling & Formatting

The documentation uses standard Markdown with:
- Headers (H1-H4)
- Code blocks with syntax highlighting
- Tables for structured data
- Blockquotes for notes/warnings
- Lists (ordered and unordered)
- Links (internal and external)

Compatible with:
- GitHub Wiki
- GitHub Pages
- GitBook
- MkDocs
- Any Markdown renderer

## 📝 Content Overview

### Installation-Guide.md
- HACS installation (recommended)
- Manual installation from release
- Manual installation from source
- Preview/PR versions
- Verification steps
- Troubleshooting installation issues

### Configuration-Guide.md
- Adding the integration
- Entering credentials
- Scan interval configuration
- Language selection
- Entity overview
- Configuration examples
- Troubleshooting configuration

### Climate-Control.md
- Basic controls (temperature, mode, preset)
- Advanced controls (fan modes)
- Reading climate state
- Extended attributes
- Lovelace UI examples
- Automation examples
- Troubleshooting

### Water-Heater-Control.md
- Operation modes (Off, Eco, Performance)
- Temperature control
- Lovelace examples
- Automation examples (schedules, boost, vacation)
- Safety considerations
- Integration with solar/smart grid

### Sensors-Reference.md
- Zone sensors (per thermostat)
- Device sensors (WiFi, connectivity)
- Water system sensors
- Environmental sensors
- System status sensors
- Configuration sensors
- OTC sensors
- Alarm sensors
- Using sensors in automations
- Custom template sensors

### Advanced-Features.md
- Silent mode (noise reduction)
- Fan speed control (fan coil systems)
- OTC (Outdoor Temperature Compensation)
- Extended attributes
- Dynamic temperature limits
- Advanced alarm monitoring
- Performance optimization

### Multi-Zone-Configuration.md
- Understanding zones vs circuits
- Configuration examples (2-floor, mixed, water)
- Independent vs coordinated control
- Demand management
- Temperature scheduling
- System monitoring dashboards
- Optimization strategies
- Troubleshooting multi-zone issues

### Troubleshooting.md
- Quick diagnosis table
- Installation issues
- Configuration issues
- Connection issues
- Control issues
- Sensor issues
- Alarm issues
- Performance issues
- Advanced troubleshooting
- Getting help

### FAQ.md
- General questions
- Installation & setup
- Configuration
- Features & capabilities
- Operation
- Zones & circuits
- DHW / Water heater
- Modes & presets
- Sensors
- Advanced features
- Alarms
- Performance
- Comparison & alternatives
- Privacy & security
- Contributing & support
- Future development

## 🔄 Maintaining Documentation

### When to Update
- New features added to integration
- Bug fixes that change behavior
- Community feedback on unclear sections
- New configuration examples discovered
- FAQ questions become frequent

### How to Update
1. Edit the relevant .md file(s)
2. Update cross-references if page names change
3. Add new sections as needed
4. Update version information in Home.md
5. Test all code examples
6. Update this README if structure changes

## 🤝 Contributing to Documentation

Community contributions welcome!

**What to contribute**:
- Screenshots from your installation
- Additional automation examples
- Configuration examples for different setups
- Clarifications for confusing sections
- Additional FAQ entries
- Translations (future)

**How to contribute**:
1. Fork the repository
2. Edit documentation files
3. Submit a Pull Request
4. Describe your changes

## 📊 Documentation Statistics

- **Total Pages**: 10
- **Estimated Reading Time**: ~2-3 hours (complete read)
- **Code Examples**: 150+
- **Automation Examples**: 50+
- **Configuration Examples**: 30+

## 📄 License

Documentation is part of the home-assistant-csnet-home project and is licensed under Apache License 2.0.

## 🙏 Acknowledgments

Documentation created with:
- User feedback from GitHub Discussions
- Code analysis of the integration
- Testing with real Hitachi systems
- Community configuration examples

---

**Ready to deploy?** Start with [Home.md](Home.md) as your wiki homepage!

**Need help?** Open an issue on [GitHub](https://github.com/mmornati/home-assistant-csnet-home/issues)

