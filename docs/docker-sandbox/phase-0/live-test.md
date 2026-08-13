# Stock Sandbox Live Test

Run this on the designated Ubuntu 24.04-or-later host with KVM. The available
Intel macOS workstation runs repository, Docker, and registry checks but cannot
run Docker's Apple-Silicon-only Sandbox package. Set `SBX_NO_TELEMETRY=1` if
telemetry is not desired. Do not put provider tokens in shell history or
repository files.

## Preflight and capability capture

```bash
sbx version
sbx login
sbx diagnose --output json
sbx template --help
sbx kit --help
sbx secret --help
sbx policy --help
sbx ports --help
sbx skills --help
sbx setup ssh --help
```

Record sanitized output, OS, architecture, and whether each command is stable,
experimental, unavailable, or subscription-gated.

## Lifecycle

Use a disposable Git repository with no secrets or user work. The test creates a
stock Codex sandbox in clone mode, confirms the private inner Docker daemon,
runs an nginx Compose service, publishes an ephemeral host port, verifies HTTP,
tests persistence over stop/start, copies the evidence out, and removes the
sandbox.

```bash
DOCKER_SANDBOXES_ROOT_SIZE=12G sbx create --clone --no-share-skills --cpus 1 --memory 4g --name odoo-phase0-codex codex /path/to/disposable-repo
sbx exec odoo-phase0-codex -- docker version
sbx exec odoo-phase0-codex -- docker compose version
sbx exec odoo-phase0-codex -- bash -lc 'mkdir -p /tmp/phase0 && cd /tmp/phase0 && printf "%s\n" "services:" "  web:" "    image: nginx:alpine" "    restart: unless-stopped" "    ports:" "      - 8080:80" > compose.yaml && docker compose up -d && curl --fail --retry 20 --retry-all-errors --retry-delay 2 http://localhost:8080'
sbx ports odoo-phase0-codex --publish 8080
sbx ports odoo-phase0-codex
sbx stop odoo-phase0-codex
sbx exec odoo-phase0-codex -- bash -lc 'test -f /tmp/phase0/compose.yaml && docker image inspect nginx:alpine >/dev/null && docker compose -f /tmp/phase0/compose.yaml up -d && docker compose -f /tmp/phase0/compose.yaml ps'
sbx exec odoo-phase0-codex -- bash -lc 'uname -a > /tmp/phase0/evidence.txt && docker version >> /tmp/phase0/evidence.txt && docker compose -f /tmp/phase0/compose.yaml ps >> /tmp/phase0/evidence.txt'
sbx cp odoo-phase0-codex:/tmp/phase0/evidence.txt ./phase0-evidence.txt
sbx rm --force odoo-phase0-codex
sbx ls
```

Before removal, confirm the evidence copy exists. After removal, confirm the
sandbox is absent and no published mapping remains. Redact usernames, workspace
paths, tokens, and organization identifiers before committing evidence.

## Current result

Ubuntu result on 2026-08-12: passed using `sbx` 0.38.0 on an Ubuntu 24.04
Oracle Cloud x86_64 VM with nested KVM. The run verified Docker 29.7.1 and
Compose 5.4.0 inside the sandbox, nginx HTTP through an ephemeral loopback port,
state across stop/start, evidence copy, removal, and port cleanup. Disk usage was
5.9 GiB of 45 GiB after cleanup.

macOS result: repository validation, Docker 29.7.2 daemon checks, and Odoo and
PostgreSQL registry manifest checks passed. The official Homebrew cask does not
support this Intel Mac, so no native macOS Sandbox support is claimed.
