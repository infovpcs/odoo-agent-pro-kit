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

Docker Sandbox sessions use `sandbox/bin/sandboxctl module` as the single
install/update/test entrypoint. It delegates to `manage_modules.sh`, preserves
local execution, and records machine-readable lifecycle-gate results.
Codex, Claude, Copilot, VS Code, and Cursor share the same versioned Odoo mixin
and thin launch/SSH adapters documented in
[`docs/docker-sandbox/phase-4/agent-adapters.md`](docs/docker-sandbox/phase-4/agent-adapters.md).
On pinned platforms where experimental Sandbox SSH fails its authentication
probe, the documented `sbx exec` terminal adapter provides the same controller
contract without exposing an additional network port.

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

**Hermes (native plugin):**
```bash
hermes plugins install infovpcs/odoo-agent-pro-kit/plugin --enable
```
Registers 7 `odoo_*` model-discovery tools (in-process, no separate MCP
server/port needed), the `/plan-analysis`, `/start-coding`, `/testing`,
`/fleet` slash commands, session-start Odoo workspace detection, and all 20
bundled skills under the `odoo-agent-pro-kit:` namespace. See
[CHANGELOG.md](CHANGELOG.md) 0.3.2 for details, or run
`hermes plugins doctor plugin --ci` from a clone to verify locally first.

**Codex:** copy `context-templates/AGENTS.md` into your project root (Codex
reads it natively). See `integrations/codex/INSTALL.md`.

**Cursor, Antigravity, VS Code, GitHub Copilot:** see the matching
`integrations/<tool>/INSTALL.md`.

## What's included

| Component | Where |
|---|---|
| 18 Odoo skills (coding standards, dependency context, tools, testing, docs) | `plugin/skills/` |
| 4 slash commands (`/plan-analysis`, `/start-coding`, `/testing`, `/fleet`) | `plugin/commands/` (Claude Code) / `plugin/__init__.py` (native Hermes) |
| 3 hooks (SessionStart/PreCompact/Stop) for context optimization | `plugin/hooks/` (Claude Code) / `plugin/__init__.py` (native Hermes: `on_session_start`/`on_session_end`) |
| Live MCP server for Odoo 17/18/19 model discovery | `plugin/odoo_mcp/` (standalone server) / `plugin/__init__.py` (native Hermes in-process tools) |
| Compose sidecar running odoo_mcp as a persistent service inside a Docker Sandbox session | `sandbox/mcp-sidecar/` |
| Portable playbook for provisioning an AI agent host for Odoo dev (any agent/IDE, any project) | `plugin/skills/OdooHermesEnvironmentSetup/` |
| Local Odoo workspace bootstrap/management scripts | `odoo_local_setup/` |
| Generic agent context templates | `context-templates/` |
| Six agent/IDE integrations | `integrations/` |

See [CHANGELOG.md](CHANGELOG.md) for release history.

## Docker Sandbox roadmap

The implementation-ready plan for isolated, concurrent Odoo 17/18/19 agent
sessions is in [`docs/docker-sandbox/`](docs/docker-sandbox/README.md). It
includes requirements, architecture, source-guide corrections, release gates,
and the full cross-version test matrix.

Community `/fleet` allocates one local Docker Sandbox per module task through
`sandbox/bin/sandbox-fleet`; shared and remote fleet scheduling remain Pro.
Session logs, redacted diagnostics, stable test artifacts, bounded recovery,
and explicit development-database backup/restore use the Phase 6 controller
contract documented in
[`docs/docker-sandbox/phase-6/observability-recovery.md`](docs/docker-sandbox/phase-6/observability-recovery.md).

Phase 7 release automation, platform setup, upgrade/rollback, benchmarks,
capacity guidance, and local migration are under
[`docs/docker-sandbox/phase-7/`](docs/docker-sandbox/phase-7/operator-runbooks.md).
AI agents should load `plugin/skills/DockerSandboxOperations/SKILL.md` when
configuring or releasing the Sandbox runtime.
The Ubuntu KVM release matrix and measured capacity limits are recorded in
[`phase-7/live-test.md`](docs/docker-sandbox/phase-7/live-test.md); Apple Silicon
and Windows procedures remain unclaimed candidate runbooks until executed.
Community members with that hardware can follow the
[`platform validation guide`](docs/docker-sandbox/community-platform-validation.md),
report results or bugs through the dedicated issue template, and propose tested
runbook or compatibility fixes by pull request.

Phase 8 (in progress) proves the full skill-orchestrated development
lifecycle — dependency/context intake, coding-standard application,
`/plan-analysis` → `/start-coding` → `/testing`, install/update lifecycle
rules, backend/frontend testing, live browser evidence, and dynamic
context-handoff/session-reset — runs correctly end to end **inside a Docker
Sandbox microVM**, using the real VPCSCloud Apps Store 17.0→18.0/19.0
module migration backlog as the proving ground rather than a synthetic
fixture. The pilot module (`edit_remove_pricelist_rule`, 18.0) has completed
all 10 sequence steps with real evidence, including sandbox-native live UI
evidence and a fresh-session context-handoff resume test; artifacts are under
[`docs/docker-sandbox/phase-8/`](docs/docker-sandbox/phase-8/live-test.md).
Phase 8's broader exit gate — a second Tier-1 module migrated inside a
sandbox, an Enterprise-dependency test, timing/resource measurement, the
standalone Phase 8 design note, and the go/no-go batching decision — remains
open. See [`docs/docker-sandbox/tasks.md`](docs/docker-sandbox/tasks.md)
"Phase 8" for the exact skill sequence and exit gate; this is the gate this
kit must pass before it is considered ready for external client project work.

The Odoo 17/18/19 inner runtime controller is documented in
[`sandbox/README.md`](sandbox/README.md). Phase gates remain authoritative in
[`docs/docker-sandbox/tasks.md`](docs/docker-sandbox/tasks.md).

The `sandbox/mcp-sidecar/` Compose-sidecar pattern runs `odoo_mcp` as a
`restart: unless-stopped` service inside the same Compose project as `db`/
`odoo`, so the MCP server survives Sandbox microVM idle-suspend and
cold-reboot instead of relying on an unmanaged bare `docker run` process.
`plugin/skills/DockerSandboxOperations/SKILL.md` documents wiring it into a
session and publishing its port with `sbx ports`.

## Commercial/open-core roadmap

VPerfectCS's plan for keeping this repository useful and open source while
building separately licensed Partner, Enterprise, Upgrade Factory, and managed
offerings is in [`docs/commercial/`](docs/commercial/README.md). It includes the
recommended public/private repository boundary and staged go-to-market plan.

## Validation

Run the complete repository validation suite from any directory inside the
clone:

```bash
./scripts/validate.sh
```

The entrypoint isolates pytest from unrelated globally installed plugins, then
runs tests, skill/artifact/release checks, Compose validation when Docker is
available, syntax checks, and Git whitespace validation.

## Delivery workflow

Docker Sandbox development proceeds one phase per session. Every phase must
finish its checklist and LIVE TEST, update the implementation and documentation
together, pass `./scripts/validate.sh`, update `SESSION_CONTEXT.md`, and receive
a focused commit before the next phase starts. Unsupported or failed live tests
remain explicit blockers and are never marked complete.

Phase 0 is complete. Its architecture, runtime baseline, image
architecture evidence, edition boundary, resource defaults, and JSON contracts
are recorded under [`docs/docker-sandbox/phase-0/`](docs/docker-sandbox/phase-0/).
The stock-sandbox LIVE TEST passed on the designated Ubuntu 24.04 KVM host;
repository, Docker, and registry checks passed on the available Intel Mac.
The Odoo 19 Phase 1 runtime and its four-pass cold/warm Sandbox lifecycle are
also complete; evidence is under
[`docs/docker-sandbox/phase-1/`](docs/docker-sandbox/phase-1/live-test.md).
The Phase 2 version matrix, XML-RPC/JSON-2 CRUD checks, multi-architecture image
builds, and concurrent Ubuntu Sandbox lifecycle are complete; evidence is under
[`docs/docker-sandbox/phase-2/`](docs/docker-sandbox/phase-2/live-test.md).
Phase 3 integrates the existing lifecycle skills and module manager with the
Compose executor; its evidence is under
[`docs/docker-sandbox/phase-3/`](docs/docker-sandbox/phase-3/live-test.md).

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
