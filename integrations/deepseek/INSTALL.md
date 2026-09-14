# Installing the DeepSeek Harness preset

This walkthrough installs the `odoo-agent-pro-kit` agent preset into the
DeepSeek Harness (DSH) user preset root and verifies that it mounts.

## 1. Install

From the kit checkout:

```bash
./integrations/deepseek/install.sh
```

The script copies the preset into

```
${DSH_HOME:-$HOME/.dsh}/.agent-presets/odoo-agent-pro-kit/
```

and writes `kit-root.txt` beside it so the plugin knows where the kit lives.
Re-running it refreshes the preset and picks up a moved checkout; the preset
root is owned by you, so nothing else in the harness is touched.

Useful flags:

```bash
./integrations/deepseek/install.sh --dry-run     # print the plan, change nothing
./integrations/deepseek/install.sh --uninstall   # remove the preset
```

The installer prints the knowledge bundles it found:

```
Odoo documentation knowledge bases:
  17.0: /Users/you/odoo-workspaces/knowledge-17/odoo17-okf
  18.0: /Users/you/odoo-workspaces/knowledge-18/odoo18-okf
  19.0: /Users/you/odoo-workspaces/knowledge-19/odoo19-okf
```

A version reported as *not found* means the `odoo_kb_*` tools will refuse for
that version with a message naming the expected path — everything else still
works.

## 2. Confirm the roster entry

Start DSH and open the agent-preset picker. **Odoo Agent Pro Kit** should be
listed with the description *Full coding agent plus the Odoo 17/18/19
custom-application lifecycle…*. DSH re-reads preset roots on every roster read,
so the entry appears without restarting the harness.

If the entry is missing, check the directory name and the composition file:

```bash
ls "${DSH_HOME:-$HOME/.dsh}/.agent-presets/odoo-agent-pro-kit/"
# agent.cordis.yml  kit-root.txt  odoo-kit.mjs  preset.yml
```

A roster row marked *broken* names its own reason (a missing composition, an
unloadable YAML dialect, or a row naming a plugin that cannot be resolved). The
most common cause after moving the checkout is a stale `kit-root.txt`; re-run
the installer.

## 3. Start a session on the preset

Create a session and select **Odoo Agent Pro Kit** before the conversation
starts — an agent's composition is fixed once its conversation has begun.

In that session, confirm the model's tool list contains the `odoo_*` tools and
that these commands resolve:

```
/plan-analysis 19.0 my_module
/start-coding 18.0 my_module
/testing 19.0 my_module
/fleet 19.0
/rules-check-drift main...HEAD
```

Each command loads its workflow body from `plugin/commands/<name>.md` and asks
the model to execute it. The Odoo skills appear in the session's skill catalog
under kebab-case names (`odoo-19-coding-standard`, `odoo-17-dependency-context`,
…), and the lifecycle rules are part of the system prompt.

## 4. Configure Odoo connections

The `odoo_*` discovery tools talk JSON-RPC-2.0 to a live Odoo database.
Configuration is per version and read from the environment, in this precedence
order:

1. the row's `config.odoo["<version>"]` in `agent.cordis.yml` (for a
   non-secret override such as a different host or database);
2. `ODOO<NN>_URL`, `ODOO<NN>_DB_NAME`, `ODOO<NN>_DB_USER`, `ODOO<NN>_DB_PASSWORD`;
3. `ODOO_URL`, `ODOO_DB_NAME`, `ODOO_DB_USER`, `ODOO_DB_PASSWORD`.

```bash
export ODOO19_URL="http://localhost:8069"
export ODOO19_DB_NAME="odoo19_dev"
export ODOO19_DB_USER="admin"
export ODOO19_DB_PASSWORD="admin"
```

Set these in the shell that launches the harness so every session inherits
them, then start a new session. Inside a Docker Sandbox session the preset also
reads `.sandbox/session.json`, which supplies the version, module, session id,
and the in-sandbox Odoo URL automatically.

Ask the session to run `odoo_workspace_info` to see exactly which version,
database, and knowledge bundles were resolved.

## 5. Verify the mount without starting a session

`./scripts/validate.sh` runs the repository test suite, which includes
`tests/test_deepseek_integration.py` (preset shape, realm placement, installer
contract, documentation links) and the plugin behavioural suite
`integrations/deepseek/tests/plugin.test.mjs`.

To mount-validate the preset inside a running harness — the same composition a
session start performs, minus the agent — have a session on any preset register
a temporary probe plugin that injects `agentPresets` and calls
`standingKeyFor('odoo-agent-pro-kit')`. It resolves when the composition mounts
and names the offending row otherwise.

The four failures it catches, and what they mean here:

| Failure | Meaning for this preset |
|---|---|
| `Cannot find package …` | A row names a plugin the harness does not have installed — usually an optional product provider that must stay `disabled: true` |
| `invalid config: $.…` | A row's config no longer matches its plugin's schema |
| `N row(s) did not activate: …` | A consumer row sits outside its provider's realm, or a service it needs never appeared |
| `row(s) published process-global service(s) […]` | A service-owning row lost its `isolate` realm |

## 6. Environment variables

| Variable | Effect |
|---|---|
| `DSH_HOME` | Harness home; the preset root is `$DSH_HOME/.agent-presets` |
| `ODOO<NN>_URL`, `ODOO<NN>_DB_NAME`, `ODOO<NN>_DB_USER`, `ODOO<NN>_DB_PASSWORD` | Per-version Odoo connection |
| `ODOO_URL`, `ODOO_DB_NAME`, `ODOO_DB_USER`, `ODOO_DB_PASSWORD` | Fallback Odoo connection |
| `ODOO_KIT_ALLOW_RAW_ODOO=1` | Lifts the raw `odoo-bin` and direct `manage_modules.sh` refusals |
| `ODOO_KIT_ALLOW_VCS_WRITE=1` | Lifts the `git push`/`merge`/`tag`, `gh pr`, and destructive-cleanup refusals |

Both lift variables accept the same truthy spellings the Python hooks do
(`1`, `true`, `yes`, `on`, case-insensitive). The VCS refusal can also be lifted
for one workspace by creating a `.sandbox/AUTHORIZED` marker, read per tool call
so it can be added or removed mid-session — exactly like
`plugin/hooks/checks/authz.py`. The repository's own `AGENTS_PHASE_AUTHORIZED`
variable is deliberately **not** consulted: it authorizes a contributor phase
workflow, not an agent's shell.

## 7. Uninstall

```bash
./integrations/deepseek/install.sh --uninstall
```

This removes only the copied preset directory. Sessions already running on the
preset keep their composed agent until they end.
