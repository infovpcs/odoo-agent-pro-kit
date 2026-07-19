---
description: Copilot CLI Fleet/Autopilot Orchestrator
---

# 🚀 /fleet : Odoo Fleet & Autopilot Orchestrator

The `/fleet` command allows you to spawn multiple robust parallel Odoo module developments inside a single workspace. It achieves this by invoking the Python `fleet_orchestrator.py` script. 

Instead of typing `/fleet m1,m2` through natural language, you should directly run the CLI utility to correctly launch processes in the background!

## Getting Started:
Ensure you are in the AgentSkills folder!
Open a bash/zsh shell session and type:
```bash
./start_fleet_agent.sh --modules custom_sale,custom_hr --version 19
```

This will automatically trigger:
1. `fleet_orchestrator.py` which tracks each module stream.
2. Background isolation and dependency tracking in `sessions/{module_name}_progress.json`.
3. Parallel execution loops.

Monitor the live results running:
```bash
tail -f sessions/fleet_orchestrator.log
```
