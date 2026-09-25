# Phase 9 Docker Cloud Sandbox runbook

Docker Cloud Sandboxes run the same microVM isolation on Docker-managed compute
(`sbx --cloud`). They need no local KVM, so any workstation with Docker can drive
them. This runbook covers the Odoo 17/18/19 runtime in cloud; the local KVM
runbook in `../phase-7/operator-runbooks.md` is unchanged.

Cloud runs are billed per sandbox lifetime. Every run needs owner approval of
the spend, and every sandbox must be removed when the run ends.

## Version contract

`sandbox/config/artifacts.lock` pins two `sbx` ranges:

| Key | Range | Used for |
|-----|-------|----------|
| `sbx_version` | `0.38.x` | local KVM microVMs (`sandbox/bin/sandbox-agent`, Phases 0–8 evidence) |
| `sbx_cloud_version` | `0.45.x` | `sbx --cloud` (cloud mode needs ≥ 0.45.1; validated with 0.45.1) |

A new minor version of either needs a fresh capability review and acceptance run.
`release-acceptance.py compare` reports changes to both keys.

## Client

On Apple Silicon macOS or Linux, install `sbx` 0.45.1+ through Docker's supported
channel and run `sbx --cloud …` directly.

On Intel macOS the `sbx` cask and every macOS release binary are arm64-only. Run
the official linux/amd64 client in a local container instead:

1. Download the linux amd64 tarball of the pinned release from
   `github.com/docker/sbx-releases` and verify its sha256 against the release's
   SLSA provenance before using it.
2. Build a local image (not published anywhere):

   ```dockerfile
   FROM ubuntu:24.04
   RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates git openssh-client \
       && rm -rf /var/lib/apt/lists/*
   COPY x/docker-sbx /opt/docker-sbx
   ENV HOME=/home/sbx PATH=/opt/docker-sbx:$PATH
   WORKDIR /work
   ENTRYPOINT ["sbx"]
   ```

   ```bash
   docker build --platform linux/amd64 -t sbx-cloud:0.45.1 .
   ```

3. Log in once with the device flow. It needs a real terminal (TTY); auth state
   lives in the `sbx_cloud_home` volume:

   ```bash
   docker run -it --rm --platform linux/amd64 -v sbx_cloud_home:/home/sbx sbx-cloud:0.45.1 login
   ```

Helper used in the rest of this runbook (bash; zsh does not word-split a command
held in a variable, so use a function):

```bash
SBX() { docker run --rm --platform linux/amd64 -v sbx_cloud_home:/home/sbx \
          -v "$PWD":/work -w /work sbx-cloud:0.45.1 --cloud "$@"; }
```

## Run the lifecycle in a cloud sandbox

1. Create the sandbox with the kit (default network policy is deny-all plus the
   mixin allowlist). Sizes are billable shapes: `medium` = `--cpus 4 --memory 8g`,
   `large` = `--cpus 8 --memory 16g`. Always set a TTL.

   ```bash
   SBX create --name kit-matrix --cpus 8 --memory 16g --platform linux/amd64 \
       --ttl 60m --kit sandbox/kits/odoo-mixin shell
   ```

2. Ship the code. No workspace follows a cloud sandbox, and cloning GitHub needs
   a cloud GitHub credential (`sbx --cloud secret`, owner action). Without one,
   copy an archive. Use `git archive <commit>` for a committed tree, or this for
   a working tree with uncommitted changes:

   ```bash
   git ls-files -co --exclude-standard -z | COPYFILE_DISABLE=1 tar --null -T - -czf kit.tgz
   SBX cp kit.tgz kit-matrix:/tmp/kit.tgz
   SBX exec kit-matrix bash -c 'mkdir -p ~/kit && tar -xzf /tmp/kit.tgz -C ~/kit'
   ```

3. Launch detached. A background job started with a plain `&` through
   `sbx --cloud exec` is killed when the exec stream closes ("interact stream
   closed before the process exited"). Put the run in a script, copy it in, and
   start it with `setsid nohup`:

   ```bash
   cat > run.sh <<'EOF'
   cd ~/kit
   date -u +%s > /tmp/life.start
   SANDBOX_EXEC_MODE=run SANDBOX_MATRIX_RUN_ID=cloud bash sandbox/tests/lifecycle.sh > /tmp/life.log 2>&1
   echo "EXIT=$? END=$(date -u +%s)" >> /tmp/life.log
   EOF
   SBX cp run.sh kit-matrix:/tmp/run.sh
   SBX exec kit-matrix bash -c 'setsid nohup bash /tmp/run.sh </dev/null >/dev/null 2>&1 &'
   ```

   `SANDBOX_LIFECYCLE_VERSIONS=19` limits the run to one version.

4. Poll `/tmp/life.log` for the `EXIT=` line, then read the result lines
   (`crud: passed` per version and the final `OK:`).

5. Remove the sandbox and prove nothing is left:

   ```bash
   SBX rm --force kit-matrix     # --force is required without a TTY
   SBX ls                        # expect "No sandboxes found."
   ```

Record the sandbox id, shape, create/remove times (UTC), exact command, exit
code, wall-clock, and per-version result in `SESSION_CONTEXT.md`. `sbx` does not
report cost; record the sandbox lifetime and shape.

## Run mode (`SANDBOX_EXEC_MODE=run`)

Inside a cloud sandbox, `docker exec` into a running container reaches neither
the container nor the VM filesystem, so exec-based health checks never pass.
`sandboxctl create` records `SANDBOX_EXEC_MODE` in the session's `runtime.env`;
with `run`:

- every `compose exec` becomes a one-shot `compose run --rm --no-deps`
  (Odoo targets get `ODOO_URL=http://odoo:8069`);
- `up --wait` / `start` become sequential `up -d --no-deps db`, then `odoo`, with
  readiness probed over the Compose network from one-shot containers
  (`pg_isready -h db`, `GET /web/health`);
- backup and restore use a one-shot `pg_dump` / `pg_restore -h db` client with
  the password only in the environment;
- `sandboxctl status` reports `Health` from those probes and keeps Docker's own
  value as `DockerHealth`;
- `manage_modules.sh`, `sandbox/tests/lifecycle.sh`, and `sandbox/tests/phase6-proof.sh`
  follow the same rules.

The default `exec` mode is unchanged for local KVM sessions.

## Known limits

- The mixin allowlist must include `production.cloudfront.docker.com` (Docker
  Hub blob host); kit 0.5.2 has it.
- GitHub: with a valid cloud `github` secret the proxy authenticates `api.github.com`
  calls, but git over HTTPS still fails (`could not read Username`, or `invalid credentials`
  with a `$GH_TOKEN` credential helper; 2026-09-25). Ship code with tar + `sbx --cloud cp`
  until a supported git path is confirmed.
- `sbx --cloud exec` rejects `-d`, `--user`, and `--privileged`.

## Evidence (2026-09-25, client `sbx-cloud:0.45.1` on Intel macOS)

| Run | Shape | Sandbox lifetime | Result |
|-----|-------|------------------|--------|
| `sandboxctl` create/install/test/backup/restore/stop/start/export/destroy, Odoo 19 | medium | 11:32–11:36 UTC | PASS |
| `lifecycle.sh`, Odoo 19, run mode | medium | 13:51–13:55 UTC | PASS, 42 s (image cached) |
| `lifecycle.sh`, Odoo 17/18/19 concurrent, run mode | large | 13:58–14:02 UTC | PASS, 117 s cold |
| `phase9-cloud-acceptance.sh` (Phase 7 steps 1–6, 8) | large | 14:13–14:22 UTC | PASS (step 5 after a driver fix) |

Acceptance timings: cold 17/18/19 lifecycle 115.6 s, warm 47.6 s, warm Odoo 19
create-to-ready 22.6 s, six concurrent sessions 33.0 s (1.39 GB used of 16.8 GB),
Phase 6 recovery 65.8 s. Step 7 (agent CLIs and SSH) is not yet run in cloud.

## Acceptance driver

`sandbox/tests/phase9-cloud-acceptance.sh` runs Phase 7 steps 1–6 and 8 in one
sandbox with `SANDBOX_EXEC_MODE=run`, writes evidence to
`.sandbox/release/phase9/` (`steps.txt`, `benchmarks.jsonl`, platform and
resource snapshots, denied-network and final-state records), and continues past
a failed step so one billed run gives the whole matrix. Launch it with the
detached pattern above. Denied network is proven by a real blocked egress
from inside the sandbox (`curl https://example.com` → proxy `403`) instead of the
host-side `sbx policy check` used on the KVM host. A cross-session restore must first copy the backup
into the target session's `backups/` directory; `sandboxctl restore` rejects
another session's artifacts by design.
