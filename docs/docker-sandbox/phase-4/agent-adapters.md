# Agent and IDE adapters

Phase 4 uses Docker Sandbox 0.38.x built-in `codex`, `claude`, and `copilot`
agents with the versioned `sandbox/kits/odoo-mixin` artifact. No custom agent
template is required: agent differences stop at launch or attach, while every
agent invokes the same `sandboxctl` and inner Compose runtime.

## Host setup

Initialize the balanced policy once, then keep credentials in Docker Sandbox's
host secret store:

```bash
sbx policy init balanced
sbx secret set openai --oauth
# Or scope an API credential to an existing sandbox interactively:
sbx secret set anthropic --sandbox <sandbox-name>
```

Do not pass `--token`, write a secret-bearing `.env`, or copy agent credential
files into the repository, kit, VM, or saved template. Registry credentials
should use `sbx secret set --registry <host> --password-stdin` and remain
host-only unless a narrower sandbox scope is explicitly needed.

Run the read-only capability, kit, and policy checks before launch:

```bash
sandbox/bin/sandbox-agent preflight
```

The mixin allows only the Docker registry endpoints and GitHub endpoints needed
by this kit. The built-in agent kit adds its provider-specific rules. A denied
preflight is a blocker; inspect it with `sbx policy ls --wide` and `sbx policy
log`. Do not switch to `allow-all` as a workaround.

## Launch agents

```bash
sandbox/bin/sandbox-agent create codex odoo-codex .
sandbox/bin/sandbox-agent create claude odoo-claude .
sandbox/bin/sandbox-agent create copilot odoo-copilot .
sbx run --name odoo-codex codex
```

Clone mode is mandatory in the wrapper. Docker exposes commits through the
host `sandbox-<name>` Git remote; export or commit work before destroy.

## Shared skills

Preview and import host skills into Docker's persistent shared-skills store:

```bash
sbx skills import --dry-run
sbx skills import
```

Docker 0.38.0 scans `~/.agents/skills`, `~/.claude/skills`,
`~/.copilot/skills`, and `~/.cursor/skills` (among others), with the first
same-named skill winning. Review every overwrite prompt. If shared skills are
unavailable or disabled with `--no-share-skills`, the repository's versioned
`plugin/skills/` and generated context files are the fallback; the Odoo mixin
instructions still point every agent to the same lifecycle controller.

## VS Code and Cursor over SSH

First authenticate Docker Sandbox and generate the idempotent SSH configuration:

```bash
sbx login
sbx setup ssh
ssh <sandbox-name>.sbx -- pwd
```

Docker 0.38.0 uses the daemon's Unix socket and active Docker login; do not copy
an SSH private key into the sandbox. In VS Code, install Remote - SSH and run
`Remote-SSH: Connect to Host...`; in Cursor use the equivalent Remote SSH
command. Select `<sandbox-name>.sbx`, open the cloned repository shown by
`ssh <sandbox-name>.sbx -- pwd`, edit the fixture, and use the repository tasks
or terminal commands below:

```bash
sandbox/bin/sandboxctl module <session> test sandbox_fixture
sandbox/bin/sandboxctl logs <session> --service odoo
```

The checked-in `.vscode/tasks.json` delegates tests and correlated logs to the
same thin launcher. Set `input:sandboxName`, `input:sessionId`, and
`input:moduleName` when prompted. Cursor reads the same workspace task format.

If the pinned experimental SSH endpoint completes protocol negotiation but
fails authentication, record the verbose SSH and daemon evidence, then use the
validated terminal fallback without opening any firewall port:

```bash
sbx exec <sandbox-name> -- bash
```

Run the same `sandboxctl module` and `sandboxctl logs` commands from that shell.
`UNKNOWN port 65535` is OpenSSH's proxy-failure placeholder, not a network port;
do not add an ingress rule for it. This fallback is accepted for Ubuntu 24.04
with `sbx` 0.38.0 because the failure remained reproducible after fresh Docker
login, daemon restart, SSH setup, and a new running sandbox.

Kits, shared skills, and SSH are experimental in 0.38.x. The launcher refuses
other minor versions; upgrades require capability and live-test review.
