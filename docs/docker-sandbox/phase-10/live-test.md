# Phase 10 LIVE TEST — Odoo 20.0 sandbox runtime

Status: **in progress.** The runtime, the requirements/import support, and `/fleet --cloud` are
implemented and pass their LIVE TESTs (commit `595c2ca`). The 19→20 custom-app migration run and
the Phase 9 carry-over agent items are **open**. They are blocked on an owner action (see
[Open items](#open-items)). Nothing below is claimed beyond what was run.

## Image design

Docker Hub had no `odoo:20.0` tag on 2026-09-27. `odoo/docker` published `20.0/` on 2026-09-26
(commit `d54316042067`). `sandbox/images/odoo-dev/20.Dockerfile` reproduces that recipe on
`ODOO_20_BASE`, a pinned `ubuntu:noble@sha256:008173c2…` digest:

- Odoo nightly deb `20260926`, sha1 `7cb4a582…`.
- wkhtmltopdf 0.12.6.1-3 (patched Qt), sha1 pinned per architecture.
- pgdg `postgresql-client`.
- `entrypoint.sh`, `odoo.conf` and `wait-for-psql.py` from that commit via `ADD --checksum=sha256:…`.
- Then the same dev layer as 17/18/19.

One deviation from upstream: the pgdg key is fetched with `curl` over HTTPS and must match
fingerprint `B97B0AFCAA1A47F044F244A07FCC7D46ACCC4CF8` (finding 4 below).

Resulting image: Odoo `20.0-20260926`, Python 3.12.3, wkhtmltopdf `0.12.6.1 (with patched qt)`,
psql 18.6 client, about 2.3 GB. Odoo 20 needs PostgreSQL ≥ 16 (`MIN_PG_VERSION`), so 20 runs on
`POSTGRES_16` = `postgres:16-bookworm@sha256:efedf359…`. 17/18/19 stay on PostgreSQL 15. When Hub
publishes `odoo:20.0`, pin that digest, cut the Dockerfile down to the dev layer, and update
`tests/test_phase10_odoo20_sandbox.py`, which pins the current recipe.

## Odoo 20 findings

Each was fixed test-first (RED → GREEN):

1. `ir.config_parameter.set_param` is gone (typed `set_str` / `get_str` …). `create` crashed in the
   credential script. It now uses `set_str` when present, else `set_param`; so does the PDF script.
2. Odoo 20 defaults `http_interface` to `127.0.0.1`. The MCP sidecar and the run-mode probes
   could not reach `odoo:8069`, while the in-container healthcheck passed.
   `odoo.conf.template` sets `http_interface = 0.0.0.0`, the 17–19 default.
3. `ir.model.access` was replaced by `ir.access`. The fixture gets `fixtures/_overlays/20/`.
4. Inside `sbx` microVMs, build containers reach the network only through transparent 80/443
   interception. `gpg --recv-keys` (dirmngr, hkp 11371 and hkps) fails, while `curl` over
   HTTPS works. Fix: pgdg key over HTTPS plus a fingerprint check.
5. A microVM created with plain `sbx create` (no kit) is default-deny for pgdg, the keyserver and
   `nightly.odoo.com`. Odoo 20 microVMs must be created with `sandbox/bin/sandbox-agent create`.
   Kit 0.6.0 added the Odoo 20 build egress.

## Evidence

### Local exec mode — macOS 15 (Intel), Docker Desktop 29.8.0

- `sandbox/tests/ci-smoke.sh 20`: rc 0, 83 s.
- `SANDBOX_MATRIX_RUN_ID=p10all sandbox/tests/lifecycle.sh` (17/18/19/20 concurrent): rc 0,
  225 s.
  - CRUD: `xmlrpc` on 17.0-20260810 / 18.0-20260810, `json2` on 19.0 / 20.0.
  - PDF `base.ir_module_reference_print`: 266 / 262 / 287 / 298 KB.
  - No leftover containers or volumes.
- MCP sidecar on a 20 session: `protocol=json-2`, `search('sandbox.fixture')` → `[1]`, SSE 200
  on port 8768.

### KVM validation host — Ubuntu 24.04, `sbx` 0.38.0

- Kit-backed microVM `odoo-phase10-kit` (2 vCPU / 8 GiB, Docker 29.7.2, Compose 5.5.0):
  `ci-smoke.sh 20` rc 0 in 425 s, including the first image build.
- Earlier attempts failed on a kit-less VM, then on `gpg` (findings 4 and 5). Their logs were
  kept on the host.
- `lifecycle.sh` 20 was **not** run on KVM because of host disk: one Odoo 20 microVM needs
  about 10 GB, and 8.6 GB is free. The owner moved it to Docker Cloud Sandboxes (below).
- Repository suite on the host: 364 passed; `validate.sh` green, including `sbx kit validate`
  and `pack` for kit 0.6.0.

### Docker Cloud Sandboxes — client `sbx-cloud:0.45.1` on Intel macOS, owner-approved spend

Setup: one large sandbox (`--cpus 8 --memory 16g --platform linux/amd64 --ttl 90m --kit
sandbox/kits/odoo-mixin`), 14:44:09–15:16:40 UTC on 2026-09-27. Afterwards `ls` → "No
sandboxes found."

- `SANDBOX_EXEC_MODE=run SANDBOX_LIFECYCLE_VERSIONS=20 lifecycle.sh`: rc 0, 278 s, including the
  cold 20 image build. No egress denials.
- `phase9-cloud-acceptance.sh`, extended to 20 (warm create 19 and 20; eight concurrent
  sessions, two per version): all 16 steps PASS, rc 0, 439 s.
  - Warm create-to-ready: 19 took 23.0 s, 20 took 22.6 s.
  - Eight concurrent sessions: 40.5 s, 1.67 GB used of 16.8 GB.
  - Phase 6 recovery: 70.7 s.
  - Denied network: `curl https://example.com` → `http_code=000` (blocked).

### Module requirements and real-module import

`sandboxctl create --import DIR --requirements FILE` (design in `sandbox/README.md`). Two pip
approaches failed live before the final design:

- `pip install --break-system-packages` failed: Debian's `typing_extensions` has no `RECORD`.
- `--ignore-installed` replaced Debian's `cryptography` and broke pyOpenSSL. `base` failed to
  load (`GEN_EMAIL`).

Final design: a `--system-site-packages` venv using the image's own pip (`--without-pip`), put
first with `PYTHONPATH`. Only missing or too-old packages are overlaid. The build imports
`odoo.addons.base.models` and fails fast. It works on 18/19/20. On 17, the LLM requirements
upgrade `cryptography`, which conflicts with 17's Debian stack, so the build fails fast there.

LIVE on macOS: a 19 session with `--import` of the real `vpcs_llm_provider` and
`vpcs_progressive_payment_terms`, plus `--requirements vpcs_llm_provider/requirements.txt`.
Create took 73 s and the install succeeded. The **19 test baseline was reproduced**:

- `vpcs_llm_provider`: 2 failed + 2 errors of 8.
- `vpcs_progressive_payment_terms`: 1 failed + 14 errors of 26.

That is 3F/16E of 34, the same as the 2026-09-24 baseline on the validation host.

### `/fleet` in cloud

`sandbox-fleet create --cloud` is internal-only by owner decision: no `sbx ports`. The code goes
in as a git bundle of a working-tree snapshot. Run on 2026-09-27 with `SANDBOX_SBX` = the Intel
wrapper:

- Sessions 20/19/18 in parallel on `codex-docker` medium. Creates rc 0 at 15:47:00, 15:47:01 and
  15:51:27 (20 builds the image).
- `run … test sandbox_fixture`: rc 0 for all three at 15:52:00.
- `sbx --cloud ports`: "No exposed ports" for each.
- `sandbox-fleet destroy --force`: rc 0 × 3 (15:52:21–15:53:13).

## Open items

| Item | State | Needed |
|------|-------|--------|
| 19→20 migration of `vpcs_llm_provider` + `vpcs_progressive_payment_terms` in a sandbox; Phase-7 acceptance for 20 | not run | Pass = both install on 20 and no test failure absent from the 19 baseline above |
| Acceptance step 7: agent CLIs in cloud | **blocked** 2026-09-27 | Claude Code 2.1.280: every call `400 … not scoped to a workspace` — **owner** replaces the cloud `anthropic` secret with a workspace-scoped key. Codex 0.157.1: `CONNECT api.openai.com 403` in a `claude` template — rerun in a `codex` template |
| `/plan-analysis` → `/start-coding` → `/testing` with hooks in a cloud sandbox, driving the migration | blocked by the step above | same |
| Private-repo clone over HTTPS with the cloud `github` secret | unproven | public `git clone` works (2026-09-27) |

Evidence files (gitignored): `.sandbox/phase10-cloud/.sandbox/release/phase9/` (cloud acceptance)
and `.sandbox/phase10-cloud/run2/r2.log` (agent CLI run).
