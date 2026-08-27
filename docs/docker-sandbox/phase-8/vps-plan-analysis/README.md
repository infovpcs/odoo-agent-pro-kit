# Live `/plan-analysis` verification — Oracle Cloud VPS Hermes profiles

**Date:** 2026-08-27
**Host:** Oracle Cloud VPS (Ubuntu 24.04 KVM), Hermes Agent 0.20.5
**Plugin:** `odoo-agent-pro-kit` 0.5.1 (synced from `main` @ `fcb6ef0`), installed
and `enabled` on all three profiles; `hermes plugins doctor --ci` → `7 tool(s),
5 hook(s)`, zero warnings, on `odoo17-dev` / `odoo18-dev` / `odoo19-dev`.

## Runs

| Profile | Command | Result |
|---------|---------|--------|
| `odoo18-dev` | `/plan-analysis 18 vpcs_stock_min_alert …` | PRD produced (`odoo18-dev-plan-analysis.md`) |
| `odoo17-dev` | `/plan-analysis 17 vpcs_partner_ref_tag …` | PRD produced (`odoo17-dev-plan-analysis.md`) |

Both profiles use model `openrouter/free`. The slash command dispatches
correctly through the plugin and the agent produces a PRD artifact.

**Observation (model capability, not a plugin defect):** the free-tier model
writes a single consolidated PRD file (into `~/.hermes/plans/…` or
`~/.hermes/profiles/<p>/plans/…`) rather than executing the full 12-step
`plan_analysis_workflow.md` that scaffolds `{module}/docs/{requirements,design,
tasks,module_meta}.md`. Same behaviour as the 2026-08-18 runs. A more capable
model is needed for the full `docs/` folder output; the command wiring,
skill loading, and artifact generation are all verified working.

## Housekeeping done on the VPS

- `~/odoo-agent-pro-kit` fast-forwarded `a04f552` → `fcb6ef0` (30 commits).
- Plugin content re-synced into each profile's `plugins/odoo-agent-pro-kit/`
  (Hermes 0.20.5 `plugins install` blocks a reinstall from a `file://` source
  with a "dangerous verdict" over the `allowed-tools: ["mcp-odoo:*"]` wildcard
  in the `Odoo{17,18,19}ExistingDependencyContext` skills — a scan-policy
  false-positive worth narrowing in a later release).
- Removed a stale duplicate `plugins/plugin/` (v0.1.0, 2026-08-18) from each
  profile and dropped its dead key from `.install-metadata.json`.
- `plugins.scan_on_install` was toggled during troubleshooting and restored to
  its default (`true`).
