---
description: Initialize and manage nexus-dev knowledge base
---

# Nexus-Dev Knowledge Management Workflow

This workflow helps you manage the nexus-dev knowledge base for the home-assistant-csnet-home project.

## Project Information

- **Project ID:** `22999c14-5d0e-4db9-b304-3c138c8756f8`
- **Project Name:** `home-assistant-csnet-home`
- **Embedding Provider:** OpenAI (text-embedding-3-small)

## Session Start

### Get project context
// turbo
```python
get_project_context()
```

## Indexing Files

### Index a specific file
```python
index_file("custom_components/csnet_home/api.py")
```

### Index key modules
```python
# Index main component files
index_file("custom_components/csnet_home/__init__.py")
index_file("custom_components/csnet_home/api.py")
index_file("custom_components/csnet_home/climate.py")
index_file("custom_components/csnet_home/coordinator.py")
index_file("custom_components/csnet_home/sensor.py")
index_file("custom_components/csnet_home/water_heater.py")
```

### Index documentation
```python
index_file("README.md")
index_file("CONTRIBUTING.md")
index_file("CI_CD_TESTING.md")
index_file("INTEGRATION_TESTING.md")
```

## Searching Knowledge

### Search all content
```python
search_knowledge("CSNet API authentication")
```

### Search code specifically
```python
search_code("class CSNetClimate")
search_code("coordinator update interval")
```

### Search documentation
```python
search_docs("integration testing setup")
search_docs("alarm handling")
```

### Search past lessons
```python
search_lessons("Home Assistant configuration error")
search_lessons("API authentication failed")
```

### Search insights
```python
search_insights("temperature limit detection")
search_insights("mistake", category="mistake")
```

### Search implementations
```python
search_implementations("alarm notification feature")
```

## Recording Knowledge

### Record a lesson after debugging
```python
record_lesson(
    problem="Climate entity not updating temperature",
    solution="Added proper coordinator listener registration in async_added_to_hass",
    context="custom_components/csnet_home/climate.py",
    problem_code="# Missing: await self.coordinator.async_add_listener(...)",
    solution_code="await self.coordinator.async_add_listener(self._handle_coordinator_update)"
)
```

### Record an insight during development
```python
record_insight(
    category="discovery",
    description="Home Assistant requires unique_id for entity registry integration",
    reasoning="Discovered while debugging entity not appearing after restart"
)
```

### Record implementation after completing feature
```python
record_implementation(
    title="Alarm monitoring with persistent notifications",
    summary="Implemented alarm detection from CSNet API with persistent Home Assistant notifications",
    approach="Monitor alarm_code attribute in coordinator updates, create/clear persistent notifications via hass.components.persistent_notification",
    design_decisions=[
        "Use persistent notifications instead of native notify platform for reliability",
        "Store notification ID based on device to support multi-device setups"
    ],
    files_changed=[
        "custom_components/csnet_home/coordinator.py",
        "custom_components/csnet_home/sensor.py"
    ]
)
```

## GitHub Integration

### Import GitHub issues and PRs
```python
import_github_issues(
    owner="mmornati",
    repo="home-assistant-csnet-home",
    state="all",
    limit=50
)
```

### Search imported issues
```python
search_knowledge("temperature limit bug", content_type="github_issue")
```

## Agent Management

### List available agents
```python
list_agents()
```

### Refresh agent definitions
```python
refresh_agents()
```

### Delegate task to agent
```python
ask_agent(
    agent_name="nexus_architect",
    task="Design implementation plan for multi-room temperature scheduling"
)
```

## MCP Tool Discovery

### Find relevant MCP tools
```python
search_tools("home assistant entity")
search_tools("github issue", server="github")
```

### Get tool schema
```python
get_tool_schema(server="homeassistant", tool="call_service")
```

### Invoke MCP tool
```python
invoke_tool(
    server="homeassistant",
    tool="get_state",
    arguments={"entity_id": "climate.living_room"}
)
```

## Workflow Tips

1. **Start every session** with `get_project_context()` to see recent work
2. **Search before implementing** - Check if similar code or solutions exist
3. **Record lessons immediately** after solving bugs
4. **Index new files** as you create them for future searchability
5. **Use specific queries** - More specific = better results
