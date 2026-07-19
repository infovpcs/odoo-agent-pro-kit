---
name: odoo_app_install_update
description: Patterns for installing and updating custom Odoo applications using manage_modules.sh and related tools. Use when installing or updating Odoo modules.
version: 1.0.0
author: VPCS Team
category: operations
odoo_versions: ["17.0", "18.0", "19.0"]
tags: ["odoo", "install", "update", "modules", "operations", "deployment"]
---
## Goal
Install or update custom modules reliably using the **MANDATORY** `manage_modules.sh` script for all operations (install, update, test).

## Preconditions
- Confirm odoo version and paths (custom addons, standard addons, manage_modules.sh).
- **CRITICAL**: Use the reference implementation at `${ODOO_AGENTS_ROOT:-$HOME/workspace/Odoo_Agents_MultiSupport}/odoo_local_setup` as a guide.
- Ensure dependencies in __manifest__.py are present and installed.

## Steps (install/update/test)
- **ALWAYS** use `manage_modules.sh` instead of raw `odoo-bin` for all operations. This ensures a single control point and consistent environment.
- **First feature** for a module: `manage_modules.sh install <module>`.
- **Subsequent changes**: `manage_modules.sh update <module>`.
- **Testing**: **ALWAYS** refer to `Odoo_Custom_Backend_Testing` skill. Use **XML-RPC** (Odoo < 19) or **JSON-RPC/JSON-2** (Odoo 19+) for testing. 
    - **Why?** RPC-based testing is the **BEST WAY** to test custom apps as it validates real-world interaction and doesn't depend on Odoo's internal test runner which can be rigid.
- Tail logs after run; fix errors and re-run until clean.
- Keep progress.json/task sub-task "LIVE TEST: install/update" as the last step.

## Configuration (use .env)

- The agent MUST read configuration from the AgentSkills `.env` (based on `env_template.txt`) and prefer those values over hard-coded paths. Key env variables to use:
	- `FILESYSTEM_ROOT_PATH` or `FILESYSTEM_ROOT_PATH` fallback: workspace root
	- `ODOO_LOCAL_PATH` (or `ODOO{X}_LOCAL_PATH` for other versions)
	- `ODOO_MANAGE_SCRIPT` (or `ODOO{X}_MANAGE_SCRIPT`)
	- `ODOO_CUSTOM_ADDONS` (or `ODOO{X}_CUSTOM_ADDONS`)
	- `ODOO_LOG_FILE`

Example: the agent should use values from `AgentSkills/env_template.txt` such as:

```
# These paths are EXAMPLES — always set from your actual environment:
# macOS:  $HOME = /Users/<name>   Linux: $HOME = /home/<name> or /root
ODOO_LOCAL_PATH=$HOME/odoo-workspaces/19_workspace
ODOO_MANAGE_SCRIPT=$HOME/odoo-workspaces/19_workspace/manage_modules.sh
ODOO_CUSTOM_ADDONS=$HOME/odoo-workspaces/19_workspace/extra-19
ODOO_LOG_FILE=$HOME/odoo-workspaces/19_workspace/logs/odoo.log
```

If a version-specific env var exists (e.g., `ODOO18_MANAGE_SCRIPT`), prefer it when the agent is operating in that version context.

## Deterministic Install vs Update Decision

- Before running any install/update, the agent MUST consult the progress file at `PROGRESS_DIR/<module>_progress.json` and filesystem/DB to decide:
	1. If the progress file shows NO completed features for this module and the module directory does NOT exist under `ODOO_CUSTOM_ADDONS`, treat this as the FIRST feature → perform `install`.
	2. If the module directory exists or any feature in the progress file is already `complete`, treat changes as incremental → perform `update`.
	3. If the module isn't present on disk but DB already has the module installed (detect via RPC or module list), treat as `update`.
    # Use xmlrpc to verify installation
    python3 -c "
import xmlrpc.client
common = xmlrpc.client.ServerProxy('http://localhost:{http_port}/xmlrpc/2/common')
uid = common.authenticate('{db_name}', 'admin', 'admin', {{}})
models = xmlrpc.client.ServerProxy('http://localhost:{http_port}/xmlrpc/2/object')
state = models.execute_kw('{db_name}', uid, 'admin', 'ir.module.module', 'search_read', [[['name', '=', '$1']]], {{'fields': ['state'], 'limit': 1}})
"
as `update`.

Pseudocode the agent should follow:

```py
progress = read_json(PROGRESS_DIR / f"{module}_progress.json")
module_path = Path(os.environ['ODOO_CUSTOM_ADDONS']) / module
if any(f['status']=='complete' for f in progress.get('features', [])) or module_path.exists():
		action = 'update'
else:
		action = 'install'
```

When uncertain, prefer safe path: attempt `update` first when module folder exists; otherwise `install`.

## Starting Odoo (examples) and using venv

- Use the `ODOO_MANAGE_SCRIPT` from env and run it under the environment the script expects (venv). Prefer invoking the venv Python or the script directly if it wraps the correct venv.

Examples:

```bash
# Start in detached/nohup mode (long start)
export ODOO_HOME="$ODOO_LOCAL_PATH"
nohup "$ODOO_MANAGE_SCRIPT" start > "$ODOO_LOCAL_PATH/logs/odoo_start.out" 2>&1 &

# Or run via the venv Python if required:
VENV_PY="$FILESYSTEM_ROOT_PATH/AgentSkills/.venv/bin/python"
nohup "$VENV_PY" "$ODOO_LOCAL_PATH/odoo-bin" -c "$ODOO_LOCAL_PATH/deploy.conf" > "$ODOO_LOCAL_PATH/logs/odoo_start.out" 2>&1 &
```

## Port readiness and verification

- Verify HTTP port (default 8069) readiness before attempting screenshots or API calls.
    # Wait for service
    attempt=0
    max_attempts=30
    while ! curl -s http://localhost:{http_port} > /dev/null; do
        if [ $attempt -ge $max_attempts ]; then
            echo "❌ Timeout waiting for Odoo on port {http_port}"
            exit 1
        fi
        echo "Waiting for Odoo to start on port {http_port} (attempt $((attempt+1))/$max_attempts)..."
        sleep 2
        attempt=$((attempt+1))
    done
    echo "✅ Odoo is running on port {http_port}"

Commands:

```bash
# Simple curl check
curl -sSf http://127.0.0.1:8069/ -o /dev/null && echo "open" || echo "closed"

# Netcat style
nc -zv 127.0.0.1 8069
```

If closed, tail the start log file and report the last 200 lines to user.

## Log parsing and error detection

- Tail the configured `ODOO_LOG_FILE` and search for errors. Look for keywords `ERROR`, `Traceback`, `ImportError`, `ModuleNotFoundError`, `odoo.exceptions`.

Examples:

```bash
tail -n 200 "$ODOO_LOG_FILE" | egrep "ERROR|Traceback|ImportError|ModuleNotFoundError|odoo.exceptions" -n || true
```

Map error lines to files by parsing file paths in tracebacks and request the agent to open that file for correction.

## Retry policy and backoff

- Use up to 3 attempts for install/update with small fixes between attempts.
- Exponential backoff: wait 2s, 5s, 10s between retries. After 3 failed attempts, mark task failed in progress file and notify user.

## Progress file update requirement

- The agent MUST update `PROGRESS_DIR/<module>_progress.json` after each sub-task (e.g., after code write, after install/update attempt, after tests). Include `last_action`, `last_action_result`, and `retry_count` fields for traceability.

Example snippet to append to progress file:

```json
"last_action": "install",
"last_action_result": "success|failed",
"retry_count": 0
```

## Common fix examples (quick reference)

- Missing dependency in manifest: add dependency to `__manifest__.py` and re-run install.
- ImportError: ensure package installed in Odoo venv; e.g., `uv pip install --python $VENV_PY <package>`.
- XML syntax error: open reported XML file, fix tag mismatch or encoding, re-run update.

## Safety notes

- Do not modify production databases without explicit user confirmation in `PROGRESS_DIR` and a backup entry noted in the progress file.
- Prefer running installs/updates on a local test DB or staging environment.


## Safety & validation
- Do not install if required parents are missing; resolve dependencies first.
- Validate access rights and data integrity after update.
- Record outcomes in tasks.md or progress file status.
