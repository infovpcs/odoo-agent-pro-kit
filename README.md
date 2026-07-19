# Odoo Agent Pro Kit

A professional, license-clean starter kit for Odoo 17/18/19 custom application
development with AI coding agents — Claude Code, Codex, Cursor, Antigravity,
VS Code Copilot Chat, and GitHub Copilot CLI/Agent, all covered.

![Architecture](docs/architecture.png)

## Who this is for

Any Odoo developer with a year or two of experience who wants a ready-made,
version-aware `/plan-analysis` → `/start-coding` → `/testing` workflow, a live
MCP server for real-time model discovery, and coding-standard/testing skills
for Odoo 17.0, 18.0, and 19.0 — without building any of it from scratch.

## Quickstart

```bash
git clone https://github.com/infovpcs/odoo-agent-pro-kit.git
cd odoo-agent-pro-kit
./bootstrap.sh --versions 19
```

This bootstraps a local Odoo 19.0 workspace under `~/odoo-workspaces/19_workspace`
and copies the agent context templates into it. See `./bootstrap.sh --help` for
multi-version setup.

## Install the agent plugin

**Claude Code:**
```
/plugin marketplace add infovpcs/odoo-agent-pro-kit
/plugin install odoo-agent-pro-kit
```

**Codex:** copy `context-templates/AGENTS.md` into your project root (Codex
reads it natively). See `integrations/codex/INSTALL.md`.

**Cursor, Antigravity, VS Code, GitHub Copilot:** see the matching
`integrations/<tool>/INSTALL.md`.

## What's included

| Component | Where |
|---|---|
| 18 Odoo skills (coding standards, dependency context, tools, testing, docs) | `plugin/skills/` |
| 4 slash commands (`/plan-analysis`, `/start-coding`, `/testing`, `/fleet`) | `plugin/commands/` |
| 3 hooks (SessionStart/PreCompact/Stop) for context optimization | `plugin/hooks/` |
| Live MCP server for Odoo 17/18/19 model discovery | `plugin/odoo_mcp/` |
| Local Odoo workspace bootstrap/management scripts | `odoo_local_setup/` |
| Generic agent context templates | `context-templates/` |
| Six agent/IDE integrations | `integrations/` |

## Contributing

Fork this repo, keep your fork's `main` synced with upstream, and open a pull
request using the PR template. See [CONTRIBUTING.md](CONTRIBUTING.md) for the
full flow, including how PR review works.

## Support this project

If this kit saves you time, consider supporting ongoing maintenance and future
releases:

- 🇮🇳 **Razorpay** (India + international cards/UPI): https://razorpay.me/@vperfectCS
- 🌍 **PayPal** (international): https://www.paypal.com/paypalme/vperfectcs

This is entirely optional — every part of this kit is free to use under the
Apache 2.0 license below, with no gated functionality.

## About the maintainer

Maintained by [Vinay Rana](https://youtube.com/@vinusoft85) — Founder & Lead
Odoo Implementation Consultant at [VPerfectCS](https://www.vperfectcs.com)
(Veracious Perfect Consultancy Services Pvt. Ltd.), a 10-consultant Odoo ERP
consultancy covering 5 industries with an AI/automation specialization.
Tutorials on Odoo, AI agents, and ERP automation:
[YouTube @vinusoft85](https://youtube.com/@vinusoft85). Contact:
vinay.ra@vperfectcs.com.

## License

Apache License 2.0 — see [LICENSE](LICENSE).
