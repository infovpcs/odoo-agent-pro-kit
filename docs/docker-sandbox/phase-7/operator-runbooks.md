# Phase 7 operator runbooks

These runbooks configure the validated controller contract. Commands are run
from a clean clone. Do not place registry, OAuth, database, or SSH credentials
in repository `.env` files.

## Common preflight

Required: Git, Python 3.11+, Docker Engine 27+, Compose v2/5 compatibility,
and enough resources for the selected concurrency policy. Verify with:

```bash
git status --short
docker version
docker compose version
./scripts/validate.sh
python3 sandbox/scripts/release-acceptance.py verify
sandbox/scripts/validate-compose.sh
```

The released Sandbox integration is pinned to `sbx` 0.38.x and must pass
`sandbox/bin/sandbox-agent preflight`. A newer minor version requires a fresh
capability and acceptance review.

## Ubuntu 24.04+ KVM — validated runtime target

Use x86_64 or arm64 with `/dev/kvm`, Docker, and a user permitted to use KVM.
Install `docker-sbx` through Docker's supported channel, authenticate using the
device flow, initialize the balanced policy, and run the acceptance procedure
in `release-acceptance.md`. The designated x86_64 host is the authoritative
microVM/runtime validation target.

## macOS Apple Silicon — runbook, runtime not yet claimed

Install current Docker Desktop and the supported Docker Sandbox cask. Confirm
`uname -m` reports `arm64`, Docker Desktop is healthy, and `sbx version` is in
the pinned range. Run repository validation, preflight, an arm64 image build,
and the complete release matrix. Record Docker Desktop, macOS, `sbx`, inner
Docker, and Compose versions. Until this clean-host matrix passes, the runbook
is published but native macOS Sandbox support is not claimed.
Community testers should submit results using
`../community-platform-validation.md`, including clean-host and cleanup evidence.

## macOS Intel — repository/daemon validation only

The official Sandbox cask used in this project rejects Intel macOS. Run static
validation, Docker daemon checks, amd64 image/Compose checks, and registry
manifest checks here; run Sandbox microVM tests on the Ubuntu KVM host.

## Windows 11 — runbook, runtime not yet claimed

Enable virtualization, WSL2, and Docker Desktop's WSL2 backend. Clone inside
the WSL ext4 filesystem to avoid permission and bind-mount drift. From Ubuntu
24.04 under WSL run common preflight and `sandbox-agent preflight`. Execute the
complete release matrix only if the pinned `sbx` build supports the platform;
otherwise record the capability failure and use the Ubuntu KVM host. Native
PowerShell paths and NTFS workspaces are compatibility surfaces, not validated
runtime targets, until the clean-host matrix passes.
Community testers should submit results using
`../community-platform-validation.md`; WSL and native Windows behavior must be
identified separately.

## Cleanup

Export or commit useful source first. Destroy sessions through the controller,
confirm no matching outer Sandbox, inner container, volume, network, or
published port remains, and preserve redacted acceptance evidence.
