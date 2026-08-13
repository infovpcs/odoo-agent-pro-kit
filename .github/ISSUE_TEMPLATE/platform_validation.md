---
name: Docker Sandbox platform validation
about: Report Apple Silicon macOS, Windows 11, or another candidate-platform test
title: "[Platform validation]: "
labels: "platform-validation"
assignees: ""
---

## Platform

- OS and exact version:
- Architecture:
- CPU/RAM/free disk:
- Virtualization backend (KVM, Apple Virtualization, WSL2, etc.):
- Docker Desktop/Engine version:
- Docker Compose version:
- `sbx version`:
- Agent/template and kit version:
- Odoo version(s):

## Test scope

- [ ] Clean clone and common preflight
- [ ] `./scripts/validate.sh`
- [ ] `sandbox/bin/sandbox-agent preflight`
- [ ] Odoo image build
- [ ] Create-to-ready lifecycle
- [ ] Module install/update/test
- [ ] RPC/API CRUD
- [ ] Stop/start and persistence
- [ ] Export and cleanup
- [ ] Failure recovery
- [ ] No orphaned sandbox/container/volume/network/port

## Commands and results

Paste exact commands and concise output. Remove tokens, passwords, private
repository URLs, customer data, and licensed Enterprise source.

## Expected and actual behavior

Describe what passed or failed, including bounded timeout and exit code.

## Evidence

Attach redacted logs, diagnostics, timings, screenshots, or a link to a branch.
Do not attach `.env`, private keys, databases, filestores, or Enterprise addons.

## Proposed classification

- [ ] Successful validation evidence
- [ ] Documentation/runbook correction
- [ ] Reproducible bug
- [ ] Platform enhancement proposal

