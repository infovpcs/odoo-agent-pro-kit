# DeepSeek Harness Integration

The [DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness) (DSH)
has no plugin marketplace. A DSH **agent preset** is a directory holding one
`agent.cordis.yml` composition plus `preset.yml` display metadata, and every
capability that agent has is a plugin row inside that composition. This
integration ships such a preset, which is the DSH equivalent of the native
Hermes plugin in `plugin/__init__.py` and the Claude Code plugin in `plugin/`.

## What the preset gives a session

| Capability | How it is provided |
|---|---|
| `/plan-analysis`, `/start-coding`, `/testing`, `/fleet`, `/rules-check-drift` | Registered on the host `commands` registry; each submits its `plugin/commands/*.md` body as a model-visible user message |
| All 22 Odoo skills | Read from `plugin/skills/*/SKILL.md` and re-registered under DSH's kebab-case skill grammar |
| Live model discovery (`odoo_search_models`, `odoo_get_fields`, `odoo_get_relationships`, `odoo_validate_field`, `odoo_get_model_info`, `odoo_list_all_models`, `odoo_get_version_info`) | In-process JSON-RPC-2.0 client, one pooled session per version |
| Odoo documentation retrieval (`odoo_kb_search`, `odoo_kb_read`, `odoo_kb_list`) | The per-version OKF knowledge bundles, searched offline |
| Workspace introspection (`odoo_workspace_info`) | Detects version/module/sandbox session from the workspace and reports the resolved configuration |
| Lifecycle prompt section | Registered on the host `systemPrompt` registry |
| `odoo-bin` / `manage_modules.sh` / VCS-write / destructive-cleanup / Enterprise-source guardrails | Registered as a `tools.guard`, the DSH equivalent of the Claude Code `PreToolUse` hook |

The preset is otherwise the shipped `standard` coding agent: shell, filesystem,
search, skills, goals, plan mode, compaction, delegation, workflows, web, and
the todo/ask-user/present tools all remain available.

## Requirements

- A working DSH installation (the `standard` preset must be on your roster).
- Node.js 22 or newer — the harness requires it anyway.
- Optional: one or more Odoo databases reachable over HTTP for the `odoo_*`
  discovery tools. Without one, those tools answer with an actionable
  "not configured" message and everything else still works.
- Optional: the per-version OKF documentation bundles under
  `~/odoo-workspaces/knowledge-{17,18,19}/odoo{NN}-okf`. They are
  auto-detected; without them the `odoo_kb_*` tools report what is missing.

## Architecture

```
${DSH_HOME:-$HOME/.dsh}/.agent-presets/odoo-agent-pro-kit/
├── agent.cordis.yml   the composition: standard agent + the odoo-kit row
├── preset.yml         display name, description, roster order
├── odoo-kit.mjs       the plugin: commands, skills, tools, prompt, guard
└── kit-root.txt       written by install.sh — the absolute kit checkout path
```

Three DSH mechanics shape this design, and each is deliberate:

1. **A user preset cannot import the harness's packages.** `~/.dsh` is outside
   any `node_modules` tree the harness resolves from, so `odoo-kit.mjs` uses
   only `node:` builtins and receives every harness service through `ctx`.
2. **A relative row specifier resolves against the preset's own directory.**
   That is why the row is `name: ./odoo-kit.mjs` and the plugin ships inside
   the preset rather than being installed as a package.
3. **Skill names must match `^[a-z0-9]+(-[a-z0-9]+)*$`.** The upstream
   frontmatter names (`odoo_17_coding_standard`) use underscores, which
   `dsh-skill-filesystem` silently drops, so the plugin registers the skills
   itself with normalized names (`odoo-17-coding-standard`).

The `odoo-kit` row registers into the scoped `tools`, `commands`, `skills`, and
`systemPrompt` registries and publishes no service of its own, so it sits loose
in the composition with no `isolate` realm. Every service-owning row
(`planning`, `compaction`, `delegation`) keeps the entry-local realm the
shipped `standard` preset gives it.

## Install

```bash
./integrations/deepseek/install.sh
```

Then start a DSH session and pick the **Odoo Agent Pro Kit** preset. DSH
discovers presets from the filesystem on every roster read, so no restart is
needed for the roster entry itself — an already-running session keeps the
composition it started with.

See [INSTALL.md](INSTALL.md) for the full walkthrough, including how to verify
the mount and how to configure Odoo connections.

## Test

The integration has two layers of test, both run by `./scripts/validate.sh`:

```bash
# Preset shape, realm placement, installer contract, documentation links
python3 -m pytest -q tests/test_deepseek_integration.py

# Plugin behaviour against a recording stub of the Cordis context
node integrations/deepseek/tests/plugin.test.mjs
```

The plugin suite asserts the registered command/skill/tool catalog, the guard's
allow and deny decisions, and a real round-trip against a knowledge bundle when
one is present.

## Relationship to the other integrations

| Agent | Mechanism | Entry point |
|---|---|---|
| Claude Code | Plugin manifest + hooks + slash commands | `.claude-plugin/marketplace.json`, `plugin/` |
| Hermes | Native plugin manifest, in-process tools | `plugin/plugin.yaml`, `plugin/__init__.py` |
| Codex / Cursor / VS Code / Copilot / Antigravity | Context templates, prompts, agent files | `integrations/<tool>/` |
| **DeepSeek Harness** | **Agent preset + Cordis plugin row** | **`integrations/deepseek/`** |

The Python pipeline hooks (`plugin/hooks/`) remain the Claude Code and Hermes
implementation. The DSH preset re-implements the deterministic *guardrails* in
JavaScript so a DSH session gets the same refusals without a Python hook
process; the full lint and gate checks stay Python-only for now.
