# Docker Sandbox CLI Capability Matrix

## Version policy

The implementation target is `sbx` 0.38.x. No broader version range is
supported. Patch upgrades require the same
capability probe and stock live test; minor upgrades require design review
because kits, policy, SSH, skills, and port behavior are evolving.

## Validated 0.38.0 contract

| Area | Command | Stability/status |
| --- | --- | --- |
| Version | `sbx version` | stable |
| Diagnostics | `sbx diagnose --output json` | stable |
| Lifecycle | `create`, `run`, `ls`, `exec`, `stop`, `rm`, `cp` | stable |
| Clone workspace | `create --clone` | stable; host ref copied, no branch created |
| Templates | `sbx template` | stable command group |
| Kits | `sbx kit` | experimental; capability-check every operation |
| Secrets | `sbx secret` | stable; credential values remain outside VM |
| Policy | `sbx policy` | stable command group; governance features may be paid |
| Ports | `sbx ports` and create/run `--publish` | stable; loopback and ephemeral allocation verified |
| Shared skills | `sbx skills import` | experimental in 0.38.0 |
| SSH | `sbx setup ssh`, then `<name>.sbx` | experimental in 0.38.0 |

Ubuntu validation host: Ubuntu 24.04 x86_64 on Oracle Cloud, kernel
6.17.0-1018-oracle, nested `kvm_intel`, 2 vCPU, 15 GiB RAM. Official apt package
`docker-sbx` 0.38.0 was installed and both CLI and daemon reported commit
`c022b14634c4bea846ca12870d1d5e97d5868b54`. After Docker OAuth login,
`sbx diagnose --output json` passed all nine checks with no warnings, failures,
or skips.

Help probes verified `template`, `kit`, `secret`, `policy`, `ports`, `skills`,
and `setup ssh`. Kits, shared skills, and SSH explicitly identify themselves as
experimental. `secret set-custom` is also experimental. The balanced local
policy was initialized before sandbox creation. No organization governance
profile was configured or required.

## Platform evidence

Host: macOS 15.7.9, Darwin x86_64, Docker client/server 29.7.2 with a Linux
amd64 daemon.

Official install attempt:

```text
brew trust docker/tap
brew install docker/tap/sbx
Error: sbx: This cask depends on hardware architecture being arm64,
but you are running intel 64-bit.
```

The cask therefore did not install, `sbx version`, login, diagnostics, command
help probes, and stock-sandbox lifecycle could not run on this host. Docker's
current macOS package is Apple-Silicon-only. Do not substitute an unverified
binary or attempt nested virtualization inside an ordinary Docker container.

Validation policy:

1. The available Intel macOS workstation runs repository validation, Docker
   daemon checks, and registry manifest checks. It cannot run the current
   Apple-Silicon-only `sbx` cask and does not claim native macOS Sandbox support.
2. The designated Ubuntu 24.04 KVM host runs all `sbx` capability and microVM
   LIVE TESTS. Ubuntu amd64 passed with `sbx` 0.38.0.

An accessible VPS was also preflighted on 2026-08-12. It runs Ubuntu 20.04
x86_64 and has no `/dev/kvm`. Docker requires Ubuntu 24.04 or later and states
that `sbx` will not start without KVM, including nested virtualization when the
host is itself a VM. The VPS is therefore not a supported live-test host. No
Sandbox package was installed there and its existing Docker workloads were not
changed.

## Sources

- [Docker Sandboxes installation](https://docs.docker.com/ai/sandboxes/)
- [Docker Sandboxes prerequisites](https://docs.docker.com/ai/sandboxes/get-started/)
- [CLI reference](https://docs.docker.com/reference/cli/sbx/)
- [Docker Sandboxes 0.37.0 release notes](https://docs.docker.com/ai/sandboxes/release-notes/)
- [Usage and clone-mode behavior](https://docs.docker.com/ai/sandboxes/usage/)
- [Kits](https://docs.docker.com/ai/sandboxes/customize/kits/)
