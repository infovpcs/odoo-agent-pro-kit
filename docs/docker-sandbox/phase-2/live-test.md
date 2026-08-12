# Odoo 17/18/19 matrix LIVE TEST

Phase 2 generalizes the Phase 1 controller through
`sandbox/config/versions.yaml`. Odoo 17 and 18 use the documented XML-RPC
`common` and `object` endpoints. Odoo 19 uses the documented JSON-2 endpoint
with a short-lived session API key rather than the Phase 1 version-info probe.

## Commands

On the Intel macOS workstation:

```bash
./scripts/validate.sh
SANDBOX_MATRIX_RUN_ID=local2 sandbox/tests/lifecycle.sh
sandbox/tests/multiarch-build.sh
```

On the designated Ubuntu 24.04 KVM host:

```bash
sbx create --clone --no-share-skills --cpus 2 --memory 8g \
  --name odoo-phase2-codex codex /home/ubuntu/phase2-src
sbx exec odoo-phase2-codex -- bash -lc \
  'cd /home/ubuntu/phase2-src && SANDBOX_MATRIX_RUN_ID=kvm sandbox/tests/lifecycle.sh'
sbx exec odoo-phase2-codex -- bash -lc \
  'test -z "$(docker ps -a --filter name=fixture-kvm --format {{.Names}})" && test -z "$(docker volume ls --filter name=fixture-kvm --format {{.Name}})"'
sbx rm --force odoo-phase2-codex
sbx ls
```

## Evidence

- Repository validation passed on 2026-08-12: 20 tests, 18 skills, shell and
  Python syntax, and Git whitespace.
- Docker 29.7.2 and Compose 5.3.1 on the Intel workstation passed one complete
  warm-cache concurrent amd64 lifecycle. An earlier run exposed and then
  confirmed the fix for Odoo 19 JSON-2 `create` returning a list of IDs.
- A temporary Docker-container BuildKit builder built all three dev images as
  OCI output for both `linux/amd64` and `linux/arm64`. Registry inspection also
  confirmed both platforms in every pinned upstream index. The temporary
  builder and OCI output were removed by the test trap.
- The required LIVE TEST passed inside `docker-sbx` 0.38.0 on the Ubuntu 24.04
  x86_64 KVM host. The 2-vCPU, 8-GiB microVM ran Docker 29.7.1 and Compose
  5.4.0. Odoo 17, 18, and 19 ran concurrently against PostgreSQL 15; each
  completed fixture install, data-changing update, protocol CRUD, stop/start,
  export, destroy, and orphan-volume checks.
- The observed server series were `17.0-20260810`, `18.0-20260810`, and `19.0`.
  Odoo 17/18 reported `xmlrpc`; Odoo 19 reported `json2`.
- Final inner container and volume queries were empty. The outer Sandbox was
  removed, `sbx ls` reported no sandboxes, and the host returned to 5.9 GiB
  used with 39 GiB available.

The amd64 runtime matrix is validated on the designated KVM host. Arm64 runtime
is not claimed because no supported arm64 Sandbox host is available; arm64
image construction and pinned upstream availability are validated.

## Protocol references

- [Odoo 17 external API](https://www.odoo.com/documentation/17.0/developer/reference/external_api.html)
- [Odoo 18 external API](https://www.odoo.com/documentation/18.0/developer/reference/external_api.html)
- [Odoo 19 external JSON-2 API](https://www.odoo.com/documentation/19.0/developer/reference/external_api.html)
