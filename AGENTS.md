# AGENTS.md - Hitachi CSNet Home Integration

> AI Assistant Instructions for the home-assistant-csnet-home project

## ⚠️ CRITICAL: RAG Usage Policy

> **MANDATORY**: You MUST use Nexus-Dev RAG tools BEFORE answering ANY question about this project.

**Search-First Approach:**
1. **Stop**: Do NOT answer questions about this codebase based solely on general knowledge.
2. **Search**: ALWAYS use `search_knowledge`, `search_code`, `search_docs`, or `search_lessons` to find project-specific information.
3. **Refine**: If your first search yields no results:
   * **Broaden** your search query
   * **Try different content types** (code → docs → lessons)
   * **Break down** complex questions into smaller searchable parts
4. **Acknowledge**: Only after exhausting RAG searches should you rely on general programming knowledge, and you **must acknowledge** that you couldn't find project-specific information.

**When to Search:**
- ✅ User asks about implementation details, architecture, or configuration
- ✅ User asks how to do something in this project
- ✅ User encounters an error or bug
- ✅ Before suggesting changes or refactors
- ✅ When unsure about existing code patterns

## Project Overview

**Hitachi CSNet Home Integration** is a custom Home Assistant integration that enables control of Hitachi heat pumps and air conditioning systems using the ATW-IOT-01 module through the CSNet Manager cloud service.

**Key Features:**
- Climate control entities per zone (HVAC modes: off, heat, cool)
- Domestic Hot Water (DHW) heater control
- Temperature sensors and monitoring
- Alarm detection and notifications
- Multi-zone support (C1/C2 circuits)
- Dynamic temperature limits based on device type

**Target Users:**
- Home Assistant users with Hitachi heat pump systems
- Systems using ATW-IOT-01 module (replaces Hi-Kumo)

**Documentation:** https://mmornati.github.io/home-assistant-csnet-home

## Architecture

```
home-assistant-csnet-home/
├── custom_components/
│   └── csnet_home/              # Home Assistant custom component
│       ├── __init__.py          # Integration entry point, setup
│       ├── api.py               # CSNet API client (HTTP auth, data parsing)
│       ├── climate.py           # Climate entity (zones, HVAC modes, presets)
│       ├── config_flow.py       # Configuration UI flow
│       ├── const.py             # Constants (domains, modes, defaults)
│       ├── coordinator.py       # DataUpdateCoordinator (polling, state management)
│       ├── helpers.py           # Utility functions
│       ├── number.py            # Number entities (temperature offsets)
│       ├── sensor.py            # Sensor entities (temp, status, alarms)
│       ├── water_heater.py      # DHW water heater entity
│       └── manifest.json        # Integration metadata
├── tests/                       # Pytest unit tests
│   ├── test_api.py              # API parsing tests
│   ├── test_climate.py          # Climate entity behavior
│   ├── test_config_flow.py      # Configuration flow tests
│   ├── test_coordinator.py      # Coordinator update logic
│   └── fixtures/                # Test data fixtures
├── docs/                        # Documentation (MkDocs)
│   └── wiki/                    # User guides
├── scripts/                     # Development scripts
│   ├── integration-test.sh      # Docker integration testing
│   └── test-workflows.sh        # GitHub Actions validation
├── .github/workflows/           # CI/CD automation
│   ├── validate.yaml            # PR validation (lint, test, type check)
│   ├── release.yaml             # Release automation
│   └── smoke-tests.yaml         # Quick compatibility checks
└── .nexus/                      # Nexus-Dev configuration
    └── mcp_config.json          # MCP server configuration (github, homeassistant)
```

## Development Commands

### Testing

```bash
# Run all unit tests
pytest

# Run with coverage report
pytest --cov=custom_components/csnet_home --cov-report term-missing

# Generate HTML coverage report
pytest --cov=custom_components/csnet_home --cov-report html
# Open: htmlcov/index.html

# Run specific test file
pytest tests/test_api.py
pytest tests/test_climate.py -v
```

### Code Formatting

```bash
# Format all Python code
black custom_components/csnet_home tests

# Sort imports
isort custom_components/csnet_home tests

# Quick format script
./format-code.sh
```

### Integration Testing (Docker)

```bash
# Start Home Assistant with the integration
./scripts/integration-test.sh start
# or: make start

# View logs (real-time)
./scripts/integration-test.sh logs
# or: make logs

# Restart after code changes
./scripts/integration-test.sh restart
# or: make restart

# Stop and clean
./scripts/integration-test.sh stop
# or: make stop
```

### Workflow Validation

```bash
# Validate GitHub Actions workflows
./scripts/test-workflows.sh

# Test with act (Docker-based)
act pull_request -W .github/workflows/validate.yaml
```

## Before Pushing Code

**Pre-commit checks:**
```bash
# Runs automatically via pre-commit hooks:
# - black (code formatting)
# - isort (import sorting)
# - pylint (linting)
# - yamllint (YAML validation)
```

**Manual validation:**
```bash
# Run tests
pytest

# Check formatting
black --check custom_components/csnet_home tests
isort --check-only custom_components/csnet_home tests
```

## Testing Guidelines

### Unit Tests
- **Coverage target:** Maintain high coverage for core modules (api.py, climate.py, coordinator.py)
- **Test fixtures:** Use fixtures in `tests/fixtures/` for realistic CSNet API responses
- **Mocking:** Mock Home Assistant components (`hass`, `async_add_entities`, etc.)

### Integration Tests
- Test with real Home Assistant instance via Docker
- Verify entities are created correctly (climate, water heater, sensors)
- Test control flows (mode changes, temperature adjustments)

### CI/CD
- **Smoke tests:** Fast compatibility checks (12 combinations)
- **Full matrix:** Python 3.11-3.13 × HA 2025.6, 2025.8, 2025.10
- **Nightly tests:** Auto-detect latest HA version, test dev branch
- **See:** `CI_CD_TESTING.md` for full details

## Nexus-Dev Knowledge Base

This project uses **Nexus-Dev** for persistent AI memory (Project ID: `22999c14-5d0e-4db9-b304-3c138c8756f8`).

### Available MCP Tools

**Core Search:**
| Tool | Purpose |
|------|---------|
| `search_knowledge` | Search all indexed content (code, docs, lessons) |
| `search_code` | Find functions, classes, methods |
| `search_docs` | Search documentation/markdown files |
| `search_lessons` | Find past problem/solution pairs |
| `search_insights` | Find past mistakes, discoveries, optimizations |
| `search_implementations` | Find how features were built |

**Knowledge Capture:**
| Tool | Purpose |
|------|---------|
| `record_lesson` | Save a debugging lesson for future reference |
| `record_insight` | Capture LLM reasoning, mistakes, backtracking |
| `record_implementation` | Save implementation summaries with design decisions |
| `index_file` | Index a new file into the knowledge base |

**Tool & Agent Management:**
| Tool | Purpose |
|------|---------|
| `search_tools` | Find other available MCP tools |
| `get_tool_schema` | Get details for an MCP tool |
| `invoke_tool` | Run an MCP tool |
| `list_agents` | See available autonomous agents |
| `ask_agent` | Delegate a task to an agent |
| `refresh_agents` | Reload agent definitions from disk |

**Integrations:**
| Tool | Purpose |
|------|---------|
| `import_github_issues` | Import GitHub issues/PRs for search |
| `get_project_context` | View project stats and recent lessons |

### Workflow Guidelines

**At Session Start:**
```python
get_project_context()
```

**Global Code Search (Before Implementing):**
If you don't know where code lives, search by *responsibility*:
```python
# "Which file handles CSNet API communication?"
search_knowledge("CSNet API authentication and requests")

# "Find the climate entity class"
search_code("class CSNetClimate")

# "How are sensors created?"
search_code("sensor entity creation")
```

**When Debugging:**
```python
search_lessons("error message or problem description")
search_insights("mistake related to Home Assistant platform")
```

**After Solving a Bug:**
```python
record_lesson(
    problem="<what went wrong>",
    solution="<how you fixed it>",
    context="<file path or additional info>",
    problem_code="<buggy code snippet>",
    solution_code="<fixed code snippet>"
)
```

### Best Practices

1. **Search first** - Always check for existing implementations before writing new code.
2. **Record lessons** - After solving non-trivial bugs, save the solution for future reference.
3. **Index important files** - When creating new modules, index them for searchability.
4. **Check context** - Start sessions with `get_project_context()` to understand the codebase.

## Automatic Knowledge Capture

> **IMPORTANT**: The tools below should be called **automatically** during development to build a knowledge base of insights and implementations.

### When to Record Insights (Real-Time)

Call `record_insight` **immediately** when any of the following happens:

**Mistakes** - You tried something that didn't work:
```python
record_insight(
    category="mistake",
    description="<what went wrong>",
    reasoning="<why you thought it would work>",
    correction="<how you fixed it>"
)
```

**Backtracking** - You changed direction on an approach:
```python
record_insight(
    category="backtrack",
    description="<original approach>",
    reasoning="<why you're changing direction>",
    correction="<new approach>"
)
```

**Discoveries** - You found something non-obvious or useful:
```python
record_insight(
    category="discovery",
    description="<what you discovered>",
    reasoning="<why it's useful/important>"
)
```

**Optimizations** - You found a better way to do something:
```python
record_insight(
    category="optimization",
    description="<optimization made>",
    reasoning="<why it's better>",
    correction="<old approach>"
)
```

### When to Record Implementations (After Completion)

After finishing a feature, refactor, or significant work, call `record_implementation`:

```python
record_implementation(
    title="<short title>",
    summary="<what was built - 1-3 sentences>",
    approach="<how it was built - technical approach>",
    design_decisions=[
        "Decision 1: rationale",
        "Decision 2: rationale"
    ],
    files_changed=["file1.py", "file2.py"]
)
```

### GitHub Integration

Import GitHub issues and PRs:

```python
import_github_issues(owner="mmornati", repo="home-assistant-csnet-home", state="all")
```

Then search issues:
```python
search_knowledge("alarm notification bug", content_type="github_issue")
```

### Agent Usage

Nexus-Dev supports autonomous sub-agents.

**Discover Agents:**
```python
list_agents()
```

**Delegate Tasks:**
```python
ask_agent(agent_name="agent_name", task="Task description")
```

## Home Assistant Specific Guidelines

### Entity Conventions
- **Climate entities:** `climate.{device_name}_{room_name}`
- **Water heater:** `water_heater.{device_name}_dhw`
- **Sensors:** `sensor.{device_name}_{room_name}_{metric}`

### State Management
- Use `DataUpdateCoordinator` for polling CSNet API (coordinator.py)
- Update interval: 30 seconds (configurable)
- Handle API errors gracefully (retry logic, logging)

### Configuration Flow
- User enters CSNet credentials via UI (config_flow.py)
- Credentials validated against CSNet API
- Integration auto-discovers devices and zones

### Platform Registration
Platforms are registered in `__init__.py`:
- `climate` - Zone control entities
- `water_heater` - DHW entity
- `sensor` - Temperature, status, alarm sensors
- `number` - Temperature offset entities

### Alarm Handling
- Monitor `alarm_code` attribute (0 = no alarm)
- Create persistent notification on alarm detection
- Clear notification when alarm resolved

## Common Development Patterns

### Adding a New Sensor
1. Define sensor type in `const.py` (domain, unit, device class)
2. Add sensor description class in `sensor.py`
3. Implement `_attr_native_value` property
4. Update coordinator data parsing if needed

### Adding HVAC Mode/Preset
1. Map CSNet mode to Home Assistant mode in `const.py`
2. Update `climate.py` supported modes/presets
3. Implement mode/preset setter methods
4. Add tests in `tests/test_climate.py`

### Debugging API Issues
1. Enable debug logging: `custom_components.csnet_home: debug`
2. Capture `/data/elements` response from CSNet web app (browser DevTools)
3. Add test fixture in `tests/fixtures/` with the response
4. Test parsing in `tests/test_api.py`

## Contributing Workflow

1. **Fork and branch:**
   ```bash
   git checkout -b feature/amazing-feature
   ```

2. **Make changes and test:**
   ```bash
   pytest
   black custom_components/csnet_home tests
   ```

3. **Integration test (optional):**
   ```bash
   ./scripts/integration-test.sh start
   # Test manually at http://localhost:8123
   ```

4. **Commit and push:**
   ```bash
   git commit -m "Add amazing feature"
   git push origin feature/amazing-feature
   ```

5. **Open Pull Request** on GitHub

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## Resources

- **User Documentation:** https://mmornati.github.io/home-assistant-csnet-home
- **GitHub Issues:** https://github.com/mmornati/home-assistant-csnet-home/issues
- **Discussions:** https://github.com/mmornati/home-assistant-csnet-home/discussions
- **Releases:** https://github.com/mmornati/home-assistant-csnet-home/releases
- **CI/CD Testing Guide:** [CI_CD_TESTING.md](CI_CD_TESTING.md)
- **Integration Testing Guide:** [INTEGRATION_TESTING.md](INTEGRATION_TESTING.md)
