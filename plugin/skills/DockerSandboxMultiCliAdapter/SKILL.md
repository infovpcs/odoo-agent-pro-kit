---
name: docker-sandbox-multi-cli-adapter
description: "Manage multiple coding-agent CLIs (Codex, Claude, Hermes, Gemini) in Docker Sandbox phases for Odoo development."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [docker-sandbox, multi-cli, adapter, odoo, phase8, agent-management]
    related_skills: [odoo-commanding-system, hermes-agent-development]
---

# Docker Sandbox Multi-CLI Adapter

## Overview

This skill provides patterns for working with multiple coding-agent CLIs in Docker Sandbox sessions when developing Odoo modules. It addresses the challenge where one agent's credentials expire or become unavailable, requiring seamless switching to alternative agents while maintaining consistent workflows.

## When to Use

- You are executing Docker Sandbox Phase 8 (skill-orchestrated migration pipeline) or similar Odoo development workflows
- One coding-agent CLI (e.g., Codex) has expired credentials or is temporarily unavailable
- You need to switch between different agent CLIs (Codex, Claude Code, Hermes CLI, Gemini CLI) for the same Odoo session
- You want to establish consistent non-interactive invocation patterns across different agent runtimes
- You are troubleshooting agent credential issues in sandboxed environments

## Supported Agent CLIs

| Agent CLI | Status | Notes |
|-----------|--------|-------|
| Codex | **Proven (Phase 8, real run)** | Docker-managed proxy OAuth token can expire; fix is a **host-level** re-auth (see below), not a per-sandbox fix |
| Hermes CLI | Proven (Phase 8) | Works via odoo17/odoo18/odoo19-dev profiles; requires profile activation |
| Claude Code CLI | Tested, works, but painful | `npm install -g claude-cli`; no interactive `/login` in headless sandbox — must set `ANTHROPIC_API_KEY` env var (see below) |
| Gemini CLI | Tested, blocked | Pre-installed in `sbx create gemini ...` sandboxes; needs a real Google `GOOGLE_API_KEY`/`GEMINI_API_KEY` — there is no `gemini auth login` device flow in headless sandbox mode |

### The fix that actually worked: host-level Codex OAuth re-auth

When Codex reports `401 unexpected status ... auth error code: token_expired`
even right after a fresh sandbox restart, the fix is **not** inside the
sandbox. Run this on the **outer Ubuntu KVM host** (not inside any `sbx exec`):

```bash
sbx secret set openai --oauth
```

This prints a `https://auth.openai.com/oauth/authorize?...` URL with a
`redirect_uri=http://localhost:1455/auth/callback`. On a remote VPS, a
browser on your local machine cannot reach the VPS's own `localhost:1455`,
so completing the login in a browser on your laptop will silently fail the
callback. **Fix: open an SSH local port-forward before starting the flow**,
then open the printed URL in your **local** browser once the tunnel is up:

```bash
ssh -L 1455:localhost:1455 <user>@<vps-host>
# in that same (or a second) SSH session on the VPS:
sbx secret set openai --oauth
```

Verify with `sbx secret ls` — look for `(global) service openai (oauth
configured)`. This credential is **global**, so every sandbox created
*after* this point automatically inherits it ("Using stored OpenAI OAuth
credentials" appears in `sbx create` output) — no per-sandbox re-auth needed
for future modules/phases.

**Stale sandboxes still hold the dead token in-container.** Removing and
recreating the sandbox after the host-level re-auth is required — an
already-running sandbox does not pick up a newly-set host credential:

```bash
sbx rm --force <old-sandbox-name>
sbx create codex --name <new-sandbox-name> <workspace-path>
```

Verify the new sandbox actually works with a live round-trip, not just a
status check:

```bash
sbx exec <sandbox> -- codex exec "say hello and tell me what model you are"
```

### `sbx create` correct syntax (this is NOT `docker create`-style flags)

```bash
sbx create <agent> --name <sandbox-name> <workspace-path>
```

`<agent>` is a **positional subcommand** (`claude`, `codex`, `gemini`,
`copilot`, `cursor`, `docker-agent`, `droid`, `kiro`, `opencode`, `shell`),
not a `--agent` flag. There is **no** `--image`, `--workspace`, or
`--detached` flag — `sbx create --help` lists the real flags
(`--clone`, `--cpus`, `--memory`, `--name`, `-p/--publish`, `-t/--template`,
etc.). The image is resolved automatically per-agent unless you override it
with `-t/--template`.

### Claude CLI headless auth (works, but no `/login` flow)

Inside a `sbx create claude ...` sandbox, `claude auth login` /
`claude /login` are **not available** in headless/non-TTY mode. The working
path is to export `ANTHROPIC_API_KEY` before invoking `claude`:

```bash
sbx exec <sandbox> -- bash -lc 'ANTHROPIC_API_KEY=<key> claude auth status'
```

Writing to `/etc/environment` fails with `Permission denied` inside the
container (non-root user) — don't attempt it; just pass the env var inline
per-invocation, or export it in the shell session before calling `claude`.
`claude -p "..."` (headless prompt mode) does **not** accept
`--approval-mode`/`--provider`/`--model` the way Hermes CLI does — check
`claude --help` inside the actual sandbox before assuming Hermes-CLI-style
flags carry over; they don't.

### Gemini CLI: no viable headless auth path found

`gemini` (pre-installed via `sbx create gemini ...`) requires a valid
`generativelanguage.googleapis.com` API key. There is no `gemini auth
login` / device-code flow available inside a non-interactive sandbox
session — every attempt returned `API key not valid`. Treat Gemini CLI as
**not currently viable** for headless Docker Sandbox phases until a
working non-interactive Google auth path is confirmed; don't spend more
than one round re-verifying this without new information.

## Core Principles

1. **Filesystem Identity**: The outer host's repo checkout and the sandbox's bind-mount must be identical for agent operations to work correctly
2. **Consistent Invocation**: All supported agents should be able to execute the same slash commands (`/plan-analysis`, `/start-coding`, `/testing`) against the sandboxed Odoo instance
3. **Credential Management**: Handle token expiry, re-auth, and graceful agent switching without losing progress

## Credential Management Patterns

### Handling Expired Tokens

When an agent's credentials expire (common with OAuth-based agents like Codex):

1. **Detect the failure**: Look for 401 Unauthorized errors or explicit "token expired" messages
2. **Verify sandbox health**: Confirm the Docker Sandbox microVM itself is still healthy and running (`sbx list`, `sbx exec <sandbox> -- ...`)
3. **Check alternative agents**: Verify if other agent CLIs are available and authenticated in the sandbox
4. **Switch gracefully**: Move to a proven-working agent (e.g., Hermes CLI via profile) without losing progress
5. **Document the switch**: Record exactly which agent was used for each step in your evidence logs

### Non-Interactive Invocation

To run agent skills without manual interaction:

1. **Prepare input**: Have all required clarification answers ready as text
2. **Pipe via stdin**: Feed answers to the agent command exactly as if typed interactively
3. **Capture output**: Record real stdout/stderr/exit-code for evidence
4. **Verify artifacts**: Check that expected output files (requirements.md, design.md, etc.) were generated
5. **Handle failures**: If the agent still fails, record the exact error - do not fabricate expected output

## Verification Checklist

- [ ] Confirmed filesystem identity between outer host repo and sandbox bind-mount
- [ ] Verified Docker Sandbox microVM is running and healthy
- [ ] Tested agent CLI availability inside sandbox (`sbx exec <sandbox> -- which <agent>`)
- [ ] Documented exactly which agent CLI was used for each workflow step
- [ ] Captured real evidence (output files, logs, timestamps) for each completed step
- [ ] Did not fabricate any evidence or mark incomplete steps as complete
- [ ] Updated progress notes and live-test documentation incrementally

## Common Pitfalls and Solutions

### Pitfall: Assuming agent health from local credential checks
**Problem**: `agent login status` may show "logged in" locally while upstream tokens are expired
**Solution**: Always test with a real command invocation; local status checks don't catch upstream token expiry

### Pitfall: Losing progress when switching agents
**Problem**: Context not properly handed off between agent switches
**Solution**: Use the episodic context files (CLAUDE.md, GEMINI.md, AGENTS.md) written by the context handoff guard to maintain state across agent switches

### Pitfall: Misattributing where agent execution occurs
**Problem**: Unclear whether agent ran inside sandbox VM or on outer host
**Solution**: Always be explicit in evidence about where the agent process executed (inner VM vs outer host) and verify filesystem identity when claiming inner-VM execution

### Pitfall: Treating one-off workarounds as reusable patterns
**Problem**: Documenting credential-specific fixes as general workflows
**Solution**: Focus on the adapter pattern itself (ability to switch agents) rather than specific credential refresh procedures

### Pitfall: Leaving the migrated module inside the pipeline/tooling repo
**Problem**: Codex/agent output for `/start-coding` lands wherever the sandbox
workspace happens to bind-mount — for Docker Sandbox Phase 8 that is
`odoo-agent-pro-kit` (the pipeline tooling repo), not the actual VPCSCloud
Apps Store module repo (`vpcs_apps_cloud_18`, `vpcs_apps_cloud_19`, etc.).
If left as-is, the finished module gets committed into the wrong repository.
**Solution**: After a module is implemented and tested inside the sandbox,
sync the generated module directory back out to the canonical module-store
repo (`vpcs_apps_cloud_<version>/<module>/`) on the correct version branch,
merge any pre-existing commercial manifest fields (`images`, `website`,
`price`, `currency`, `application`) that a from-scratch agent regeneration
will otherwise drop, then remove the staging copy from the pipeline repo
before committing there. Only pipeline evidence/docs/skills belong in
`odoo-agent-pro-kit`; the module itself belongs in the module-store repo.

### Pitfall: `sandboxctl create` "session already exists" with a corrupted session
**Problem**: After recreating the outer `sbx` sandbox (e.g. to pick up a new
OAuth credential), an inner Compose session directory
(`.sandbox/sessions/<session>/`) can be left as an empty scaffold (missing
`session.json`) from the old sandbox lifecycle. `sandboxctl create` then
fails with `session already exists`, and `sandboxctl status`/`destroy` both
crash with `FileNotFoundError: session.json`.
**Solution**: `rm -rf .sandbox/sessions/<session>/` to fully clear the stale
scaffold, then re-run `sandboxctl create --version <v> --module
sandbox_fixture --session <session>`. This is safe — it only recreates the
inner Compose stack, not the outer sandbox or the bind-mounted repo.

### Pitfall: Confusing "you are inside the target host" with "SSH elsewhere"
**Problem**: An agent running inside the Docker Sandbox microVM may read
stale `SESSION_CONTEXT.md` instructions telling it to SSH to the
"validation host" — but the sandbox already *is* running on that host. This
caused a real false blocker where Codex looked for a local-Mac-only
credential file (`.sandbox/validation-host.env`) that is correctly absent
inside the sandbox, and refused to implement the module.
**Solution**: When prompting an agent that will execute *inside* the
sandbox, explicitly state "you are already running inside the target
environment; do not SSH anywhere; implement directly in this filesystem."

## References

- Docker Sandbox Phase 8 specification: `docs/docker-sandbox/tasks.md` (Phase 8 section)
- Context handoff workflow: `plugin/context_guard.py` and `context_handoff_workflow.md`
- Agent CLI adapter pattern demonstrated in Phase 4: `docs/docker-sandbox/phase-4/`
- Hermes profile activation: `source /home/ubuntu/.hermes/hermes-agent/venv/bin/activate`