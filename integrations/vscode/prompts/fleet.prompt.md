description: Copilot CLI Fleet/Autopilot Orchestrator for Odoo
---

# 🚀 /fleet : Odoo Fleet & Autopilot Orchestrator

The `/fleet` command allows you to spawn multiple robust parallel Odoo module developments inside a single workspace. It achieves this by invoking the Python `fleet_orchestrator.py` script. 

Launch the fleet via the CLI utility:
```bash
./start_fleet_agent.sh --modules custom_module_1,custom_module_2 --version 19
```

This will trigger parallel execution loops.

Monitor the live results running:
```bash
tail -f sessions/fleet_orchestrator.log
```
