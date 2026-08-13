# Odoo 19 runtime LIVE TEST

Run this on the designated Ubuntu 24.04+ KVM host inside a stock Codex Docker
Sandbox. The repository must be the Phase 1 revision under test. Do not copy
`.sandbox/` credentials into evidence.

```bash
sbx version
sbx create --clone --no-share-skills --cpus 2 --memory 4g \
  --name odoo-phase1-codex codex /path/to/odoo-agent-pro-kit
sbx exec odoo-phase1-codex -- bash -lc \
  'cd /workspace/odoo-agent-pro-kit && env -i PATH="$PATH" HOME="$HOME" /bin/bash --noprofile --norc ./scripts/validate.sh'
sbx exec odoo-phase1-codex -- bash -lc \
  'cd /workspace/odoo-agent-pro-kit && SANDBOX_LIFECYCLE_RUNS=4 sandbox/tests/lifecycle.sh'
sbx exec odoo-phase1-codex -- bash -lc \
  'docker volume ls --filter name=19-fixture-live --format "{{.Name}}"; docker ps -a --filter name=19-fixture-live --format "{{.Names}}"'
sbx rm --force odoo-phase1-codex
sbx ls
```

Runs 1 and 2 are clean-state runs because each session receives new database,
filestore, and cache volumes. Runs 3 and 4 reuse the locally cached images.
Every run installs and updates `sandbox_fixture`, checks Odoo 19 through its
JSON-RPC version endpoint, restarts the full stack, exports state, destroys the
Compose project, and asserts that no session volumes remain.

## Evidence

- Intel macOS workstation, 2026-08-12: Docker 29.7.2, Compose 5.3.1, Linux
  amd64 daemon. One disposable local lifecycle run passed. This is an
  implementation check and is not the Phase 1 exit gate.
- Ubuntu Docker Sandbox run, 2026-08-12: passed four runs using `sbx` 0.38.0,
  Ubuntu 24.04 x86_64, a 2-vCPU/6-GiB Codex microVM, Docker 29.7.1, and Compose
  5.4.0. Runs 1-2 used clean session volumes and runs 3-4 used the warm image
  cache. Every run passed base initialization, fixture install/update, Odoo 19
  JSON-RPC version verification, stop/start persistence, export, destroy, and
  orphan-volume checks. The final run also verified writable Odoo file logs.
- After the test, no matching containers or volumes remained, `sbx rm --force`
  succeeded, and `sbx ls` reported no sandboxes.
- The stock Codex template lacks pytest, so an attempted repository validation
  inside the microVM stopped at `/usr/bin/python3: No module named pytest`.
  Repository validation is assigned to the Intel workstation by the approved
  platform policy and passed there; no package was installed into the template.
